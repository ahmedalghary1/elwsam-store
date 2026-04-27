from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache

from products.models import Category
from products.services import get_product_collection_queryset
from .seo import (
    SITE_NAME,
    build_absolute_uri,
    build_store_schema,
    build_website_schema,
    serialize_schema,
)


@never_cache
def index(request):
    """
    الصفحة الرئيسية - عرض الأقسام وتبويبات المنتجات
    """
    categories = Category.objects.filter(is_active=True).order_by('order')
    product_tabs = [
        {
            'type': 'offers',
            'label': 'العروض',
            'heading': 'عروض مختارة لك',
            'description': 'منتجات عليها خصومات فعلية وأسعار أقل من السعر السابق.',
        },
        {
            'type': 'best-sellers',
            'label': 'الأفضل مبيعاً',
            'heading': 'الأكثر طلباً',
            'description': 'منتجات رائجة يختارها العملاء بكثرة من مستلزمات الكهرباء.',
        },
        {
            'type': 'latest',
            'label': 'حديثاً',
            'heading': 'وصل حديثاً',
            'description': 'أحدث المنتجات المضافة إلى متجر الوسام.',
        },
    ]
    initial_product_tab = product_tabs[0]
    initial_tab_products = get_product_collection_queryset(initial_product_tab['type'])[:10]
    absolute_home_url = build_absolute_uri(request, '/')
    
    context = {
        'categories': categories,
        'product_tabs': product_tabs,
        'initial_product_tab': initial_product_tab,
        'initial_tab_products': initial_tab_products,
        'seo_title': f"{SITE_NAME} | مشترك كهرباء ومستلزمات الكهرباء في مصر",
        'seo_h1': "متجر الوسام لمستلزمات الكهرباء المنزلية",
        'seo_meta_description': (
            "تسوق مشترك كهرباء وبرايز متعددة ومستلزمات الكهرباء المنزلية من متجر الوسام "
            "مع خيارات مناسبة للمنزل والمكتب داخل مصر والدول العربية."
        ),
        'seo_canonical_url': absolute_home_url,
        'seo_structured_data': [
            serialize_schema(build_store_schema(request)),
            serialize_schema(build_website_schema(request)),
        ],
    }
    return render(request, 'index.html', context)


def robots_txt(request):
    return render(
        request,
        'robots.txt',
        {'sitemap_url': build_absolute_uri(request, reverse('sitemap'))},
        content_type='text/plain; charset=utf-8',
    )
