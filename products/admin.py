from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib import messages
from django import forms
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin
from .models import (
    Category, Product, Pattern, Color, ProductColor, Size, ProductSize,
    ProductImage, ProductVariant, ProductSpecification, PatternSize,
    PatternColor, PatternImage
)


# ================================================
# Inlines — used inside ProductAdmin
# ================================================

class PatternInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Pattern
    extra = 0
    fields = ['name', 'has_sizes', 'base_price', 'edit_link']
    readonly_fields = ['edit_link']
    ordering = ['order']
    verbose_name = 'نقش'
    verbose_name_plural = 'الأنماط'
    show_change_link = False

    def edit_link(self, instance):
        if instance.pk:
            url = reverse('admin:products_pattern_change', args=[instance.pk])
            # تم تصحيح السلسلة النصية: دمج الأجزاء في سلسلة واحدة
            return format_html(
                '<a href="{}" style="background:#007bff;color:white;padding:3px 10px;border-radius:4px;text-decoration:none;font-size:0.82em;">✒ إدارة المقاسات والمتغيرات</a>',
                url
            )
        return '—'
    edit_link.short_description = 'إدارة'


class ProductColorInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductColor
    extra = 1
    fields = ['color', 'color_preview']
    readonly_fields = ['color_preview']
    ordering = ['order']
    verbose_name = 'لون'
    verbose_name_plural = 'الألوان'
    autocomplete_fields = ['color']

    def color_preview(self, obj):
        if obj.pk and obj.color and obj.color.code:
            return format_html(
                '<span style="display:inline-block;width:26px;height:26px;background:{};border-radius:50%;border:2px solid #ddd;vertical-align:middle;"></span>',
                obj.color.code
            )
        return '—'
    color_preview.short_description = 'معاينة'


class ProductSizeInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductSize
    extra = 1
    fields = ['size', 'price']
    ordering = ['order']
    verbose_name = 'مقاس'
    verbose_name_plural = 'المقاسات'
    autocomplete_fields = ['size']


class ProductImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'color', 'preview']
    readonly_fields = ['preview']
    ordering = ['order']
    verbose_name = 'صورة'
    verbose_name_plural = 'الصور (اللون اختياري للمنتجات البسيطة)'
    autocomplete_fields = ['color']

    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="width:60px;height:60px;object-fit:cover;border-radius:6px;" />',
                obj.image.url
            )
        return '—'
    preview.short_description = 'معاينة'


class ProductSpecificationInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductSpecification
    extra = 1
    fields = ['key', 'value']
    ordering = ['order']
    verbose_name = 'مواصفة'
    verbose_name_plural = 'المواصفات'


