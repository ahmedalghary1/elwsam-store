from django.contrib import admin
import nested_admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg, Sum
from django.contrib import messages
from .models import (
    Category, Product, Pattern, Color, ProductColor, Size, ProductSize,
    ProductImage, ProductVariant, ProductSpecification, PatternSize
)


# ================================================
# Inlines
# ================================================

class PatternSizeInline(nested_admin.NestedTabularInline):
    model = PatternSize
    extra = 1
    fields = ['size', 'price', 'stock', 'stock_badge', 'order']
    readonly_fields = ['stock_badge']
    ordering = ['order']
    verbose_name = 'مقاس النمط'
    verbose_name_plural = 'مقاسات النمط'
    autocomplete_fields = ['size']
    
    classes = ['collapse']
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.help_texts = {
            'size': 'اختر المقاس من القائمة',
            'price': 'السعر لهذا المقاس في هذا النمط',
            'stock': 'المخزون المتاح لهذا المقاس',
            'order': 'ترتيب العرض (الأصغر يظهر أولاً)'
        }
        return formset
    
    def save_formset(self, request, form, formset, change):
        """Override to create variants when PatternSize is saved via inline"""
        instances = formset.save(commit=False)
        
        for instance in instances:
            is_new = instance.pk is None
            instance.save()
            
            # If new PatternSize, create variants
            if is_new:
                instance.create_variants_for_colors()
        
        # Delete removed instances
        for obj in formset.deleted_objects:
            obj.delete()
    
    def stock_badge(self, obj):
        if not obj.pk:
            return '—'
        if obj.stock > 10:
            color = '#28a745'
            icon = '✓'
            text = 'متوفر'
        elif obj.stock > 0:
            color = '#ffc107'
            icon = '⚠'
            text = 'قليل'
        else:
            color = '#dc3545'
            icon = '✗'
            text = 'نفذ'
        return format_html(
            '<span style="color:{};font-weight:bold;padding:4px 8px;background:rgba({},0.1);border-radius:4px;">{} {} ({})</span>',
            color, 
            '40,167,69' if obj.stock > 10 else '255,193,7' if obj.stock > 0 else '220,53,69',
            icon, obj.stock, text
        )
    stock_badge.short_description = 'حالة المخزون'


class PatternInline(nested_admin.NestedStackedInline):
    model = Pattern
    extra = 0
    fields = ['name', 'has_sizes', 'base_price', 'order']
    ordering = ['order']
    verbose_name = 'نمط'
    verbose_name_plural = 'الأنماط'
    inlines = [PatternSizeInline]
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.validate_min = True
        return formset


class ProductColorInline(nested_admin.NestedTabularInline):
    model = ProductColor
    extra = 0
    fields = ['color', 'color_preview', 'order']
    readonly_fields = ['color_preview']
    ordering = ['order']
    verbose_name = 'لون'
    verbose_name_plural = 'الألوان'
    autocomplete_fields = ['color']
    
    def color_preview(self, obj):
        if obj.color and obj.color.code:
            return format_html(
                '<span style="display:inline-block;width:24px;height:24px;background:{};'
                'border-radius:50%;border:2px solid #ddd;"></span>',
                obj.color.code
            )
        return '—'
    color_preview.short_description = 'معاينة'


class ProductSizeInline(nested_admin.NestedTabularInline):
    model = ProductSize
    extra = 0
    fields = ['size', 'price', 'order']
    ordering = ['order']
    verbose_name = 'مقاس'
    verbose_name_plural = 'المقاسات'
    autocomplete_fields = ['size']


class ProductImageInline(nested_admin.NestedTabularInline):
    model = ProductImage
    extra = 0
    fields = ['color', 'image', 'preview', 'order']
    readonly_fields = ['preview']
    ordering = ['order']
    verbose_name = 'صورة'
    verbose_name_plural = 'الصور'
    autocomplete_fields = ['color']

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:60px;height:60px;object-fit:cover;border-radius:6px;box-shadow:0 2px 4px rgba(0,0,0,0.1);" />', obj.image.url)
        return '—'
    preview.short_description = 'معاينة'


