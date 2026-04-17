from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0001_initial"),
        ("products", "0008_add_product_type_colors_and_images"),
    ]

    operations = [
        migrations.AddField(
            model_name="cartitem",
            name="product_type",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="products.producttype"),
        ),
        migrations.AlterUniqueTogether(
            name="cartitem",
            unique_together={("cart", "product", "variant", "product_type")},
        ),
        migrations.AddField(
            model_name="orderitem",
            name="product_type",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="products.producttype"),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="type_name",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="النوع"),
        ),
    ]
