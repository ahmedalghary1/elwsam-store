from django.test import TestCase
from django.urls import reverse
from urllib.parse import quote

from products.models import Category, Product


def as_latin1_mojibake(value):
    return value.encode("utf-8").decode("latin-1")


class CategoryVisibilityTests(TestCase):
    def setUp(self):
        self.active_category = Category.objects.create(
            name="Active Category",
            is_active=True,
        )
        self.inactive_category = Category.objects.create(
            name="Inactive Category",
            is_active=False,
        )

    def test_category_list_shows_inactive_categories_as_coming_soon(self):
        response = self.client.get(reverse("category_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.active_category.name)
        self.assertContains(response, self.inactive_category.name)
        self.assertContains(response, "قريبا")
        self.assertNotContains(response, f'href="{self.inactive_category.get_absolute_url()}"')

    def test_home_page_shows_inactive_categories_as_coming_soon(self):
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.active_category.name)
        self.assertContains(response, self.inactive_category.name)
        self.assertContains(response, "قريبا")
        self.assertNotContains(response, f'href="{self.inactive_category.get_absolute_url()}"')

    def test_inactive_category_page_returns_404(self):
        response = self.client.get(
            reverse(
                "category_products",
                kwargs={"id": self.inactive_category.id, "slug": self.inactive_category.slug},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_category_page_redirects_to_canonical_when_slug_is_outdated(self):
        response = self.client.get(
            reverse(
                "category_products",
                kwargs={"id": self.active_category.id, "slug": "old-category-slug"},
            )
        )

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers["Location"], self.active_category.get_absolute_url())

    def test_category_page_accepts_percent_encoded_arabic_slug_without_loop(self):
        arabic_category = Category.objects.create(
            name="قسم المشترك",
            is_active=True,
        )
        double_encoded_slug = quote(quote(arabic_category.slug, safe=""), safe="")

        response = self.client.get(f"/categories/{arabic_category.id}/{double_encoded_slug}/")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Location", response.headers)

    def test_category_page_accepts_server_mojibake_arabic_slug(self):
        arabic_category = Category.objects.create(
            name="\u0642\u0633\u0645 \u0627\u0644\u0645\u0634\u062a\u0631\u0643",
            is_active=True,
        )
        mojibake_slug = as_latin1_mojibake(arabic_category.slug)

        response = self.client.get(f"/categories/{arabic_category.id}/{mojibake_slug}/")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Location", response.headers)


class ProductCanonicalSlugTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Products", is_active=True)
        self.product = Product.objects.create(
            name="مشترك USB",
            category=self.category,
            description="منتج للاختبار",
            price=100,
            is_active=True,
        )

    def test_product_page_redirects_to_canonical_when_slug_is_outdated(self):
        response = self.client.get(
            reverse(
                "product_detail",
                kwargs={"id": self.product.id, "slug": "old-product-slug"},
            )
        )

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers["Location"], self.product.get_absolute_url())

    def test_product_page_accepts_percent_encoded_arabic_slug_without_loop(self):
        product = Product.objects.create(
            name="\u0645\u0646\u062a\u062c \u0642\u064a\u0627\u0633 \u0639\u0631\u0628\u064a",
            category=self.category,
            description="Product for encoded slug test",
            price=100,
            is_active=True,
        )
        double_encoded_slug = quote(quote(product.slug, safe=""), safe="")

        response = self.client.get(f"/products/{product.id}/{double_encoded_slug}/")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Location", response.headers)

    def test_product_page_accepts_server_mojibake_arabic_slug(self):
        product = Product.objects.create(
            name="\u0645\u0646\u062a\u062c \u0639\u0631\u0628\u064a \u0644\u0644\u062a\u0631\u0645\u064a\u0632",
            category=self.category,
            description="Product for mojibake slug test",
            price=100,
            is_active=True,
        )
        mojibake_slug = as_latin1_mojibake(product.slug)

        response = self.client.get(f"/products/{product.id}/{mojibake_slug}/")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Location", response.headers)

    def test_product_page_renders_single_description_container(self):
        response = self.client.get(self.product.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="product-description-tab"', count=1)
        self.assertNotContains(response, 'id="product-description-main"')

    def test_product_description_preserves_line_breaks(self):
        product = Product.objects.create(
            name="منتج وصف متعدد",
            category=self.category,
            description="السطر الأول\nالسطر الثاني\nالسطر الثالث",
            price=100,
            is_active=True,
        )

        response = self.client.get(product.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "السطر الأول<br>السطر الثاني<br>السطر الثالث")


class ProductListViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Products", is_active=True)
        self.hidden_category = Category.objects.create(name="Hidden", is_active=False)
        self.visible_product = Product.objects.create(
            name="Visible Product",
            category=self.category,
            description="Visible product description",
            price=150,
            is_active=True,
        )
        self.inactive_product = Product.objects.create(
            name="Inactive Product",
            category=self.category,
            description="Inactive product description",
            price=90,
            is_active=False,
        )
        self.hidden_category_product = Product.objects.create(
            name="Hidden Category Product",
            category=self.hidden_category,
            description="Hidden category product description",
            price=120,
            is_active=True,
        )

    def test_product_list_page_renders_active_products(self):
        response = self.client.get(reverse("product_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visible Product")
        self.assertNotContains(response, "Inactive Product")
        self.assertNotContains(response, "Hidden Category Product")

    def test_product_list_can_filter_by_active_category(self):
        response = self.client.get(reverse("product_list"), {"category": self.category.slug})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visible Product")
        self.assertNotContains(response, "Hidden Category Product")