class ProductSpecificationInline(nested_admin.NestedTabularInline):
    model = ProductSpecification
    extra = 0
    fields = ['key', 'value', 'order']
    ordering = ['order']
    verbose_name = 'مواصفة'
    verbose_name_plural = 'المواصفات'


class ProductVariantInline(nested_admin.NestedTabularInline):
    model = ProductVariant
    extra = 0
    fields = ['pattern', 'color', 'size', 'price', 'stock', 'sku', 'stock_status_badge', 'order']
    readonly_fields = ['stock_status_badge']
    ordering = ['order']
    verbose_name = 'متغير'
    verbose_name_plural = 'المتغيرات (اللون/المقاس/النمط)'
    autocomplete_fields = ['pattern', 'color', 'size']
    
    def stock_status_badge(self, obj):
        if not obj.pk:
            return '—'
        if obj.stock > 10:
            return format_html('<span style="background:#28a745;color:white;padding:2px 8px;border-radius:4px;font-size:0.8em;">{}</span>', '✓ متوفر')
        elif obj.stock > 0:
            return format_html('<span style="background:#ffc107;color:black;padding:2px 8px;border-radius:4px;font-size:0.8em;">{}</span>', '⚠ محدود')
        return format_html('<span style="background:#dc3545;color:white;padding:2px 8px;border-radius:4px;font-size:0.8em;">{}</span>', '✗ نفد')
    stock_status_badge.short_description = 'الحالة'


