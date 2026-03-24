from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.http import JsonResponse
from django.db import transaction
from .models import Cart, CartItem, Order, OrderItem
from products.models import Product, ProductVariant
from accounts.models import Address
import json


# =========================
# Cart View (سلة التسوق)
# =========================
class CartView(View):
    template_name = "orders/cart.html"

    def get(self, request):
        if request.user.is_authenticated:
            # للمستخدمين المسجلين
            try:
                cart = request.user.cart
                cart_items = cart.items.all().select_related('product', 'variant')
            except Cart.DoesNotExist:
                cart = None
                cart_items = []
        else:
            # للمستخدمين غير المسجلين، البيانات تأتي من JavaScript
            cart = None
            cart_items = []

        return render(request, self.template_name, {
            'cart': cart,
            'cart_items': cart_items,
            'is_guest': not request.user.is_authenticated,
        })


# =========================
# Add to Cart (إضافة للسلة)
# =========================
def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        variant_id = request.POST.get('variant_id')
        quantity = int(request.POST.get('quantity', 1))

        try:
            product = get_object_or_404(Product, id=product_id, is_active=True)

            if request.user.is_authenticated:
                # للمستخدمين المسجلين
                cart, created = Cart.objects.get_or_create(user=request.user)

                variant = None
                if variant_id:
                    variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=product,
                    variant=variant,
                    defaults={'quantity': quantity}
                )

                if not created:
                    cart_item.quantity += quantity
                    cart_item.save()

                messages.success(request, f"تم إضافة {product.name} للسلة")
                return redirect('orders:cart')
            else:
                # للمستخدمين غير المسجلين - يتم التعامل معها عبر JavaScript
                messages.info(request, "يرجى تسجيل الدخول لإضافة المنتجات للسلة")
                return redirect('accounts:login')

        except Exception as e:
            messages.error(request, "حدث خطأ أثناء إضافة المنتج للسلة")
            return redirect('products:product_list')

    return redirect('products:product_list')


# =========================
# Update Cart Item (تحديث كمية)
# =========================
@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))

        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, "تم تحديث الكمية")
            else:
                cart_item.delete()
                messages.success(request, "تم حذف المنتج من السلة")

        except CartItem.DoesNotExist:
            messages.error(request, "المنتج غير موجود في السلة")

    return redirect('orders:cart')


# =========================
# Remove from Cart (حذف من السلة)
# =========================
@login_required
def remove_from_cart(request, item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        messages.success(request, "تم حذف المنتج من السلة")
    except CartItem.DoesNotExist:
        messages.error(request, "المنتج غير موجود في السلة")

    return redirect('orders:cart')


# =========================
# Checkout View (الدفع والشراء)
# =========================
class CheckoutView(LoginRequiredMixin, View):
    template_name = "orders/checkout.html"

    def get(self, request):
        try:
            cart = request.user.cart
            cart_items = cart.items.all().select_related('product', 'variant')

            if not cart_items:
                messages.warning(request, "سلة التسوق فارغة")
                return redirect('orders:cart')

            addresses = request.user.addresses.all()

            return render(request, self.template_name, {
                'cart': cart,
                'cart_items': cart_items,
                'addresses': addresses,
            })

        except Cart.DoesNotExist:
            messages.warning(request, "سلة التسوق فارغة")
            return redirect('products:product_list')

    def post(self, request):
        try:
            cart = request.user.cart
            cart_items = cart.items.all().select_related('product', 'variant')

            if not cart_items:
                messages.error(request, "سلة التسوق فارغة")
                return redirect('orders:cart')

            # الحصول على بيانات الشحن
            address_id = request.POST.get('address_id')
            payment_method = request.POST.get('payment_method', 'cash_on_delivery')

            if not address_id:
                messages.error(request, "يرجى اختيار عنوان الشحن")
                return redirect('orders:checkout')

            address = get_object_or_404(Address, id=address_id, user=request.user)

            # إنشاء الطلب
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    total_price=cart.get_total_price(),
                    shipping_address=f"{address.full_name}\n{address.street}\n{address.city}, {address.country}\n{address.postal_code}",
                    shipping_phone=address.phone,
                    payment_method=payment_method,
                    status='pending' if payment_method == 'cash_on_delivery' else 'paid'
                )

                # إنشاء عناصر الطلب
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        variant=cart_item.variant,
                        quantity=cart_item.quantity,
                        price=cart_item.get_total_price() / cart_item.quantity
                    )

                # حذف السلة بعد إنشاء الطلب
                cart_items.delete()

            messages.success(request, f"تم إنشاء الطلب بنجاح. رقم الطلب: #{order.id}")
            return redirect('orders:order_detail', order_id=order.id)

        except Exception as e:
            messages.error(request, "حدث خطأ أثناء إنشاء الطلب")
            return redirect('orders:checkout')


# =========================
# Order Detail View (تفاصيل الطلب)
# =========================
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all().select_related('product', 'variant')

    return render(request, 'orders/order_detail.html', {
        'order': order,
        'order_items': order_items,
    })


# =========================
# Order List View (قائمة الطلبات)
# =========================
class OrderListView(LoginRequiredMixin, View):
    template_name = "orders/order_list.html"

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')

        return render(request, self.template_name, {
            'orders': orders,
        })


# =========================
# Wishlist View (المفضلة)
# =========================
class WishlistView(LoginRequiredMixin, View):
    template_name = "orders/wishlist.html"

    def get(self, request):
        wishlist_items = request.user.wishlist.all().select_related('product')

        return render(request, self.template_name, {
            'wishlist_items': wishlist_items,
        })


