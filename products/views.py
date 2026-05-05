from urllib.parse import unquote

from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView
from django.http import Http404, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Exists, OuterRef
from django.core.cache import cache
from django.utils.text import slugify
from django.views.decorators.cache import never_cache
from core.seo import (
    build_absolute_uri,
    build_breadcrumb_schema,
    build_collection_page_schema,
    build_item_list_schema,
    serialize_schema,
)
from .models import (
    Product, Category, ProductVariant, ProductImage, ProductColor,
    ProductSize, ProductType, ProductTypeColor, ProductTypeImage, Pattern,
    ProductSpecification, PatternSize, Size, Color, PatternColor, PatternImage
)
from .services import (
    PRODUCT_COLLECTION_TYPES,
    get_product_collection_queryset,
    serialize_product_card,
)


def _decode_slug(raw_slug):
    """Decode once- or twice-encoded slugs without breaking normal Unicode slugs."""
    decoded = (raw_slug or "").strip().strip("/")
    for _ in range(3):
        if "%" not in decoded:
            break
        next_value = unquote(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    return decoded


def _normalize_slug(raw_slug):
    """Normalize user-supplied slugs for safe comparison against stored canonical slugs."""
    decoded = _decode_slug(raw_slug)
    return slugify(decoded, allow_unicode=True) or decoded


# =========================
# List of Categories
# =========================
class CategoryListView(ListView):
    model = Category
    template_name = "seo/categories.html"
    context_object_name = "categories"
    ordering = ['order']
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True).order_by('order').prefetch_related('product_set')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = list(context['categories'])
        absolute_url = build_absolute_uri(self.request, self.request.path)
        seo_meta_description = (
            "تصفح أقسام متجر الوسام واكتشف المشترك الكهربائي ومستلزمات الكهرباء المنزلية "
            "والإضاءة والمنتجات المناسبة للمنزل والمكتب داخل مصر والدول العربية."
        )
        category_items = [
            (category.name, build_absolute_uri(self.request, category.get_absolute_url()))
            for category in categories
        ]

        context.update({
            'seo_title': "أقسام متجر الوسام | تسوق المنتجات الكهربائية",
            'seo_h1': "أقسام متجر الوسام",
            'seo_meta_description': seo_meta_description,
            'seo_canonical_url': absolute_url,
            'seo_structured_data': [
                serialize_schema(build_breadcrumb_schema([
                    ("الرئيسية", build_absolute_uri(self.request, '/')),
                    ("الأقسام", absolute_url),
                ])),
                serialize_schema(build_collection_page_schema(
                    name="أقسام متجر الوسام",
                    description=seo_meta_description,
                    url=absolute_url,
                )),
                serialize_schema(build_item_list_schema(
                    name="قائمة الأقسام",
                    url=absolute_url,
                    items=category_items,
                )),
            ],
        })
        return context


def category_products(request, id, slug):
    """
    عرض جميع المنتجات الخاصة بقسم معين (حسب ID)
    مع إمكانية الفرز والتصفية
    """
    category = get_object_or_404(Category, id=id, is_active=True)
    requested_slug = _normalize_slug(slug)
    if "%" in slug or requested_slug != category.slug:
        return redirect(category.get_absolute_url(), permanent=True)
    
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

    paginator = Paginator(products, 36)
    page_obj = paginator.get_page(request.GET.get("page"))
    visible_products = page_obj.object_list
    query_params = request.GET.copy()
    query_params.pop("page", None)
    
    absolute_category_url = build_absolute_uri(request, category.get_absolute_url())
    category_items = [
        (product.get_seo_h1(), build_absolute_uri(request, product.get_absolute_url()))
        for product in visible_products[:36]
    ]
    seo_meta_description = category.meta_description or category.description or (
        f"تسوق منتجات {category.name} من متجر الوسام مع تفاصيل واضحة وأسعار مناسبة "
        "وشحن داخل مصر والدول العربية."
    )
    seo_intro = category.seo_intro or seo_meta_description

    context = {
        'category': category,
        'products': visible_products,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'query_params': query_params.urlencode(),
        'search_query': search_query,
        'sort_by': sort_by,
        'products_count': paginator.count,
        'seo_title': category.seo_title or f"{category.name} | تسوق الآن من متجر الوسام",
        'seo_h1': category.name,
        'seo_meta_description': seo_meta_description,
        'seo_intro': seo_intro,
        'seo_canonical_url': absolute_category_url,
        'seo_structured_data': [
            serialize_schema(build_breadcrumb_schema([
                ("الرئيسية", build_absolute_uri(request, '/')),
                ("الأقسام", build_absolute_uri(request, '/categories/')),
                (category.name, absolute_category_url),
            ])),
            serialize_schema(build_collection_page_schema(
                name=category.name,
                description=seo_meta_description,
                url=absolute_category_url,
            )),
            serialize_schema(build_item_list_schema(
                name=f"منتجات {category.name}",
                url=absolute_category_url,
                items=category_items,
            )),
        ],
    }
    return render(request, 'seo/category-products.html', context)


