from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import AdminPasswordChangeRequest
from orders.models import Order, OrderItem
from products.models import (
    Category,
    Color,
    HeroSlide,
    HomeExclusiveOffer,
    Product,
    ProductColor,
    ProductImage,
    ProductType,
    ProductTypeColor,
    ProductTypeImage,
    Type,
)


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

    def test_dashboard_30_day_sales_counts_delivered_orders_only(self):
        delivered_order = Order.objects.create(
            status="delivered",
            total_price="120.00",
            shipping_address="Delivered address",
            shipping_phone="01000000000",
        )
        Order.objects.create(
            status="pending",
            total_price="999.00",
            shipping_address="Pending address",
            shipping_phone="01111111111",
        )
        old_delivered_order = Order.objects.create(
            status="delivered",
            total_price="300.00",
            shipping_address="Old delivered address",
            shipping_phone="01222222222",
        )
        Order.objects.filter(pk=old_delivered_order.pk).update(
            created_at=timezone.now() - timezone.timedelta(days=31)
        )

        self.client.login(email="admin@example.com", password="pass12345")
        response = self.client.get(reverse("staff_dashboard:dashboard"))

        self.assertEqual(response.status_code, 200)
        sales_stat = next(item for item in response.context["stats"] if item["icon"] == "fa-chart-line")
        self.assertEqual(Decimal(sales_stat["value"].split()[0]), Decimal(delivered_order.total_price))


class AdminPasswordChangeApprovalTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.requester = User.objects.create_superuser(
            email="requester@example.com",
            username="requester",
            password="oldpass123",
        )
        self.approver = User.objects.create_superuser(
            email="approver@example.com",
            username="approver",
            password="approver123",
        )

    def prepare_reset_session(self):
        session = self.client.session
        session["password_reset_email"] = self.requester.email
        session["reset_code_verified"] = True
        session.save()

    def test_superuser_password_reset_creates_pending_approval_request(self):
        self.prepare_reset_session()
        response = self.client.post(
            reverse("accounts:reset_password"),
            {"password1": "newpass12345", "password2": "newpass12345"},
        )

        self.assertRedirects(response, reverse("accounts:login"))
        change_request = AdminPasswordChangeRequest.objects.get(requester=self.requester)
        self.assertEqual(change_request.status, AdminPasswordChangeRequest.STATUS_PENDING)
        self.requester.refresh_from_db()
        self.assertTrue(self.requester.check_password("oldpass123"))

    def test_other_superuser_can_approve_request_and_change_password(self):
        self.requester.set_password("newpass12345")
        password_hash = self.requester.password
        self.requester.set_password("oldpass123")
        self.requester.save()
        change_request = AdminPasswordChangeRequest.objects.create(
            requester=self.requester,
            password_hash=password_hash,
        )

        self.client.login(email=self.approver.email, password="approver123")
        response = self.client.post(
            reverse("staff_dashboard:admin_password_change_request_detail", args=[change_request.token]),
            {"action": "approve"},
        )

        self.assertRedirects(response, reverse("staff_dashboard:admin_password_change_requests"))
        change_request.refresh_from_db()
        self.requester.refresh_from_db()
        self.assertEqual(change_request.status, AdminPasswordChangeRequest.STATUS_APPROVED)
        self.assertEqual(change_request.approved_by, self.approver)
        self.assertTrue(self.requester.check_password("newpass12345"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.requester.email])
        self.assertIn("تمت الموافقة على طلب تغيير كلمة مرور", mail.outbox[0].body)
        self.assertIn(self.approver.username, mail.outbox[0].body)
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
        self.assertIn("متجر الوسام", mail.outbox[0].alternatives[0][0])
        self.assertNotIn("ELWSAM-LOGO2020-104.webp", mail.outbox[0].alternatives[0][0])

    def test_superuser_cannot_approve_own_password_change_request(self):
        self.requester.set_password("newpass12345")
        password_hash = self.requester.password
        self.requester.set_password("oldpass123")
        self.requester.save()
        change_request = AdminPasswordChangeRequest.objects.create(
            requester=self.requester,
            password_hash=password_hash,
        )

        self.client.login(email=self.requester.email, password="oldpass123")
        response = self.client.post(
            reverse("staff_dashboard:admin_password_change_request_detail", args=[change_request.token]),
            {"action": "approve"},
        )

        self.assertEqual(response.status_code, 200)
        change_request.refresh_from_db()
        self.requester.refresh_from_db()
        self.assertEqual(change_request.status, AdminPasswordChangeRequest.STATUS_PENDING)
        self.assertTrue(self.requester.check_password("oldpass123"))
        self.assertEqual(len(mail.outbox), 0)


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
                "is_best_seller": "on",
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
        self.assertTrue(Product.objects.get(name="منتج تجريبي").is_best_seller)

    def test_superuser_can_add_color_to_product(self):
        product = Product.objects.create(
            name="Color Product",
            category=self.category,
            description="Product with colors",
            price="100.00",
        )

        response = self.client.post(
            reverse("staff_dashboard:product_color_add", args=[product.pk]),
            {
                "color": "",
                "new_color_name": "Black",
                "new_color_code": "#111111",
                "order": "1",
            },
        )

        self.assertRedirects(response, reverse("staff_dashboard:product_edit", args=[product.pk]))
        self.assertTrue(ProductColor.objects.filter(product=product, color__name="Black").exists())
        product.refresh_from_db()
        self.assertTrue(product.has_colors)

    def test_superuser_can_upload_and_delete_multiple_product_images(self):
        product = Product.objects.create(
            name="Gallery Product",
            category=self.category,
            description="Product with gallery",
            price="100.00",
        )
        first_image = SimpleUploadedFile(
            "gallery-1.gif",
            b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )
        second_image = SimpleUploadedFile(
            "gallery-2.gif",
            b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )

        response = self.client.post(
            reverse("staff_dashboard:product_image_add", args=[product.pk]),
            {
                "images": [first_image, second_image],
                "color": "",
                "order": "3",
            },
        )

        self.assertRedirects(response, reverse("staff_dashboard:product_edit", args=[product.pk]))
        self.assertEqual(ProductImage.objects.filter(product=product).count(), 2)
        self.assertEqual(list(ProductImage.objects.filter(product=product).values_list("order", flat=True)), [3, 4])

        image_to_delete = ProductImage.objects.filter(product=product).order_by("order").first()
        delete_response = self.client.post(
            reverse("staff_dashboard:product_image_delete", args=[product.pk, image_to_delete.pk])
        )

        self.assertRedirects(delete_response, reverse("staff_dashboard:product_edit", args=[product.pk]))
        self.assertEqual(ProductImage.objects.filter(product=product).count(), 1)

    def test_superuser_can_manage_color_library(self):
        response = self.client.post(
            reverse("staff_dashboard:color_add"),
            {
                "name": "Warm White",
                "code": "#fff1c2",
            },
        )

        color = Color.objects.get(name="Warm White")
        self.assertRedirects(response, reverse("staff_dashboard:color_edit", args=[color.pk]))
        self.assertEqual(color.code, "#fff1c2")

    def test_superuser_can_add_product_type_and_manage_details(self):
        product = Product.objects.create(
            name="Typed Product",
            category=self.category,
            description="Product with types",
            price="100.00",
        )

        response = self.client.post(
            reverse("staff_dashboard:product_type_add", args=[product.pk]),
            {
                "type": "",
                "new_type_name": "Premium",
                "price": "150.00",
                "description": "Premium details",
                "order": "1",
            },
        )

        product_type = ProductType.objects.get(product=product, type__name="Premium")
        self.assertRedirects(
            response,
            reverse("staff_dashboard:product_type_edit", args=[product.pk, product_type.pk]),
        )
        self.assertTrue(Type.objects.filter(name="Premium").exists())

        color_response = self.client.post(
            reverse("staff_dashboard:product_type_color_add", args=[product_type.pk]),
            {
                "color": "",
                "new_color_name": "Gold",
                "new_color_code": "#f5c542",
                "order": "1",
            },
        )
        self.assertRedirects(
            color_response,
            reverse("staff_dashboard:product_type_edit", args=[product.pk, product_type.pk]),
        )
        self.assertTrue(ProductTypeColor.objects.filter(product_type=product_type, color__name="Gold").exists())

        image = SimpleUploadedFile(
            "type.gif",
            b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )
        image_response = self.client.post(
            reverse("staff_dashboard:product_type_image_add", args=[product_type.pk]),
            {
                "color": Color.objects.get(name="Gold").pk,
                "image": image,
                "order": "1",
            },
        )
        self.assertRedirects(
            image_response,
            reverse("staff_dashboard:product_type_edit", args=[product.pk, product_type.pk]),
        )
        self.assertTrue(ProductTypeImage.objects.filter(product_type=product_type, color__name="Gold").exists())


class StaffDashboardHeroSlideTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="pass12345",
        )
        self.client.login(email="admin@example.com", password="pass12345")

    def test_superuser_can_create_hero_slide_from_custom_dashboard(self):
        image = SimpleUploadedFile(
            "hero.gif",
            b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )

        response = self.client.post(
            reverse("staff_dashboard:hero_slide_add"),
            {
                "title": "Homepage banner",
                "image": image,
                "link_url": "/products/",
                "alt_text": "Homepage banner alt",
                "is_active": "on",
                "order": "1",
            },
        )

        slide = HeroSlide.objects.get(title="Homepage banner")
        self.assertRedirects(response, reverse("staff_dashboard:hero_slide_edit", args=[slide.pk]))
        self.assertEqual(slide.link_url, "/products/")


class StaffDashboardHomeOfferTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="pass12345",
        )
        self.client.login(email="admin@example.com", password="pass12345")

    def test_superuser_can_create_home_offer_from_custom_dashboard(self):
        image = SimpleUploadedFile(
            "offer.gif",
            b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )

        response = self.client.post(
            reverse("staff_dashboard:home_offer_add"),
            {
                "tag": "اختبار العرض",
                "title": "عنوان العرض\nسطر ثان",
                "discount_text": "حتى 25%",
                "button_label": "تسوق الآن",
                "link_url": "/products/",
                "image": image,
                "alt_text": "صورة العرض",
                "tone": HomeExclusiveOffer.TONE_YELLOW,
                "is_active": "on",
                "order": "1",
            },
        )

        offer = HomeExclusiveOffer.objects.get(tag="اختبار العرض")
        self.assertRedirects(response, reverse("staff_dashboard:home_offer_edit", args=[offer.pk]))
        self.assertEqual(offer.link_url, "/products/")
        self.assertEqual(offer.tone, HomeExclusiveOffer.TONE_YELLOW)


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
        self.guest_order = Order.objects.create(
            total_price="49.00",
            shipping_address="Guest address",
            shipping_phone="01111111111",
            shipping_name="Guest Customer",
            shipping_city="Cairo",
            guest_email="guest@example.com",
        )
        self.client.login(email="admin@example.com", password="pass12345")

    def test_main_dashboard_pages_render_for_superuser(self):
        urls = [
            reverse("staff_dashboard:dashboard"),
            reverse("staff_dashboard:products"),
            reverse("staff_dashboard:categories"),
            reverse("staff_dashboard:orders"),
            reverse("staff_dashboard:order_detail", args=[self.order.pk]),
            reverse("staff_dashboard:order_detail", args=[self.guest_order.pk]),
            reverse("staff_dashboard:customers"),
            reverse("staff_dashboard:admin_password_change_requests"),
            reverse("staff_dashboard:home_collections"),
            reverse("staff_dashboard:hero_slides"),
            reverse("staff_dashboard:home_offers"),
            reverse("staff_dashboard:settings"),
            reverse("staff_dashboard:colors"),
            reverse("staff_dashboard:product_add"),
            reverse("staff_dashboard:hero_slide_add"),
            reverse("staff_dashboard:home_offer_add"),
            reverse("staff_dashboard:product_edit", args=[self.product.pk]),
            reverse("staff_dashboard:product_type_add", args=[self.product.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_orders_list_has_visible_detail_button(self):
        response = self.client.get(reverse("staff_dashboard:orders"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "تفاصيل")
        self.assertContains(response, reverse("staff_dashboard:order_detail", args=[self.order.pk]))

    def test_order_detail_shows_details_and_editable_status(self):
        response = self.client.get(reverse("staff_dashboard:order_detail", args=[self.order.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "طلب #")
        self.assertContains(response, "عميل تجريبي")
        self.assertContains(response, "عنوان تجريبي")
        self.assertContains(response, "تحديث حالة الطلب")
        self.assertContains(response, 'name="status"')

    def test_superuser_can_update_order_status_from_dashboard_detail(self):
        response = self.client.post(
            reverse("staff_dashboard:order_detail", args=[self.order.pk]),
            {
                "status": "shipped",
                "payment_method": self.order.payment_method,
                "contact_method": self.order.contact_method,
                "shipping_name": self.order.shipping_name,
                "shipping_phone": self.order.shipping_phone,
                "shipping_city": self.order.shipping_city,
                "shipping_address": self.order.shipping_address,
                "shipping_notes": self.order.shipping_notes or "",
                "order_notes": self.order.order_notes or "",
            },
        )

        self.assertRedirects(response, reverse("staff_dashboard:order_detail", args=[self.order.pk]))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "shipped")
