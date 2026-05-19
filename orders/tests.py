from decimal import Decimal

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from orders.admin import OrderAdmin
from orders.models import Cart, CartItem, Order
from products.models import Category, Color, Pattern, PatternSize, Product, ProductType, ProductVariant, Size, Type


class CartVariantPricingTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email='cart@example.com',
            username='cart-user',
            password='secret123'
        )
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Variant Product',
            category=self.category,
            description='Test product',
            price=Decimal('100.00'),
            is_active=True
        )
        self.pattern = Pattern.objects.create(
            product=self.product,
            name='Pattern A',
            has_sizes=True
        )
        self.size = Size.objects.create(name='M')
        self.color = Color.objects.create(name='Black', code='#111111')
        PatternSize.objects.create(
            pattern=self.pattern,
            size=self.size,
            price=Decimal('180.00'),
            stock=5
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            pattern=self.pattern,
            size=self.size,
            color=self.color,
            price=Decimal('999.99'),
            stock=5
        )
        self.cart = Cart.objects.create(user=self.user)

    def test_cart_item_uses_dynamic_variant_price(self):
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            variant=self.variant,
            quantity=2
        )

        self.assertEqual(cart_item.get_unit_price(), Decimal('180.00'))
        self.assertEqual(cart_item.get_total_price(), Decimal('360.00'))

    def test_cart_view_displays_dynamic_variant_price(self):
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            variant=self.variant,
            quantity=1
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('orders:cart'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '180.00')
        self.assertNotContains(response, '999.99')


class CartProductTypePricingTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email='type@example.com',
            username='type-user',
            password='secret123'
        )
        self.category = Category.objects.create(name='Type Category')
        self.product = Product.objects.create(
            name='Typed Product',
            category=self.category,
            description='Typed product',
            price=Decimal('5.00'),
            is_active=True
        )
        self.type = Type.objects.create(name='Premium')
        self.product_type = ProductType.objects.create(
            product=self.product,
            type=self.type,
            price=Decimal('10.00')
        )
        self.cart = Cart.objects.create(user=self.user)

    def test_cart_item_uses_selected_product_type_price(self):
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            product_type=self.product_type,
            quantity=2
        )

        self.assertEqual(cart_item.get_unit_price(), Decimal('10.00'))
        self.assertEqual(cart_item.get_total_price(), Decimal('20.00'))
        self.assertEqual(cart_item.get_variant_display(), 'النوع: Premium')

    def test_cart_view_displays_selected_product_type(self):
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            product_type=self.product_type,
            quantity=1
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('orders:checkout'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'النوع: Premium')
        self.assertContains(response, '10.00')


class OrderAdminDeletePermissionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="secret123",
        )
        self.order = Order.objects.create(
            total_price=Decimal("150.00"),
            shipping_address="Admin test address",
            shipping_phone="01000000000",
        )
        self.client.force_login(self.admin_user)

    def test_order_admin_change_page_does_not_show_delete_button(self):
        response = self.client.get(reverse("admin:orders_order_change", args=[self.order.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "deletelink")
        self.assertNotContains(response, reverse("admin:orders_order_delete", args=[self.order.pk]))

    def test_order_admin_direct_delete_url_is_forbidden(self):
        response = self.client.post(reverse("admin:orders_order_delete", args=[self.order.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())


class OrderEditorAdminPermissionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.editor = user_model.objects.create_user(
            email="editor@example.com",
            username="editor",
            password="secret123",
            is_staff=True,
            is_active=True,
        )
        self.editor.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="orders",
                codename__in=["view_order", "change_order"],
            )
        )
        self.order = Order.objects.create(
            total_price=Decimal("150.00"),
            shipping_address="Admin test address",
            shipping_phone="01000000000",
        )
        self.client.force_login(self.editor)

    def test_order_editor_can_open_order_admin_only(self):
        response = self.client.get(reverse("admin:orders_order_changelist"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("admin:orders_order_change", args=[self.order.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="status"')
        self.assertNotContains(response, 'name="shipping_phone"')

    def test_order_editor_admin_form_keeps_only_status_editable(self):
        request = self.client.get(reverse("admin:orders_order_change", args=[self.order.pk])).wsgi_request
        request.user = self.editor
        order_admin = OrderAdmin(Order, AdminSite())

        readonly_fields = order_admin.get_readonly_fields(request, self.order)

        self.assertNotIn("status", readonly_fields)
        self.assertIn("shipping_phone", readonly_fields)
        self.assertIn("shipping_address", readonly_fields)
        self.assertNotIn("delete_selected", order_admin.get_actions(request))
