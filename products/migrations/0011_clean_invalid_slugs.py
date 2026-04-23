import re

from django.db import migrations
from django.utils.text import slugify


def clean_slug(value, fallback):
    raw_value = (value or fallback or "").strip()
    raw_value = re.sub(r"[\\/%?#]+", "-", raw_value)
    raw_value = re.sub(r"\s+", " ", raw_value)
    return slugify(raw_value, allow_unicode=True) or fallback


def unique_slug(model_class, instance, value, fallback):
    base_slug = clean_slug(value, fallback)
    candidate = base_slug
    counter = 1
    while model_class.objects.filter(slug=candidate).exclude(pk=instance.pk).exists():
        candidate = f"{base_slug}-{counter}"
        counter += 1
    return candidate


def clean_existing_slugs(apps, schema_editor):
    for model_name, fallback in (("Category", "category"), ("Product", "product")):
        model_class = apps.get_model("products", model_name)
        for instance in model_class.objects.all().only("id", "name", "slug"):
            cleaned_slug = clean_slug(instance.slug or instance.name, fallback)
            if cleaned_slug != instance.slug:
                instance.slug = unique_slug(model_class, instance, cleaned_slug, fallback)
                instance.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0010_add_product_seo_fields"),
    ]

    operations = [
        migrations.RunPython(clean_existing_slugs, migrations.RunPython.noop),
    ]
