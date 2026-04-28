from django.urls import path

from . import views


app_name = "staff_dashboard"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("products/", views.products_list, name="products"),
    path("products/add/", views.product_form, name="product_add"),
    path("products/<int:pk>/edit/", views.product_form, name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("products/<int:pk>/colors/add/", views.product_color_add, name="product_color_add"),
    path("products/<int:pk>/colors/<int:color_pk>/delete/", views.product_color_delete, name="product_color_delete"),
    path("products/<int:product_pk>/types/add/", views.product_type_form, name="product_type_add"),
    path("products/<int:product_pk>/types/<int:type_pk>/edit/", views.product_type_form, name="product_type_edit"),
    path("products/<int:product_pk>/types/<int:type_pk>/delete/", views.product_type_delete, name="product_type_delete"),
    path("product-types/<int:type_pk>/colors/add/", views.product_type_color_add, name="product_type_color_add"),
    path("product-types/<int:type_pk>/colors/<int:color_pk>/delete/", views.product_type_color_delete, name="product_type_color_delete"),
    path("product-types/<int:type_pk>/images/add/", views.product_type_image_add, name="product_type_image_add"),
    path("product-types/<int:type_pk>/images/<int:image_pk>/delete/", views.product_type_image_delete, name="product_type_image_delete"),
    path("colors/", views.colors_list, name="colors"),
    path("colors/add/", views.color_form, name="color_add"),
    path("colors/<int:pk>/edit/", views.color_form, name="color_edit"),
    path("colors/<int:pk>/delete/", views.color_delete, name="color_delete"),
    path("categories/", views.categories_list, name="categories"),
    path("categories/add/", views.category_form, name="category_add"),
    path("categories/<int:pk>/edit/", views.category_form, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    path("orders/", views.orders_list, name="orders"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("customers/", views.customers_list, name="customers"),
    path("customers/<int:pk>/edit/", views.customer_form, name="customer_edit"),
    path("home-sections/", views.home_collections_list, name="home_collections"),
    path("home-sections/add/", views.home_collection_form, name="home_collection_add"),
    path("home-sections/<int:pk>/edit/", views.home_collection_form, name="home_collection_edit"),
    path("home-sections/<int:pk>/delete/", views.home_collection_delete, name="home_collection_delete"),
    path("settings/", views.settings_overview, name="settings"),
]
