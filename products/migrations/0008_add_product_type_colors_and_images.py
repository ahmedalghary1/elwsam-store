from django.db import migrations


class Migration(migrations.Migration):
    """
    Compatibility migration.

    ProductTypeColor and ProductTypeImage were already introduced in 0003.
    This placeholder keeps the historical numbering intact without trying to
    recreate tables or depending on a missing 0007 migration.
    """

    dependencies = [
        ("products", "0003_product_types"),
    ]

    operations = []
