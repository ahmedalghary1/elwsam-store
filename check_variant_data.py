#!/usr/bin/env python
"""
سكريبت للتحقق من بيانات المنتجات والأنماط والألوان والمقاسات
"""

import os
import django

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from products.models import (
    Product, Pattern, Color, Size, ProductColor, ProductSize, 
    PatternSize, ProductVariant
)

def print_separator(title=""):
    """طباعة خط فاصل"""
    print("\n" + "="*80)
    if title:
        print(f"  {title}")
        print("="*80)

def check_product_data():
    """التحقق من بيانات المنتجات"""
    print_separator("📦 المنتجات")
    
    products = Product.objects.filter(is_active=True)
    print(f"عدد المنتجات النشطة: {products.count()}")
    
    for product in products[:5]:  # عرض أول 5 منتجات
        print(f"\n🔹 المنتج: {product.name} (ID: {product.id})")
        print(f"   السعر: {product.price} ج.م")
        print(f"   له أنماط: {product.has_patterns()}")
        print(f"   له مقاسات على مستوى المنتج: {product.has_product_level_sizes()}")
        
        # عدد الأنماط
        patterns_count = Pattern.objects.filter(product=product).count()
        print(f"   عدد الأنماط: {patterns_count}")
        
        # عدد الألوان
        colors_count = ProductColor.objects.filter(product=product).count()
        print(f"   عدد الألوان: {colors_count}")
        
        # عدد المقاسات على مستوى المنتج
        sizes_count = ProductSize.objects.filter(product=product).count()
        print(f"   عدد المقاسات (مستوى المنتج): {sizes_count}")
        
        # عدد المتغيرات
        variants_count = ProductVariant.objects.filter(product=product).count()
        print(f"   عدد المتغيرات (Variants): {variants_count}")

def check_patterns():
    """التحقق من بيانات الأنماط"""
    print_separator("🎨 الأنماط (Patterns)")
    
    patterns = Pattern.objects.all()
    print(f"عدد الأنماط الكلي: {patterns.count()}")
    
    for pattern in patterns:
        print(f"\n🔹 النمط: {pattern.name} (ID: {pattern.id})")
        print(f"   المنتج: {pattern.product.name}")
        print(f"   له مقاسات: {pattern.has_sizes}")
        print(f"   السعر الأساسي: {pattern.base_price or 'غير محدد'}")
        
        # المقاسات المرتبطة بالنمط
        if pattern.has_sizes:
            pattern_sizes = PatternSize.objects.filter(pattern=pattern)
            print(f"   عدد المقاسات المرتبطة: {pattern_sizes.count()}")
            for ps in pattern_sizes:
                print(f"      - {ps.size.name}: {ps.price} ج.م (المخزون: {ps.stock})")
        
        # المتغيرات المرتبطة بالنمط
        variants = ProductVariant.objects.filter(pattern=pattern)
        print(f"   عدد المتغيرات: {variants.count()}")

def check_colors():
    """التحقق من بيانات الألوان"""
    print_separator("🌈 الألوان")
    
    colors = Color.objects.all()
    print(f"عدد الألوان الكلي: {colors.count()}")
    
    for color in colors[:10]:  # عرض أول 10 ألوان
        print(f"\n🔹 اللون: {color.name} (ID: {color.id})")
        print(f"   الكود: {color.code}")
        
        # المنتجات التي تستخدم هذا اللون
        product_colors = ProductColor.objects.filter(color=color)
        print(f"   عدد المنتجات: {product_colors.count()}")
        
        # المتغيرات التي تستخدم هذا اللون
        variants = ProductVariant.objects.filter(color=color)
        print(f"   عدد المتغيرات: {variants.count()}")

def check_sizes():
    """التحقق من بيانات المقاسات"""
    print_separator("📏 المقاسات")
    
    sizes = Size.objects.all()
    print(f"عدد المقاسات الكلي: {sizes.count()}")
    
    for size in sizes:
        print(f"\n🔹 المقاس: {size.name} (ID: {size.id})")
        
        # المنتجات التي تستخدم هذا المقاس (مستوى المنتج)
        product_sizes = ProductSize.objects.filter(size=size)
        print(f"   عدد المنتجات (مستوى المنتج): {product_sizes.count()}")
        
        # الأنماط التي تستخدم هذا المقاس
        pattern_sizes = PatternSize.objects.filter(size=size)
        print(f"   عدد الأنماط (مستوى النمط): {pattern_sizes.count()}")
        
        # المتغيرات التي تستخدم هذا المقاس
        variants = ProductVariant.objects.filter(size=size)
        print(f"   عدد المتغيرات: {variants.count()}")

