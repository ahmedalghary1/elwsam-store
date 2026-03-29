"""
Template tags for order and variant display
"""

from django import template
from django.utils.safestring import mark_safe
from orders.utils import get_variant_display_for_template, format_variant_for_email

register = template.Library()


@register.simple_tag
def get_variant_info(item):
    """
    Get variant information for template display.
    Works with both CartItem and OrderItem.
    
    Usage:
        {% get_variant_info item as variant %}
        {{ variant.display }}
    """
    return get_variant_display_for_template(item)


@register.filter
def variant_display(item):
    """
    Display variant details in standard format.
    
    Usage:
        {{ item|variant_display }}
    """
    if hasattr(item, 'get_variant_display'):
        return item.get_variant_display()
    return ''


@register.filter
def variant_display_short(item):
    """
    Display variant details in short format.
    
    Usage:
        {{ item|variant_display_short }}
    """
    if hasattr(item, 'get_variant_display_short'):
        return item.get_variant_display_short()
    return ''


@register.filter
def format_variant_for_email(item):
    """
    Format variant for email display.
    
    Usage:
        {{ item|format_variant_for_email }}
    """
    from orders.utils import format_variant_for_email as format_func
    return format_func(item)


@register.inclusion_tag('orders/includes/variant_badges.html')
def variant_badges(item):
    """
    Render variant badges with icons and colors.
    
    Usage:
        {% variant_badges item %}
    """
    variant_info = get_variant_display_for_template(item)
    
    # For OrderItem
    if hasattr(item, 'pattern_name'):
        return {
            'pattern': item.pattern_name,
            'color_name': item.color_name,
            'color_code': item.color_code,
            'size': item.size_name,
            'has_variant': bool(item.pattern_name or item.color_name or item.size_name)
        }
    
    # For CartItem with variant
    if hasattr(item, 'variant') and item.variant:
        return {
            'pattern': item.variant.pattern.name if item.variant.pattern else None,
            'color_name': item.variant.color.name if item.variant.color else None,
            'color_code': item.variant.color.code if item.variant.color else None,
            'size': item.variant.size.name if item.variant.size else None,
            'has_variant': True
        }
    
    return {
        'pattern': None,
        'color_name': None,
        'color_code': None,
        'size': None,
        'has_variant': False
    }


@register.simple_tag
def variant_json(item):
    """
    Get variant details as JSON for JavaScript.
    
    Usage:
        <script>
            var variantData = {{ item|variant_json|safe }};
        </script>
    """
    import json
    
    if hasattr(item, 'get_variant_details_dict'):
        return mark_safe(json.dumps(item.get_variant_details_dict()))
    
    # For OrderItem
    if hasattr(item, 'pattern_name'):
        data = {}
        if item.pattern_name:
            data['pattern'] = item.pattern_name
        if item.color_name:
            data['color'] = {
                'name': item.color_name,
                'code': item.color_code
            }
        if item.size_name:
            data['size'] = item.size_name
        return mark_safe(json.dumps(data))
    
    return mark_safe('{}')


@register.filter
def has_variant(item):
    """
    Check if item has variant information.
    
    Usage:
        {% if item|has_variant %}
            ...
        {% endif %}
    """
    if hasattr(item, 'pattern_name'):
        return bool(item.pattern_name or item.color_name or item.size_name)
    
    if hasattr(item, 'variant') and item.variant:
        return True
    
    return False
