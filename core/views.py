from django.shortcuts import render
from django.urls import reverse
from products.models import Category, Product
from .seo import (
    SITE_NAME,
    build_absolute_uri,
    build_store_schema,
    build_website_schema,
    serialize_schema,
)


def index(request):
    """
    الصفحة الرئيسية - عرض الأقسام والمنتجات المميزة والحديثة
    """
    categories = Category.objects.filter(is_active=True).order_by('order')
    featured_products = Product.objects.filter(is_hot=True, is_active=True).order_by('order')[:10]
    latest_products = Product.objects.filter(is_active=True).order_by('-created_at')[:10]
    absolute_home_url = build_absolute_uri(request, '/')
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'latest_products': latest_products,
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
