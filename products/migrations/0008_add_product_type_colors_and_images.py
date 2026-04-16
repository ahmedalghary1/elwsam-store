from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0007_alter_producttype_description_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductTypeColor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveIntegerField(default=0)),
                ("color", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="product_type_colors", to="products.color")),
                ("product_type", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="type_colors", to="products.producttype")),
            ],
            options={
                "ordering": ["order"],
                "unique_together": {("product_type", "color")},
                "verbose_name": "لون نوع المنتج",
                "verbose_name_plural": "ألوان أنواع المنتجات",
            },
        ),
        migrations.AddIndex(
            model_name="producttypecolor",
            index=models.Index(fields=["product_type", "color"], name="products_pr_product_3dbd44_idx"),
        ),
        migrations.CreateModel(
            name="ProductTypeImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="product-types/")),
                ("order", models.PositiveIntegerField(default=0)),
                ("color", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="product_type_images", to="products.color")),
                ("product_type", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="type_images", to="products.producttype")),
            ],
            options={
                "ordering": ["order"],
                "verbose_name": "صورة نوع المنتج",
                "verbose_name_plural": "صور أنواع المنتجات",
            },
        ),
    ]
