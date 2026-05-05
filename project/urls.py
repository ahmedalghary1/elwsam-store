from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from core import views as core_views
from core.sitemaps import CategorySitemap, ProductSitemap, StaticViewSitemap
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
    product_collection_api,
    search_products
)

from django.conf import settings
from django.conf.urls.static import static


SITEMAPS = {
    'static': StaticViewSitemap,
    'categories': CategorySitemap,
    'products': ProductSitemap,
}



urlpatterns = [
    # Admin Panel
    path('_nested_admin/', include('nested_admin.urls')),
    path('admin/', admin.site.urls),
    path('control-panel/', include('staff_dashboard.urls')),
    
    # Core Routes
    path('', core_views.index, name='index'),
    path('robots.txt', core_views.robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': SITEMAPS}, name='sitemap'),
    
    # Products Routes
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/<int:id>/<str:slug>/', category_products, name='category_products'),
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<int:id>/<str:slug>/', ProductDetailView.as_view(), name='product_detail'),
    
    # Accounts Routes
    path('accounts/', include('accounts.urls')),
    
    # Orders Routes
    path('orders/', include('orders.urls')),
    
    # API Routes
    path('api/v1/', include('api.urls')),
    path('api/products/', product_collection_api, name='product_collection_api'),
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
