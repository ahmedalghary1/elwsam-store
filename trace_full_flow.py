import os
import sys
import django

# Fix encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from products.models import Product, Pattern, PatternSize, ProductVariant, ProductColor, Size

print("\n" + "="*80)
print("  🔍 تتبع كامل لمسار البيانات من PatternSize إلى الواجهة")
print("="*80)

# المنتج للاختبار
product_id = 2
product = Product.objects.get(id=product_id)

print(f"\n📦 المنتج: {product.name} (ID: {product_id})")
print("="*80)

# 1. فحص الأنماط
print("\n1️⃣ الأنماط (Pattern):")
patterns = Pattern.objects.filter(product=product)
for pattern in patterns:
    print(f"\n   النمط: {pattern.name} (ID: {pattern.id})")
    print(f"   has_sizes: {pattern.has_sizes}")
    
    # 2. فحص PatternSize
    print(f"\n   2️⃣ PatternSize المرتبطة:")
    pattern_sizes = PatternSize.objects.filter(pattern=pattern)
    print(f"   عدد PatternSize: {pattern_sizes.count()}")
    
    for ps in pattern_sizes:
        print(f"      ✓ {ps.size.name}: {ps.price} ج.م (مخزون: {ps.stock})")
        
        # 3. فحص ProductVariant لهذا المقاس
        print(f"        3️⃣ ProductVariant لهذا المقاس:")
        variants = ProductVariant.objects.filter(
            product=product,
            pattern=pattern,
            size=ps.size
        )
        print(f"        عدد Variants: {variants.count()}")
        
        if variants.count() == 0:
            print(f"        ❌ لا توجد متغيرات! هذا هو السبب!")
            
            # التحقق من الألوان المتاحة
            colors = ProductColor.objects.filter(product=product)
            print(f"        الألوان المتاحة: {colors.count()}")
            for pc in colors:
                print(f"          - {pc.color.name}")
        else:
            for v in variants:
                color_name = v.color.name if v.color else "بدون لون"
                print(f"          ✓ {color_name}: {v.price} ج.م (مخزون: {v.stock})")

# 4. محاكاة API call
print("\n" + "="*80)
print("4️⃣ محاكاة API Call:")
print("="*80)

pattern_id = 1
color_id = 1

print(f"\nالطلب: /api/variant-options/{product_id}/?pattern_id={pattern_id}&color_id={color_id}")

try:
    pattern = Pattern.objects.get(id=pattern_id)
    print(f"\nالنمط: {pattern.name}")
    print(f"has_sizes: {pattern.has_sizes}")
    
    if pattern.has_sizes:
        # هذا هو الكود الفعلي من views.py
        pattern_sizes = PatternSize.objects.filter(
            pattern=pattern
        ).select_related('size').order_by('order')
        
        print(f"\nعدد PatternSize: {pattern_sizes.count()}")
        
        sizes_data = []
        for ps in pattern_sizes:
            # التحقق من المتغيرات
            filter_kwargs = {
                'product': product,
                'pattern_id': pattern_id,
                'size': ps.size
            }
            if color_id:
                filter_kwargs['color_id'] = color_id
            
            variant_exists = ProductVariant.objects.filter(**filter_kwargs).exists()
            has_stock = ProductVariant.objects.filter(
                **filter_kwargs,
                stock__gt=0
            ).exists() if variant_exists else (ps.stock > 0)
            
            size_info = {
                'id': ps.size.id,
                'name': ps.size.name,
                'available': has_stock,
                'price': str(ps.price),
                'stock': ps.stock
            }
            sizes_data.append(size_info)
            
            print(f"\n   المقاس: {ps.size.name}")
            print(f"   variant_exists: {variant_exists}")
            print(f"   has_stock: {has_stock}")
            print(f"   سيتم إرجاعه في API: {size_info}")
        
        print(f"\n📊 النتيجة النهائية:")
        print(f"   sizes_data: {sizes_data}")
        print(f"   عدد المقاسات المُرجعة: {len(sizes_data)}")
        
        if len(sizes_data) == 0:
            print("\n   ❌ المشكلة: لا توجد مقاسات في PatternSize!")
        elif len(sizes_data) > 0:
            print("\n   ✅ المقاسات موجودة في PatternSize")
            
            # التحقق من ProductVariant
            total_variants = ProductVariant.objects.filter(
                product=product,
                pattern=pattern,
                color_id=color_id
            ).count()
            
            print(f"\n   التحقق من ProductVariant:")
            print(f"   عدد Variants للنمط + اللون: {total_variants}")
            
            if total_variants == 0:
                print(f"   ❌ المشكلة: لا توجد ProductVariant!")
                print(f"   الحل: تشغيل زر 'إنشاء المتغيرات تلقائياً' في الأدمن")

except Exception as e:
    print(f"\n❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80 + "\n")