# ================================================
# Category Admin
# ================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category_icon', 'name', 'product_count', 'is_hot', 'order', 'created_at']
    list_display_links = ['name']
    list_editable = ['is_hot', 'order']
    list_filter = ['is_hot', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['order']
    readonly_fields = ['created_at', 'updated_at', 'category_image_preview']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    actions = ['mark_as_hot', 'mark_as_not_hot']
    
    def mark_as_hot(self, request, queryset):
        updated = queryset.update(is_hot=True)
        self.message_user(request, f'تم تحديد {updated} قسم كمشهور', messages.SUCCESS)
    mark_as_hot.short_description = 'تحديد كمشهور'
    
    def mark_as_not_hot(self, request, queryset):
        updated = queryset.update(is_hot=False)
        self.message_user(request, f'تم إلغاء {updated} قسم من المشهورة', messages.SUCCESS)
    mark_as_not_hot.short_description = 'إلغاء من المشهورة'

    fieldsets = (
        ('📁 معلومات القسم', {
            'fields': ('name', 'slug', 'description', 'icon')
        }),
        ('🖼️ الصورة', {
            'fields': ('image', 'category_image_preview')
        }),
        ('⚙️ الإعدادات', {
            'fields': ('is_hot', 'order')
        }),
        ('📅 التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def category_icon(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:36px;height:36px;object-fit:cover;border-radius:6px;" />', obj.image.url)
        return format_html('<span style="font-size:1.5rem;">{}</span>', obj.icon or '📁')
    category_icon.short_description = ''

    def category_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width:200px;border-radius:8px;margin-top:8px;" />', obj.image.url)
        return 'لا توجد صورة'
    category_image_preview.short_description = 'معاينة الصورة'

    def product_count(self, obj):
        count = obj.product_set.count()
        color = '#28a745' if count > 0 else '#6c757d'
        return format_html('<span style="color:{};font-weight:bold;">{} منتج</span>', color, count)
    product_count.short_description = 'عدد المنتجات'

    class Meta:
        verbose_name = 'قسم'
        verbose_name_plural = 'الأقسام'


# ================================================
# Product Admin
# ================================================

@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    list_display = [
        'product_thumbnail', 'name', 'category', 'price_display',
        'discount_badge', 'stock_status', 'is_active', 'is_hot', 'is_new',
        'rating', 'order'
    ]
    list_display_links = ['name']
    list_editable = ['is_active', 'is_hot', 'is_new', 'order']
    list_filter = ['category', 'is_active', 'is_hot', 'is_new', 'created_at']
    search_fields = ['name', 'description', 'category__name']
    ordering = ['order']
    readonly_fields = ['created_at', 'updated_at', 'main_image_preview', 'discount_percent_display']
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    list_per_page = 25

    fieldsets = (
        ('📦 معلومات المنتج الأساسية', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('🖼️ الصورة الرئيسية', {
            'fields': ('image', 'main_image_preview')
        }),
        ('💰 الأسعار', {
            'fields': ('price', 'old_price', 'discount_percent_display')
        }),
        ('⭐ الحالة والتقييم', {
            'fields': ('is_active', 'is_new', 'is_hot', 'rating', 'order')
        }),
        ('📅 التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [
        PatternInline,
        ProductColorInline,
        ProductSizeInline,
        ProductImageInline,
        ProductSpecificationInline,
        ProductVariantInline,
    ]

    def product_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:8px;border:1px solid #ddd;" />', obj.image.url)
        return mark_safe('<div style="width:48px;height:48px;background:#f0f0f0;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;">📦</div>')
    product_thumbnail.short_description = ''

    def price_display(self, obj):
        if obj.old_price and obj.old_price > obj.price:
            return format_html(
                '<span style="font-weight:bold;color:#28a745;">{} ج.م</span> '
                '<span style="text-decoration:line-through;color:#999;font-size:0.85em;">{} ج.م</span>',
                obj.price, obj.old_price
            )
        return format_html('<span style="font-weight:bold;">{} ج.م</span>', obj.price)
    price_display.short_description = 'السعر'
    price_display.admin_order_field = 'price'

    def discount_badge(self, obj):
        pct = obj.get_discount_percent()
        if pct > 0:
            return format_html('<span style="background:#dc3545;color:white;padding:2px 8px;border-radius:12px;font-size:0.8em;font-weight:bold;">-%{}%</span>', pct)
        return '—'
    discount_badge.short_description = 'الخصم'

    def stock_status(self, obj):
        total_stock = sum(v.stock for v in obj.variants.all())
        if total_stock > 10:
            return format_html('<span style="color:#28a745;font-weight:bold;">✓ متوفر ({})</span>', total_stock)
        elif total_stock > 0:
            return format_html('<span style="color:#ffc107;font-weight:bold;">⚠ محدود ({})</span>', total_stock)
        return mark_safe('<span style="color:#dc3545;font-weight:bold;">✗ نفد</span>')
    stock_status.short_description = 'المخزون'

    def main_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width:250px;border-radius:10px;margin-top:8px;" />', obj.image.url)
        return 'لا توجد صورة'
    main_image_preview.short_description = 'معاينة الصورة'

    def discount_percent_display(self, obj):
        pct = obj.get_discount_percent()
        if pct > 0:
            return format_html('<strong style="color:#dc3545;">{}%</strong> خصم', pct)
        return 'لا يوجد خصم'
    discount_percent_display.short_description = 'نسبة الخصم'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category').prefetch_related('variants', 'images')
    
    def save_formset(self, request, form, formset, change):
        """Override to create variants when ProductColor is saved via inline"""
        if formset.model == ProductColor:
            instances = formset.save(commit=False)
            
            for instance in instances:
                is_new = instance.pk is None
                instance.save()
                
                # If new ProductColor, create variants
                if is_new:
                    instance.create_variants_for_pattern_sizes()
            
            # Delete removed instances
            for obj in formset.deleted_objects:
                obj.delete()
        else:
            formset.save()
    
    actions = ['mark_as_active', 'mark_as_inactive', 'mark_as_hot', 'mark_as_new', 'duplicate_product']
    
    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'تم تفعيل {updated} منتج', messages.SUCCESS)
    mark_as_active.short_description = 'تفعيل المنتجات'
    
    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'تم إلغاء تفعيل {updated} منتج', messages.SUCCESS)
    mark_as_inactive.short_description = 'إلغاء تفعيل المنتجات'
    
    def mark_as_hot(self, request, queryset):
        updated = queryset.update(is_hot=True)
        self.message_user(request, f'تم تحديد {updated} منتج كمشهور', messages.SUCCESS)
    mark_as_hot.short_description = 'تحديد كمشهور'
    
    def mark_as_new(self, request, queryset):
        updated = queryset.update(is_new=True)
        self.message_user(request, f'تم تحديد {updated} منتج كجديد', messages.SUCCESS)
    mark_as_new.short_description = 'تحديد كجديد'
    
    def duplicate_product(self, request, queryset):
        for product in queryset:
            product.pk = None
            product.name = f'{product.name} (نسخة)'
            product.slug = None
            product.save()
        self.message_user(request, f'تم نسخ {queryset.count()} منتج', messages.SUCCESS)
    duplicate_product.short_description = 'نسخ المنتجات'

    class Meta:
        verbose_name = 'منتج'
        verbose_name_plural = 'المنتجات'


# ================================================
# Color Admin
# ================================================

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['color_swatch', 'name', 'code', 'usage_count']
    list_display_links = ['name']
    search_fields = ['name', 'code']
    list_per_page = 30
    
    def usage_count(self, obj):
        count = obj.productcolor_set.count()
        if count > 0:
            return format_html('<span style="color:#007bff;font-weight:bold;">{} منتج</span>', count)
        return '—'
    usage_count.short_description = 'الاستخدام'

    def color_swatch(self, obj):
        if obj.code:
            return format_html(
                '<span style="display:inline-block;width:24px;height:24px;background:{};'
                'border-radius:50%;border:2px solid #ddd;"></span>',
                obj.code
            )
        return '—'
    color_swatch.short_description = 'اللون'


# ================================================
# Size Admin
# ================================================

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_usage', 'pattern_usage']
    list_display_links = ['name']
    search_fields = ['name']
    list_per_page = 30
    
    def product_usage(self, obj):
        count = obj.productsize_set.count()
        if count > 0:
            return format_html('<span style="color:#28a745;font-weight:bold;">{} منتج</span>', count)
        return '—'
    product_usage.short_description = 'استخدام المنتجات'
    
    def pattern_usage(self, obj):
        count = obj.patternsize_set.count()
        if count > 0:
            return format_html('<span style="color:#007bff;font-weight:bold;">{} نمط</span>', count)
        return '—'
    pattern_usage.short_description = 'استخدام الأنماط'

    class Meta:
        verbose_name = 'مقاس'
        verbose_name_plural = 'المقاسات'


# ================================================
# Pattern Admin
# ================================================

@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'has_sizes', 'base_price_display', 'pattern_sizes_count', 'order']
    list_display_links = ['name']
    list_editable = ['order']
    list_filter = ['has_sizes', 'product__category']
    search_fields = ['name', 'product__name']
    ordering = ['product', 'order']
    autocomplete_fields = ['product']
    list_per_page = 30
    
    fieldsets = (
        ('معلومات النمط', {
            'fields': ('product', 'name', 'order')
        }),
        ('إعدادات التسعير', {
            'fields': ('has_sizes', 'base_price'),
            'description': 'إذا كان النمط له مقاسات، حدد "له مقاسات" وأضف المقاسات أدناه. وإلا، حدد السعر الأساسي.'
        }),
    )
    
    inlines = [PatternSizeInline]
    
    actions = ['generate_variants_for_patterns']
    
    def save_formset(self, request, form, formset, change):
        """Override to create variants when PatternSize is saved via inline"""
        if formset.model == PatternSize:
            instances = formset.save(commit=False)
            
            for instance in instances:
                is_new = instance.pk is None
                instance.save()
                
                # If new PatternSize, create variants
                if is_new:
                    instance.create_variants_for_colors()
            
            # Delete removed instances
            for obj in formset.deleted_objects:
                obj.delete()
        else:
            formset.save()
    
    def generate_variants_for_patterns(self, request, queryset):
        """إنشاء المتغيرات تلقائياً لكل الأنماط المحددة"""
        total_created = 0
        
        for pattern in queryset:
            product = pattern.product
            
            # Get all pattern sizes
            pattern_sizes = PatternSize.objects.filter(pattern=pattern)
            
            # Get all colors
            product_colors = ProductColor.objects.filter(product=product)
            
            for ps in pattern_sizes:
                for pc in product_colors:
                    # Check if variant exists
                    variant, created = ProductVariant.objects.get_or_create(
                        product=product,
                        pattern=pattern,
                        color=pc.color,
                        size=ps.size,
                        defaults={
                            'price': ps.price,
                            'stock': ps.stock,
                            'order': 0
                        }
                    )
                    if created:
                        total_created += 1
        
        self.message_user(request, f'✅ تم إنشاء {total_created} متغير جديد', messages.SUCCESS)
    
    generate_variants_for_patterns.short_description = '🔄 إنشاء المتغيرات تلقائياً'
    
    def base_price_display(self, obj):
        if obj.base_price:
            return format_html('<span style="font-weight:bold;color:#28a745;">{} ج.م</span>', obj.base_price)
        return '—'
    base_price_display.short_description = 'السعر الأساسي'
    base_price_display.admin_order_field = 'base_price'
    
    def pattern_sizes_count(self, obj):
        count = obj.pattern_sizes.count()
        if count > 0:
            return format_html('<span style="color:#007bff;font-weight:bold;">{} مقاس</span>', count)
        return '—'
    pattern_sizes_count.short_description = 'عدد المقاسات'

    class Meta:
        verbose_name = 'نمط'
        verbose_name_plural = 'الأنماط'


# ================================================
# ProductVariant Admin
# ================================================

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'pattern', 'color_display', 'size', 'dynamic_price_display', 'stock_display', 'sku', 'order']
    list_display_links = ['product']
    list_editable = ['order']
    list_filter = ['product__category', 'color', 'size', 'pattern', 'stock']
    search_fields = ['product__name', 'sku', 'pattern__name', 'color__name', 'size__name']
    ordering = ['product', 'order']
    autocomplete_fields = ['product', 'pattern', 'color', 'size']
    list_per_page = 50
    list_select_related = ['product', 'pattern', 'color', 'size']
    
    fieldsets = (
        ('معلومات المتغير', {
            'fields': ('product', 'pattern', 'color', 'size', 'sku', 'order')
        }),
        ('المخزون والسعر', {
            'fields': ('stock', 'price', 'dynamic_price_display'),
            'description': 'ملاحظة: حقل السعر قديم. السعر الفعلي يُحسب ديناميكياً من التسلسل الهرمي للأسعار.'
        }),
    )
    
    readonly_fields = ['dynamic_price_display']
    
    actions = ['update_stock_to_zero', 'update_stock_to_ten', 'mark_as_available']
    
    def dynamic_price_display(self, obj):
        if obj.pk:
            dynamic_price = obj.get_price()
            if dynamic_price != obj.price:
                return format_html(
                    '<span style="font-weight:bold;color:#28a745;">{} ج.م</span> '
                    '<span style="color:#999;font-size:0.85em;">(محسوب ديناميكياً)</span><br>'
                    '<span style="color:#dc3545;font-size:0.85em;">السعر القديم: {} ج.م</span>',
                    dynamic_price, obj.price
                )
            return format_html('<span style="font-weight:bold;">{} ج.م</span>', dynamic_price)
        return '—'
    dynamic_price_display.short_description = 'السعر الديناميكي'
    
    def update_stock_to_zero(self, request, queryset):
        updated = queryset.update(stock=0)
        self.message_user(request, f'تم تحديث المخزون إلى 0 لـ {updated} متغير', messages.SUCCESS)
    update_stock_to_zero.short_description = 'تحديث المخزون إلى 0'
    
    def update_stock_to_ten(self, request, queryset):
        updated = queryset.update(stock=10)
        self.message_user(request, f'تم تحديث المخزون إلى 10 لـ {updated} متغير', messages.SUCCESS)
    update_stock_to_ten.short_description = 'تحديث المخزون إلى 10'
    
    def mark_as_available(self, request, queryset):
        updated = queryset.filter(stock=0).update(stock=5)
        self.message_user(request, f'تم تحديث {updated} متغير إلى متوفر', messages.SUCCESS)
    mark_as_available.short_description = 'تحديد كمتوفر (5 قطع)'
    
    def color_display(self, obj):
        if obj.color and obj.color.code:
            return format_html(
                '<span style="display:inline-block;width:16px;height:16px;background:{};'
                'border-radius:50%;border:1px solid #ccc;margin-left:6px;vertical-align:middle;"></span> {}',
                obj.color.code, obj.color.name
            )
        return obj.color.name if obj.color else '—'
    color_display.short_description = 'اللون'
    
    def stock_display(self, obj):
        if obj.stock > 10:
            color = '#28a745'
        elif obj.stock > 0:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html('<span style="color:{};font-weight:bold;">{}</span>', color, obj.stock)
    stock_display.short_description = 'المخزون'
    stock_display.admin_order_field = 'stock'


