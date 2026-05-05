from django.urls import path

from . import views


app_name = 'api'

urlpatterns = [
    path('health/', views.health, name='health'),
    path('home/', views.home, name='home'),
    path('catalog/categories/', views.category_list, name='category_list'),
    path('catalog/categories/<int:category_id>/', views.category_detail, name='category_detail'),
    path('catalog/products/', views.product_list, name='product_list'),
    path('catalog/products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('catalog/products/<int:product_id>/configuration/', views.product_configuration, name='product_configuration'),
    path('catalog/products/<int:product_id>/configuration-legacy/', views.product_configuration_legacy, name='product_configuration_legacy'),
    path('catalog/products/<int:product_id>/variant-options/', views.variant_options, name='variant_options'),
    path('catalog/products/<int:product_id>/variant-info/', views.variant_info, name='variant_info'),
    path('catalog/products/<int:product_id>/images/', views.product_images, name='product_images'),
    path('orders/guest/', views.create_guest_order, name='create_guest_order'),
]
