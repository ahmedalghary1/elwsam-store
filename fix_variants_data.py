#!/usr/bin/env python
"""
سكريبت شامل لإصلاح بيانات المنتجات والمتغيرات
=================================================

المهام:
1. إصلاح Pattern.has_sizes بناءً على الـ Variants الموجودة
2. إنشاء جميع التركيبات الناقصة من Variants
3. التحقق من صحة البيانات
4. إخراج تقرير مفصل

الاستخدام:
    python fix_variants_data.py
"""

import os
import sys
import django
from decimal import Decimal
from collections import defaultdict

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.db import transaction
from django.core.exceptions import ValidationError
from products.models import (
    Product, Pattern, Color, Size, ProductColor, ProductSize,
    PatternSize, ProductVariant
)


class VariantDataFixer:
    """فئة لإصلاح بيانات المتغيرات"""
    
    def __init__(self):
        self.report = {
            'patterns_fixed': 0,
            'variants_created': 0,
            'variants_skipped': 0,
            'errors': [],
            'warnings': [],
            'products_processed': 0,
        }
    
    def print_header(self, title):
        """طباعة عنوان"""
        print("\n" + "="*80)
        print(f"  {title}")
        print("="*80)
    
    def print_section(self, title):
        """طباعة قسم فرعي"""
        print(f"\n{'─'*80}")
        print(f"  {title}")
        print(f"{'─'*80}")
    
    def fix_pattern_has_sizes(self):
        """
        إصلاح حقل has_sizes في Pattern بناءً على الـ Variants الموجودة
        """
        self.print_header("🔧 إصلاح Pattern.has_sizes")
        
        patterns = Pattern.objects.all()
        fixed_count = 0
        
        for pattern in patterns:
            # تحقق من وجود variants لهذا النمط تحتوي على sizes
            variants_with_size = ProductVariant.objects.filter(
                pattern=pattern,
                size__isnull=False
            ).exists()
            
            # تحقق من وجود PatternSize
            has_pattern_sizes = PatternSize.objects.filter(pattern=pattern).exists()
            
            should_have_sizes = variants_with_size or has_pattern_sizes
            
            if pattern.has_sizes != should_have_sizes:
                old_value = pattern.has_sizes
                pattern.has_sizes = should_have_sizes
                pattern.save(update_fields=['has_sizes'])
                
                print(f"✅ تم إصلاح: {pattern.product.name} - {pattern.name}")
                print(f"   القيمة القديمة: {old_value} → القيمة الجديدة: {should_have_sizes}")
                
                fixed_count += 1
                self.report['patterns_fixed'] += 1
        
        if fixed_count == 0:
            print("✅ جميع الأنماط صحيحة - لا يوجد ما يحتاج إصلاح")
        else:
            print(f"\n📊 تم إصلاح {fixed_count} نمط")
    
    def get_product_combinations(self, product):
        """
        الحصول على جميع التركيبات الممكنة للمنتج
        
        Returns:
            list: قائمة من tuples (pattern, color, size)
        """
        combinations = []
        
        # الحصول على جميع الأنماط
        patterns = Pattern.objects.filter(product=product)
        
        # الحصول على جميع الألوان
        product_colors = ProductColor.objects.filter(product=product).select_related('color')
        colors = [pc.color for pc in product_colors]
        
        if not patterns.exists():
            self.report['warnings'].append(
                f"المنتج '{product.name}' ليس له أنماط - سيتم تخطيه"
            )
            return combinations
        
        if not colors:
            self.report['warnings'].append(
                f"المنتج '{product.name}' ليس له ألوان - سيتم تخطيه"
            )
            return combinations
        
        # لكل نمط
        for pattern in patterns:
            # تحقق إذا كان النمط يحتاج مقاسات
            if pattern.has_sizes:
                # الحصول على المقاسات من PatternSize
                pattern_sizes = PatternSize.objects.filter(
                    pattern=pattern
                ).select_related('size')
                
                if not pattern_sizes.exists():
                    self.report['warnings'].append(
                        f"النمط '{pattern.name}' مُعلّم كـ has_sizes=True لكن لا توجد مقاسات في PatternSize"
                    )
                    continue
                
                sizes = [ps.size for ps in pattern_sizes]
                
                # إنشاء تركيبة: pattern × color × size
                for color in colors:
                    for size in sizes:
                        combinations.append((pattern, color, size))
            else:
                # النمط بدون مقاسات: pattern × color
                for color in colors:
                    combinations.append((pattern, color, None))
        
        return combinations
    
    def get_variant_price(self, product, pattern, color, size):
        """
        حساب السعر للمتغير بناءً على التسلسل الهرمي
        """
        return product.get_price(
            pattern_id=pattern.id if pattern else None,
            size_id=size.id if size else None,
            color_id=color.id if color else None
        )
    
    def get_variant_stock(self, pattern, size):
        """
        الحصول على المخزون الافتراضي
        """
        # إذا كان هناك PatternSize، استخدم المخزون منه
        if pattern and size:
            try:
                ps = PatternSize.objects.get(pattern=pattern, size=size)
                return ps.stock
            except PatternSize.DoesNotExist:
                pass
        
        # افتراضي: 0 (يجب تحديثه يدوياً)
        return 0
    
    def create_missing_variants(self, dry_run=False):
        """
        إنشاء جميع المتغيرات الناقصة
        
        Args:
            dry_run: إذا كان True، لا يتم الحفظ فعلياً (فقط عرض)
        """
        self.print_header("🔄 إنشاء المتغيرات الناقصة")
        
        if dry_run:
            print("⚠️  وضع المعاينة (Dry Run) - لن يتم حفظ أي تغييرات")
        
        products = Product.objects.filter(is_active=True)
        
        for product in products:
            self.report['products_processed'] += 1
            
            print(f"\n📦 معالجة: {product.name} (ID: {product.id})")
            
            # الحصول على جميع التركيبات الممكنة
            combinations = self.get_product_combinations(product)
            
            if not combinations:
                print("   ⏭️  تم التخطي - لا توجد تركيبات ممكنة")
                continue
            
            print(f"   📊 عدد التركيبات الممكنة: {len(combinations)}")
            
            # التحقق من المتغيرات الموجودة
            existing_variants = set()
            for variant in ProductVariant.objects.filter(product=product):
                key = (
                    variant.pattern_id,
                    variant.color_id,
                    variant.size_id
                )
                existing_variants.add(key)
            
            print(f"   ✅ المتغيرات الموجودة: {len(existing_variants)}")
            
            # إنشاء المتغيرات الناقصة
            variants_to_create = []
            created_count = 0
            skipped_count = 0
            
            for pattern, color, size in combinations:
                key = (
                    pattern.id if pattern else None,
                    color.id if color else None,
                    size.id if size else None
                )
                
                if key in existing_variants:
                    skipped_count += 1
                    continue
                
                # حساب السعر
                price = self.get_variant_price(product, pattern, color, size)
                
                # الحصول على المخزون
                stock = self.get_variant_stock(pattern, size)
                
                # إنشاء المتغير
                variant = ProductVariant(
                    product=product,
                    pattern=pattern,
                    color=color,
                    size=size,
                    price=price,
                    stock=stock,
                    order=0
                )
                
                variants_to_create.append(variant)
                created_count += 1
                
                # عرض التفاصيل
                pattern_name = pattern.name if pattern else "—"
                color_name = color.name if color else "—"
                size_name = size.name if size else "—"
                
                print(f"   ➕ جديد: {pattern_name} | {color_name} | {size_name} | {price} ج.م | مخزون: {stock}")
            
            # الحفظ الجماعي
            if variants_to_create and not dry_run:
                try:
                    ProductVariant.objects.bulk_create(
                        variants_to_create,
                        ignore_conflicts=True  # تجاهل التكرارات
                    )
                    print(f"   💾 تم حفظ {created_count} متغير جديد")
                    self.report['variants_created'] += created_count
                except Exception as e:
                    error_msg = f"خطأ في حفظ متغيرات المنتج '{product.name}': {str(e)}"
                    print(f"   ❌ {error_msg}")
                    self.report['errors'].append(error_msg)
            elif variants_to_create and dry_run:
                print(f"   👁️  سيتم إنشاء {created_count} متغير (معاينة)")
            
            self.report['variants_skipped'] += skipped_count
            
            if created_count == 0:
                print("   ✅ جميع المتغيرات موجودة - لا يوجد ما يحتاج إنشاء")
    
    def validate_data(self):
        """
        التحقق من صحة البيانات
        """
        self.print_header("🔍 التحقق من صحة البيانات")
        
        issues = []
        
        # 1. التحقق من الأنماط بدون مقاسات ولا سعر أساسي
        patterns_without_price = Pattern.objects.filter(
            has_sizes=False,
            base_price__isnull=True
        )
        
        if patterns_without_price.exists():
            print("\n⚠️  أنماط بدون مقاسات وبدون سعر أساسي:")
            for pattern in patterns_without_price:
                msg = f"   - {pattern.product.name} - {pattern.name}"
                print(msg)
                issues.append(msg)
        
        # 2. التحقق من الأنماط has_sizes=True بدون PatternSize
        patterns_with_sizes = Pattern.objects.filter(has_sizes=True)
        
        for pattern in patterns_with_sizes:
            if not PatternSize.objects.filter(pattern=pattern).exists():
                msg = f"النمط '{pattern.product.name} - {pattern.name}' مُعلّم كـ has_sizes=True لكن لا توجد مقاسات"
                print(f"⚠️  {msg}")
                issues.append(msg)
        
        # 3. التحقق من المتغيرات بدون نمط
        variants_without_pattern = ProductVariant.objects.filter(pattern__isnull=True)
        
        if variants_without_pattern.exists():
            print(f"\n⚠️  متغيرات بدون نمط: {variants_without_pattern.count()}")
            for variant in variants_without_pattern[:5]:
                msg = f"   - {variant.product.name}"
                print(msg)
        
        # 4. التحقق من المتغيرات: pattern.has_sizes=True لكن بدون size
        invalid_variants = []
        for variant in ProductVariant.objects.select_related('pattern'):
            if variant.pattern and variant.pattern.has_sizes and not variant.size:
                invalid_variants.append(variant)
        
        if invalid_variants:
            print(f"\n⚠️  متغيرات غير صحيحة (النمط يحتاج مقاس لكن لا يوجد): {len(invalid_variants)}")
            for variant in invalid_variants[:5]:
                msg = f"   - {variant.product.name} - {variant.pattern.name}"
                print(msg)
                issues.append(msg)
        
        # 5. التحقق من المنتجات بدون متغيرات
        products_without_variants = Product.objects.filter(
            is_active=True,
            variants__isnull=True
        ).distinct()
        
        if products_without_variants.exists():
            print(f"\n⚠️  منتجات نشطة بدون متغيرات: {products_without_variants.count()}")
            for product in products_without_variants[:5]:
                msg = f"   - {product.name}"
                print(msg)
        
        if not issues:
            print("\n✅ جميع البيانات صحيحة!")
        
        return issues
    
    def print_report(self):
        """
        طباعة التقرير النهائي
        """
        self.print_header("📊 التقرير النهائي")
        
        print(f"\n📦 المنتجات المعالجة: {self.report['products_processed']}")
        print(f"🔧 الأنماط المُصلحة: {self.report['patterns_fixed']}")
        print(f"➕ المتغيرات المُنشأة: {self.report['variants_created']}")
        print(f"⏭️  المتغيرات المتخطاة (موجودة): {self.report['variants_skipped']}")
        
        if self.report['warnings']:
            print(f"\n⚠️  التحذيرات ({len(self.report['warnings'])}):")
            for warning in self.report['warnings'][:10]:
                print(f"   - {warning}")
            if len(self.report['warnings']) > 10:
                print(f"   ... و {len(self.report['warnings']) - 10} تحذير آخر")
        
        if self.report['errors']:
            print(f"\n❌ الأخطاء ({len(self.report['errors'])}):")
            for error in self.report['errors']:
                print(f"   - {error}")
        
        if not self.report['errors']:
            print("\n✅ اكتمل التنفيذ بنجاح!")
    
    def run(self, dry_run=False, skip_validation=False):
        """
        تشغيل السكريبت الكامل
        
        Args:
            dry_run: معاينة فقط بدون حفظ
            skip_validation: تخطي التحقق من البيانات
        """
        self.print_header("🚀 بدء إصلاح بيانات المتغيرات")
        
        if dry_run:
            print("\n⚠️  وضع المعاينة (Dry Run) - لن يتم حفظ أي تغييرات\n")
        
        try:
            with transaction.atomic():
                # 1. إصلاح Pattern.has_sizes
                self.fix_pattern_has_sizes()
                
                # 2. إنشاء المتغيرات الناقصة
                self.create_missing_variants(dry_run=dry_run)
                
                # 3. التحقق من صحة البيانات
                if not skip_validation:
                    self.validate_data()
                
                # 4. طباعة التقرير
                self.print_report()
                
                # إذا كان dry_run، إلغاء التغييرات
                if dry_run:
                    print("\n🔄 تم إلغاء جميع التغييرات (وضع المعاينة)")
                    transaction.set_rollback(True)
        
        except Exception as e:
            print(f"\n❌ حدث خطأ: {str(e)}")
            import traceback
            traceback.print_exc()
            self.report['errors'].append(str(e))


def main():
    """الدالة الرئيسية"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='إصلاح بيانات المنتجات والمتغيرات'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='معاينة فقط بدون حفظ التغييرات'
    )
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='تخطي التحقق من البيانات'
    )
    
    args = parser.parse_args()
    
    fixer = VariantDataFixer()
    fixer.run(dry_run=args.dry_run, skip_validation=args.skip_validation)


if __name__ == "__main__":
    main()
