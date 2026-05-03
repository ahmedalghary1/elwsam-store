import re
from decimal import Decimal

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from products.models import Category, HeroSlide, HomeProductCollectionItem, Product
from products.services import get_product_collection_queryset


class HomeProductCollectionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="قسم الصفحة الرئيسية")
        self.first_product = Product.objects.create(
            name="منتج أول",
            category=self.category,
            description="منتج مختار",
            price=Decimal("100.00"),
        )
        self.second_product = Product.objects.create(
            name="منتج ثان",
            category=self.category,
            description="منتج مختار",
            price=Decimal("120.00"),
        )

    def test_curated_collection_controls_products_and_order(self):
        HomeProductCollectionItem.objects.create(
            collection_type=HomeProductCollectionItem.COLLECTION_OFFERS,
            product=self.second_product,
            order=1,
        )
        HomeProductCollectionItem.objects.create(
            collection_type=HomeProductCollectionItem.COLLECTION_OFFERS,
            product=self.first_product,
            order=0,
        )

        products = list(get_product_collection_queryset("offers"))

        self.assertEqual(products, [self.first_product, self.second_product])

    def test_inactive_curated_items_are_ignored(self):
        HomeProductCollectionItem.objects.create(
            collection_type=HomeProductCollectionItem.COLLECTION_BEST_SELLERS,
            product=self.first_product,
            is_active=False,
        )
        self.second_product.is_hot = True
        self.second_product.save(update_fields=["is_hot"])

        products = list(get_product_collection_queryset("best-sellers"))

        self.assertEqual(products, [self.second_product])

    def test_collection_falls_back_to_existing_offer_rules(self):
        self.first_product.old_price = Decimal("150.00")
        self.first_product.save(update_fields=["old_price"])

        products = list(get_product_collection_queryset("offers"))

        self.assertEqual(products, [self.first_product])

    def test_legacy_numeric_collection_values_are_still_displayed(self):
        HomeProductCollectionItem.objects.bulk_create([
            HomeProductCollectionItem(
                collection_type="1",
                product=self.first_product,
            ),
            HomeProductCollectionItem(
                collection_type="2",
                product=self.second_product,
            ),
        ])

        offer_products = list(get_product_collection_queryset("offers"))
        best_seller_products = list(get_product_collection_queryset("best-sellers"))

        self.assertEqual(offer_products, [self.first_product])
        self.assertEqual(best_seller_products, [self.second_product])

    def test_collection_type_is_normalized_on_save(self):
        item = HomeProductCollectionItem.objects.create(
            collection_type="3",
            product=self.first_product,
        )

        item.refresh_from_db()

        self.assertEqual(item.collection_type, HomeProductCollectionItem.COLLECTION_LATEST)

    def test_home_template_renders_curated_offer_without_public_cache(self):
        HomeProductCollectionItem.objects.create(
            collection_type=HomeProductCollectionItem.COLLECTION_OFFERS,
            product=self.second_product,
        )

        response = self.client.get(reverse("index"))

        self.assertContains(response, self.second_product.name)
        self.assertContains(response, 'data-api-url="/api/products/"')
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_home_template_renders_dashboard_hero_slides_with_links(self):
        image = SimpleUploadedFile(
            "hero.gif",
            b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )
        HeroSlide.objects.create(
            title="Dashboard hero",
            image=image,
            link_url="/products/",
            alt_text="Dashboard hero alt",
            order=0,
        )

        response = self.client.get(reverse("index"))

        self.assertContains(response, 'href="/products/"')
        self.assertContains(response, "Dashboard hero alt")
        self.assertContains(response, f"{settings.MEDIA_URL}home/slides/")
        self.assertNotContains(response, "image/slide.webp")

    def test_home_template_renders_one_dot_for_each_dashboard_hero_slide(self):
        for index in range(3):
            HeroSlide.objects.create(
                title=f"Dashboard hero {index}",
                image=f"home/slides/hero-{index}.gif",
                order=index,
            )

        response = self.client.get(reverse("index"))
        html = response.content.decode()

        self.assertEqual(len(re.findall(r'<div class="slide(?:\s|")', html)), 3)
        self.assertEqual(len(re.findall(r'<button type="button" class="dot(?:\s|")', html)), 3)

    def test_product_collection_api_returns_curated_latest_without_public_cache(self):
        HomeProductCollectionItem.objects.create(
            collection_type=HomeProductCollectionItem.COLLECTION_LATEST,
            product=self.first_product,
        )

        response = self.client.get(reverse("product_collection_api"), {"type": "latest"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["products"][0]["name"], self.first_product.name)
        self.assertIn("no-store", response.headers["Cache-Control"])
