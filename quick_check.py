"""
سكريبت سريع للتحقق من بيانات المتغيرات
استخدم: python manage.py shell < quick_check.py
"""
import os
import django

# ضع اسم مشروعك هنا (اسم مجلد settings)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')  # عدلها لو اسم مشروعك مختلف

django.setup()
from products.models import Product, Pattern, PatternSize, ProductVariant, ProductColor

print("\n" + "="*80)
print("🔍 فحص سريع للبيانات")
print("="*80)

# اختر أول منتج له أنماط
products = Product.objects.filter(is_active=True)
print(f"\n📦 عدد المنتجات النشطة: {products.count()}")

for product in products:
    patterns = Pattern.objects.filter(product=product)
    if patterns.exists():
        print(f"\n{'='*80}")
        print(f"📦 المنتج: {product.name} (ID: {product.id})")
        print(f"   السعر: {product.price} ج.م")
        
        # الأنماط
        print(f"\n   🎨 الأنماط ({patterns.count()}):")
        for pattern in patterns:
            print(f"      - {pattern.name} (ID: {pattern.id})")
            print(f"        له مقاسات: {pattern.has_sizes}")
            print(f"        السعر الأساسي: {pattern.base_price or 'غير محدد'}")
            
            # المقاسات المرتبطة بالنمط
            if pattern.has_sizes:
                pattern_sizes = PatternSize.objects.filter(pattern=pattern)
                print(f"        المقاسات ({pattern_sizes.count()}):")
                for ps in pattern_sizes:
                    print(f"           * {ps.size.name}: {ps.price} ج.م (المخزون: {ps.stock})")
        
        # الألوان
        colors = ProductColor.objects.filter(product=product)
        print(f"\n   🌈 الألوان ({colors.count()}):")
        for pc in colors:
            print(f"      - {pc.color.name} ({pc.color.code})")
        
        # المتغيرات
        variants = ProductVariant.objects.filter(product=product)
        print(f"\n   🔄 المتغيرات ({variants.count()}):")
        
        if variants.exists():
            print("\n   تفاصيل المتغيرات:")
            print("   " + "-"*76)
            print(f"   {'النمط':<20} {'اللون':<20} {'المقاس':<15} {'المخزون':<10}")
            print("   " + "-"*76)
            
            for v in variants:
                pattern_name = v.pattern.name if v.pattern else "—"
                color_name = v.color.name if v.color else "—"
                size_name = v.size.name if v.size else "—"
                
                print(f"   {pattern_name:<20} {color_name:<20} {size_name:<15} {v.stock:<10}")
        else:
            print("   ⚠️  لا توجد متغيرات لهذا المنتج!")
        
        # التحقق من المشاكل المحتملة
        print(f"\n   🔍 التحقق من المشاكل:")
        
        # هل المقاسات مربوطة بالأنماط؟
        for pattern in patterns:
            if pattern.has_sizes:
                pattern_sizes = PatternSize.objects.filter(pattern=pattern)
                if not pattern_sizes.exists():
                    print(f"   ⚠️  النمط '{pattern.name}' مُعلّم كـ 'له مقاسات' لكن لا توجد مقاسات مرتبطة!")
                
                # هل توجد متغيرات لكل مقاس؟
                for ps in pattern_sizes:
                    variants_for_size = ProductVariant.objects.filter(
                        product=product,
                        pattern=pattern,
                        size=ps.size
                    )
                    if not variants_for_size.exists():
                        print(f"   ⚠️  لا توجد متغيرات للنمط '{pattern.name}' والمقاس '{ps.size.name}'")
                    
                    # هل توجد متغيرات لكل لون؟
                    for pc in colors:
                        variant_exists = ProductVariant.objects.filter(
                            product=product,
                            pattern=pattern,
                            color=pc.color,
                            size=ps.size
                        ).exists()
                        
                        if not variant_exists:
                            print(f"   ⚠️  مفقود: {pattern.name} + {pc.color.name} + {ps.size.name}")
        
        print("\n" + "="*80)
        break  # عرض منتج واحد فقط

print("\n✅ انتهى الفحص\n")
