import json

from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from orders.models import Order, OrderItem
from products.models import (
    Category,
    HeroSlide,
    Product,
    ProductImage,
    ProductType,
    ProductVariant,
)
from products.services import PRODUCT_COLLECTION_TYPES, get_product_collection_queryset
from products.validators import VariantValidator
from products.views import (
    get_product_config as legacy_product_config,
    get_variant_options as legacy_variant_options,
    product_images_by_color as legacy_product_images_by_color,
)

from .responses import api_error, api_response, paginate_queryset, positive_int, read_json_body
from .serializers import (
    absolute_url,
    media_url,
    serialize_category,
    serialize_product_configuration,
    serialize_product_detail,
    serialize_product_summary,
    serialize_variant,
)


SORT_OPTIONS = {
    'order': 'order',
    'price': 'price',
    'price_desc': '-price',
    'newest': '-created_at',
    'rating': '-rating',
}


def _active_products():
    return Product.objects.filter(
        is_active=True,
        category__is_active=True,
    ).select_related('category').prefetch_related('images')


def _legacy_json(response):
    try:
        return json.loads(response.content.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


@require_GET
def health(request):
    return api_response({
        'service': 'elwsam-store-api',
        'status': 'ok',
    })


@require_GET
def home(request):
    categories = Category.objects.filter(is_active=True).order_by('order')[:12]
    hero_slides = HeroSlide.objects.filter(is_active=True).order_by('order', '-created_at')
    collections = []
    for collection_type in sorted(PRODUCT_COLLECTION_TYPES):
        products = get_product_collection_queryset(collection_type)[:10]
        collections.append({
            'type': collection_type,
            'products': [serialize_product_summary(product, request) for product in products],
        })

    return api_response({
        'categories': [serialize_category(category, request) for category in categories],
        'hero_slides': [
            {
                'id': slide.id,
                'title': slide.title,
                'subtitle': slide.subtitle,
                'image': media_url(request, slide.image),
                'link_url': slide.link_url,
                'alt_text': slide.effective_alt_text,
                'order': slide.order,
            }
            for slide in hero_slides
        ],
        'collections': collections,
    })


@require_GET
def category_list(request):
    categories = Category.objects.filter(is_active=True).order_by('order')
    return api_response({
        'items': [serialize_category(category, request) for category in categories],
    })


@require_GET
def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id, is_active=True)
    products = _active_products().filter(category=category).order_by('order')
    page_obj, meta = paginate_queryset(products, request, default_page_size=24)
    return api_response({
        'category': serialize_category(category, request),
        'products': [serialize_product_summary(product, request) for product in page_obj.object_list],
    }, meta=meta)


@require_GET
def product_list(request):
    collection_type = request.GET.get('collection')
    if collection_type:
        if collection_type not in PRODUCT_COLLECTION_TYPES:
            return api_error('نوع المجموعة غير مدعوم', {'collection': collection_type}, status=400)
        queryset = get_product_collection_queryset(collection_type)
    else:
        queryset = _active_products()

    category = request.GET.get('category')
    if category:
        if category.isdigit():
            queryset = queryset.filter(category_id=int(category))
        else:
            queryset = queryset.filter(category__slug=category)

    query = request.GET.get('q', '').strip()
    if query:
        queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))

    sort = request.GET.get('sort', 'order')
    if sort not in SORT_OPTIONS:
        return api_error('طريقة الترتيب غير مدعومة', {'sort': sort}, status=400)
    queryset = queryset.order_by(SORT_OPTIONS[sort])

    page_obj, meta = paginate_queryset(queryset, request, default_page_size=24)
    return api_response({
        'items': [serialize_product_summary(product, request) for product in page_obj.object_list],
    }, meta={**meta, 'filters': {'q': query, 'category': category or '', 'sort': sort, 'collection': collection_type or ''}})


@require_GET
def product_detail(request, product_id):
    product = get_object_or_404(_active_products(), id=product_id)
    return api_response(serialize_product_detail(product, request))


