from django.db import migrations


LEGACY_COLLECTION_ALIASES = {
    "1": "offers",
    "2": "best-sellers",
    "3": "latest",
}


def normalize_home_collection_types(apps, schema_editor):
    home_item = apps.get_model("products", "HomeProductCollectionItem")
    for legacy_value, canonical_value in LEGACY_COLLECTION_ALIASES.items():
        legacy_items = home_item.objects.filter(collection_type=legacy_value).order_by("order", "id")
        for legacy_item in legacy_items:
            canonical_item = home_item.objects.filter(
                collection_type=canonical_value,
                product_id=legacy_item.product_id,
            ).first()
            if canonical_item:
                update_fields = []
                if legacy_item.is_active and not canonical_item.is_active:
                    canonical_item.is_active = True
                    update_fields.append("is_active")
                if legacy_item.order < canonical_item.order:
                    canonical_item.order = legacy_item.order
                    update_fields.append("order")
                if update_fields:
                    canonical_item.save(update_fields=update_fields)
                legacy_item.delete()
            else:
                legacy_item.collection_type = canonical_value
                legacy_item.save(update_fields=["collection_type"])


def restore_legacy_home_collection_types(apps, schema_editor):
    home_item = apps.get_model("products", "HomeProductCollectionItem")
    for legacy_value, canonical_value in LEGACY_COLLECTION_ALIASES.items():
        home_item.objects.filter(collection_type=canonical_value).update(collection_type=legacy_value)


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0013_home_product_collection_item"),
    ]

    operations = [
        migrations.RunPython(normalize_home_collection_types, restore_legacy_home_collection_types),
    ]
