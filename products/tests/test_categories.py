from django.test import TestCase
from django.urls import reverse

from products.models import Category


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
