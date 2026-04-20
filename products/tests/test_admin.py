from decimal import Decimal

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from products.admin import (
    PatternAdmin,
    PatternBasePriceFilter,
    ProductAdmin,
    ProductPriceFilter,
)
from products.models import Category, Pattern, Product


class ProductAdminPriceFilterTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.category = Category.objects.create(name='قسم تجريبي')
        self.product_admin = ProductAdmin(Product, self.site)

        self.low = Product.objects.create(
            name='منتج منخفض',
            category=self.category,
            description='منتج منخفض السعر',
            price=Decimal('80.00'),
        )
        self.mid = Product.objects.create(
            name='منتج متوسط',
            category=self.category,
            description='منتج متوسط السعر',
            price=Decimal('180.00'),
        )
        self.high = Product.objects.create(
            name='منتج مرتفع',
            category=self.category,
            description='منتج مرتفع السعر',
            price=Decimal('1200.00'),
        )

    def test_product_admin_includes_price_filter(self):
        self.assertIn(ProductPriceFilter, self.product_admin.list_filter)

    def test_product_price_filter_returns_expected_min_max_match(self):
        request = self.factory.get(
            '/admin/products/product/',
            {'product_price_min': '100', 'product_price_max': '200'},
        )
        price_filter = ProductPriceFilter(
            request,
            {'product_price_min': '100', 'product_price_max': '200'},
            Product,
            self.product_admin,
        )

        filtered_products = price_filter.queryset(request, Product.objects.all())

        self.assertQuerysetEqual(
            filtered_products.order_by('id'),
            [self.mid],
            transform=lambda obj: obj,
        )


class PatternAdminPriceFilterTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.category = Category.objects.create(name='قسم الأنماط')
        self.product = Product.objects.create(
            name='منتج أنماط',
            category=self.category,
            description='منتج للاختبار',
            price=Decimal('100.00'),
        )
        self.pattern_admin = PatternAdmin(Pattern, self.site)

        self.low_pattern = Pattern.objects.create(
            product=self.product,
            name='نمط منخفض',
            base_price=Decimal('120.00'),
        )
        self.high_pattern = Pattern.objects.create(
            product=self.product,
            name='نمط مرتفع',
            base_price=Decimal('1500.00'),
        )

    def test_pattern_admin_includes_base_price_filter(self):
        self.assertIn(PatternBasePriceFilter, self.pattern_admin.list_filter)

    def test_pattern_base_price_filter_returns_expected_min_value(self):
        request = self.factory.get(
            '/admin/products/pattern/',
            {'pattern_base_price_min': '1000'},
        )
        price_filter = PatternBasePriceFilter(
            request,
            {'pattern_base_price_min': '1000'},
            Pattern,
            self.pattern_admin,
        )

        filtered_patterns = price_filter.queryset(request, Pattern.objects.all())

        self.assertQuerysetEqual(
            filtered_patterns.order_by('id'),
            [self.high_pattern],
            transform=lambda obj: obj,
        )
