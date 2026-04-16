from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_add_product_stock'),
    ]

    operations = [
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'نوع',
                'verbose_name_plural': 'الأنواع',
            },
        ),
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(default=0)),
                ('image', models.ImageField(upload_to='product-types/')),
                ('price', models.DecimalField(decimal_places=2, help_text='السعر لهذا النوع على مستوى المنتج', max_digits=10)),
                ('description', models.TextField(help_text='الوصف الخاص بهذا النوع')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_types', to='products.product')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.type')),
            ],
            options={
                'verbose_name': 'نوع منتج',
                'verbose_name_plural': 'أنواع المنتجات',
                'ordering': ['order'],
                'unique_together': {('product', 'type')},
            },
        ),
        migrations.AddIndex(
            model_name='producttype',
            index=models.Index(fields=['product', 'type'], name='products_pr_product_5bf3c1_idx'),
        ),
    ]