# =========================
# Add to Wishlist (إضافة للمفضلة)
# =========================
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    if request.user.is_authenticated:
        wishlist_item, created = request.user.wishlist.get_or_create(product=product)

        if created:
            messages.success(request, f"تم إضافة {product.name} للمفضلة")
        else:
            messages.info(request, f"{product.name} موجود بالفعل في المفضلة")

        return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))
    else:
        # للمستخدمين غير المسجلين - يتم التعامل معها عبر JavaScript
        messages.info(request, "يرجى تسجيل الدخول لإضافة المنتجات للمفضلة")
        return redirect('accounts:login')


# =========================
# Remove from Wishlist (حذف من المفضلة)
# =========================
@login_required
def remove_from_wishlist(request, product_id):
    try:
        wishlist_item = get_object_or_404(
            request.user.wishlist,
            product_id=product_id
        )
        product_name = wishlist_item.product.name
        wishlist_item.delete()
        messages.success(request, f"تم حذف {product_name} من المفضلة")
    except:
        messages.error(request, "حدث خطأ أثناء حذف المنتج من المفضلة")

    return redirect('orders:wishlist')


# =========================
# AJAX: Add to Wishlist (إضافة للمفضلة عبر AJAX)
# =========================
def add_to_wishlist_ajax(request, product_id):
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id, is_active=True)

            if request.user.is_authenticated:
                wishlist_item, created = request.user.wishlist.get_or_create(product=product)

                if created:
                    return JsonResponse({
                        'success': True,
                        'message': f"تم إضافة {product.name} للمفضلة",
                        'action': 'added'
                    })
                else:
                    return JsonResponse({
                        'success': True,
                        'message': f"{product.name} موجود بالفعل في المفضلة",
                        'action': 'already_exists'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'يرجى تسجيل الدخول لإضافة المنتجات للمفضلة',
                    'login_required': True
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'حدث خطأ أثناء إضافة المنتج للمفضلة'
            })

    return JsonResponse({'success': False})


# =========================
# AJAX: Remove from Wishlist (حذف من المفضلة عبر AJAX)
# =========================
@login_required
def remove_from_wishlist_ajax(request, product_id):
    if request.method == 'POST':
        try:
            wishlist_item = get_object_or_404(
                request.user.wishlist,
                product_id=product_id
            )
            product_name = wishlist_item.product.name
            wishlist_item.delete()

            return JsonResponse({
                'success': True,
                'message': f"تم حذف {product_name} من المفضلة"
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'حدث خطأ أثناء حذف المنتج من المفضلة'
            })

    return JsonResponse({'success': False})


# =========================
# AJAX: Update Cart Item (تحديث كمية عبر AJAX)
# =========================
@login_required
def update_cart_item_ajax(request, item_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))

        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()

                cart = cart_item.cart
                return JsonResponse({
                    'success': True,
                    'item_total': cart_item.get_total_price(),
                    'cart_total': cart.get_total_price(),
                    'cart_subtotal': cart.get_subtotal(),
                })
            else:
                cart_item.delete()
                cart = request.user.cart
                return JsonResponse({
                    'success': True,
                    'deleted': True,
                    'cart_total': cart.get_total_price() if hasattr(request.user, 'cart') else 0,
                    'cart_subtotal': cart.get_subtotal() if hasattr(request.user, 'cart') else 0,
                })

        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'المنتج غير موجود في السلة'})

    return JsonResponse({'success': False})


# =========================
# AJAX: Remove from Cart (حذف من السلة عبر AJAX)
# =========================
@login_required
def remove_from_cart_ajax(request, item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()

        cart = request.user.cart
        return JsonResponse({
            'success': True,
            'cart_total': cart.get_total_price(),
            'cart_subtotal': cart.get_subtotal(),
        })
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'المنتج غير موجود في السلة'})

    return JsonResponse({'success': False})


# =========================
# AJAX: Sync Cart from localStorage (للمستخدمين غير المسجلين)
# =========================
@login_required
def sync_cart_from_localstorage(request):
    if request.method == 'POST':
        try:
            cart_data = json.loads(request.POST.get('cart_data', '[]'))

            cart, created = Cart.objects.get_or_create(user=request.user)

            for item in cart_data:
                product_id = item.get('product_id')
                variant_id = item.get('variant_id')
                quantity = item.get('quantity', 1)

                try:
                    product = Product.objects.get(id=product_id, is_active=True)

                    variant = None
                    if variant_id:
                        variant = ProductVariant.objects.get(id=variant_id, product=product)

                    cart_item, created = CartItem.objects.get_or_create(
                        cart=cart,
                        product=product,
                        variant=variant,
                        defaults={'quantity': quantity}
                    )

                    if not created:
                        cart_item.quantity += quantity
                        cart_item.save()

                except (Product.DoesNotExist, ProductVariant.DoesNotExist):
                    continue

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False})


# =========================
# AJAX: Sync Wishlist from localStorage (للمستخدمين غير المسجلين)
# =========================
@login_required
def sync_wishlist_from_localstorage(request):
    if request.method == 'POST':
        try:
            wishlist_data = json.loads(request.POST.get('wishlist_data', '[]'))

            for product_id in wishlist_data:
                try:
                    product = Product.objects.get(id=product_id, is_active=True)
                    request.user.wishlist.get_or_create(product=product)
                except Product.DoesNotExist:
                    continue

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False})
