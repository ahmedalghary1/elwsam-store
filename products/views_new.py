"""
REDESIGNED API ENDPOINTS FOR FLEXIBLE VARIANT SYSTEM
====================================================

Endpoints:
1. GET /api/product-config/<id>/ - Returns product configuration
2. GET /api/variant-price/ - Returns price for specific combination
3. GET /api/variant-options/<id>/ - Returns available options based on selection
"""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Exists, OuterRef
from decimal import Decimal

# Import from new models (will need to be replaced in actual implementation)
# For now, using relative imports
from .models import (
    Product, Pattern, Size, Color,
    ProductSize, PatternSize, ProductColor,
    ProductVariant
)


@require_http_methods(["GET"])
def get_product_config(request, product_id):
    """
    GET /api/product-config/<product_id>/
    
    Returns complete product configuration including:
    - Product type (simple, size_based, pattern_based)
    - Available patterns (if any)
    - Available sizes (product-level or pattern-level)
    - Configuration flags
    
    Response Example:
    {
        "success": true,
        "product_id": 1,
        "product_name": "قميص رياضي",
        "configuration_type": "pattern_based",
        "base_price": "299.99",
        "has_patterns": true,
        "has_product_level_sizes": false,
        "requires_size": false,  // At product level
        "patterns": [
            {
                "id": 1,
                "name": "كلاسيك",
                "has_sizes": true,
                "requires_size": true,
                "base_price": "299.99",
                "sizes": [
                    {"id": 1, "name": "S", "price": "299.99", "stock": 10},
                    {"id": 2, "name": "M", "price": "319.99", "stock": 15}
                ]
            },
            {
                "id": 2,
                "name": "رياضي",
                "has_sizes": false,
                "requires_size": false,
                "base_price": "349.99",
                "sizes": []
            }
        ],
        "product_sizes": [],
        "colors": [
            {"id": 1, "name": "أحمر", "code": "#FF0000"},
            {"id": 2, "name": "أزرق", "code": "#0000FF"}
        ]
    }
    """
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Get patterns with their sizes
        patterns_data = []
        if product.has_patterns:
            patterns = Pattern.objects.filter(product=product).prefetch_related(
                'pattern_sizes__size'
            ).order_by('order')
            
            for pattern in patterns:
                pattern_sizes_data = []
                if pattern.has_sizes:
                    pattern_sizes = PatternSize.objects.filter(
                        pattern=pattern
                    ).select_related('size').order_by('order')
                    
                    for ps in pattern_sizes:
                        pattern_sizes_data.append({
                            'id': ps.size.id,
                            'name': ps.size.name,
                            'price': str(ps.price),
                            'stock': ps.stock
                        })
                
                patterns_data.append({
                    'id': pattern.id,
                    'name': pattern.name,
                    'has_sizes': pattern.has_sizes,
                    'requires_size': pattern.requires_size_selection(),
                    'base_price': str(pattern.base_price) if pattern.base_price else None,
                    'sizes': pattern_sizes_data
                })
        
        # Get product-level sizes
        product_sizes_data = []
        if product.has_product_level_sizes:
            product_sizes = ProductSize.objects.filter(
                product=product
            ).select_related('size').order_by('order')
            
            for ps in product_sizes:
                product_sizes_data.append({
                    'id': ps.size.id,
                    'name': ps.size.name,
                    'price': str(ps.price)
                })
        
        # Get colors
        colors_data = []
        product_colors = ProductColor.objects.filter(
            product=product
        ).select_related('color').order_by('order')
        
        for pc in product_colors:
            colors_data.append({
                'id': pc.color.id,
                'name': pc.color.name,
                'code': pc.color.code or '#CCCCCC'
            })
        
        return JsonResponse({
            'success': True,
            'product_id': product.id,
            'product_name': product.name,
            'configuration_type': product.get_configuration_type(),
            'base_price': str(product.base_price),
            'has_patterns': product.has_patterns,
            'has_product_level_sizes': product.has_product_level_sizes,
            'requires_size': product.requires_size_selection(),
            'patterns': patterns_data,
            'product_sizes': product_sizes_data,
            'colors': colors_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["GET"])
def get_variant_price(request):
    """
    GET /api/variant-price/
    
    Query Parameters:
    - product_id (required)
    - pattern_id (optional)
    - size_id (optional)
    - color_id (optional)
    
    Returns price and availability for specific combination
    
    Response Example:
    {
        "success": true,
        "price": "319.99",
        "available": true,
        "stock": 15,
        "variant_id": 42,
        "requires_size": false,
        "validation": {
            "valid": true,
            "message": null
        }
    }
    
    Validation Scenarios:
    - Pattern selected but has_sizes=true and no size selected → invalid
    - Product has_product_level_sizes but no size selected → invalid
    - Valid combination but out of stock → available=false
    """
    try:
        product_id = request.GET.get('product_id')
        pattern_id = request.GET.get('pattern_id')
        size_id = request.GET.get('size_id')
        color_id = request.GET.get('color_id')
        
        if not product_id:
            return JsonResponse({
                'success': False,
                'error': 'product_id is required'
            }, status=400)
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Validation logic
        validation_result = validate_selection(product, pattern_id, size_id)
        
        if not validation_result['valid']:
            return JsonResponse({
                'success': True,
                'price': None,
                'available': False,
                'stock': 0,
                'variant_id': None,
                'requires_size': validation_result.get('requires_size', False),
                'validation': validation_result
            })
        
        # Calculate price using product's price resolution logic
        price = product.get_price(
            pattern_id=pattern_id if pattern_id else None,
            size_id=size_id if size_id else None
        )
        
        # Check stock availability
        variant = ProductVariant.objects.filter(
            product=product,
            pattern_id=pattern_id if pattern_id else None,
            size_id=size_id if size_id else None,
            color_id=color_id if color_id else None
        ).first()
        
        if variant:
            stock = variant.stock
            available = variant.is_available()
            variant_id = variant.id
        else:
            # No variant found - check if it's a valid simple product
            if not product.has_patterns and not product.has_product_level_sizes:
                stock = 0
                available = False
                variant_id = None
            else:
                stock = 0
                available = False
                variant_id = None
        
        return JsonResponse({
            'success': True,
            'price': str(price),
            'available': available,
            'stock': stock,
            'variant_id': variant_id,
            'requires_size': validation_result.get('requires_size', False),
            'validation': validation_result
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["GET"])
def get_variant_options(request, product_id):
    """
    GET /api/variant-options/<product_id>/
    
    Query Parameters:
    - pattern_id (optional) - If provided, returns sizes for this pattern
    - color_id (optional) - For future filtering
    
    Returns available options based on current selection
    Stock-aware: Only returns options with stock > 0
    
    Response Example:
    {
        "success": true,
        "patterns": [
            {"id": 1, "name": "كلاسيك", "has_sizes": true}
        ],
        "sizes": [
            {"id": 1, "name": "S", "price": "299.99"},
            {"id": 2, "name": "M", "price": "319.99"}
        ],
        "colors": [
            {"id": 1, "name": "أحمر", "code": "#FF0000"}
        ],
        "requires_size": true
    }
    """
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        pattern_id = request.GET.get('pattern_id')
        color_id = request.GET.get('color_id')
        
        # Get available patterns (with stock)
        patterns_data = []
        if product.has_patterns:
            # Only show patterns that have stock
            patterns = Pattern.objects.filter(
                product=product
            ).filter(
                Q(has_sizes=False) |  # Patterns without sizes
                Q(  # Patterns with sizes that have stock
                    has_sizes=True,
                    pattern_sizes__stock__gt=0
                )
            ).distinct().order_by('order')
            
            for pattern in patterns:
                patterns_data.append({
                    'id': pattern.id,
                    'name': pattern.name,
                    'has_sizes': pattern.has_sizes,
                    'requires_size': pattern.requires_size_selection()
                })
        
        # Get available sizes based on selection
        sizes_data = []
        requires_size = False
        
        if pattern_id:
            # Pattern selected - get pattern-level sizes
            pattern = Pattern.objects.filter(id=pattern_id).first()
            if pattern and pattern.has_sizes:
                requires_size = True
                pattern_sizes = PatternSize.objects.filter(
                    pattern_id=pattern_id,
                    stock__gt=0
                ).select_related('size').order_by('order')
                
                for ps in pattern_sizes:
                    sizes_data.append({
                        'id': ps.size.id,
                        'name': ps.size.name,
                        'price': str(ps.price)
                    })
        elif product.has_product_level_sizes:
            # No pattern, but product has sizes
            requires_size = True
            product_sizes = ProductSize.objects.filter(
                product=product
            ).select_related('size').order_by('order')
            
            # Filter by stock in variants
            for ps in product_sizes:
                has_stock = ProductVariant.objects.filter(
                    product=product,
                    size=ps.size,
                    stock__gt=0
                ).exists()
                
                if has_stock:
                    sizes_data.append({
                        'id': ps.size.id,
                        'name': ps.size.name,
                        'price': str(ps.price)
                    })
        
        # Get available colors (with stock)
        colors_data = []
        product_colors = ProductColor.objects.filter(
            product=product
        ).select_related('color')
        
        for pc in product_colors:
            # Check if this color has stock for current selection
            has_stock = ProductVariant.objects.filter(
                product=product,
                color=pc.color,
                stock__gt=0
            ).exists()
            
            if has_stock:
                colors_data.append({
                    'id': pc.color.id,
                    'name': pc.color.name,
                    'code': pc.color.code or '#CCCCCC'
                })
        
        return JsonResponse({
            'success': True,
            'patterns': patterns_data,
            'sizes': sizes_data,
            'colors': colors_data,
            'requires_size': requires_size
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def validate_selection(product, pattern_id, size_id):
    """
    Business logic for validating variant selection
    
    Rules:
    1. If product has patterns and pattern selected:
       - If pattern has_sizes=True → size REQUIRED
       - If pattern has_sizes=False → size NOT required
    
    2. If product has product_level_sizes (no patterns):
       - Size REQUIRED
    
    3. If product is simple (no patterns, no sizes):
       - No validation needed
    
    Returns:
    {
        "valid": bool,
        "message": str or None,
        "requires_size": bool
    }
    """
    # Scenario 1: Pattern-based product
    if product.has_patterns:
        if not pattern_id:
            return {
                'valid': False,
                'message': 'يجب اختيار نمط',
                'requires_size': False
            }
        
        pattern = Pattern.objects.filter(id=pattern_id).first()
        if not pattern:
            return {
                'valid': False,
                'message': 'النمط المحدد غير موجود',
                'requires_size': False
            }
        
        # Check if pattern requires size
        if pattern.has_sizes and not size_id:
            return {
                'valid': False,
                'message': f'يجب اختيار مقاس للنمط {pattern.name}',
                'requires_size': True
            }
        
        return {
            'valid': True,
            'message': None,
            'requires_size': pattern.has_sizes
        }
    
    # Scenario 2: Size-based product (no patterns)
    elif product.has_product_level_sizes:
        if not size_id:
            return {
                'valid': False,
                'message': 'يجب اختيار مقاس',
                'requires_size': True
            }
        
        return {
            'valid': True,
            'message': None,
            'requires_size': True
        }
    
    # Scenario 3: Simple product
    else:
        return {
            'valid': True,
            'message': None,
            'requires_size': False
        }
