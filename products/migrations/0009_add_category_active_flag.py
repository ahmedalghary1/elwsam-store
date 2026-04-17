from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0008_add_product_type_colors_and_images"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="is_active",
            field=models.BooleanField(default=True, help_text="Active visibility flag for categories"),
        ),
    ]
