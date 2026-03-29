from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.db.models import Q, Exists, OuterRef
from django.core.cache import cache
from .models import (
    Product, Category, ProductVariant, ProductImage, ProductColor, 
    ProductSize, Pattern, ProductSpecification, PatternSize, Size, Color
)


# =========================
# List of Categories
# =========================
class CategoryListView(ListView):
    model = Category
    template_name = "categories.html"
    context_object_name = "categories"
    ordering = ['order']
    
    def get_queryset(self):
        return Category.objects.all().order_by('order').prefetch_related('product_set')


def category_products(request, slug):
    """
    عرض جميع المنتجات الخاصة بقسم معين (حسب slug)
    مع إمكانية الفرز والتصفية
    """
    category = get_object_or_404(Category, slug=slug)
    
    # الحصول على جميع المنتجات النشطة للقسم
    products = Product.objects.filter(
        category=category,
        is_active=True
    ).order_by('order').prefetch_related('images', 'variants', 'specs')
    
    # التصفية حسب المعاملات (Query Parameters)
    sort_by = request.GET.get('sort', 'order')
    if sort_by == 'price':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    
    # البحث عن منتج محدد
    search_query = request.GET.get('q', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
    
    context = {
        'category': category,
        'products': products,
        'search_query': search_query,
        'sort_by': sort_by,
        'products_count': products.count(),
    }
    return render(request, 'category-products.html', context)


# =========================
#  List of All Products
# =========================
class ProductListView(ListView):
    model = Product
    template_name = "products.html"
    context_object_name = "products"
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).order_by('order')
        queryset = queryset.prefetch_related('images', 'variants', 'specs')
        
        # التصفية حسب الفئة إن وجدت
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        return queryset


# =========================
# Product Detail View
# =========================
class ProductDetailView(View):
    template_name = "product.html"

    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_active=True)
        
        # كل الصور الخاصة بالمنتج (مرتبة حسب الرتبة)
        images = ProductImage.objects.filter(product=product).order_by('order')
        
        # كل الألوان المتاحة للمنتج
        product_colors = ProductColor.objects.filter(product=product).order_by('order')
        
        # كل المقاسات المتاحة للمنتج
        product_sizes = ProductSize.objects.filter(product=product).order_by('order')
        
        # كل الأنماط (Patterns)
        patterns = Pattern.objects.filter(product=product).order_by('order')
        
        # Variants مع البيانات المرتبطة
        variants_qs = ProductVariant.objects.filter(product=product).select_related(
            'color', 'size', 'pattern'
        ).order_by('order')

        variants = list(variants_qs.values(
            'id', 'price', 'stock',
            'pattern__id', 'pattern__name',
            'color__id', 'color__name', 'color__code',
            'size__id', 'size__name'
        ))
        
        # مواصفات المنتج
        specs = product.specs.all().order_by('order')
        
        # المنتجات المشابهة (من نفس الفئة)
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id).order_by('order')[:6]

        context = {
            'product': product,
            'images': images,
            'colors': product_colors,
            'sizes': product_sizes,
            'patterns': patterns,
            'variants': variants,
            'specs': specs,
            'related_products': related_products,
        }

        return render(request, self.template_name, context)


# =========================
# Helper: Validate Selection
# =========================
def validate_selection(product, pattern_id=None, size_id=None, color_id=None):
    """
    Validate variant selection based on product configuration.
    Returns dict with 'valid' boolean and 'message' string.
    """
    # Check if pattern is required
    if product.has_patterns() and not pattern_id:
        return {
            'valid': False,
            'message': 'يجب اختيار النمط',
            'field': 'pattern'
        }
    
    # Check if pattern requires size
    if pattern_id:
        try:
            pattern = Pattern.objects.get(id=pattern_id)
            if pattern.has_sizes and not size_id:
                return {
                    'valid': False,
                    'message': 'يجب اختيار المقاس لهذا النمط',
                    'field': 'size'
                }
        except Pattern.DoesNotExist:
            return {
                'valid': False,
                'message': 'النمط المحدد غير موجود',
                'field': 'pattern'
            }
    
    # Check if product has product-level sizes
    if product.has_product_level_sizes() and not pattern_id and not size_id:
        return {
            'valid': False,
            'message': 'يجب اختيار المقاس',
            'field': 'size'
        }
    
    # Check if color is required (if product has colors)
    if ProductColor.objects.filter(product=product).exists() and not color_id:
        return {
            'valid': False,
            'message': 'يجب اختيار اللون',
            'field': 'color'
        }
    
    return {'valid': True, 'message': '', 'field': None}


