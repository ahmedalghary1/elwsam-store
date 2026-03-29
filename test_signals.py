import os
import sys
import django

# Fix encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from products.models import Pattern, PatternSize, ProductVariant, ProductColor, Size, Product
from django.db.models.signals import post_save

print("\n" + "="*80)
print("  🔍 تشخيص شامل لمشكلة عدم ظهور المقاسات الجديدة")
print("="*80)

# 1. التحقق من تحميل الـ Signals
print("\n1️⃣ التحقق من تحميل Signals:")
print("-" * 80)

try:
    from products import signals
    print("✅ ملف signals.py تم استيراده بنجاح")
    
    # التحقق من الـ receivers المسجلة
    receivers = post_save.receivers
    pattern_size_receivers = [r for r in receivers if 'PatternSize' in str(r)]
    
    print(f"   عدد receivers لـ post_save: {len(receivers)}")
    print(f"   عدد receivers لـ PatternSize: {len(pattern_size_receivers)}")
    
    if pattern_size_receivers:
        print("   ✅ Signals مسجلة بنجاح")
    else:
        print("   ❌ لا توجد signals مسجلة لـ PatternSize!")
        
except Exception as e:
    print(f"❌ خطأ في استيراد signals: {e}")

# 2. اختبار إنشاء PatternSize يدوياً
print("\n2️⃣ اختبار إنشاء PatternSize:")
print("-" * 80)

try:
    # الحصول على بيانات اختبار
    product = Product.objects.first()
    pattern = Pattern.objects.filter(product=product).first()
    
    if not pattern:
        print("❌ لا يوجد نمط للاختبار")
    else:
        print(f"   المنتج: {product.name}")
        print(f"   النمط: {pattern.name}")
        
        # الحصول على الألوان
        colors_count = ProductColor.objects.filter(product=product).count()
        print(f"   عدد الألوان: {colors_count}")
        
        # الحصول على مقاس للاختبار
        test_size = Size.objects.first()
        
        if test_size:
            print(f"   المقاس للاختبار: {test_size.name}")
            
            # التحقق من عدد المتغيرات قبل
            variants_before = ProductVariant.objects.filter(
                product=product,
                pattern=pattern,
                size=test_size
            ).count()
            
            print(f"\n   المتغيرات قبل إضافة PatternSize: {variants_before}")
            
            # محاولة إنشاء PatternSize (للاختبار فقط)
            print("\n   ⚠️  هذا اختبار فقط - لن يتم الحفظ الفعلي")
            print(f"   إذا تم إنشاء PatternSize للمقاس '{test_size.name}'")
            print(f"   يجب أن يتم إنشاء {colors_count} متغير تلقائياً")
            
except Exception as e:
    print(f"❌ خطأ في الاختبار: {e}")

# 3. فحص البيانات الحالية
print("\n3️⃣ فحص البيانات الحالية:")
print("-" * 80)

try:
    product = Product.objects.get(id=2)
    patterns = Pattern.objects.filter(product=product)
    
    for pattern in patterns:
        print(f"\n   النمط: {pattern.name}")
        
        # المقاسات في PatternSize
        pattern_sizes = PatternSize.objects.filter(pattern=pattern)
        print(f"   عدد PatternSize: {pattern_sizes.count()}")
        
        if pattern_sizes.exists():
            for ps in pattern_sizes:
                print(f"      - {ps.size.name}: {ps.price} ج.م")
                
                # المتغيرات لهذا المقاس
                variants = ProductVariant.objects.filter(
                    product=product,
                    pattern=pattern,
                    size=ps.size
                )
                print(f"        المتغيرات: {variants.count()}")
                
                if variants.count() == 0:
                    print(f"        ⚠️  لا توجد متغيرات لهذا المقاس!")
                    
                    # التحقق من الألوان
                    colors = ProductColor.objects.filter(product=product)
                    print(f"        الألوان المتاحة: {colors.count()}")
                    print(f"        المتوقع: {colors.count()} متغير")
                    print(f"        الموجود: 0 متغير")
                    print(f"        ❌ المشكلة: Signals لم تعمل!")
                    
except Exception as e:
    print(f"❌ خطأ: {e}")

# 4. التحقق من AppConfig
print("\n4️⃣ التحقق من AppConfig:")
print("-" * 80)

try:
    from django.apps import apps
    products_config = apps.get_app_config('products')
    
    print(f"   App name: {products_config.name}")
    print(f"   Verbose name: {products_config.verbose_name}")
    
    # التحقق من وجود ready method
    if hasattr(products_config, 'ready'):
        print("   ✅ ready() method موجودة")
    else:
        print("   ❌ ready() method غير موجودة!")
        
except Exception as e:
    print(f"❌ خطأ: {e}")

# 5. الحل المقترح
print("\n5️⃣ الحل المقترح:")
print("-" * 80)
print("""
المشكلة المحتملة:
1. Signals قد لا تكون مسجلة بشكل صحيح
2. AppConfig.ready() قد لا تُستدعى
3. قد يكون هناك خطأ في استيراد الـ signals

الحل:
1. التأكد من أن INSTALLED_APPS يستخدم 'products.apps.ProductsConfig'
2. إعادة تشغيل السيرفر بعد إضافة signals
3. استخدام admin actions كبديل للـ signals
""")

print("\n" + "="*80 + "\n")