# =========================
#  List of All Products
# =========================
class ProductListView(ListView):
    model = Product
    template_name = "products.html"
    context_object_name = "products"
    paginate_by = 24
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True, category__is_active=True).select_related('category').order_by('order')
        queryset = queryset.prefetch_related('images', 'variants', 'specs')
        
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug, category__is_active=True)

        sort_by = self.request.GET.get('sort', 'order')
        if sort_by == 'price':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'rating':
            queryset = queryset.order_by('-rating')

        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(description__icontains=q)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = Category.objects.filter(is_active=True).order_by('order')
        selected_category_slug = self.request.GET.get('category', '')
        selected_category = categories.filter(slug=selected_category_slug).first() if selected_category_slug else None
        absolute_products_url = build_absolute_uri(self.request, self.request.path)
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        visible_products = list(context.get('products', []))
        product_items = [
            (product.get_seo_h1(), build_absolute_uri(self.request, product.get_absolute_url()))
            for product in visible_products
        ]
        page_obj = context.get('page_obj')
        if page_obj:
            pagination_start = max(page_obj.number - 2, 1)
            pagination_end = min(page_obj.number + 2, context['paginator'].num_pages)
            pagination_range = range(pagination_start, pagination_end + 1)
        else:
            pagination_range = []
        seo_meta_description = (
            "تصفح جميع منتجات متجر الوسام من المشترك الكهربائي والإضاءة ومستلزمات الكهرباء المنزلية "
            "مع خيارات متعددة وأسعار مناسبة وشحن داخل مصر والدول العربية."
        )

        context.update({
            'categories': categories,
            'sort_by': self.request.GET.get('sort', 'order'),
            'search_query': self.request.GET.get('q', '').strip(),
            'selected_category': selected_category_slug,
            'selected_category_object': selected_category,
            'query_params': query_params.urlencode(),
            'pagination_range': pagination_range,
            'total_products_count': Product.objects.filter(is_active=True, category__is_active=True).count(),
            'filtered_products_count': context['paginator'].count if context.get('paginator') else len(visible_products),
            'seo_title': "جميع المنتجات | متجر الوسام",
            'seo_h1': "جميع منتجات متجر الوسام",
            'seo_meta_description': seo_meta_description,
            'seo_canonical_url': absolute_products_url,
            'seo_structured_data': [
                serialize_schema(build_breadcrumb_schema([
                    ("الرئيسية", build_absolute_uri(self.request, '/')),
                    ("جميع المنتجات", absolute_products_url),
                ])),
                serialize_schema(build_collection_page_schema(
                    name="جميع منتجات متجر الوسام",
                    description=seo_meta_description,
                    url=absolute_products_url,
                )),
                serialize_schema(build_item_list_schema(
                    name="قائمة منتجات متجر الوسام",
                    url=absolute_products_url,
                    items=product_items,
                )),
            ],
        })
        return context