# =========================
#  AJAX: Get Product Configuration
# =========================
def get_product_config(request, product_id):
    """
    Get complete product configuration including patterns, sizes, colors.
    Cached for 5 minutes.
    """
    cache_key = f'product_config_{product_id}'
    cached_config = cache.get(cache_key)
    
    if cached_config:
        return JsonResponse(cached_config)
    
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Determine configuration type
        has_patterns = product.has_patterns()
        has_product_sizes = product.has_product_level_sizes()
        
        if has_patterns:
            config_type = 'pattern_based'
        elif has_product_sizes:
            config_type = 'size_based'
        else:
            config_type = 'simple'
        
        # Get patterns with their configuration
        patterns_data = []
        if has_patterns:
            patterns = Pattern.objects.filter(product=product).order_by('order')
            for pattern in patterns:
                pattern_info = {
                    'id': pattern.id,
                    'name': pattern.name,
                    'has_sizes': pattern.has_sizes,
                    'base_price': str(pattern.base_price) if pattern.base_price else None,
                    'sizes': []
                }
                
                # Get pattern-specific sizes if pattern has sizes
                if pattern.has_sizes:
                    pattern_sizes = PatternSize.objects.filter(
                        pattern=pattern
                    ).select_related('size').order_by('order')
                    pattern_info['sizes'] = [
                        {
                            'id': ps.size.id,
                            'name': ps.size.name,
                            'price': str(ps.price),
                            'stock': ps.stock,
                            'available': ps.is_available()
                        }
                        for ps in pattern_sizes
                    ]
                
                patterns_data.append(pattern_info)
        
        # Get product-level sizes
        product_sizes_data = []
        if has_product_sizes:
            product_sizes = ProductSize.objects.filter(
                product=product
            ).select_related('size').order_by('order')
            product_sizes_data = [
                {
                    'id': ps.size.id,
                    'name': ps.size.name,
                    'price': str(ps.price)
                }
                for ps in product_sizes
            ]
        
        # Get colors - only for non-pattern-based products
        colors_data = []
        if not has_patterns:
            # Only return colors for size_based or simple products
            product_colors = ProductColor.objects.filter(
                product=product
            ).select_related('color').order_by('order')
            colors_data = [
                {
                    'id': pc.color.id,
                    'name': pc.color.name,
                    'code': pc.color.code or '#ccc'
                }
                for pc in product_colors
            ]
        
        config = {
            'success': True,
            'configuration_type': config_type,
            'patterns': patterns_data,
            'product_sizes': product_sizes_data,
            'colors': colors_data,
            'base_price': str(product.price),
            'has_patterns': has_patterns,
            'has_product_level_sizes': has_product_sizes,
            'has_colors': len(colors_data) > 0
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, config, 300)
        
        return JsonResponse(config)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =========================
