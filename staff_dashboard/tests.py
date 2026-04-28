from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from orders.models import Order, OrderItem
from products.models import Category, Product


class StaffDashboardAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="pass12345",
        )
        self.user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="pass12345",
            is_active=True,
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("staff_dashboard:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])

    def test_regular_user_cannot_open_dashboard(self):
        self.client.login(email="user@example.com", password="pass12345")
        response = self.client.get(reverse("staff_dashboard:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("index"))

    def test_superuser_can_open_dashboard(self):
        self.client.login(email="admin@example.com", password="pass12345")
        response = self.client.get(reverse("staff_dashboard:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "لوحة التحكم")


class StaffDashboardProductTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="pass12345",
        )
        self.category = Category.objects.create(name="اختبار")
        self.client.login(email="admin@example.com", password="pass12345")

    def test_superuser_can_create_product_from_custom_dashboard(self):
        response = self.client.post(
            reverse("staff_dashboard:product_add"),
            {
                "name": "منتج تجريبي",
                "slug": "",
                "category": self.category.pk,
                "description": "وصف المنتج",
                "price": "125.00",
                "old_price": "",
                "stock": "7",
                "is_active": "on",
                "is_new": "on",
                "rating": "5",
                "order": "0",
                "seo_title": "",
                "meta_description": "",
                "seo_h1": "",
                "seo_description": "",
                "focus_keywords": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(name="منتج تجريبي").exists())


class StaffDashboardSmokeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="pass12345",
        )
        self.customer = User.objects.create_user(
            email="customer@example.com",
            username="customer",
            password="pass12345",
            is_active=True,
        )
        self.category = Category.objects.create(name="تصنيف smoke")
        self.product = Product.objects.create(
            name="منتج smoke",
            category=self.category,
            description="وصف smoke",
            price="99.00",
            stock=3,
        )
        self.order = Order.objects.create(
            user=self.customer,
            total_price="99.00",
            shipping_address="عنوان تجريبي",
            shipping_phone="01000000000",
            shipping_name="عميل تجريبي",
            shipping_city="القاهرة",
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price="99.00",
        )
        self.client.login(email="admin@example.com", password="pass12345")

    def test_main_dashboard_pages_render_for_superuser(self):
        urls = [
            reverse("staff_dashboard:dashboard"),
            reverse("staff_dashboard:products"),
            reverse("staff_dashboard:categories"),
            reverse("staff_dashboard:orders"),
            reverse("staff_dashboard:order_detail", args=[self.order.pk]),
            reverse("staff_dashboard:customers"),
            reverse("staff_dashboard:home_collections"),
            reverse("staff_dashboard:settings"),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
