import os
import django
import sys

# =========================
# إعداد Django
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

# =========================
# Imports
# =========================
from django.utils.text import slugify
from django.db import transaction
from products.models import Product, ProductVariant, ProductImage

BATCH_SIZE = 200


def generate_unique_slug(name, existing_slugs):
    base_slug = slugify(name, allow_unicode=True) or "product"
    slug = base_slug
    counter = 1

    while slug in existing_slugs:
        slug = f"{base_slug}-{counter}"
        counter += 1

    existing_slugs.add(slug)
    return slug


def build_name(variant):
    parts = [variant.product.name]

    if variant.pattern:
        parts.append(variant.pattern.name)
    if variant.color:
        parts.append(variant.color.name)
    if variant.size:
        parts.append(variant.size.name)

    return " - ".join(parts)


def main():
    print("🚀 Start...\n")

    existing_slugs = set(Product.objects.values_list('slug', flat=True))

    variants = list(
        ProductVariant.objects.select_related(
            'product', 'pattern', 'color', 'size'
        )
    )

    print(f"📦 Variants: {len(variants)}\n")

    created_count = 0
    image_count = 0

    with transaction.atomic():

        for i in range(0, len(variants), BATCH_SIZE):

            batch = variants[i:i+BATCH_SIZE]

            products_to_create = []
            variant_map = {}

            # =========================
            # تجهيز المنتجات
            # =========================
            for v in batch:
                name = build_name(v)
                slug = generate_unique_slug(name, existing_slugs)

                p = Product(
                    name=name,
                    slug=slug,
                    description=v.product.description,
                    category=v.product.category,
                    price=v.get_price(),
                    is_active=True,
                    has_patterns=False,
                    has_product_level_sizes=False,
                    has_colors=False,
                )

                products_to_create.append(p)
                variant_map[slug] = v  # 🔥 ربط آمن

            # =========================
            # bulk create
            # =========================
            Product.objects.bulk_create(products_to_create, batch_size=BATCH_SIZE)

            # =========================
            # جلب المنتجات
            # =========================
            created_products = Product.objects.filter(
                slug__in=[p.slug for p in products_to_create]
            )

            images_to_create = []

            for p in created_products:
                v = variant_map[p.slug]
                base = v.product

                images_added = False

                # 1. pattern + color
                if v.pattern:
                    imgs = v.pattern.pattern_images.filter(color=v.color)

                    for img in imgs:
                        images_to_create.append(ProductImage(
                            product=p,
                            image=img.image,
                            order=img.order,
                            color=v.color
                        ))
                        image_count += 1
                        images_added = True

                # 2. product color
                if not images_added and v.color:
                    imgs = base.images.filter(color=v.color)

                    for img in imgs:
                        images_to_create.append(ProductImage(
                            product=p,
                            image=img.image,
                            order=img.order,
                            color=v.color
                        ))
                        image_count += 1
                        images_added = True

                # 3. fallback
                if not images_added:
                    for img in base.images.all():
                        images_to_create.append(ProductImage(
                            product=p,
                            image=img.image,
                            order=img.order,
                            color=None
                        ))
                        image_count += 1

            ProductImage.objects.bulk_create(images_to_create)

            created_count += len(products_to_create)

            print(f"✅ {created_count}/{len(variants)} done")

    print("\n🎯 DONE")
    print(f"Products: {created_count}")
    print(f"Images: {image_count}")


if __name__ == "__main__":
    main()