# ================================================
# ProductImage Admin
# ================================================

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'product', 'color_display', 'order']
    list_display_links = ['product']
    list_editable = ['order']
    list_filter = ['product__category', 'color']
    search_fields = ['product__name', 'color__name']
    ordering = ['product', 'order']
    autocomplete_fields = ['product', 'color']
    list_per_page = 40
    list_select_related = ['product', 'color']
    
    def color_display(self, obj):
        if obj.color:
            if obj.color.code:
                return format_html(
                    '<span style="display:inline-block;width:16px;height:16px;background:{};'
                    'border-radius:50%;border:1px solid #ccc;margin-left:6px;vertical-align:middle;"></span> {}',
                    obj.color.code, obj.color.name
                )
            return obj.color.name
        return '—'
    color_display.short_description = 'اللون'

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:6px;" />', obj.image.url)
        return '—'
    image_preview.short_description = 'معاينة'


# ================================================
# ProductSpecification Admin
# ================================================

@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ['product', 'key', 'value', 'order']
    list_display_links = ['product']
    list_editable = ['order']
    list_filter = ['product__category', 'key']
    search_fields = ['key', 'value', 'product__name']
    ordering = ['product', 'order']
    autocomplete_fields = ['product']
    list_per_page = 40
    list_select_related = ['product']

    class Meta:
        verbose_name = 'مواصفة'
        verbose_name_plural = 'مواصفات المنتجات'