@never_cache
def product_collection_api(request):
    """
    Return home product-tab collections.

    Supported types: offers, best-sellers, latest.
    """
    collection_type = request.GET.get('type', 'offers')
    if collection_type not in PRODUCT_COLLECTION_TYPES:
        return JsonResponse({
            'success': False,
            'message': 'نوع المنتجات غير مدعوم',
            'products': [],
        }, status=400)

    try:
        limit = int(request.GET.get('limit', 10))
    except (TypeError, ValueError):
        limit = 10
    limit = max(1, min(limit, 24))

    try:
        page_number = int(request.GET.get('page', 1))
    except (TypeError, ValueError):
        page_number = 1

    queryset = get_product_collection_queryset(collection_type)
    paginator = Paginator(queryset, limit)
    page_obj = paginator.get_page(page_number)

    return JsonResponse({
        'success': True,
        'type': collection_type,
        'products': [serialize_product_card(product) for product in page_obj.object_list],
        'pagination': {
            'page': page_obj.number,
            'limit': limit,
            'total': paginator.count,
            'num_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        },
    })


# =========================
# Product Detail View
# =========================
class ProductDetailView(View):
    template_name = "product.html"

    def get(self, request, id, slug):
        product = get_object_or_404(Product, id=id, is_active=True)
        requested_slug = _normalize_slug(slug)
        if "%" in slug or requested_slug != product.slug:
            return redirect(product.get_absolute_url(), permanent=True)
        
        # كل الصور الخاصة بالمنتج (مرتبة حسب الرتبة)
        images = ProductImage.objects.filter(product=product).order_by('order')
        
        # كل الألوان المتاحة للمنتج
        product_colors = ProductColor.objects.filter(product=product).order_by('order')
        
        # كل المقاسات المتاحة للمنتج
        product_sizes = ProductSize.objects.filter(product=product).order_by('order')
        product_types = ProductType.objects.filter(product=product).select_related('type').order_by('order')
        
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

        primary_image = images.first().image.url if images.exists() else (product.image.url if product.image else None)
        absolute_product_url = build_absolute_uri(request, product.get_absolute_url())
        absolute_category_url = build_absolute_uri(request, product.category.get_absolute_url())
        absolute_image_url = build_absolute_uri(request, primary_image) if primary_image else ""
        faq_items = product.get_faq_items()

        context = {
            'product': product,
            'images': images,
            'colors': product_colors,
            'sizes': product_sizes,
            'types': product_types,
            'patterns': patterns,
            'variants': variants,
            'specs': specs,
            'related_products': related_products,
            'is_simple_product': product.is_simple_product(),
            'product_stock': product.stock if product.is_simple_product() else None,
            'seo_title': product.get_seo_title(),
            'seo_meta_description': product.get_meta_description(),
            'seo_h1': product.get_seo_h1(),
            'seo_description': product.get_seo_description(),
            'seo_canonical_url': absolute_product_url,
            'seo_primary_image_url': absolute_image_url,
            'seo_product_schema': product.get_schema_markup(url=absolute_product_url, image_url=absolute_image_url),
            'seo_breadcrumb_schema': product.get_breadcrumb_schema(
                category_url=absolute_category_url,
                product_url=absolute_product_url,
            ),
            'seo_faq_schema': product.get_faq_schema(),
            'seo_faq_items': faq_items,
        }

        return render(request, self.template_name, context)


def serialize_product_type(product_type):
    """Serialize product type with nested colors and color-specific images."""
    fallback_images = [
        type_image.image.url
        for type_image in product_type.type_images.all()
        if not type_image.color_id
    ]
    images_by_color = {}
    for type_image in product_type.type_images.all():
        if type_image.color_id:
            images_by_color.setdefault(type_image.color_id, []).append(type_image.image.url)

    colors = []
    for type_color in product_type.type_colors.all():
        color_images = images_by_color.get(type_color.color_id, []) or fallback_images[:]
        primary_image = color_images[0] if color_images else (product_type.image.url if product_type.image else None)
        colors.append({
            'id': type_color.color.id,
            'name': type_color.color.name,
            'code': type_color.color.code or '#ccc',
            'images': color_images,
            'primary_image': primary_image
        })

    return {
        'id': product_type.type.id,
        'product_type_id': product_type.id,
        'name': product_type.type.name,
        'price': str(product_type.price),
        'description': product_type.description,
        'image': product_type.image.url if product_type.image else None,
        'colors': colors,
        'has_colors': len(colors) > 0
    }


# =========================
# Helper: Validate Selection
# =========================
def validate_selection(product, pattern_id=None, size_id=None, color_id=None):
    """
    Validate variant selection based on product configuration.
    Returns dict with 'valid' boolean and 'message' string.
    """
    # Check if pattern is required
    if product.check_if_has_patterns() and not pattern_id:
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
    if product.check_if_has_product_level_sizes() and not pattern_id and not size_id:
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
        has_patterns = product.check_if_has_patterns()
        has_product_sizes = product.check_if_has_product_level_sizes()
        has_colors = ProductColor.objects.filter(product=product).exists()
        
        # Use the model's configuration type logic
        if has_patterns:
            config_type = 'pattern_based'
        elif has_product_sizes:
            config_type = 'size_based'
        elif has_colors:
            config_type = 'color_only'
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

        product_types = ProductType.objects.filter(
            product=product
        ).select_related('type').prefetch_related(
            'type_colors__color',
            'type_images__color'
        ).order_by('order')
        product_types_data = [serialize_product_type(product_type) for product_type in product_types]
        has_type_colors = any(product_type['colors'] for product_type in product_types_data)
        
        # Get product-level colors for all configuration types.
        colors_data = []
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
            'product_types': product_types_data,
            'colors': colors_data,
            'base_price': str(product.get_price()),
            'has_patterns': has_patterns,
            'has_product_level_sizes': has_product_sizes,
            'has_product_types': len(product_types_data) > 0,
            'has_colors': len(colors_data) > 0 or has_type_colors,
            'has_type_colors': has_type_colors
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
        type_id = request.GET.get('type_id')
        
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
        # If pattern selected and has PatternColors → use those; else use variant-derived colors
        colors_data = []
        type_colors = None
        if type_id:
            type_colors = ProductTypeColor.objects.filter(
                product_type__product=product,
                product_type__type_id=type_id
            ).select_related('color').order_by('order')

        if type_colors and type_colors.exists():
            for type_color in type_colors:
                has_stock = True
                if pattern_id:
                    color_variants = ProductVariant.objects.filter(
                        product=product,
                        pattern_id=pattern_id,
                        color=type_color.color
                    )
                    if color_variants.exists():
                        has_stock = color_variants.filter(stock__gt=0).exists()

                colors_data.append({
                    'id': type_color.color.id,
                    'name': type_color.color.name,
                    'code': type_color.color.code or '#ccc',
                    'available': has_stock
                })
        elif pattern_id:
            try:
                sel_pattern = Pattern.objects.get(id=pattern_id)
                p_colors = PatternColor.objects.filter(
                    pattern=sel_pattern
                ).select_related('color').order_by('order')
                if p_colors.exists():
                    for pc in p_colors:
                        has_stock = ProductVariant.objects.filter(
                            product=product,
                            pattern_id=pattern_id,
                            color=pc.color,
                            stock__gt=0
                        ).exists()
                        colors_data.append({
                            'id': pc.color.id,
                            'name': pc.color.name,
                            'code': pc.color.code or '#ccc',
                            'available': has_stock
                        })
                else:
                    color_ids = variants_qs.values_list('color_id', flat=True).distinct()
                    colors = Color.objects.filter(id__in=color_ids)
                    for color in colors:
                        has_stock = ProductVariant.objects.filter(
                            product=product, color=color,
                            pattern_id=pattern_id, stock__gt=0
                        ).exists()
                        colors_data.append({
                            'id': color.id, 'name': color.name,
                            'code': color.code or '#ccc', 'available': has_stock
                        })
            except Pattern.DoesNotExist:
                pass
        else:
            color_ids = variants_qs.values_list('color_id', flat=True).distinct()
            colors = Color.objects.filter(id__in=color_ids)
            for color in colors:
                has_stock = ProductVariant.objects.filter(
                    product=product, color=color, stock__gt=0
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
        elif product.check_if_has_product_level_sizes():
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
        type_id = request.GET.get('type_id')
        
        # Convert to int if provided
        pattern_id = int(pattern_id) if pattern_id else None
        color_id = int(color_id) if color_id else None
        size_id = int(size_id) if size_id else None
        type_id = int(type_id) if type_id else None
        
        # Use comprehensive validator
        variant, validation = VariantValidator.get_variant_or_validate(
            product_id, pattern_id, color_id, size_id, type_id
        )
        
        if not validation['valid']:
            if validation.get('errors', {}).get('stock'):
                stale_variant = ProductVariant.objects.filter(
                    product=product,
                    pattern_id=pattern_id,
                    color_id=color_id,
                    size_id=size_id
                ).first()
                dynamic_price = product.get_price(
                    pattern_id=pattern_id,
                    size_id=size_id,
                    color_id=color_id,
                    type_id=type_id
                )
                if stale_variant and stale_variant.price != dynamic_price:
                    return JsonResponse({
                        'success': True,
                        'variant': {
                            'id': stale_variant.id,
                            'price': str(dynamic_price),
                            'stock': stale_variant.stock,
                            'available': stale_variant.is_available()
                        },
                        'validation': {'valid': True, 'message': '', 'field': None, 'errors': {}}
                    })
            return JsonResponse({
                'success': False,
                'message': validation['message'],
                'validation': validation,
                'available': False
            })
        
        price = product.get_price(
            pattern_id=pattern_id,
            size_id=size_id,
            color_id=color_id,
            type_id=type_id
        )

        if variant:
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

        return JsonResponse({
            'success': True,
            'variant': {
                'id': None,
                'price': str(price),
                'stock': None,
                'available': True
            },
            'validation': {'valid': True, 'message': '', 'field': None, 'errors': {}}
        })
            
    except Http404:
        raise
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
#  AJAX: Get Variant Details by ID
# =========================
def get_variant_detail(request, variant_id):
    """
    Get variant details by variant_id for displaying in cart modal.
    Returns pattern, color, size, and price information.
    """
    try:
        variant = get_object_or_404(ProductVariant, id=variant_id)
        
        return JsonResponse({
            'success': True,
            'variant': {
                'id': variant.id,
                'pattern_name': variant.pattern.name if variant.pattern else None,
                'color_name': variant.color.name if variant.color else None,
                'color_code': variant.color.code if variant.color else None,
                'size_name': variant.size.name if variant.size else None,
                'price': str(variant.get_price()),
                'sku': variant.sku,
                'stock': variant.stock,
                'available': variant.is_available()
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =========================
#  AJAX: تغيير الصور حسب اللون 
# =========================
def product_images_by_color(request, product_id, color_id):
    """
    إرجاع قائمة الصور حسب اللون باستخدام AJAX.
    إذا تم تمرير pattern_id → يتحقق من PatternImage أولاً،
    وإذا لم توجد صور للنمط يرجع إلى ProductImage.
    """
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        pattern_id = request.GET.get('pattern_id')
        type_id = request.GET.get('type_id')

        image_urls = []

        if type_id:
            type_images = ProductTypeImage.objects.filter(
                product_type__product=product,
                product_type__type_id=type_id,
                color_id=color_id
            ).order_by('order')

            if not type_images.exists():
                type_images = ProductTypeImage.objects.filter(
                    product_type__product=product,
                    product_type__type_id=type_id,
                    color__isnull=True
                ).order_by('order')

            image_urls = [type_image.image.url for type_image in type_images]

            if not image_urls:
                product_type = ProductType.objects.filter(
                    product=product,
                    type_id=type_id
                ).first()
                if product_type and product_type.image:
                    image_urls = [product_type.image.url]

        if not image_urls and pattern_id:
            pattern_images = PatternImage.objects.filter(
                pattern_id=pattern_id,
                color_id=color_id
            ).order_by('order')

            if not pattern_images.exists():
                pattern_images = PatternImage.objects.filter(
                    pattern_id=pattern_id,
                    color__isnull=True
                ).order_by('order')

            image_urls = [pi.image.url for pi in pattern_images]

        if not image_urls:
            product_imgs = ProductImage.objects.filter(
                product=product,
                color_id=color_id
            ).order_by('order')
            image_urls = [img.image.url for img in product_imgs]

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
            is_active=True,
            category__is_active=True,
        ).select_related('category').order_by('-created_at').prefetch_related('images', 'variants', 'specs')
    else:
        products = Product.objects.none()

    search_url = build_absolute_uri(request, request.get_full_path())
    search_description = (
        f"نتائج البحث عن {query} في منتجات متجر الوسام من مشتركات كهرباء وبرايز وكشافات ليد."
        if query
        else "ابحث داخل منتجات متجر الوسام عن مشتركات كهرباء وبرايز وكشافات ليد ومستلزمات الكهرباء."
    )
    
    context = {
        'products': products,
        'query': query,
        'results_count': products.count(),
        'seo_title': f"نتائج البحث عن {query} | متجر الوسام" if query else "البحث في منتجات متجر الوسام",
        'seo_meta_description': search_description,
        'seo_canonical_url': search_url,
        'meta_robots': 'noindex,follow',
    }
    return render(request, "search_results.html", context)
