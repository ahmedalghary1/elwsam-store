"""
Utility functions for order management
Includes helper functions for saving variant details and creating orders
"""

from .models import Order, OrderItem
from products.models import ProductVariant


def create_order_item_with_variant_details(order, product, variant, quantity, price):
    """
    Create an OrderItem with complete variant details stored as text.
    This ensures variant information is preserved even if the variant is deleted later.
    
    Args:
        order: Order instance
        product: Product instance
        variant: ProductVariant instance (can be None)
        quantity: int
        price: Decimal
    
    Returns:
        OrderItem instance
    """
    order_item = OrderItem(
        order=order,
        product=product,
        variant=variant,
        quantity=quantity,
        price=price
    )
    
    # Store variant details as text for permanent record
    if variant:
        if variant.pattern:
            order_item.pattern_name = variant.pattern.name
        
        if variant.color:
            order_item.color_name = variant.color.name
            order_item.color_code = variant.color.code
        
        if variant.size:
            order_item.size_name = variant.size.name
    
    order_item.save()
    return order_item


def get_variant_display_for_template(variant):
    """
    Get formatted variant details for template display.
    Works with both ProductVariant and OrderItem.
    
    Args:
        variant: ProductVariant or OrderItem instance
    
    Returns:
        dict with formatted variant information
    """
    if not variant:
        return {
            'has_variant': False,
            'display': '',
            'short': '',
            'pattern': None,
            'color': None,
            'size': None
        }
    
    # Check if it's an OrderItem (has pattern_name, color_name, size_name)
    if hasattr(variant, 'pattern_name'):
        # OrderItem
        return {
            'has_variant': bool(variant.pattern_name or variant.color_name or variant.size_name),
            'display': variant.get_variant_display(),
            'short': variant.get_variant_display_short(),
            'pattern': variant.pattern_name,
            'color': {
                'name': variant.color_name,
                'code': variant.color_code
            } if variant.color_name else None,
            'size': variant.size_name
        }
    
    # ProductVariant or CartItem with variant
    if hasattr(variant, 'get_variant_display'):
        return {
            'has_variant': True,
            'display': variant.get_variant_display(),
            'short': variant.get_variant_display_short() if hasattr(variant, 'get_variant_display_short') else '',
            'pattern': variant.pattern.name if hasattr(variant, 'pattern') and variant.pattern else None,
            'color': {
                'name': variant.color.name if hasattr(variant, 'color') and variant.color else None,
                'code': variant.color.code if hasattr(variant, 'color') and variant.color else None
            },
            'size': variant.size.name if hasattr(variant, 'size') and variant.size else None
        }
    
    # Fallback for ProductVariant without helper methods
    pattern_name = variant.pattern.name if hasattr(variant, 'pattern') and variant.pattern else None
    color_name = variant.color.name if hasattr(variant, 'color') and variant.color else None
    color_code = variant.color.code if hasattr(variant, 'color') and variant.color else None
    size_name = variant.size.name if hasattr(variant, 'size') and variant.size else None
    
    parts = []
    if pattern_name:
        parts.append(f"النمط: {pattern_name}")
    if color_name:
        parts.append(f"اللون: {color_name}")
    if size_name:
        parts.append(f"المقاس: {size_name}")
    
    return {
        'has_variant': bool(parts),
        'display': " | ".join(parts),
        'short': ", ".join([p.split(": ")[1] for p in parts]) if parts else '',
        'pattern': pattern_name,
        'color': {
            'name': color_name,
            'code': color_code
        } if color_name else None,
        'size': size_name
    }


def format_variant_for_email(order_item):
    """
    Format variant details for email templates.
    
    Args:
        order_item: OrderItem instance
    
    Returns:
        str: Formatted variant string for email
    """
    parts = []
    
    if order_item.pattern_name:
        parts.append(f"النمط: {order_item.pattern_name}")
    
    if order_item.color_name:
        parts.append(f"اللون: {order_item.color_name}")
    
    if order_item.size_name:
        parts.append(f"المقاس: {order_item.size_name}")
    
    if parts:
        return " | ".join(parts)
    
    return "بدون متغيرات"


def get_cart_item_variant_info(cart_item):
    """
    Get variant information from a cart item for JSON serialization.
    
    Args:
        cart_item: CartItem instance
    
    Returns:
        dict: Variant information
    """
    if not cart_item.variant:
        return {}
    
    return {
        'variant_id': cart_item.variant.id,
        'pattern': {
            'id': cart_item.variant.pattern.id,
            'name': cart_item.variant.pattern.name
        } if cart_item.variant.pattern else None,
        'color': {
            'id': cart_item.variant.color.id,
            'name': cart_item.variant.color.name,
            'code': cart_item.variant.color.code
        } if cart_item.variant.color else None,
        'size': {
            'id': cart_item.variant.size.id,
            'name': cart_item.variant.size.name
        } if cart_item.variant.size else None,
        'display': cart_item.get_variant_display(),
        'display_short': cart_item.get_variant_display_short()
    }
