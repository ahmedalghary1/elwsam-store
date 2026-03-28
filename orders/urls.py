from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Cart
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/item/<int:item_id>/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/item/<int:item_id>/remove/', views.remove_from_cart, name='remove_from_cart'),
    
    # Checkout
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('guest-order-success/<int:order_id>/', views.guest_order_success, name='guest_order_success'),

    # Orders
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),

    # Wishlist
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # AJAX Wishlist
    path('wishlist/add-ajax/<int:product_id>/', views.add_to_wishlist_ajax, name='add_to_wishlist_ajax'),
    path('wishlist/remove-ajax/<int:product_id>/', views.remove_from_wishlist_ajax, name='remove_from_wishlist_ajax'),
    path('wishlist/sync/', views.sync_wishlist_from_localstorage, name='sync_wishlist'),

    # AJAX Cart
    path('cart/sync/', views.sync_cart_from_localstorage, name='sync_cart'),
    path('cart/item/<int:item_id>/update-ajax/', views.update_cart_item_ajax, name='update_cart_item_ajax'),
    path('cart/item/<int:item_id>/remove-ajax/', views.remove_from_cart_ajax, name='remove_from_cart_ajax'),
]