# Generated migration for multi-level pricing support
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        # Add fields to Pattern model
        migrations.AddField(
            model_name='pattern',
            name='has_sizes',
            field=models.BooleanField(default=False, help_text='هل هذا النمط يتطلب اختيار مقاس؟'),
        ),
        migrations.AddField(
            model_name='pattern',
            name='base_price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='السعر الأساسي للنمط (إذا لم يكن له مقاسات)', max_digits=10, null=True),
        ),
        
        # Add price field to ProductSize model
        migrations.AddField(
            model_name='productsize',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0, help_text='السعر لهذا المقاس على مستوى المنتج', max_digits=10),
            preserve_default=False,
        ),
        
        # Create PatternSize model
        migrations.CreateModel(
            name='PatternSize',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, help_text='السعر لهذا المقاس في هذا النمط', max_digits=10)),
                ('stock', models.IntegerField(default=0, help_text='المخزون المتاح لهذا المقاس في هذا النمط')),
                ('order', models.PositiveIntegerField(default=0)),
                ('pattern', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pattern_sizes', to='products.pattern')),
                ('size', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.size')),
            ],
            options={
                'verbose_name': 'مقاس نمط',
                'verbose_name_plural': 'مقاسات الأنماط',
                'ordering': ['order'],
                'unique_together': {('pattern', 'size')},
            },
        ),
        
        # Add indexes to ProductSize
        migrations.AddIndex(
            model_name='productsize',
            index=models.Index(fields=['product', 'size'], name='products_pr_product_idx'),
        ),
        
        # Add indexes to PatternSize
        migrations.AddIndex(
            model_name='patternsize',
            index=models.Index(fields=['pattern', 'size'], name='products_pa_pattern_idx'),
        ),
        migrations.AddIndex(
            model_name='patternsize',
            index=models.Index(fields=['pattern', 'stock'], name='products_pa_pattern_stock_idx'),
        ),
        
        # Add indexes to ProductVariant
        migrations.AddIndex(
            model_name='productvariant',
            index=models.Index(fields=['product', 'pattern', 'size'], name='products_pr_product_pattern_idx'),
        ),
        migrations.AddIndex(
            model_name='productvariant',
            index=models.Index(fields=['product', 'stock'], name='products_pr_product_stock_idx'),
        ),
        migrations.AddIndex(
            model_name='productvariant',
            index=models.Index(fields=['product', 'pattern', 'color', 'size'], name='products_pr_product_full_idx'),
        ),
        
        # Update ProductVariant price field help text
        migrations.AlterField(
            model_name='productvariant',
            name='price',
            field=models.DecimalField(decimal_places=2, help_text='DEPRECATED: Use Product.get_price() instead', max_digits=10),
        ),
    ]
