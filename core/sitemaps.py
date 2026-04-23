from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from products.models import Category, Product


class StaticViewSitemap(Sitemap):
    protocol = "https"

    def items(self):
        return ["index", "product_list", "category_list"]

    def location(self, item):
        return reverse(item)

    def changefreq(self, item):
        if item == "index":
            return "daily"
        if item == "product_list":
            return "daily"
        return "weekly"

    def priority(self, item):
        if item == "index":
            return 1.0
        if item == "product_list":
            return 0.9
        return 0.8

    def lastmod(self, item):
        if item in {"index", "product_list"}:
            latest_product = Product.objects.filter(is_active=True).order_by("-updated_at").first()
            return latest_product.updated_at if latest_product else None
        latest_category = Category.objects.filter(is_active=True).order_by("-updated_at").first()
        return latest_category.updated_at if latest_category else None


class CategorySitemap(Sitemap):
    protocol = "https"
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Category.objects.filter(is_active=True).order_by("order")

    def lastmod(self, obj):
        return obj.updated_at


class ProductSitemap(Sitemap):
    protocol = "https"
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Product.objects.filter(is_active=True).order_by("order")

    def lastmod(self, obj):
        return obj.updated_at
