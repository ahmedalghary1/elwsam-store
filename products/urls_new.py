"""
URL Routes for Flexible Variant System
======================================
"""

from django.urls import path
from .views_new import (
    get_product_config,
    get_variant_price,
    get_variant_options
)

# These routes should be added to project/urls.py
urlpatterns = [
    # Product configuration endpoint
    path('api/product-config/<int:product_id>/', 
         get_product_config, 
         name='get_product_config'),
    
    # Variant price and validation endpoint
    path('api/variant-price/', 
         get_variant_price, 
         name='get_variant_price'),
    
    # Available options endpoint (stock-aware)
    path('api/variant-options/<int:product_id>/', 
         get_variant_options, 
         name='get_variant_options'),
]
