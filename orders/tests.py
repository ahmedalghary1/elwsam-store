from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from orders.models import Cart, CartItem
from products.models import Category, Color, Pattern, PatternSize, Product, ProductVariant, Size


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