# ================================================
# ProductColor & ProductSize Admin (مدمجة)
# ================================================

@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['product', 'color_display', 'order']
    list_display_links = ['product']
    list_editable = ['order']
    list_filter = ['color', 'product__category']
    search_fields = ['product__name', 'color__name']
    ordering = ['product', 'order']
    autocomplete_fields = ['product', 'color']
    list_per_page = 30
    list_select_related = ['product', 'color']

    def color_display(self, obj):
        if obj.color.code:
            return format_html(
                '<span style="display:inline-block;width:16px;height:16px;background:{};'
                'border-radius:50%;border:1px solid #ccc;margin-left:6px;vertical-align:middle;"></span> {}',
                obj.color.code, obj.color.name
            )
        return obj.color.name
    color_display.short_description = 'اللون'

    class Meta:
        verbose_name = 'لون منتج'
        verbose_name_plural = 'ألوان المنتجات'


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ['product', 'size', 'price_display', 'order']
    list_display_links = ['product']
    list_editable = ['order']
    list_filter = ['size', 'product__category']
    search_fields = ['product__name', 'size__name']
    ordering = ['product', 'order']
    autocomplete_fields = ['product', 'size']
    list_per_page = 30
    list_select_related = ['product', 'size']
    
    def price_display(self, obj):
        return format_html('<span style="font-weight:bold;color:#28a745;">{} ج.م</span>', obj.price)
    price_display.short_description = 'السعر'
    price_display.admin_order_field = 'price'

    class Meta:
        verbose_name = 'مقاس منتج'
        verbose_name_plural = 'مقاسات المنتجات'