def check_variants():
    """التحقق من بيانات المتغيرات"""
    print_separator("🔄 المتغيرات (ProductVariant)")
    
    variants = ProductVariant.objects.all()
    print(f"عدد المتغيرات الكلي: {variants.count()}")
    
    # تجميع حسب المنتج
    products_with_variants = Product.objects.filter(
        variants__isnull=False
    ).distinct()
    
    print(f"عدد المنتجات التي لها متغيرات: {products_with_variants.count()}")
    
    for product in products_with_variants[:3]:  # عرض أول 3 منتجات
        print(f"\n🔹 المنتج: {product.name}")
        product_variants = ProductVariant.objects.filter(product=product)
        
        for variant in product_variants[:5]:  # عرض أول 5 متغيرات
            pattern_name = variant.pattern.name if variant.pattern else "بدون نمط"
            color_name = variant.color.name if variant.color else "بدون لون"
            size_name = variant.size.name if variant.size else "بدون مقاس"
            
            print(f"   - {pattern_name} | {color_name} | {size_name}")
            print(f"     السعر: {variant.price} ج.م | المخزون: {variant.stock}")

def check_pattern_size_relationship():
    """التحقق من العلاقة بين الأنماط والمقاسات"""
    print_separator("🔗 العلاقة بين الأنماط والمقاسات")
    
    patterns_with_sizes = Pattern.objects.filter(has_sizes=True)
    print(f"عدد الأنماط التي لها مقاسات: {patterns_with_sizes.count()}")
    
    for pattern in patterns_with_sizes:
        print(f"\n🔹 النمط: {pattern.name} (المنتج: {pattern.product.name})")
        
        # المقاسات المرتبطة
        pattern_sizes = PatternSize.objects.filter(pattern=pattern)
        print(f"   المقاسات المرتبطة ({pattern_sizes.count()}):")
        
        for ps in pattern_sizes:
            print(f"      - {ps.size.name}: {ps.price} ج.م (المخزون: {ps.stock})")
            
            # التحقق من وجود متغيرات لهذا النمط والمقاس
            variants = ProductVariant.objects.filter(
                pattern=pattern,
                size=ps.size
            )
            print(f"        المتغيرات: {variants.count()}")
            
            if variants.exists():
                for v in variants:
                    color_name = v.color.name if v.color else "بدون لون"
                    print(f"          * {color_name}: {v.stock} في المخزون")

def check_specific_product(product_id=None):
    """التحقق من منتج محدد"""
    if not product_id:
        print("\n⚠️  لم يتم تحديد ID المنتج")
        return
    
    print_separator(f"🔍 فحص تفصيلي للمنتج ID: {product_id}")
    
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        print(f"❌ المنتج ID {product_id} غير موجود")
        return
    
    print(f"📦 المنتج: {product.name}")
    print(f"   السعر: {product.price} ج.م")
    print(f"   نشط: {product.is_active}")
    
    # الأنماط
    patterns = Pattern.objects.filter(product=product)
    print(f"\n🎨 الأنماط ({patterns.count()}):")
    for pattern in patterns:
        print(f"   - {pattern.name} (ID: {pattern.id})")
        print(f"     له مقاسات: {pattern.has_sizes}")
        print(f"     السعر الأساسي: {pattern.base_price or 'غير محدد'}")
        
        if pattern.has_sizes:
            pattern_sizes = PatternSize.objects.filter(pattern=pattern)
            print(f"     المقاسات ({pattern_sizes.count()}):")
            for ps in pattern_sizes:
                print(f"        * {ps.size.name}: {ps.price} ج.م (المخزون: {ps.stock})")
    
    # الألوان
    colors = ProductColor.objects.filter(product=product)
    print(f"\n🌈 الألوان ({colors.count()}):")
    for pc in colors:
        print(f"   - {pc.color.name} ({pc.color.code})")
    
    # المقاسات على مستوى المنتج
    sizes = ProductSize.objects.filter(product=product)
    print(f"\n📏 المقاسات على مستوى المنتج ({sizes.count()}):")
    for ps in sizes:
        print(f"   - {ps.size.name}: {ps.price} ج.م")
    
    # المتغيرات
    variants = ProductVariant.objects.filter(product=product)
    print(f"\n🔄 المتغيرات ({variants.count()}):")
    for variant in variants:
        pattern_name = variant.pattern.name if variant.pattern else "—"
        color_name = variant.color.name if variant.color else "—"
        size_name = variant.size.name if variant.size else "—"
        
        print(f"   - {pattern_name} | {color_name} | {size_name}")
        print(f"     السعر: {variant.price} ج.م | المخزون: {variant.stock}")

def main():
    """الدالة الرئيسية"""
    print("\n" + "🔍 " * 20)
    print("   سكريبت فحص بيانات المنتجات والمتغيرات")
    print("🔍 " * 20)
    
    # فحص عام
    check_product_data()
    check_patterns()
    check_colors()
    check_sizes()
    check_variants()
    check_pattern_size_relationship()
    
    # فحص منتج محدد (غيّر الرقم حسب حاجتك)
    print("\n" + "="*80)
    product_id = input("\nأدخل ID المنتج للفحص التفصيلي (أو اضغط Enter للتخطي): ")
    if product_id:
        try:
            check_specific_product(int(product_id))
        except ValueError:
            print("❌ الرجاء إدخال رقم صحيح")
    
    print_separator("✅ انتهى الفحص")

if __name__ == "__main__":
    main()
