# Generated migration for adding variant details to OrderItem

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='pattern_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='النمط'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='color_name',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='اللون'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='color_code',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='كود اللون'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='size_name',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='المقاس'),
        ),
    ]