class SimpleProductVariantInline(SortableInlineAdminMixin, admin.TabularInline):
    """
    Inline for creating variants directly without Pattern requirement.
    Shows only variants where pattern is NULL (simple variants).
    """
    model = ProductVariant
    extra = 1
    fields = ['color', 'size', 'price', 'stock', 'sku']
    ordering = ['order']
    verbose_name = 'متغير بسيط (لون + مقاس)'
    verbose_name_plural = 'المتغيرات البسيطة (بدون أنماط)'

    def get_queryset(self, request):
        """Show only variants without pattern (simple variants)"""
        qs = super().get_queryset(request)
        return qs.filter(pattern__isnull=True)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filter colors and sizes to show only those added to this product.
        This ensures you can only select colors/sizes that were added via
        ProductColor and ProductSize inlines.
        """
        # Get product ID from URL
        object_id = request.resolver_match.kwargs.get('object_id')

        if object_id:
            try:
                product = Product.objects.get(pk=object_id)

                if db_field.name == 'color':
                    # Show only colors added to this product
                    kwargs['queryset'] = Color.objects.filter(
                        productcolor__product=product
                    ).distinct()

                elif db_field.name == 'size':
                    # Show only sizes added to this product
                    kwargs['queryset'] = Size.objects.filter(
                        productsize__product=product
                    ).distinct()

            except Product.DoesNotExist:
                pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ================================================
# Inlines — used inside PatternAdmin
# ================================================

class PatternSizeInline(SortableInlineAdminMixin, admin.TabularInline):
    model = PatternSize
    extra = 1
    fields = ['size', 'price', 'stock']
    ordering = ['order']
    verbose_name = 'مقاس النمط'
    verbose_name_plural = 'مقاسات النمط (سعر + مخزون لكل مقاس)'
    autocomplete_fields = ['size']


class PatternColorInline(SortableInlineAdminMixin, admin.TabularInline):
    model = PatternColor
    extra = 1
    fields = ['color', 'color_preview']
    readonly_fields = ['color_preview']
    ordering = ['order']
    verbose_name = 'لون النمط'
    verbose_name_plural = 'ألوان النمط'
    autocomplete_fields = ['color']

    def color_preview(self, obj):
        if obj.pk and obj.color and obj.color.code:
            return format_html(
                '<span style="display:inline-block;width:26px;height:26px;background:{};border-radius:50%;border:2px solid #ddd;vertical-align:middle;"></span>',
                obj.color.code
            )
        return '—'
    color_preview.short_description = 'معاينة'


class PatternImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = PatternImage
    extra = 1
    fields = ['color', 'image', 'preview']
    readonly_fields = ['preview']
    ordering = ['order']
    verbose_name = 'صورة النمط'
    verbose_name_plural = 'صور النمط'
    autocomplete_fields = ['color']

    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="width:70px;height:70px;object-fit:cover;border-radius:6px;" />',
                obj.image.url
            )
        return '—'
    preview.short_description = 'معاينة'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        object_id = request.resolver_match.kwargs.get('object_id')
        if object_id and db_field.name == 'color':
            try:
                pattern = Pattern.objects.get(pk=object_id)
                pattern_colors = Color.objects.filter(
                    pattern_colors__pattern=pattern
                ).distinct()
                if pattern_colors.exists():
                    kwargs['queryset'] = pattern_colors
            except Pattern.DoesNotExist:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PatternVariantForm(forms.ModelForm):
    """
    Custom form for PatternVariantInline that auto-fills price
    from PatternSize (pattern + size) or Pattern.base_price.
    Removes the need to enter price manually — it comes from PatternSizeInline.
    """
    class Meta:
        model = ProductVariant
        exclude = ['price']

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Priority 1: PatternSize price (pattern + size combination)
        if instance.pattern_id and instance.size_id:
            try:
                ps = PatternSize.objects.get(
                    pattern_id=instance.pattern_id,
                    size_id=instance.size_id
                )
                instance.price = ps.price
            except PatternSize.DoesNotExist:
                instance.price = 0
        # Priority 2: Pattern base_price (pattern without sizes)
        elif instance.pattern_id:
            try:
                patt = Pattern.objects.get(pk=instance.pattern_id)
                instance.price = patt.base_price or 0
            except Pattern.DoesNotExist:
                instance.price = 0
        else:
            instance.price = 0
        if commit:
            instance.save()
            self._save_m2m()
        return instance


class PatternVariantInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductVariant
    form = PatternVariantForm
    extra = 1
    fields = ['color', 'size', 'stock', 'sku']
    ordering = ['order']
    verbose_name = 'متغير (لون + مقاس)'
    verbose_name_plural = 'المتغيرات — اربط كل لون بمقاس (السعر يؤخذ تلقائياً من مقاسات النمط)'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        object_id = request.resolver_match.kwargs.get('object_id')
        if object_id:
            try:
                pattern = Pattern.objects.get(pk=object_id)
                return qs.filter(pattern=pattern)
            except Pattern.DoesNotExist:
                pass
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        object_id = request.resolver_match.kwargs.get('object_id')
        if object_id:
            try:
                pattern = Pattern.objects.select_related('product').get(pk=object_id)
                product = pattern.product
                if db_field.name == 'color':
                    # Priority: PatternColor → fallback to ProductColor
                    pattern_colors = Color.objects.filter(
                        pattern_colors__pattern=pattern
                    ).distinct()
                    if pattern_colors.exists():
                        kwargs['queryset'] = pattern_colors
                    else:
                        kwargs['queryset'] = Color.objects.filter(
                            productcolor__product=product
                        ).distinct()
                elif db_field.name == 'size':
                    kwargs['queryset'] = Size.objects.filter(
                        patternsize__pattern=pattern
                    ).distinct()
            except Pattern.DoesNotExist:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ================================================
# Category Admin
# ================================================

@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['cat_icon', 'name', 'product_count', 'is_hot', 'order']
    list_display_links = ['name']
    list_editable = ['is_hot']
    list_filter = ['is_hot']
    search_fields = ['name']
    ordering = ['order']
    list_per_page = 25

    fieldsets = (
        ('معلومات القسم', {'fields': ('name', 'slug', 'description', 'icon')}),
        ('الصورة', {'fields': ('image',)}),
        ('الإعدادات', {'fields': ('is_hot', 'order')}),
    )

    def cat_icon(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:34px;height:34px;object-fit:cover;border-radius:6px;" />',
                obj.image.url
            )
        return format_html('<span style="font-size:1.4rem;">{}</span>', obj.icon or '📁')
    cat_icon.short_description = ''

    def product_count(self, obj):
        count = obj.product_set.count()
        color = '#28a745' if count > 0 else '#999'
        return format_html('<span style="color:{};font-weight:bold;">{}</span>', color, count)
    product_count.short_description = 'عدد المنتجات'


# ================================================
# Product Admin
# ================================================

@admin.register(Product)
class ProductAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = [
        'thumb', 'name', 'category', 'price_display',
        'discount_badge', 'stock_badge', 'variants_count', 'is_active', 'is_hot', 'is_new', 'order'
    ]
    list_display_links = ['name']
    list_editable = ['is_active', 'is_hot', 'is_new']
    list_filter = ['category', 'is_active', 'is_hot', 'is_new']
    search_fields = ['name', 'category__name']
    ordering = ['order']
    readonly_fields = ['created_at', 'updated_at', 'image_preview', 'discount_info', 'product_type_info']
    list_per_page = 25
    list_select_related = ['category']

    fieldsets = (
        ('معلومات المنتج', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('الصورة الرئيسية', {
            'fields': ('image', 'image_preview')
        }),
        ('الأسعار', {
            'fields': ('price', 'old_price', 'discount_info'),
            'description': 'سعر المنتج الأساسي. سعر المتغيرات يُحدد من خلال مقاسات النمط.'
        }),
        ('المخزون (للمنتجات البسيطة فقط)', {
            'fields': ('stock',),
            'description': 'المخزون يُستخدم فقط للمنتجات البسيطة (بدون ألوان أو مقاسات أو أنماط). إذا كان للمنتج متغيرات، استخدم المخزون في جدول المتغيرات.'
        }),
        ('الوصف والتكوين', {
            'fields': ('product_type_info', 'has_patterns', 'has_product_level_sizes', 'has_colors'),
            'description': 'حدد وصف المنتج: عليه أنماط؟ عليه مقاسات؟ عليه ألوان فقط؟ إذا لم تحدد شيئاً، سيكون منتج بسيط.'
        }),
        ('الحالة', {
            'fields': ('is_active', 'is_new', 'is_hot', 'rating', 'order')
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [
        PatternInline,
        ProductColorInline,
        ProductSizeInline,
        SimpleProductVariantInline,
        ProductImageInline,
        ProductSpecificationInline,
    ]

    def thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:44px;height:44px;object-fit:cover;border-radius:6px;border:1px solid #eee;" />',
                obj.image.url
            )
        return mark_safe('<span style="font-size:1.5rem;">📦</span>')
    thumb.short_description = ''

    def price_display(self, obj):
        if obj.old_price and obj.old_price > obj.price:
            return format_html(
                '<b style="color:#28a745;">{} ج.م</b> <s style="color:#999;font-size:0.8em;">{} ج.م</s>',
                obj.price, obj.old_price
            )
        return format_html('<b>{} ج.م</b>', obj.price)
    price_display.short_description = 'السعر'
    price_display.admin_order_field = 'price'

    def discount_badge(self, obj):
        pct = obj.get_discount_percent()
        if pct > 0:
            return format_html(
                '<span style="background:#dc3545;color:#fff;padding:2px 7px;border-radius:10px;font-size:0.8em;font-weight:bold;">-{}%</span>',
                pct
            )
        return '—'
    discount_badge.short_description = 'خصم'

    def variants_count(self, obj):
        count = obj.variants.count()
        if count > 0:
            return format_html('<span style="color:#007bff;font-weight:bold;">{} متغير</span>', count)
        return format_html('<span style="color:#dc3545;">{}</span>', 'لا يوجد')
    variants_count.short_description = 'المتغيرات'

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:220px;border-radius:8px;margin-top:6px;" />',
                obj.image.url
            )
        return format_html('<span>{}</span>', 'لا توجد صورة')
    image_preview.short_description = 'معاينة'

    def discount_info(self, obj):
        pct = obj.get_discount_percent()
        if pct > 0:
            return format_html('<b style="color:#dc3545;">{}% خصم</b>', pct)
        return format_html('<span>{}</span>', 'لا يوجد خصم')
    discount_info.short_description = 'نسبة الخصم'
    
    def stock_badge(self, obj):
        """عرض حالة المخزون للمنتجات البسيطة"""
        if obj.is_simple_product():
            if obj.stock > 10:
                return format_html('<span style="color:#28a745;font-weight:bold;">✓ {}</span>', obj.stock)
            elif obj.stock > 0:
                return format_html('<span style="color:#ffc107;font-weight:bold;">⚠ {}</span>', obj.stock)
            else:
                return format_html('<span style="color:#dc3545;font-weight:bold;">✗ نفد</span>', obj.stock)
        else:
            return format_html('<span style="color:#6c757d;">—</span>')
    stock_badge.short_description = 'المخزون'
    
    def product_type_info(self, obj):
        """عرض نوع المنتج"""
        if obj.is_simple_product():
            return format_html('<span style="background:#28a745;color:white;padding:4px 10px;border-radius:4px;font-size:0.85em;">منتج بسيط</span>')
        elif obj.check_if_has_patterns():
            return format_html('<span style="background:#007bff;color:white;padding:4px 10px;border-radius:4px;font-size:0.85em;">له أنماط</span>')
        elif obj.check_if_has_product_level_sizes():
            return format_html('<span style="background:#17a2b8;color:white;padding:4px 10px;border-radius:4px;font-size:0.85em;">له مقاسات</span>')
        elif obj.has_colors:
            return format_html('<span style="background:#ffc107;color:#000;padding:4px 10px;border-radius:4px;font-size:0.85em;">له ألوان فقط</span>')
        return format_html('<span style="color:#6c757d;">غير محدد</span>')
    product_type_info.short_description = 'نوع المنتج'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('variants')

    actions = ['activate', 'deactivate', 'mark_hot', 'mark_new', 'generate_simple_variants', 'generate_color_only_variants']

    def generate_simple_variants(self, request, queryset):
        """
        إنشاء متغيرات تلقائياً من الألوان والمقاسات بدون أنماط
        يربط كل لون مع كل مقاس للمنتجات المحددة
        """
        total_created = 0
        total_skipped = 0
        
        for product in queryset:
            # Get all colors for this product
            colors = ProductColor.objects.filter(product=product).select_related('color')
            # Get all sizes for this product
            sizes = ProductSize.objects.filter(product=product).select_related('size')
            
            if not colors.exists():
                self.message_user(
                    request, 
                    f'المنتج "{product.name}" ليس له ألوان. أضف ألوان أولاً.', 
                    messages.WARNING
                )
                continue
                
            if not sizes.exists():
                self.message_user(
                    request, 
                    f'المنتج "{product.name}" ليس له مقاسات. أضف مقاسات أولاً.', 
                    messages.WARNING
                )
                continue
            
            # Create variant for each color-size combination
            for product_color in colors:
                for product_size in sizes:
                    # Check if variant already exists
                    variant, created = ProductVariant.objects.get_or_create(
                        product=product,
                        pattern=None,  # No pattern - direct color-size linking
                        color=product_color.color,
                        size=product_size.size,
                        defaults={
                            'price': product_size.price,
                            'stock': 0,  # Set initial stock to 0
                            'order': 0
                        }
                    )
                    
                    if created:
                        total_created += 1
                    else:
                        total_skipped += 1
        
        if total_created > 0:
            self.message_user(
                request, 
                f'تم إنشاء {total_created} متغير جديد بنجاح! (تم تخطي {total_skipped} متغير موجود مسبقاً)', 
                messages.SUCCESS
            )
        else:
            self.message_user(
                request, 
                f'لم يتم إنشاء متغيرات جديدة. جميع المتغيرات ({total_skipped}) موجودة مسبقاً.', 
                messages.INFO
            )
    
    def generate_color_only_variants(self, request, queryset):
        """
        إنشاء متغيرات تلقائياً من الألوان فقط (بدون مقاسات)
        للمنتجات التي لها ألوان فقط بدون أنماط أو مقاسات
        """
        total_created = 0
        total_skipped = 0
        
        for product in queryset:
            # Skip products with patterns or sizes - they should use other generators
            if product.check_if_has_patterns() or product.check_if_has_product_level_sizes():
                continue
                
            # Get all colors for this product
            colors = ProductColor.objects.filter(product=product).select_related('color')
            
            if not colors.exists():
                self.message_user(
                    request, 
                    f'المنتج "{product.name}" ليس له ألوان. أضف ألوان أولاً.', 
                    messages.WARNING
                )
                continue
            
            # Create variant for each color (no size, no pattern)
            for product_color in colors:
                # Check if variant already exists
                variant, created = ProductVariant.objects.get_or_create(
                    product=product,
                    pattern=None,  # No pattern
                    color=product_color.color,
                    size=None,  # No size
                    defaults={
                        'price': product.price,
                        'stock': 0,  # Set initial stock to 0
                        'order': 0
                    }
                )
                
                if created:
                    total_created += 1
                else:
                    total_skipped += 1
        
        if total_created > 0:
            self.message_user(
                request, 
                f'تم إنشاء {total_created} متغير ألوان جديد! (تم تخطي {total_skipped} متغير موجود مسبقاً)', 
                messages.SUCCESS
            )
        else:
            self.message_user(
                request, 
                f'لم يتم إنشاء متغيرات جديدة. جميع المتغيرات ({total_skipped}) موجودة مسبقاً.', 
                messages.INFO
            )
    
    generate_color_only_variants.short_description = '🎨 إنشاء متغيرات ألوان فقط (بدون مقاسات)'

    def activate(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, 'تم تفعيل المنتجات', messages.SUCCESS)
    activate.short_description = 'تفعيل'

    def deactivate(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, 'تم إيقاف المنتجات', messages.SUCCESS)
    deactivate.short_description = 'إيقاف'

    def mark_hot(self, request, queryset):
        queryset.update(is_hot=True)
        self.message_user(request, 'تم التحديد كمشهور', messages.SUCCESS)
    mark_hot.short_description = 'تحديد كمشهور'

    def mark_new(self, request, queryset):
        queryset.update(is_new=True)
        self.message_user(request, 'تم التحديد كجديد', messages.SUCCESS)
    mark_new.short_description = 'تحديد كجديد'


# ================================================
# Color Admin  (required for autocomplete)
# ================================================

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['swatch', 'name', 'code', 'products_count']
    list_display_links = ['name']
    search_fields = ['name', 'code']
    list_per_page = 30

    def swatch(self, obj):
        if obj.code:
            return format_html(
                '<span style="display:inline-block;width:22px;height:22px;background:{};border-radius:50%;border:2px solid #ccc;"></span>',
                obj.code
            )
        return '—'
    swatch.short_description = ''

    def products_count(self, obj):
        count = obj.productcolor_set.count()
        return format_html('<span style="color:#007bff;">{}</span>', count) if count else '—'
    products_count.short_description = 'المنتجات'


# ================================================
# Size Admin  (required for autocomplete)
# ================================================

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['name', 'products_count', 'patterns_count']
    list_display_links = ['name']
    search_fields = ['name']
    list_per_page = 30

    def products_count(self, obj):
        count = obj.productsize_set.count()
        return format_html('<span style="color:#28a745;">{}</span>', count) if count else '—'
    products_count.short_description = 'المنتجات'

    def patterns_count(self, obj):
        count = obj.patternsize_set.count()
        return format_html('<span style="color:#007bff;">{}</span>', count) if count else '—'
    patterns_count.short_description = 'الأنماط'


# ================================================
# Pattern Admin — central hub for variant management
# ================================================

@admin.register(Pattern)
class PatternAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['product', 'name', 'has_sizes', 'base_price_display', 'sizes_count', 'variants_count', 'order']
    list_display_links = ['name']
    list_editable = []
    list_filter = ['has_sizes', 'product__category']
    search_fields = ['name', 'product__name']
    ordering = ['product', 'order']
    autocomplete_fields = ['product']
    list_per_page = 30
    list_select_related = ['product']

    fieldsets = (
        ('معلومات النمط', {
            'fields': ('product', 'name', 'order'),
            'description': 'اختر المنتج أولاً ثم أدخل اسم النمط.'
        }),
        ('التسعير', {
            'fields': ('has_sizes', 'base_price'),
            'description': (
                'إذا كان للنمط مقاسات: فعّل "له مقاسات" وأضفها في جدول "مقاسات النمط" أدناه. '
                'وإلا أدخل السعر الأساسي فقط.'
            )
        }),
    )

    inlines = [PatternColorInline, PatternImageInline, PatternSizeInline, PatternVariantInline]

    def base_price_display(self, obj):
        if obj.base_price:
            return format_html('<b style="color:#28a745;">{} ج.م</b>', obj.base_price)
        return '—'
    base_price_display.short_description = 'السعر الأساسي'
    base_price_display.admin_order_field = 'base_price'

    def sizes_count(self, obj):
        count = obj.pattern_sizes.count()
        return format_html('<span style="color:#17a2b8;">{} مقاس</span>', count) if count else '—'
    sizes_count.short_description = 'المقاسات'

    def variants_count(self, obj):
        count = ProductVariant.objects.filter(pattern=obj).count()
        if count > 0:
            return format_html('<span style="color:#28a745;font-weight:bold;">{} متغير</span>', count)
        return format_html('<span style="color:#dc3545;">{}</span>', 'لا يوجد')
    variants_count.short_description = 'المتغيرات'

    def save_formset(self, request, form, formset, change):
        """
        ROOT FIX for IntegrityError:
        Use formset.save(commit=False) so we can set product_id and pattern_id
        on every new ProductVariant BEFORE Django issues the DB INSERT.
        """
        if formset.model is not ProductVariant:
            super().save_formset(request, form, formset, change)
            return

        pattern = form.instance
        product_id = (
            Pattern.objects
            .filter(pk=pattern.pk)
            .values_list('product_id', flat=True)
            .first()
        )

        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.product_id:
                instance.product_id = product_id
            if not instance.pattern_id:
                instance.pattern_id = pattern.pk
            instance.save()

        for obj in formset.deleted_objects:
            obj.delete()

        formset.save_m2m()

    actions = ['auto_generate_variants']

    def auto_generate_variants(self, request, queryset):
        total = 0
        for pattern in queryset.select_related('product'):
            product = pattern.product
            colors = ProductColor.objects.filter(product=product).select_related('color')
            sizes = PatternSize.objects.filter(pattern=pattern).select_related('size')
            for pc in colors:
                for ps in sizes:
                    _, created = ProductVariant.objects.get_or_create(
                        product=product, pattern=pattern,
                        color=pc.color, size=ps.size,
                        defaults={'price': ps.price, 'stock': ps.stock}
                    )
                    if created:
                        total += 1
        self.message_user(request, f'تم إنشاء {total} متغير جديد', messages.SUCCESS)
    auto_generate_variants.short_description = 'إنشاء المتغيرات تلقائياً من المقاسات والألوان'


# ================================================
# ProductVariant Admin
# ================================================

@admin.register(ProductVariant)
class ProductVariantAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['product', 'pattern', 'color_badge', 'size', 'price_display', 'stock_badge', 'sku', 'order']
    list_display_links = ['product']
    list_editable = []
    list_filter = ['product__category', 'pattern', 'color', 'size']
    search_fields = ['product__name', 'pattern__name', 'color__name', 'size__name', 'sku']
    ordering = ['product', 'order']
    autocomplete_fields = ['product', 'pattern', 'color', 'size']
    list_per_page = 50
    list_select_related = ['product', 'pattern', 'color', 'size']

    fieldsets = (
        ('الربط', {
            'fields': ('product', 'pattern', 'color', 'size', 'sku', 'order'),
            'description': 'اربط هذا المتغير بمنتج ونمط ولون ومقاس.'
        }),
        ('المخزون والسعر', {
            'fields': ('stock', 'price'),
        }),
    )

    def color_badge(self, obj):
        if obj.color:
            if obj.color.code:
                return format_html(
                    '<span style="display:inline-block;width:14px;height:14px;background:{};border-radius:50%;border:1px solid #ccc;margin-left:4px;vertical-align:middle;"></span> {}',
                    obj.color.code, obj.color.name
                )
            return obj.color.name
        return '—'
    color_badge.short_description = 'اللون'

    def price_display(self, obj):
        price = obj.get_price()
        return format_html('<b style="color:#28a745;">{} ج.م</b>', price)
    price_display.short_description = 'السعر'

    def stock_badge(self, obj):
        if obj.stock > 10:
            color, label = '#28a745', f'✓ {obj.stock}'
        elif obj.stock > 0:
            color, label = '#ffc107', f'⚠ {obj.stock}'
        else:
            color, label = '#dc3545', '✗ نفد'
        return format_html('<span style="color:{};font-weight:bold;">{}</span>', color, label)
    stock_badge.short_description = 'المخزون'

    actions = ['reset_stock', 'set_stock_ten']

    def reset_stock(self, request, queryset):
        queryset.update(stock=0)
        self.message_user(request, 'تم تصفير المخزون', messages.SUCCESS)
    reset_stock.short_description = 'تصفير المخزون'

    def set_stock_ten(self, request, queryset):
        queryset.update(stock=10)
        self.message_user(request, 'تم ضبط المخزون على 10', messages.SUCCESS)
    set_stock_ten.short_description = 'ضبط المخزون على 10'


# ================================================
# Supporting standalone admins
# ================================================

@admin.register(ProductColor)
class ProductColorAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['product', 'color_badge', 'order']
    list_display_links = ['product']
    list_editable = []
    list_filter = ['color', 'product__category']
    search_fields = ['product__name', 'color__name']
    autocomplete_fields = ['product', 'color']
    list_per_page = 30
    list_select_related = ['product', 'color']

    def color_badge(self, obj):
        if obj.color.code:
            return format_html(
                '<span style="display:inline-block;width:16px;height:16px;background:{};border-radius:50%;border:1px solid #ccc;margin-left:5px;vertical-align:middle;"></span> {}',
                obj.color.code, obj.color.name
            )
        return obj.color.name
    color_badge.short_description = 'اللون'


@admin.register(ProductSize)
class ProductSizeAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['product', 'size', 'price_display', 'order']
    list_display_links = ['product']
    list_editable = []
    list_filter = ['size', 'product__category']
    search_fields = ['product__name', 'size__name']
    autocomplete_fields = ['product', 'size']
    list_per_page = 30
    list_select_related = ['product', 'size']

    def price_display(self, obj):
        return format_html('<b style="color:#28a745;">{} ج.م</b>', obj.price)
    price_display.short_description = 'السعر'


@admin.register(PatternSize)
class PatternSizeAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['pattern', 'size', 'price_display', 'stock_badge', 'order']
    list_display_links = ['pattern']
    list_editable = []
    list_filter = ['pattern__product__category', 'size']
    search_fields = ['pattern__name', 'pattern__product__name', 'size__name']
    autocomplete_fields = ['pattern', 'size']
    list_per_page = 40
    list_select_related = ['pattern', 'pattern__product', 'size']

    fieldsets = (
        ('الربط', {'fields': ('pattern', 'size', 'order')}),
        ('السعر والمخزون', {'fields': ('price', 'stock')}),
    )

    def price_display(self, obj):
        return format_html('<b style="color:#28a745;">{} ج.م</b>', obj.price)
    price_display.short_description = 'السعر'

    def stock_badge(self, obj):
        if obj.stock > 0:
            return format_html('<span style="color:#28a745;font-weight:bold;">✓ {}</span>', obj.stock)
        return format_html('<span style="color:#dc3545;font-weight:bold;">✗ نفد</span>')
    stock_badge.short_description = 'المخزون'


@admin.register(ProductImage)
class ProductImageAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['preview', 'product', 'color_badge', 'order']
    list_display_links = ['product']
    list_editable = []
    list_filter = ['product__category', 'color']
    search_fields = ['product__name', 'color__name']
    autocomplete_fields = ['product', 'color']
    list_per_page = 40
    list_select_related = ['product', 'color']

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:6px;" />',
                obj.image.url
            )
        return '—'
    preview.short_description = ''

    def color_badge(self, obj):
        if obj.color and obj.color.code:
            return format_html(
                '<span style="display:inline-block;width:14px;height:14px;background:{};border-radius:50%;border:1px solid #ccc;margin-left:4px;vertical-align:middle;"></span> {}',
                obj.color.code, obj.color.name
            )
        return obj.color.name if obj.color else '—'
    color_badge.short_description = 'اللون'


@admin.register(ProductSpecification)
class ProductSpecificationAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['product', 'key', 'value', 'order']
    list_display_links = ['product']
    list_editable = []
    search_fields = ['key', 'value', 'product__name']
    autocomplete_fields = ['product']
    list_per_page = 40
    list_select_related = ['product']


@admin.register(PatternColor)
class PatternColorAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['pattern', 'color_badge', 'order']
    list_display_links = ['pattern']
    list_editable = []
    list_filter = ['pattern__product__category', 'color']
    search_fields = ['pattern__name', 'pattern__product__name', 'color__name']
    autocomplete_fields = ['pattern', 'color']
    list_per_page = 40
    list_select_related = ['pattern', 'pattern__product', 'color']

    def color_badge(self, obj):
        if obj.color and obj.color.code:
            return format_html(
                '<span style="display:inline-block;width:16px;height:16px;background:{};border-radius:50%;border:1px solid #ccc;margin-left:5px;vertical-align:middle;"></span> {}',
                obj.color.code, obj.color.name
            )
        return obj.color.name if obj.color else '—'
    color_badge.short_description = 'اللون'


@admin.register(PatternImage)
class PatternImageAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['preview', 'pattern', 'color_badge', 'order']
    list_display_links = ['pattern']
    list_editable = []
    list_filter = ['pattern__product__category', 'color']
    search_fields = ['pattern__name', 'pattern__product__name', 'color__name']
    autocomplete_fields = ['pattern', 'color']
    list_per_page = 40
    list_select_related = ['pattern', 'pattern__product', 'color']

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:6px;" />',
                obj.image.url
            )
        return '—'
    preview.short_description = ''

    def color_badge(self, obj):
        if obj.color and obj.color.code:
            return format_html(
                '<span style="display:inline-block;width:14px;height:14px;background:{};border-radius:50%;border:1px solid #ccc;margin-left:4px;vertical-align:middle;"></span> {}',
                obj.color.code, obj.color.name
            )
        return obj.color.name if obj.color else '—'
    color_badge.short_description = 'اللون'