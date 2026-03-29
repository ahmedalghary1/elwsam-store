import os
import sys
import django

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from products.models import Product, Pattern, PatternSize, ProductVariant, Size
from django.db import transaction

print("\n" + "="*80)
print("  🔧 إنشاء PatternSize من ProductVariant الموجودة")
print("="*80)

product_id = 2
product = Product.objects.get(id=product_id)

print(f"\nالمنتج: {product.name} (ID: {product_id})")

patterns = Pattern.objects.filter(product=product, has_sizes=True)

with transaction.atomic():
    created_count = 0
    
    for pattern in patterns:
        print(f"\n📌 النمط: {pattern.name}")
        
        # الحصول على جميع المقاسات الفريدة من ProductVariant
        variant_sizes = ProductVariant.objects.filter(
            product=product,
            pattern=pattern,
            size__isnull=False
        ).values_list('size', flat=True).distinct()
        
        print(f"   المقاسات الموجودة في Variants: {variant_sizes.count()}")
        
        for size_id in variant_sizes:
            size = Size.objects.get(id=size_id)
            
            # تحقق من عدم وجود PatternSize
            if not PatternSize.objects.filter(pattern=pattern, size=size).exists():
                # احسب متوسط السعر من Variants
                variants = ProductVariant.objects.filter(
                    product=product,
                    pattern=pattern,
                    size=size
                )
                
                avg_price = variants.first().price if variants.exists() else pattern.base_price or product.price
                total_stock = sum(v.stock for v in variants)
                
                # إنشاء PatternSize
                ps = PatternSize.objects.create(
                    pattern=pattern,
                    size=size,
                    price=avg_price,
                    stock=total_stock,
                    order=0
                )
                
                print(f"   ✅ تم إنشاء: {size.name} - {avg_price} ج.م (مخزون: {total_stock})")
                created_count += 1
            else:
                print(f"   ⏭️  موجود: {size.name}")
    
    print(f"\n{'='*80}")
    print(f"✅ تم إنشاء {created_count} PatternSize")
    print(f"{'='*80}\n")
