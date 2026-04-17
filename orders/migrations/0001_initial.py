from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("products", "0008_add_product_type_colors_and_images"),
    ]

    operations = [
        migrations.CreateModel(
            name="Cart",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="cart", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "سلة تسوق",
                "verbose_name_plural": "سلات التسوق",
            },
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "في انتظار الدفع"), ("paid", "مدفوع"), ("processing", "قيد المعالجة"), ("shipped", "تم الشحن"), ("delivered", "تم التسليم"), ("cancelled", "ملغي")], default="pending", max_length=20)),
                ("total_price", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("shipping_address", models.TextField()),
                ("shipping_phone", models.CharField(max_length=20)),
                ("shipping_name", models.CharField(blank=True, default="", max_length=255)),
                ("shipping_city", models.CharField(blank=True, default="", max_length=100)),
                ("shipping_notes", models.TextField(blank=True, null=True)),
                ("payment_method", models.CharField(default="cash_on_delivery", max_length=50)),
                ("contact_method", models.CharField(choices=[("whatsapp", "واتساب"), ("call", "مكالمة هاتفية")], default="whatsapp", max_length=20, verbose_name="طريقة التواصل المفضلة")),
                ("order_notes", models.TextField(blank=True, help_text="أي ملاحظات إضافية للطلب", null=True, verbose_name="ملاحظات الطلب")),
                ("guest_email", models.EmailField(blank=True, max_length=254, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="orders", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "طلب",
                "verbose_name_plural": "الطلبات",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("pattern_name", models.CharField(blank=True, max_length=255, null=True, verbose_name="النمط")),
                ("color_name", models.CharField(blank=True, max_length=100, null=True, verbose_name="اللون")),
                ("color_code", models.CharField(blank=True, max_length=20, null=True, verbose_name="كود اللون")),
                ("size_name", models.CharField(blank=True, max_length=50, null=True, verbose_name="المقاس")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="orders.order")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="products.product")),
                ("variant", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="products.productvariant")),
            ],
            options={
                "verbose_name": "عنصر طلب",
                "verbose_name_plural": "عناصر الطلبات",
            },
        ),
        migrations.CreateModel(
            name="CartItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                ("cart", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="orders.cart")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="products.product")),
                ("variant", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="products.productvariant")),
            ],
            options={
                "verbose_name": "عنصر سلة",
                "verbose_name_plural": "عناصر السلات",
                "unique_together": {("cart", "product", "variant")},
            },
        ),
    ]