#  AJAX: Get Variant Options (Stock-Aware)
# =========================
def get_variant_options(request, product_id):
    """
    Get available variant options based on current selection.
    Returns ALL options with 'available' flag (not filtered out).
    """
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        pattern_id = request.GET.get('pattern_id')
        color_id = request.GET.get('color_id')
        
        # Get ALL variants (not just in-stock)
        variants_qs = ProductVariant.objects.filter(
            product=product
        ).select_related('pattern', 'color', 'size')
        
        # Filter by pattern if selected
        if pattern_id:
            variants_qs = variants_qs.filter(pattern_id=pattern_id)
        
        # Filter by color if selected
        if color_id:
            variants_qs = variants_qs.filter(color_id=color_id)
        
        # Get patterns with availability
        patterns_data = []
        if not pattern_id:
            patterns = Pattern.objects.filter(product=product).order_by('order')
            for pattern in patterns:
                # Check if pattern has any stock
                has_stock = ProductVariant.objects.filter(
                    product=product,
                    pattern=pattern,
                    stock__gt=0
                ).exists()
                
                patterns_data.append({
                    'id': pattern.id,
                    'name': pattern.name,
                    'available': has_stock,
                    'has_sizes': pattern.has_sizes
                })
        
        # Get colors with availability
        colors_data = []
        color_ids = variants_qs.values_list('color_id', flat=True).distinct()
        colors = Color.objects.filter(id__in=color_ids)
        for color in colors:
            # Check if this color has stock with current selection
            filter_kwargs = {'product': product, 'color': color}
            if pattern_id:
                filter_kwargs['pattern_id'] = pattern_id
            
            has_stock = ProductVariant.objects.filter(
                **filter_kwargs,
                stock__gt=0
            ).exists()
            
            colors_data.append({
                'id': color.id,
                'name': color.name,
                'code': color.code or '#ccc',
                'available': has_stock
            })
        
        # Get sizes with availability
        sizes_data = []
        
        # Check if we should show pattern sizes or product sizes
        if pattern_id:
            try:
                pattern = Pattern.objects.get(id=pattern_id)
                if pattern.has_sizes:
                    # Show pattern-specific sizes
                    pattern_sizes = PatternSize.objects.filter(
                        pattern=pattern
                    ).select_related('size').order_by('order')
                    
                    for ps in pattern_sizes:
                        # Check stock with current selection
                        filter_kwargs = {
                            'product': product,
                            'pattern_id': pattern_id,
                            'size': ps.size
                        }
                        if color_id:
                            filter_kwargs['color_id'] = color_id
                        
                        # Check if ProductVariant exists and has stock
                        variant_exists = ProductVariant.objects.filter(**filter_kwargs).exists()
                        has_stock = ProductVariant.objects.filter(
                            **filter_kwargs,
                            stock__gt=0
                        ).exists() if variant_exists else (ps.stock > 0)
                        
                        # Always show the size, mark as available based on stock
                        sizes_data.append({
                            'id': ps.size.id,
                            'name': ps.size.name,
                            'available': has_stock,
                            'price': str(ps.price),
                            'stock': ps.stock
                        })
            except Pattern.DoesNotExist:
                pass
        else:
            # Show product-level sizes if they exist
            product_sizes = ProductSize.objects.filter(
                product=product
            ).select_related('size').order_by('order')
            
            for ps in product_sizes:
                filter_kwargs = {'product': product, 'size': ps.size}
                if color_id:
                    filter_kwargs['color_id'] = color_id
                
                has_stock = ProductVariant.objects.filter(
                    **filter_kwargs,
                    stock__gt=0
                ).exists()
                
                sizes_data.append({
                    'id': ps.size.id,
                    'name': ps.size.name,
                    'available': has_stock,
                    'price': str(ps.price)
                })
        
        # Determine if size selection is required
        requires_size = False
        if pattern_id:
            try:
                pattern = Pattern.objects.get(id=pattern_id)
                requires_size = pattern.has_sizes
            except Pattern.DoesNotExist:
                pass
        elif product.has_product_level_sizes():
            requires_size = True
        
        return JsonResponse({
            'success': True,
            'patterns': patterns_data,
            'colors': colors_data,
            'sizes': sizes_data,
            'requires_size': requires_size,
            'has_patterns': len(patterns_data) > 0 or pattern_id is not None,
            'has_colors': len(colors_data) > 0,
            'has_sizes': len(sizes_data) > 0
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =========================
#  AJAX: Get Variant Price & Validation
# =========================
def get_variant_info(request, product_id):
    """
    Get variant price and validate selection.
    Uses dynamic price calculation from Product.get_price().
    Enhanced with comprehensive validation.
    """
    from .validators import VariantValidator
    
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        pattern_id = request.GET.get('pattern_id')
        color_id = request.GET.get('color_id')
        size_id = request.GET.get('size_id')
        
        # Convert to int if provided
        pattern_id = int(pattern_id) if pattern_id else None
        color_id = int(color_id) if color_id else None
        size_id = int(size_id) if size_id else None
        
        # Use comprehensive validator
        variant, validation = VariantValidator.get_variant_or_validate(
            product_id, pattern_id, color_id, size_id
        )
        
        if not validation['valid']:
            return JsonResponse({
                'success': False,
                'message': validation['message'],
                'validation': validation,
                'available': False
            })
        
        if variant:
            # Calculate dynamic price
            price = product.get_price(
                pattern_id=pattern_id,
                size_id=size_id,
                color_id=color_id
            )
            
            return JsonResponse({
                'success': True,
                'variant': {
                    'id': variant.id,
                    'price': str(price),
                    'stock': variant.stock,
                    'available': variant.is_available()
                },
                'validation': {'valid': True, 'message': '', 'field': None, 'errors': {}}
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'هذا التركيب غير متوفر',
                'validation': {
                    'valid': False,
                    'message': 'التركيبة المحددة غير موجودة',
                    'field': None,
                    'errors': {'variant': 'غير موجود'}
                },
                'available': False
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'validation': {
                'valid': False,
                'message': 'حدث خطأ في التحقق من الاختيار',
                'field': None
            }
        }, status=400)


# =========================
#  AJAX: تغيير الصور حسب اللون 
# =========================
def product_images_by_color(request, product_id, color_id):
    """
    إرجاع قائمة الصور حسب اللون باستخدام AJAX
    """
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        images = ProductImage.objects.filter(
            product=product,
            color_id=color_id
        ).order_by('order')
        
        image_urls = [img.image.url for img in images]
        
        return JsonResponse({
            'success': True,
            'images': image_urls
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =========================
#  Search / Filter Products
# =========================
def search_products(request):
    """
    بحث شامل عن المنتجات
    """
    query = request.GET.get('q', '').strip()
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True
        ).order_by('-created_at').prefetch_related('images', 'variants', 'specs')
    else:
        products = Product.objects.none()
    
    context = {
        'products': products,
        'query': query,
        'results_count': products.count(),
    }
    return render(request, "search_results.html", context)