@require_GET
def product_configuration(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True, category__is_active=True)
    return api_response(serialize_product_configuration(product))


@require_GET
def product_configuration_legacy(request, product_id):
    response = legacy_product_config(request, product_id)
    payload = _legacy_json(response)
    if not payload:
        return api_error('تعذر قراءة إعدادات المنتج', status=502)
    if response.status_code >= 400 or not payload.get('success', False):
        return api_error(payload.get('error') or payload.get('message') or 'تعذر قراءة إعدادات المنتج', payload, status=response.status_code)
    payload.pop('success', None)
    return api_response(payload)


@require_GET
def variant_options(request, product_id):
    response = legacy_variant_options(request, product_id)
    payload = _legacy_json(response)
    if not payload:
        return api_error('تعذر قراءة خيارات المنتج', status=502)
    if response.status_code >= 400 or not payload.get('success', False):
        return api_error(payload.get('error') or payload.get('message') or 'تعذر قراءة خيارات المنتج', payload, status=response.status_code)
    payload.pop('success', None)
    return api_response(payload)


@require_GET
def variant_info(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True, category__is_active=True)
    try:
        pattern_id = int(request.GET['pattern_id']) if request.GET.get('pattern_id') else None
        color_id = int(request.GET['color_id']) if request.GET.get('color_id') else None
        size_id = int(request.GET['size_id']) if request.GET.get('size_id') else None
        type_id = int(request.GET['type_id']) if request.GET.get('type_id') else None
    except (TypeError, ValueError):
        return api_error('قيم الاختيارات يجب أن تكون أرقامًا صحيحة', status=400)

    variant, validation = VariantValidator.get_variant_or_validate(
        product.id,
        pattern_id=pattern_id,
        color_id=color_id,
        size_id=size_id,
        type_id=type_id,
    )
    if not validation['valid']:
        return api_error(validation['message'], validation, status=422, code='invalid_selection')

    price = product.get_price(
        pattern_id=pattern_id,
        size_id=size_id,
        color_id=color_id,
        type_id=type_id,
    )
    return api_response({
        'variant': serialize_variant(variant, price),
        'validation': validation,
    })


@require_GET
def product_images(request, product_id):
    color_id = request.GET.get('color_id')
    if color_id:
        response = legacy_product_images_by_color(request, product_id, color_id)
        payload = _legacy_json(response)
        if not payload:
            return api_error('تعذر قراءة صور المنتج', status=502)
        if response.status_code >= 400 or not payload.get('success', False):
            return api_error(payload.get('error') or 'تعذر قراءة صور المنتج', payload, status=response.status_code)
        return api_response({'images': payload.get('images', [])})

    product = get_object_or_404(Product, id=product_id, is_active=True, category__is_active=True)
    images = ProductImage.objects.filter(product=product).select_related('color').order_by('order')
    return api_response({
        'images': [
            {
                'id': image.id,
                'url': media_url(request, image.image),
                'color_id': image.color_id,
                'order': image.order,
            }
            for image in images
        ],
    })


def _validate_customer(customer):
    errors = {}
    required_fields = {
        'name': 'الاسم مطلوب',
        'phone': 'رقم الهاتف مطلوب',
        'city': 'المدينة مطلوبة',
        'address': 'العنوان مطلوب',
    }
    for field, message in required_fields.items():
        if not str(customer.get(field, '')).strip():
            errors[field] = message
    phone = str(customer.get('phone', '')).strip()
    if phone and len(phone) < 10:
        errors['phone'] = 'رقم الهاتف غير صحيح'
    return errors


