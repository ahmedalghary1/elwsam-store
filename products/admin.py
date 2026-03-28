from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg
from .models import (
    Category, Product, Pattern, Color, ProductColor, Size, ProductSize,
    ProductImage, ProductVariant, ProductSpecification
)


# ================================================
# Inlines
# ================================================

class PatternInline(admin.TabularInline):
    model = Pattern
    extra = 1
    fields = ['name', 'order']
    ordering = ['order']
    verbose_name = 'نمط'
    verbose_name_plural = 'الأنماط'


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    fields = ['color', 'order']
    ordering = ['order']
    verbose_name = 'لون'
    verbose_name_plural = 'الألوان'


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1
    fields = ['size', 'order']
    ordering = ['order']
    verbose_name = 'مقاس'
    verbose_name_plural = 'المقاسات'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['color', 'image', 'preview', 'order']
    readonly_fields = ['preview']
    ordering = ['order']
    verbose_name = 'صورة'
    verbose_name_plural = 'الصور'

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:60px;height:60px;object-fit:cover;border-radius:6px;" />', obj.image.url)
        return '—'
    preview.short_description = 'معاينة'


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1
    fields = ['key', 'value', 'order']
    ordering = ['order']
    verbose_name = 'مواصفة'
    verbose_name_plural = 'المواصفات'


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['pattern', 'color', 'size', 'price', 'stock', 'sku', 'order']
    ordering = ['order']
    verbose_name = 'متغير'
    verbose_name_plural = 'المتغيرات (اللون/المقاس/النمط)'


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
    readonly_fields = ['slug', 'created_at', 'updated_at', 'category_image_preview']
    prepopulated_fields = {}

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
class ProductAdmin(admin.ModelAdmin):
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
    readonly_fields = ['slug', 'created_at', 'updated_at', 'main_image_preview', 'discount_percent_display']
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
        return super().get_queryset(request).select_related('category')

    class Meta:
        verbose_name = 'منتج'
        verbose_name_plural = 'المنتجات'


# ================================================
# Color Admin
# ================================================

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['color_swatch', 'name', 'code']
    search_fields = ['name', 'code']

    def color_swatch(self, obj):
        if obj.code:
            return format_html(
                '<span style="display:inline-block;width:24px;height:24px;'
                'background:{};border-radius:50%;border:2px solid #ddd;vertical-align:middle;"></span>',
                obj.code
            )
        return '—'
    color_swatch.short_description = 'اللون'

    class Meta:
        verbose_name = 'لون'
        verbose_name_plural = 'الألوان'


# ================================================
# Size Admin
# ================================================

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

    class Meta:
        verbose_name = 'مقاس'
        verbose_name_plural = 'المقاسات'


# ================================================
# Pattern Admin
# ================================================

@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'order']
    list_editable = ['order']
    list_filter = ['product']
    search_fields = ['name', 'product__name']
    ordering = ['order']
    autocomplete_fields = ['product']

    class Meta:
        verbose_name = 'نمط'
        verbose_name_plural = 'الأنماط'


# ================================================
# ProductVariant Admin
# ================================================

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'color_display', 'size', 'pattern', 'price', 'stock_display', 'sku', 'order']
    list_editable = ['price', 'order']
    list_filter = ['product__category', 'color', 'size', 'pattern']
    search_fields = ['product__name', 'sku']
    ordering = ['product', 'order']
    autocomplete_fields = ['product']
    list_per_page = 30

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

    class Meta:
        verbose_name = 'متغير منتج'
        verbose_name_plural = 'متغيرات المنتجات'


# ================================================
# ProductImage Admin
# ================================================

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'product', 'color', 'order']
    list_editable = ['order']
    list_filter = ['product', 'color']
    ordering = ['product', 'order']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:6px;" />', obj.image.url)
        return '—'
    image_preview.short_description = 'معاينة'

    class Meta:
        verbose_name = 'صورة منتج'
        verbose_name_plural = 'صور المنتجات'


# ================================================
# ProductSpecification Admin
# ================================================

@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ['product', 'key', 'value', 'order']
    list_editable = ['order']
    list_filter = ['product']
    search_fields = ['key', 'value', 'product__name']
    ordering = ['product', 'order']

    class Meta:
        verbose_name = 'مواصفة'
        verbose_name_plural = 'مواصفات المنتجات'


# ================================================
# ProductColor & ProductSize Admin (مدمجة)
# ================================================

@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['product', 'color_display', 'order']
    list_editable = ['order']
    list_filter = ['color']
    search_fields = ['product__name', 'color__name']
    ordering = ['order']

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
    list_display = ['product', 'size', 'order']
    list_editable = ['order']
    list_filter = ['size']
    search_fields = ['product__name', 'size__name']
    ordering = ['order']

    class Meta:
        verbose_name = 'مقاس منتج'
        verbose_name_plural = 'مقاسات المنتجات'