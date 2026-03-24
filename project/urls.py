
from django.contrib import admin
from django.urls import path, include
from core import views as core_views
from products.views import (
    CategoryListView, 
    category_products,
    ProductDetailView,
    ProductListView,
    product_images_by_color,
    search_products
)

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Admin Panel
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
    path('', include('orders.urls')),
    
    # API Routes
    path('api/product-images/<int:product_id>/<int:color_id>/', product_images_by_color, name='product_images_by_color'),
    path('search/', search_products, name='search_products'),
    
    # Static and Media
    *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]