# ================================================
# PatternSize Admin (NEW - Multi-level Pricing)
# ================================================

@admin.register(PatternSize)
class PatternSizeAdmin(admin.ModelAdmin):
    list_display = ['pattern', 'size', 'price_display', 'stock_display', 'availability_badge', 'order']
    list_display_links = ['pattern']
    list_editable = ['order']
    list_filter = ['pattern__product__category', 'size', 'stock']
    search_fields = ['pattern__name', 'pattern__product__name', 'size__name']
    ordering = ['pattern', 'order']
    autocomplete_fields = ['pattern', 'size']
    list_per_page = 40
    list_select_related = ['pattern', 'pattern__product', 'size']
    
    fieldsets = (
        ('معلومات المقاس', {
            'fields': ('pattern', 'size', 'order')
        }),
        ('السعر والمخزون', {
            'fields': ('price', 'stock'),
            'description': 'هذا السعر له الأولوية القصوى في التسلسل الهرمي للأسعار.'
        }),
    )
    
    actions = ['update_stock_to_zero', 'update_stock_to_ten', 'mark_as_available']
    
    def price_display(self, obj):
        return format_html('<span style="font-weight:bold;color:#28a745;">{} ج.م</span>', obj.price)
    price_display.short_description = 'السعر'
    price_display.admin_order_field = 'price'
    
    def stock_display(self, obj):
        if obj.stock > 10:
            color = '#28a745'
        elif obj.stock > 0:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html('<span style="color:{};font-weight:bold;">{}</span>', color, obj.stock)
    stock_display.short_description = 'المخزون'
    stock_display.admin_order_field = 'stock'
    
    def availability_badge(self, obj):
        if obj.is_available():
            return format_html('<span style="background:#28a745;color:white;padding:2px 8px;border-radius:4px;font-size:0.8em;">✓ متوفر</span>')
        return format_html('<span style="background:#dc3545;color:white;padding:2px 8px;border-radius:4px;font-size:0.8em;">✗ نفد</span>')
    availability_badge.short_description = 'الحالة'
    
    def update_stock_to_zero(self, request, queryset):
        updated = queryset.update(stock=0)
        self.message_user(request, f'تم تحديث المخزون إلى 0 لـ {updated} مقاس نمط', messages.SUCCESS)
    update_stock_to_zero.short_description = 'تحديث المخزون إلى 0'
    
    def update_stock_to_ten(self, request, queryset):
        updated = queryset.update(stock=10)
        self.message_user(request, f'تم تحديث المخزون إلى 10 لـ {updated} مقاس نمط', messages.SUCCESS)
    update_stock_to_ten.short_description = 'تحديث المخزون إلى 10'
    
    def mark_as_available(self, request, queryset):
        updated = queryset.filter(stock=0).update(stock=5)
        self.message_user(request, f'تم تحديث {updated} مقاس نمط إلى متوفر', messages.SUCCESS)
    mark_as_available.short_description = 'تحديد كمتوفر (5 قطع)'
    
    class Meta:
        verbose_name = 'مقاس نمط'
        verbose_name_plural = 'مقاسات الأنماط'