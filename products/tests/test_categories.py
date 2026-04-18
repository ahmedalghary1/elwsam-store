from django.test import TestCase
from django.urls import reverse
from urllib.parse import quote

from products.models import Category, Product


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

    def test_category_list_hides_inactive_categories(self):
        response = self.client.get(reverse("category_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.active_category.name)
        self.assertNotContains(response, self.inactive_category.name)

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

    def test_category_page_redirects_when_slug_is_double_encoded(self):
        arabic_category = Category.objects.create(
            name="قسم المشترك",
            is_active=True,
        )
        double_encoded_slug = quote(quote(arabic_category.slug, safe=""), safe="")

        response = self.client.get(f"/categories/{arabic_category.id}/{double_encoded_slug}/")

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers["Location"], arabic_category.get_absolute_url())


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