def _build_order_item(item):
    errors = {}
    product_id = item.get('product_id')
    variant_id = item.get('variant_id')
    product_type_id = item.get('product_type_id')
    quantity = positive_int(item.get('quantity'), 1, 1, 100)

    try:
        product = Product.objects.get(id=product_id, is_active=True, category__is_active=True)
    except (Product.DoesNotExist, TypeError, ValueError):
        return None, {'product_id': 'المنتج غير موجود أو غير متاح'}

    variant = None
    if variant_id:
        try:
            variant = ProductVariant.objects.select_related('pattern', 'color', 'size').get(
                id=variant_id,
                product=product,
            )
        except (ProductVariant.DoesNotExist, TypeError, ValueError):
            errors['variant_id'] = 'اختيار المنتج غير صحيح'

    product_type = None
    if product_type_id:
        try:
            product_type = ProductType.objects.select_related('type').get(
                id=product_type_id,
                product=product,
            )
        except (ProductType.DoesNotExist, TypeError, ValueError):
            errors['product_type_id'] = 'نوع المنتج غير صحيح'

    if not variant and not product_type and not product.is_simple_product():
        errors['selection'] = 'يجب إرسال اختيارات المنتج المطلوبة'

    if variant and variant.stock < quantity:
        errors['quantity'] = f'الكمية المتاحة لهذا الاختيار هي {variant.stock}'

    if product.is_simple_product() and product.stock < quantity:
        errors['quantity'] = f'الكمية المتاحة لهذا المنتج هي {product.stock}'

    if errors:
        return None, errors

    price = product.get_price(
        pattern_id=variant.pattern_id if variant else None,
        size_id=variant.size_id if variant else None,
        color_id=variant.color_id if variant else None,
        type_id=product_type.type_id if product_type else None,
    )
    return {
        'product': product,
        'variant': variant,
        'product_type': product_type,
        'quantity': quantity,
        'price': price,
    }, {}


@csrf_exempt
@require_http_methods(['POST'])
def create_guest_order(request):
    payload = read_json_body(request)
    if payload is None:
        return api_error('JSON غير صالح', status=400, code='invalid_json')

    customer = payload.get('customer') or {}
    items = payload.get('items') or []
    errors = {'customer': _validate_customer(customer), 'items': []}
    if not items:
        errors['items'].append({'items': 'يجب إرسال منتج واحد على الأقل'})

    order_items = []
    for index, item in enumerate(items):
        order_item, item_errors = _build_order_item(item)
        if item_errors:
            errors['items'].append({'index': index, 'errors': item_errors})
        elif order_item:
            order_items.append(order_item)

    if errors['customer'] or errors['items']:
        return api_error('بيانات الطلب غير مكتملة', errors, status=422, code='validation_error')

    total_price = sum(item['price'] * item['quantity'] for item in order_items)
    with transaction.atomic():
        order = Order.objects.create(
            user=None,
            total_price=total_price,
            shipping_address=str(customer.get('address', '')).strip(),
            shipping_phone=str(customer.get('phone', '')).strip(),
            shipping_name=str(customer.get('name', '')).strip(),
            shipping_city=str(customer.get('city', '')).strip(),
            shipping_notes=str(customer.get('notes', '')).strip() or None,
            guest_email=str(customer.get('email', '')).strip() or None,
            payment_method='cash_on_delivery',
            contact_method=customer.get('contact_method') or 'whatsapp',
            order_notes=str(payload.get('notes', '')).strip() or None,
            status='pending',
        )
        for item in order_items:
            variant = item['variant']
            product_type = item['product_type']
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                variant=variant,
                product_type=product_type,
                quantity=item['quantity'],
                price=item['price'],
                type_name=product_type.type.name if product_type else None,
                pattern_name=variant.pattern.name if variant and variant.pattern else None,
                color_name=variant.color.name if variant and variant.color else None,
                color_code=variant.color.code if variant and variant.color else None,
                size_name=variant.size.name if variant and variant.size else None,
            )

    return api_response(
        {
            'order': {
                'id': order.id,
                'status': order.status,
                'total_price': str(order.total_price),
                'items_count': order.get_total_items(),
                'detail_url': absolute_url(request, f'/orders/guest-order-success/{order.id}/'),
            }
        },
        message='تم إنشاء الطلب بنجاح',
        status=201,
    )
