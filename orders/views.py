from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.http import JsonResponse
from django.db import transaction
from .models import Cart, CartItem, Order, OrderItem
from products.models import Product, ProductType, ProductVariant
from accounts.models import Address
import json


def _get_product_type(product, product_type_id):
    if not product_type_id:
        return None
    return get_object_or_404(ProductType, id=product_type_id, product=product)


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
                cart_items = cart.items.all().select_related(
                    'product',
                    'variant',
                    'product_type',
                    'product_type__type',
                )
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
        product_type_id = request.POST.get('product_type_id')
        quantity = int(request.POST.get('quantity', 1))

        try:
            product = get_object_or_404(Product, id=product_id, is_active=True)

            if request.user.is_authenticated:
                cart, created = Cart.objects.get_or_create(user=request.user)
                variant = None
                if variant_id:
                    variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
                product_type = _get_product_type(product, product_type_id)

                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=product,
                    variant=variant,
                    product_type=product_type,
                    defaults={'quantity': quantity}
                )
                if not created:
                    cart_item.quantity += quantity
                    cart_item.save()

                # للطلبات AJAX: نرسل JSON
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f"تم إضافة {product.name} للسلة",
                        'cart_count': cart.get_total_items()
                    })
                else:
                    messages.success(request, f"تم إضافة {product.name} للسلة")
                    return redirect('orders:cart')

            else:
                # المستخدم غير مسجل – يتم التعامل من localStorage في الواجهة
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f"تم إضافة {product.name} للسلة",
                        'cart_count': 0
                    })
                else:
                    messages.info(request, "تم إضافة المنتج للسلة")
                    return redirect('orders:cart')

        except Exception as e:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'حدث خطأ أثناء إضافة المنتج للسلة'})
            else:
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
class CheckoutView(View):
    template_name = "orders/checkout.html"

    def get(self, request):
        if request.user.is_authenticated:
            try:
                cart = request.user.cart
                cart_items = cart.items.all().select_related(
                    'product',
                    'variant',
                    'product_type',
                    'product_type__type',
                )

                if not cart_items:
                    messages.warning(request, "سلة التسوق فارغة")
                    return redirect('orders:cart')

                addresses = request.user.addresses.all()

                return render(request, self.template_name, {
                    'cart': cart,
                    'cart_items': cart_items,
                    'addresses': addresses,
                    'is_guest': False,
                })

            except Cart.DoesNotExist:
                messages.warning(request, "سلة التسوق فارغة")
                return redirect('products:product_list')
        else:
            # Guest checkout
            return render(request, self.template_name, {
                'is_guest': True,
            })

    def post(self, request):
        if request.user.is_authenticated:
            return self._authenticated_checkout(request)
        else:
            return self._guest_checkout(request)

    def _authenticated_checkout(self, request):
        try:
            cart = request.user.cart
            cart_items = cart.items.all().select_related(
                'product',
                'variant',
                'product_type',
                'product_type__type',
            )

            if not cart_items:
                messages.error(request, "سلة التسوق فارغة")
                return redirect('orders:cart')

            # الحصول على بيانات الشحن
            address_id = request.POST.get('address_id')
            payment_method = request.POST.get('payment_method', 'cash_on_delivery')
            contact_method = request.POST.get('contact_method', 'whatsapp')
            order_notes = request.POST.get('order_notes', '').strip()

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
                    shipping_name=address.full_name,
                    shipping_city=address.city,
                    payment_method=payment_method,
                    contact_method=contact_method,
                    order_notes=order_notes if order_notes else None,
                    status='pending' if payment_method == 'cash_on_delivery' else 'paid'
                )

                # إنشاء عناصر الطلب
                for cart_item in cart_items:
                    v = cart_item.variant
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        variant=v,
                        product_type=cart_item.product_type,
                        quantity=cart_item.quantity,
                        price=cart_item.get_unit_price(),
                        type_name=cart_item.get_selected_type_name(),
                        pattern_name=v.pattern.name if v and v.pattern else None,
                        color_name=v.color.name if v and v.color else None,
                        color_code=v.color.code if v and v.color else None,
                        size_name=v.size.name if v and v.size else None,
                    )

                # حذف السلة بعد إنشاء الطلب
                cart_items.delete()

            messages.success(request, f"تم إنشاء الطلب بنجاح. رقم الطلب: #{order.id}")
            return redirect('orders:order_success', order_id=order.id)

        except Exception as e:
            import traceback
            print(f"Checkout Error: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f"حدث خطأ أثناء إنشاء الطلب: {str(e)}")
            return redirect('orders:checkout')

    def _guest_checkout(self, request):
        try:
            # الحصول على بيانات النموذج
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            address = request.POST.get('address', '').strip()
            city = request.POST.get('city', '').strip()
            notes = request.POST.get('notes', '').strip()
            email = request.POST.get('email', '').strip()
            contact_method = request.POST.get('contact_method', 'whatsapp')
            order_notes = request.POST.get('order_notes', '').strip()
            cart_data = request.POST.get('cart_data', '[]')

            # التحقق من البيانات المطلوبة
            if not all([full_name, phone, address, city]):
                messages.error(request, "يرجى ملء جميع الحقول المطلوبة")
                return redirect('orders:checkout')

            # التحقق من رقم الهاتف
            if len(phone) < 10:
                messages.error(request, "رقم الهاتف غير صحيح")
                return redirect('orders:checkout')

            # تحليل بيانات السلة من localStorage
            try:
                cart_items = json.loads(cart_data)
            except:
                messages.error(request, "بيانات السلة غير صحيحة")
                return redirect('orders:cart')

            if not cart_items:
                messages.error(request, "سلة التسوق فارغة")
                return redirect('orders:cart')

            # حساب الإجمالي
            total_price = 0
            order_items_data = []

            for item in cart_items:
                try:
                    product = Product.objects.get(id=item['product_id'], is_active=True)
                    variant = None
                    product_type = None
                    if item.get('variant_id'):
                        variant = ProductVariant.objects.get(id=item['variant_id'], product=product)
                    if item.get('product_type_id'):
                        product_type = ProductType.objects.get(
                            id=item['product_type_id'],
                            product=product
                        )

                    price = product.get_price(
                        pattern_id=variant.pattern_id if variant else None,
                        size_id=variant.size_id if variant else None,
                        color_id=variant.color_id if variant else None,
                        type_id=product_type.type_id if product_type else None,
                    )
                    quantity = int(item.get('quantity', 1))
                    item_total = price * quantity
                    total_price += item_total

                    order_items_data.append({
                        'product': product,
                        'variant': variant,
                        'product_type': product_type,
                        'quantity': quantity,
                        'price': price,
                        'type_name': item.get('product_type_name'),
                    })
                except (Product.DoesNotExist, ProductType.DoesNotExist, ProductVariant.DoesNotExist, ValueError):
                    continue

            if not order_items_data:
                messages.error(request, "لا توجد منتجات صالحة في السلة")
                return redirect('orders:cart')

            # إنشاء الطلب
            with transaction.atomic():
                order = Order.objects.create(
                    user=None,
                    total_price=total_price,
                    shipping_address=address,
                    shipping_phone=phone,
                    shipping_name=full_name,
                    shipping_city=city,
                    shipping_notes=notes,
                    guest_email=email if email else None,
                    payment_method='cash_on_delivery',
                    contact_method=contact_method,
                    order_notes=order_notes if order_notes else None,
                    status='pending'
                )

                # إنشاء عناصر الطلب
                for item_data in order_items_data:
                    v = item_data['variant']
                    product_type = item_data['product_type']
                    OrderItem.objects.create(
                        order=order,
                        product=item_data['product'],
                        variant=v,
                        product_type=product_type,
                        quantity=item_data['quantity'],
                        price=item_data['price'],
                        type_name=product_type.type.name if product_type else item_data.get('type_name'),
                        pattern_name=v.pattern.name if v and v.pattern else None,
                        color_name=v.color.name if v and v.color else None,
                        color_code=v.color.code if v and v.color else None,
                        size_name=v.size.name if v and v.size else None,
                    )

            messages.success(request, f"تم إنشاء الطلب بنجاح. رقم الطلب: #{order.id}")
            return redirect('orders:guest_order_success', order_id=order.id)

        except Exception as e:
            messages.error(request, "حدث خطأ أثناء إنشاء الطلب")
            return redirect('orders:checkout')


# =========================
# Order Success View (للمستخدمين المسجلين)
# =========================
def order_success(request, order_id):
    if not request.user.is_authenticated:
        messages.warning(request, "يرجى تسجيل الدخول لعرض تفاصيل الطلب")
        return redirect('accounts:login')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all().select_related('product', 'variant', 'product_type', 'product_type__type')

    return render(request, 'orders/order_success.html', {
        'order': order,
        'order_items': order_items,
    })


# =========================
# Guest Order Success View
# =========================
def guest_order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=None)
    order_items = order.items.all().select_related('product', 'variant', 'product_type', 'product_type__type')

    return render(request, 'orders/guest_order_success.html', {
        'order': order,
        'order_items': order_items,
    })


# =========================
# Order Detail View (تفاصيل الطلب)
# =========================
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all().select_related('product', 'variant', 'product_type', 'product_type__type')

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
                })
            else:
                cart_item.delete()
                cart = request.user.cart
                return JsonResponse({
                    'success': True,
                    'deleted': True,
                    'cart_total': cart.get_total_price() if hasattr(request.user, 'cart') else 0,
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
        })
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'المنتج غير موجود في السلة'})
        
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
                product_type_id = item.get('product_type_id')
                quantity = item.get('quantity', 1)

                try:
                    product = Product.objects.get(id=product_id, is_active=True)

                    variant = None
                    if variant_id:
                        variant = ProductVariant.objects.get(id=variant_id, product=product)
                    product_type = None
                    if product_type_id:
                        product_type = ProductType.objects.get(id=product_type_id, product=product)

                    cart_item, created = CartItem.objects.get_or_create(
                        cart=cart,
                        product=product,
                        variant=variant,
                        product_type=product_type,
                        defaults={'quantity': quantity}
                    )

                    if not created:
                        cart_item.quantity += quantity
                        cart_item.save()

                except (Product.DoesNotExist, ProductType.DoesNotExist, ProductVariant.DoesNotExist):
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
