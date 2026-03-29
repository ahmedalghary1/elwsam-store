import os
import sys
import django

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from products.models import Product, Pattern, PatternSize, ProductVariant, ProductColor

# فحص المنتج ID 2
product_id = 2
product = Product.objects.get(id=product_id)

print(f"\n{'='*80}")
print(f"المنتج: {product.name} (ID: {product_id})")
print(f"{'='*80}")

# الأنماط
patterns = Pattern.objects.filter(product=product)
print(f"\nالأنماط ({patterns.count()}):")
for pattern in patterns:
    print(f"  - {pattern.name} (ID: {pattern.id})")
    print(f"    has_sizes: {pattern.has_sizes}")
    print(f"    base_price: {pattern.base_price}")
    
    # المقاسات المرتبطة بالنمط
    pattern_sizes = PatternSize.objects.filter(pattern=pattern)
    print(f"    PatternSize count: {pattern_sizes.count()}")
    
    if pattern_sizes.exists():
        print(f"    المقاسات:")
        for ps in pattern_sizes:
            print(f"      * {ps.size.name}: {ps.price} ج.م (مخزون: {ps.stock})")
    else:
        print(f"    ⚠️  لا توجد مقاسات في PatternSize!")

# الألوان
colors = ProductColor.objects.filter(product=product)
print(f"\nالألوان ({colors.count()}):")
for pc in colors:
    print(f"  - {pc.color.name} (ID: {pc.color.id})")

# المتغيرات
variants = ProductVariant.objects.filter(product=product)
print(f"\nالمتغيرات ({variants.count()}):")
if variants.exists():
    for v in variants[:5]:
        pattern_name = v.pattern.name if v.pattern else "—"
        color_name = v.color.name if v.color else "—"
        size_name = v.size.name if v.size else "—"
        print(f"  - {pattern_name} | {color_name} | {size_name} | مخزون: {v.stock}")
else:
    print("  ⚠️  لا توجد متغيرات!")

# محاكاة الـ API call
print(f"\n{'='*80}")
print("محاكاة API Call:")
print(f"{'='*80}")

pattern_id = 1
color_id = 1

try:
    pattern = Pattern.objects.get(id=pattern_id)
    print(f"\nالنمط: {pattern.name}")
    print(f"has_sizes: {pattern.has_sizes}")
    
    if pattern.has_sizes:
        pattern_sizes = PatternSize.objects.filter(pattern=pattern).select_related('size')
        print(f"PatternSize count: {pattern_sizes.count()}")
        
        if pattern_sizes.exists():
            print("\nالمقاسات التي يجب أن تُرجع:")
            for ps in pattern_sizes:
                print(f"  - {ps.size.name}: {ps.price} ج.م (مخزون: {ps.stock})")
        else:
            print("\n⚠️  لا توجد مقاسات في PatternSize - هذا هو السبب!")
    else:
        print("\n⚠️  النمط has_sizes=False - لن يتم إرجاع مقاسات")
        
except Pattern.DoesNotExist:
    print(f"\n❌ النمط ID {pattern_id} غير موجود!")

print(f"\n{'='*80}\n")
