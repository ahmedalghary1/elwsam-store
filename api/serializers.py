from products.models import (
    Category,
    Color,
    Pattern,
    PatternSize,
    Product,
    ProductColor,
    ProductImage,
    ProductSize,
    ProductSpecification,
    ProductType,
)
from products.views import serialize_product_type


def absolute_url(request, url):
    if not url:
        return ''
    return request.build_absolute_uri(url)


def media_url(request, field):
    if not field:
        return ''
    try:
        return request.build_absolute_uri(field.url)
    except ValueError:
        return ''


def decimal_string(value):
    return str(value) if value is not None else None


def serialize_category(category, request=None, include_counts=True):
    data = {
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'description': category.description or '',
        'image': media_url(request, category.image) if request else '',
        'icon': category.icon,
        'is_hot': category.is_hot,
        'is_active': category.is_active,
        'order': category.order,
        'url': category.get_absolute_url(),
    }
    if request:
        data['absolute_url'] = absolute_url(request, data['url'])
    if include_counts:
        data['product_count'] = category.get_product_count()
    return data


def _primary_product_image(product, request):
    if product.image:
        return media_url(request, product.image)

    prefetched_images = getattr(product, '_prefetched_objects_cache', {}).get('images')
    first_image = prefetched_images[0] if prefetched_images else product.images.first()
    return media_url(request, first_image.image) if first_image else ''


def serialize_product_summary(product, request):
    old_price = product.old_price if product.old_price and product.old_price > product.price else None
    url = product.get_absolute_url()
    return {
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'category': {
            'id': product.category_id,
            'name': product.category.name if product.category_id else '',
            'slug': product.category.slug if product.category_id else '',
        },
        'price': decimal_string(product.price),
        'old_price': decimal_string(old_price) if old_price else None,
        'discount_percent': product.get_discount_percent(),
        'rating': product.rating,
        'image': _primary_product_image(product, request),
        'image_alt': product.get_primary_image_alt(),
        'url': url,
        'absolute_url': absolute_url(request, url),
        'is_new': product.is_new,
        'is_hot': product.is_hot,
        'is_available': product.is_available(),
        'configuration_type': product.get_configuration_type(),
    }


def serialize_product_detail(product, request):
    data = serialize_product_summary(product, request)
    images = ProductImage.objects.filter(product=product).select_related('color').order_by('order')
    specs = ProductSpecification.objects.filter(product=product).order_by('order')
    data.update({
        'description': product.description,
        'seo': {
            'title': product.get_seo_title(),
            'h1': product.get_seo_h1(),
            'meta_description': product.get_meta_description(),
            'focus_keywords': product.get_focus_keywords_list(),
        },
        'stock': product.get_stock(),
        'images': [
            {
                'id': image.id,
                'url': media_url(request, image.image),
                'color': serialize_color(image.color) if image.color_id else None,
                'order': image.order,
            }
            for image in images
        ],
        'specifications': [
            {
                'key': spec.key,
                'value': spec.value,
                'order': spec.order,
            }
            for spec in specs
        ],
    })
    return data


def serialize_color(color):
    return {
        'id': color.id,
        'name': color.name,
        'code': color.code or '#ccc',
    }


def serialize_size(size, price=None, stock=None, available=None):
    data = {
        'id': size.id,
        'name': size.name,
    }
    if price is not None:
        data['price'] = decimal_string(price)
    if stock is not None:
        data['stock'] = stock
    if available is not None:
        data['available'] = available
    return data


def serialize_product_configuration(product):
    has_patterns = product.check_if_has_patterns()
    has_product_sizes = product.check_if_has_product_level_sizes()
    has_product_colors = ProductColor.objects.filter(product=product).exists()

    if has_patterns:
        configuration_type = 'pattern_based'
    elif has_product_sizes:
        configuration_type = 'size_based'
    elif has_product_colors:
        configuration_type = 'color_only'
    else:
        configuration_type = 'simple'

    patterns = []
    for pattern in Pattern.objects.filter(product=product).order_by('order'):
        pattern_sizes = PatternSize.objects.filter(pattern=pattern).select_related('size').order_by('order')
        patterns.append({
            'id': pattern.id,
            'name': pattern.name,
            'has_sizes': pattern.has_sizes,
            'base_price': decimal_string(pattern.base_price),
            'sizes': [
                serialize_size(
                    pattern_size.size,
                    price=pattern_size.price,
                    stock=pattern_size.stock,
                    available=pattern_size.is_available(),
                )
                for pattern_size in pattern_sizes
            ],
        })

    product_sizes = ProductSize.objects.filter(product=product).select_related('size').order_by('order')
    product_colors = ProductColor.objects.filter(product=product).select_related('color').order_by('order')
    product_types = ProductType.objects.filter(product=product).select_related('type').prefetch_related(
        'type_colors__color',
        'type_images__color',
    ).order_by('order')
    product_types_data = [serialize_product_type(product_type) for product_type in product_types]

    return {
        'configuration_type': configuration_type,
        'base_price': decimal_string(product.get_price()),
        'patterns': patterns,
        'product_sizes': [
            serialize_size(product_size.size, price=product_size.price)
            for product_size in product_sizes
        ],
        'colors': [
            serialize_color(product_color.color)
            for product_color in product_colors
        ],
        'product_types': product_types_data,
        'flags': {
            'has_patterns': has_patterns,
            'has_product_level_sizes': has_product_sizes,
            'has_product_types': bool(product_types_data),
            'has_colors': has_product_colors or any(item['colors'] for item in product_types_data),
            'has_type_colors': any(item['colors'] for item in product_types_data),
        },
    }


def serialize_variant(variant, price):
    if not variant:
        return {
            'id': None,
            'price': decimal_string(price),
            'stock': None,
            'available': True,
        }
    return {
        'id': variant.id,
        'price': decimal_string(price),
        'stock': variant.stock,
        'available': variant.is_available(),
        'sku': variant.sku,
        'pattern': {
            'id': variant.pattern_id,
            'name': variant.pattern.name if variant.pattern_id else None,
        } if variant.pattern_id else None,
        'color': serialize_color(variant.color) if variant.color_id else None,
        'size': {
            'id': variant.size_id,
            'name': variant.size.name if variant.size_id else None,
        } if variant.size_id else None,
    }
