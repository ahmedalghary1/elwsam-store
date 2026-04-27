from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0012_add_category_seo_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="HomeProductCollectionItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "collection_type",
                    models.CharField(
                        choices=[
                            ("offers", "العروض"),
                            ("best-sellers", "الأفضل مبيعا"),
                            ("latest", "حديثا"),
                        ],
                        db_index=True,
                        max_length=32,
                        verbose_name="تبويب الصفحة الرئيسية",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="نشط")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="الترتيب")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="home_collection_items",
                        to="products.product",
                        verbose_name="المنتج",
                    ),
                ),
            ],
            options={
                "verbose_name": "عنصر تبويب الصفحة الرئيسية",
                "verbose_name_plural": "عناصر تبويبات الصفحة الرئيسية",
                "ordering": ["collection_type", "order", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="homeproductcollectionitem",
            index=models.Index(fields=["collection_type", "is_active", "order"], name="products_ho_collect_7bc669_idx"),
        ),
        migrations.AddConstraint(
            model_name="homeproductcollectionitem",
            constraint=models.UniqueConstraint(fields=("collection_type", "product"), name="unique_home_collection_product"),
        ),
    ]
