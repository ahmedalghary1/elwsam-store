from django.shortcuts import render
from products.models import Category, Product


def index(request):
    """
    الصفحة الرئيسية - عرض الأقسام والمنتجات المميزة والحديثة
    """
    categories = Category.objects.all().order_by('order')
    featured_products = Product.objects.filter(is_hot=True, is_active=True).order_by('order')[:10]
    latest_products = Product.objects.filter(is_active=True).order_by('-created_at')[:10]
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'latest_products': latest_products,
    }
    return render(request, 'index.html', context)
