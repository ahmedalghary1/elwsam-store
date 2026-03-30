from django.contrib import admin
from django.urls import path, include
from core import views as core_views
from products.views import (
    CategoryListView, 
    category_products,
    ProductDetailView,
    ProductListView,
    product_images_by_color,
    get_product_config,
    get_variant_options,
    get_variant_info,
    get_variant_detail,
    search_products
)

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Admin Panel
    path('_nested_admin/', include('nested_admin.urls')),
    path('admin/', admin.site.urls),
    
    # Core Routes
    path('', core_views.index, name='index'),
    
    # Products Routes
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/<str:slug>/', category_products, name='category_products'),
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<str:slug>/', ProductDetailView.as_view(), name='product_detail'),
    
    # Accounts Routes
    path('accounts/', include('accounts.urls')),
    
    # Orders Routes
    path('orders/', include('orders.urls')),
    
    # API Routes
    path('api/product-config/<int:product_id>/', get_product_config, name='get_product_config'),
    path('api/variant-options/<int:product_id>/', get_variant_options, name='get_variant_options'),
    path('api/variant-info/<int:product_id>/', get_variant_info, name='get_variant_info'),
    path('api/variant-detail/<int:variant_id>/', get_variant_detail, name='get_variant_detail'),
    path('api/product-images/<int:product_id>/<int:color_id>/', product_images_by_color, name='product_images_by_color'),
    path('search/', search_products, name='search_products'),
    
    # Static and Media
    *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]