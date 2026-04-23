from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0011_clean_invalid_slugs"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="seo_title",
            field=models.CharField(blank=True, help_text="Custom SEO title for category pages", max_length=255),
        ),
        migrations.AddField(
            model_name="category",
            name="meta_description",
            field=models.CharField(blank=True, help_text="Custom meta description for category pages", max_length=320),
        ),
        migrations.AddField(
            model_name="category",
            name="seo_intro",
            field=models.TextField(blank=True, help_text="Intro content displayed on category pages"),
        ),
    ]
