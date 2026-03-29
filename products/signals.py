"""
Signals for automatic ProductVariant creation
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import PatternSize, ProductVariant, ProductColor


@receiver(post_save, sender=PatternSize)
def create_variants_for_pattern_size(sender, instance, created, **kwargs):
    """
    عند إضافة PatternSize جديد، قم بإنشاء ProductVariant لكل لون
    """
    if created:
        pattern = instance.pattern
        product = pattern.product
        size = instance.size
        
        # الحصول على جميع الألوان للمنتج
        product_colors = ProductColor.objects.filter(product=product).select_related('color')
        
        variants_to_create = []
        
        for pc in product_colors:
            # تحقق من عدم وجود المتغير
            if not ProductVariant.objects.filter(
                product=product,
                pattern=pattern,
                color=pc.color,
                size=size
            ).exists():
                # إنشاء المتغير
                variant = ProductVariant(
                    product=product,
                    pattern=pattern,
                    color=pc.color,
                    size=size,
                    price=instance.price,  # السعر من PatternSize
                    stock=instance.stock,  # المخزون من PatternSize
                    order=0
                )
                variants_to_create.append(variant)
        
        # الحفظ الجماعي
        if variants_to_create:
            ProductVariant.objects.bulk_create(variants_to_create, ignore_conflicts=True)
            print(f"✅ تم إنشاء {len(variants_to_create)} متغير تلقائياً للمقاس: {size.name} في النمط: {pattern.name}")


@receiver(post_save, sender=PatternSize)
def update_variants_for_pattern_size(sender, instance, created, **kwargs):
    """
    عند تحديث PatternSize، قم بتحديث السعر والمخزون في ProductVariant
    """
    if not created:
        pattern = instance.pattern
        product = pattern.product
        size = instance.size
        
        # تحديث جميع المتغيرات المرتبطة
        updated = ProductVariant.objects.filter(
            product=product,
            pattern=pattern,
            size=size
        ).update(
            price=instance.price,
            stock=instance.stock
        )
        
        if updated > 0:
            print(f"✅ تم تحديث {updated} متغير للمقاس: {size.name} في النمط: {pattern.name}")


@receiver(post_delete, sender=PatternSize)
def delete_variants_for_pattern_size(sender, instance, **kwargs):
    """
    عند حذف PatternSize، قم بحذف ProductVariant المرتبطة (اختياري)
    """
    pattern = instance.pattern
    product = pattern.product
    size = instance.size
    
    # حذف جميع المتغيرات المرتبطة
    deleted_count, _ = ProductVariant.objects.filter(
        product=product,
        pattern=pattern,
        size=size
    ).delete()
    
    if deleted_count > 0:
        print(f"⚠️  تم حذف {deleted_count} متغير للمقاس: {size.name} من النمط: {pattern.name}")


@receiver(post_save, sender=ProductColor)
def create_variants_for_new_color(sender, instance, created, **kwargs):
    """
    عند إضافة لون جديد للمنتج، قم بإنشاء ProductVariant لكل نمط ومقاس
    """
    if created:
        product = instance.product
        color = instance.color
        
        # الحصول على جميع الأنماط
        from .models import Pattern
        patterns = Pattern.objects.filter(product=product, has_sizes=True)
        
        variants_to_create = []
        
        for pattern in patterns:
            # الحصول على جميع المقاسات للنمط
            pattern_sizes = PatternSize.objects.filter(pattern=pattern).select_related('size')
            
            for ps in pattern_sizes:
                # تحقق من عدم وجود المتغير
                if not ProductVariant.objects.filter(
                    product=product,
                    pattern=pattern,
                    color=color,
                    size=ps.size
                ).exists():
                    variant = ProductVariant(
                        product=product,
                        pattern=pattern,
                        color=color,
                        size=ps.size,
                        price=ps.price,
                        stock=ps.stock,
                        order=0
                    )
                    variants_to_create.append(variant)
        
        # الحفظ الجماعي
        if variants_to_create:
            ProductVariant.objects.bulk_create(variants_to_create, ignore_conflicts=True)
            print(f"✅ تم إنشاء {len(variants_to_create)} متغير تلقائياً للون: {color.name}")
