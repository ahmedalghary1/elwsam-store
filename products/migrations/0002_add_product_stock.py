# Generated manually for adding stock field to Product model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='stock',
            field=models.IntegerField(default=0, help_text='المخزون المتاح للمنتج البسيط (يُستخدم فقط إذا لم يكن للمنتج ألوان أو مقاسات أو أنماط)'),
        ),
    ]
