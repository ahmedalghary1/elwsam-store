from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0009_add_category_active_flag"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="focus_keywords",
            field=models.TextField(blank=True, help_text="الكلمات المفتاحية الأساسية والفرعية"),
        ),
        migrations.AddField(
            model_name="product",
            name="internal_linking_suggestions",
            field=models.TextField(blank=True, help_text="اقتراحات الربط الداخلي لكل منتج"),
        ),
        migrations.AddField(
            model_name="product",
            name="meta_description",
            field=models.CharField(blank=True, help_text="وصف Meta Description مخصص", max_length=320),
        ),
        migrations.AddField(
            model_name="product",
            name="schema_markup",
            field=models.TextField(blank=True, help_text="Product JSON-LD schema جاهز إذا توفر"),
        ),
        migrations.AddField(
            model_name="product",
            name="seo_description",
            field=models.TextField(blank=True, help_text="وصف SEO طويل مخصص للظهور داخل صفحة المنتج"),
        ),
        migrations.AddField(
            model_name="product",
            name="seo_faq",
            field=models.TextField(blank=True, help_text="FAQ منسق بصيغة: س: ... ثم ج: ..."),
        ),
        migrations.AddField(
            model_name="product",
            name="seo_h1",
            field=models.CharField(blank=True, help_text="عنوان H1 مخصص داخل صفحة المنتج", max_length=255),
        ),
        migrations.AddField(
            model_name="product",
            name="seo_image_alt_texts",
            field=models.TextField(blank=True, help_text="اقتراحات Alt Text للصور، سطر لكل اقتراح"),
        ),
        migrations.AddField(
            model_name="product",
            name="seo_title",
            field=models.CharField(blank=True, help_text="عنوان SEO مخصص لصفحة المنتج", max_length=255),
        ),
    ]
