from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib import messages
from django import forms
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin
from .models import (
    Category, Product, Pattern, Color, ProductColor, Size, Type, ProductSize,
    ProductType, ProductTypeColor, ProductTypeImage, ProductImage, ProductVariant,
    ProductSpecification, PatternSize, PatternColor, PatternImage
)

import csv
from django.http import HttpResponse
from django.utils.html import strip_tags

# ================================================
# Admin list filters
# ================================================

class BasePriceRangeFilter(admin.SimpleListFilter):
    title = 'السعر'
    parameter_name = 'price_range'
    field_name = 'price'

    PRICE_RANGES = (
        ('under_100', 'أقل من 100 ج.م'),
        ('100_250', 'من 100 إلى 250 ج.م'),
        ('250_500', 'من 250 إلى 500 ج.م'),
        ('500_1000', 'من 500 إلى 1000 ج.م'),
        ('1000_plus', 'أكثر من 1000 ج.م'),
    )

    def lookups(self, request, model_admin):
        return self.PRICE_RANGES

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset

        filters_map = {
            'under_100': {f'{self.field_name}__lt': 100},
            '100_250': {f'{self.field_name}__gte': 100, f'{self.field_name}__lt': 250},
            '250_500': {f'{self.field_name}__gte': 250, f'{self.field_name}__lt': 500},
            '500_1000': {f'{self.field_name}__gte': 500, f'{self.field_name}__lt': 1000},
            '1000_plus': {f'{self.field_name}__gte': 1000},
        }

        selected_filters = filters_map.get(value)
        if not selected_filters:
            return queryset
        return queryset.filter(**selected_filters)


class ProductPriceRangeFilter(BasePriceRangeFilter):
    title = 'سعر المنتج'
    parameter_name = 'product_price_range'
    field_name = 'price'


class PatternBasePriceRangeFilter(BasePriceRangeFilter):
    title = 'السعر الأساسي'
    parameter_name = 'pattern_base_price_range'
    field_name = 'base_price'


class ProductSizePriceRangeFilter(BasePriceRangeFilter):
    title = 'سعر المقاس'
    parameter_name = 'product_size_price_range'
    field_name = 'price'


class ProductTypePriceRangeFilter(BasePriceRangeFilter):
    title = 'سعر النوع'
    parameter_name = 'product_type_price_range'
    field_name = 'price'


class PatternSizePriceRangeFilter(BasePriceRangeFilter):
    title = 'سعر مقاس النمط'
    parameter_name = 'pattern_size_price_range'
    field_name = 'price'


# ================================================
# Inlines — used inside ProductAdmin
# ================================================

class PatternInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Pattern
    extra = 0
    fields = ['name', 'has_sizes', 'base_price', 'edit_link']
    readonly_fields = ['edit_link']
    ordering = ['order']
    verbose_name = '\u0646\u0645\u0637'
    verbose_name_plural = '\u0627\u0644\u0623\u0646\u0645\u0627\u0637'
    show_change_link = False

    def edit_link(self, instance):
        if instance.pk:
            url = reverse('admin:products_pattern_change', args=[instance.pk])
            return format_html(
                '<a href="{}" style="background:#007bff;color:white;padding:3px 10px;'                'border-radius:4px;text-decoration:none;font-size:0.82em;">'                '\u2712 \u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u0642\u0627\u0633\u0627\u062a \u0648\u0627\u0644\u0645\u062a\u063a\u064a\u0631\u0627\u062a</a>',
                url
            )
        return '\u2014'
    edit_link.short_description = '\u0625\u062f\u0627\u0631\u0629'


class ProductColorInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductColor
    extra = 1
    fields = ['color', 'color_preview']
    readonly_fields = ['color_preview']
    ordering = ['order']
    verbose_name = '\u0644\u0648\u0646'
    verbose_name_plural = '\u0627\u0644\u0623\u0644\u0648\u0627\u0646'
    autocomplete_fields = ['color']

    def color_preview(self, obj):
        if obj.pk and obj.color and obj.color.code:
            return format_html(
                '<span style="display:inline-block;width:26px;height:26px;background:{};'                'border-radius:50%;border:2px solid #ddd;vertical-align:middle;"></span>',
                obj.color.code
            )
        return '\u2014'
    color_preview.short_description = '\u0645\u0639\u0627\u064a\u0646\u0629'


class ProductSizeInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductSize
    extra = 1
    fields = ['size', 'price']
    ordering = ['order']
    verbose_name = '\u0645\u0642\u0627\u0633'
    verbose_name_plural = '\u0627\u0644\u0645\u0642\u0627\u0633\u0627\u062a'
    autocomplete_fields = ['size']


class ProductTypeInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductType
    extra = 1
    fields = ['type', 'image', 'price', 'description', 'edit_link']
    readonly_fields = ['edit_link']
    ordering = ['order']
    verbose_name = 'نوع'
    verbose_name_plural = 'الأنواع'
    autocomplete_fields = ['type']

    def edit_link(self, instance):
        if instance.pk:
            url = reverse('admin:products_producttype_change', args=[instance.pk])
            return format_html(
                '<a href="{}" style="background:#007bff;color:white;padding:3px 10px;'
                'border-radius:4px;text-decoration:none;font-size:0.82em;">'
                '✒ إدارة الألوان والصور</a>',
                url
            )
        return '—'
    edit_link.short_description = 'إدارة'


class ProductImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'color', 'preview']
    readonly_fields = ['preview']
    ordering = ['order']
    verbose_name = '\u0635\u0648\u0631\u0629'
    verbose_name_plural = '\u0627\u0644\u0635\u0648\u0631 (\u0627\u0644\u0644\u0648\u0646 \u0627\u062e\u062a\u064a\u0627\u0631\u064a \u0644\u0644\u0645\u0646\u062a\u062c\u0627\u062a \u0627\u0644\u0628\u0633\u064a\u0637\u0629)'
    autocomplete_fields = ['color']

    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="width:60px;height:60px;object-fit:cover;border-radius:6px;" />',
                obj.image.url
            )
        return '\u2014'
    preview.short_description = '\u0645\u0639\u0627\u064a\u0646\u0629'


class ProductSpecificationInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductSpecification
    extra = 1
    fields = ['key', 'value']
    ordering = ['order']
    verbose_name = '\u0645\u0648\u0627\u0635\u0641\u0629'
    verbose_name_plural = '\u0627\u0644\u0645\u0648\u0627\u0635\u0641\u0627\u062a'


class SimpleProductVariantInline(SortableInlineAdminMixin, admin.TabularInline):
    """
    Inline for creating variants directly without Pattern requirement.
    Shows only variants where pattern is NULL (simple variants).
    """
    model = ProductVariant
    extra = 1
    fields = ['color', 'size', 'price', 'stock', 'sku']
    ordering = ['order']
    verbose_name = '\u0645\u062a\u063a\u064a\u0631 \u0628\u0633\u064a\u0637 (\u0644\u0648\u0646 + \u0645\u0642\u0627\u0633)'
    verbose_name_plural = '\u0627\u0644\u0645\u062a\u063a\u064a\u0631\u0627\u062a \u0627\u0644\u0628\u0633\u064a\u0637\u0629 (\u0628\u062f\u0648\u0646 \u0623\u0646\u0645\u0627\u0637)'

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
    verbose_name = '\u0645\u0642\u0627\u0633 \u0627\u0644\u0646\u0645\u0637'
    verbose_name_plural = '\u0645\u0642\u0627\u0633\u0627\u062a \u0627\u0644\u0646\u0645\u0637 (\u0633\u0639\u0631 + \u0645\u062e\u0632\u0648\u0646 \u0644\u0643\u0644 \u0645\u0642\u0627\u0633)'
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
                '<span style="display:inline-block;width:26px;height:26px;background:{};'
                'border-radius:50%;border:2px solid #ddd;vertical-align:middle;"></span>',
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


class ProductTypeColorInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductTypeColor
    extra = 1
    fields = ['color', 'color_preview']
    readonly_fields = ['color_preview']
    ordering = ['order']
    verbose_name = 'لون النوع'
    verbose_name_plural = 'ألوان النوع'
    autocomplete_fields = ['color']

    def color_preview(self, obj):
        if obj.pk and obj.color and obj.color.code:
            return format_html(
                '<span style="display:inline-block;width:26px;height:26px;background:{};'
                'border-radius:50%;border:2px solid #ddd;vertical-align:middle;"></span>',
                obj.color.code
            )
        return '—'
    color_preview.short_description = 'معاينة'


class ProductTypeImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductTypeImage
    extra = 1
    fields = ['color', 'image', 'preview']
    readonly_fields = ['preview']
    ordering = ['order']
    verbose_name = 'صورة النوع'
    verbose_name_plural = 'صور النوع'
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
                product_type = ProductType.objects.get(pk=object_id)
                type_colors = Color.objects.filter(
                    product_type_colors__product_type=product_type
                ).distinct()
                if type_colors.exists():
                    kwargs['queryset'] = type_colors
            except ProductType.DoesNotExist:
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
    verbose_name = '\u0645\u062a\u063a\u064a\u0631 (\u0644\u0648\u0646 + \u0645\u0642\u0627\u0633)'
    verbose_name_plural = '\u0627\u0644\u0645\u062a\u063a\u064a\u0631\u0627\u062a — اربط كل لون بمقاس (السعر يؤخذ تلقائياً من مقاسات النمط)'

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
    list_display = ['cat_icon', 'name', 'product_count', 'is_active', 'is_hot', 'order']
    list_display_links = ['name']
    list_editable = ['is_active', 'is_hot']
    list_filter = ['is_active', 'is_hot']
    search_fields = ['name']
    ordering = ['order']
    list_per_page = 25

    fieldsets = (
        ('\u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0627\u0644\u0642\u0633\u0645', {'fields': ('name', 'slug', 'description', 'icon')}),
        ('\u0627\u0644\u0635\u0648\u0631\u0629', {'fields': ('image',)}),
        ('\u0627\u0644\u0625\u0639\u062f\u0627\u062f\u0627\u062a', {'fields': ('is_active', 'is_hot', 'order')}),
    )

    def cat_icon(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:34px;height:34px;object-fit:cover;border-radius:6px;" />',
                obj.image.url
            )
        return format_html('<span style="font-size:1.4rem;">{}</span>', obj.icon or '\U0001f4c1')
    cat_icon.short_description = ''

    def product_count(self, obj):
        count = obj.product_set.filter(is_active=True).count()
        color = '#28a745' if count > 0 else '#999'
        return format_html('<span style="color:{};font-weight:bold;">{}</span>', color, count)
    product_count.short_description = '\u0639\u062f\u062f \u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a'


# ================================================
# Product Admin
# ================================================
@admin.register(Product)
class ProductAdmin(SortableAdminMixin, admin.ModelAdmin):
    sortable_field_name = "order"
    list_display = [
        'thumb', 'name', 'category', 'price_display',
        'discount_badge', 'stock_badge', 'variants_count', 'is_active', 'is_hot', 'is_new', 'order'
    ]
    list_display_links = ['name']
    list_editable = ['is_active', 'is_hot', 'is_new']
    list_filter = ['category', 'is_active', 'is_hot', 'is_new', ProductPriceRangeFilter]
    search_fields = ['name', 'seo_title', 'meta_description', 'category__name']
    ordering = ['order']
    readonly_fields = ['created_at', 'updated_at', 'image_preview', 'discount_info']
    list_per_page = 25
    list_select_related = ['category']
    fieldsets = (
        ('معلومات المنتج', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('SEO', {
            'fields': (
                'seo_title',
                'meta_description',
                'seo_h1',
                'seo_description',
                'focus_keywords',
                'seo_faq',
                'seo_image_alt_texts',
                'internal_linking_suggestions',
                'schema_markup',
            ),
            'classes': ('collapse',),
            'description': 'حقول SEO مخصصة لصفحة المنتج. عند تركها فارغة سيستخدم الموقع fallback تلقائي من اسم ووصف المنتج.'
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
        ('التوصيف والتكوين', {
            'fields': ('has_patterns', 'has_product_level_sizes', 'has_colors'),
            'description': 'حدد توصيف المنتج: عليه أنماط؟ عليه مقاسات؟ عليه ألوان فقط؟ إذا لم تحدد شيئاً، سيكون منتج بسيط.'
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
        ProductTypeInline,
        SimpleProductVariantInline,
        ProductImageInline,
        ProductSpecificationInline,
    ]

    actions = [
        'activate',
        'deactivate',
        'mark_hot',
        'mark_new',
        'generate_simple_variants',
        'generate_color_only_variants',
        'export_products_csv',
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
                return format_html('<span style="color:#dc3545;font-weight:bold;">✗ نفد</span>')
        else:
            return '—'
    stock_badge.short_description = 'المخزون'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('variants')

    def export_products_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="products_export.csv"'
        response.write('\ufeff')  # لدعم العربية في Excel

        writer = csv.writer(response)
        writer.writerow(['اسم المنتج', 'Slug', 'الوصف', 'السعر', 'القسم'])

        for product in queryset.select_related('category'):
            writer.writerow([
                product.name,
                product.slug,
                strip_tags(product.description or ''),
                product.price,
                product.category.name if product.category else '',
            ])

        return response
    export_products_csv.short_description = '📥 تصدير المنتجات المحددة إلى CSV'

    def generate_simple_variants(self, request, queryset):
        """
        إنشاء متغيرات تلقائياً من الألوان والمقاسات بدون أنماط
        يربط كل لون مع كل مقاس للمنتجات المحددة
        """
        total_created = 0
        total_skipped = 0
        
        for product in queryset:
            colors = ProductColor.objects.filter(product=product).select_related('color')
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
            
            for product_color in colors:
                for product_size in sizes:
                    variant, created = ProductVariant.objects.get_or_create(
                        product=product,
                        pattern=None,
                        color=product_color.color,
                        size=product_size.size,
                        defaults={
                            'price': product_size.price,
                            'stock': 0,
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
    generate_simple_variants.short_description = 'إنشاء متغيرات من الألوان والمقاسات'

    def generate_color_only_variants(self, request, queryset):
        """
        إنشاء متغيرات تلقائياً من الألوان فقط (بدون مقاسات)
        للمنتجات التي لها ألوان فقط بدون أنماط أو مقاسات
        """
        total_created = 0
        total_skipped = 0
        
        for product in queryset:
            if product.check_if_has_patterns() or product.check_if_has_product_level_sizes():
                continue
                
            colors = ProductColor.objects.filter(product=product).select_related('color')
            
            if not colors.exists():
                self.message_user(
                    request,
                    f'المنتج "{product.name}" ليس له ألوان. أضف ألوان أولاً.',
                    messages.WARNING
                )
                continue
            
            for product_color in colors:
                variant, created = ProductVariant.objects.get_or_create(
                    product=product,
                    pattern=None,
                    color=product_color.color,
                    size=None,
                    defaults={
                        'price': product.price,
                        'stock': 0,
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
                '<span style="display:inline-block;width:22px;height:22px;'                'background:{};border-radius:50%;border:2px solid #ccc;"></span>',
                obj.code
            )
        return '\u2014'
    swatch.short_description = ''

    def products_count(self, obj):
        count = obj.productcolor_set.count()
        return format_html('<span style="color:#007bff;">{}</span>', count) if count else '\u2014'
    products_count.short_description = '\u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a'


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
        return format_html('<span style="color:#28a745;">{}</span>', count) if count else '\u2014'
    products_count.short_description = '\u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a'

    def patterns_count(self, obj):
        count = obj.patternsize_set.count()
        return format_html('<span style="color:#007bff;">{}</span>', count) if count else '\u2014'
    patterns_count.short_description = '\u0627\u0644\u0623\u0646\u0645\u0627\u0637'


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'products_count']
    list_display_links = ['name']
    search_fields = ['name']
    list_per_page = 30

    def products_count(self, obj):
        count = obj.producttype_set.count()
        return format_html('<span style="color:#28a745;">{}</span>', count) if count else '\u2014'
    products_count.short_description = '\u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a'


# ================================================
# Pattern Admin — central hub for variant management
# ================================================

@admin.register(Pattern)
class PatternAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['product', 'name', 'has_sizes', 'base_price_display', 'sizes_count', 'variants_count', 'order']
    list_display_links = ['name']
    list_editable = []
    list_filter = ['has_sizes', 'product__category', PatternBasePriceRangeFilter]
    search_fields = ['name', 'product__name']
    ordering = ['product', 'order']
    autocomplete_fields = ['product']
    list_per_page = 30
    list_select_related = ['product']

    fieldsets = (
        ('\u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0627\u0644\u0646\u0645\u0637', {
            'fields': ('product', 'name', 'order'),
            'description': '\u0627\u062e\u062a\u0631 \u0627\u0644\u0645\u0646\u062a\u062c \u0623\u0648\u0644\u0627\u064b \u062b\u0645 \u0623\u062f\u062e\u0644 \u0627\u0633\u0645 \u0627\u0644\u0646\u0645\u0637.'
        }),
        ('\u0627\u0644\u062a\u0633\u0639\u064a\u0631', {
            'fields': ('has_sizes', 'base_price'),
            'description': (
                '\u0625\u0630\u0627 \u0643\u0627\u0646 \u0644\u0644\u0646\u0645\u0637 \u0645\u0642\u0627\u0633\u0627\u062a: \u0641\u0639\u0651\u0644 "\u0644\u0647 \u0645\u0642\u0627\u0633\u0627\u062a" \u0648\u0623\u0636\u0641\u0647\u0627 \u0641\u064a \u062c\u062f\u0648\u0644 "\u0645\u0642\u0627\u0633\u0627\u062a \u0627\u0644\u0646\u0645\u0637" \u0623\u062f\u0646\u0627\u0647. '
                '\u0648\u0625\u0644\u0627 \u0623\u062f\u062e\u0644 \u0627\u0644\u0633\u0639\u0631 \u0627\u0644\u0623\u0633\u0627\u0633\u064a \u0641\u0642\u0637.'
            )
        }),
    )

    inlines = [PatternColorInline, PatternImageInline, PatternSizeInline, PatternVariantInline]

    def base_price_display(self, obj):
        if obj.base_price:
            return format_html('<b style="color:#28a745;">{} \u062c.\u0645</b>', obj.base_price)
        return '\u2014'
    base_price_display.short_description = '\u0627\u0644\u0633\u0639\u0631 \u0627\u0644\u0623\u0633\u0627\u0633\u064a'
    base_price_display.admin_order_field = 'base_price'

    def sizes_count(self, obj):
        count = obj.pattern_sizes.count()
        return format_html('<span style="color:#17a2b8;">{} \u0645\u0642\u0627\u0633</span>', count) if count else '\u2014'
    sizes_count.short_description = '\u0627\u0644\u0645\u0642\u0627\u0633\u0627\u062a'

    def variants_count(self, obj):
        count = ProductVariant.objects.filter(pattern=obj).count()
        if count > 0:
            return format_html('<span style="color:#28a745;font-weight:bold;">{} متغير</span>', count)
        return format_html('<span style="color:#dc3545;">{}</span>', 'لا يوجد')
    variants_count.short_description = '\u0627\u0644\u0645\u062a\u063a\u064a\u0631\u0627\u062a'

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
        self.message_user(request, f'\u062a\u0645 \u0625\u0646\u0634\u0627\u0621 {total} \u0645\u062a\u063a\u064a\u0631 \u062c\u062f\u064a\u062f', messages.SUCCESS)
    auto_generate_variants.short_description = '\u0625\u0646\u0634\u0627\u0621 \u0627\u0644\u0645\u062a\u063a\u064a\u0631\u0627\u062a \u062a\u0644\u0642\u0627\u0626\u064a\u0627\u064b \u0645\u0646 \u0627\u0644\u0645\u0642\u0627\u0633\u0627\u062a \u0648\u0627\u0644\u0623\u0644\u0648\u0627\u0646'


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
        ('\u0627\u0644\u0631\u0628\u0637', {
            'fields': ('product', 'pattern', 'color', 'size', 'sku', 'order'),
            'description': '\u0627\u0631\u0628\u0637 \u0647\u0630\u0627 \u0627\u0644\u0645\u062a\u063a\u064a\u0631 \u0628\u0645\u0646\u062a\u062c \u0648\u0646\u0645\u0637 \u0648\u0644\u0648\u0646 \u0648\u0645\u0642\u0627\u0633.'
        }),
        ('\u0627\u0644\u0645\u062e\u0632\u0648\u0646 \u0648\u0627\u0644\u0633\u0639\u0631', {
            'fields': ('stock', 'price'),
        }),
    )

    def color_badge(self, obj):
        if obj.color:
            if obj.color.code:
                return format_html(
                    '<span style="display:inline-block;width:14px;height:14px;background:{};'                    'border-radius:50%;border:1px solid #ccc;margin-left:4px;vertical-align:middle;"></span> {}',
                    obj.color.code, obj.color.name
                )
            return obj.color.name
        return '\u2014'
    color_badge.short_description = '\u0627\u0644\u0644\u0648\u0646'

    def price_display(self, obj):
        price = obj.get_price()
        return format_html('<b style="color:#28a745;">{} \u062c.\u0645</b>', price)
    price_display.short_description = '\u0627\u0644\u0633\u0639\u0631'

    def stock_badge(self, obj):
        if obj.stock > 10:
            color, label = '#28a745', f'\u2713 {obj.stock}'
        elif obj.stock > 0:
            color, label = '#ffc107', f'\u26a0 {obj.stock}'
        else:
            color, label = '#dc3545', '\u2717 \u0646\u0641\u062f'
        return format_html('<span style="color:{};font-weight:bold;">{}</span>', color, label)
    stock_badge.short_description = '\u0627\u0644\u0645\u062e\u0632\u0648\u0646'

    actions = ['reset_stock', 'set_stock_ten']

    def reset_stock(self, request, queryset):
        queryset.update(stock=0)
        self.message_user(request, '\u062a\u0645 \u062a\u0635\u0641\u064a\u0631 \u0627\u0644\u0645\u062e\u0632\u0648\u0646', messages.SUCCESS)
    reset_stock.short_description = '\u062a\u0635\u0641\u064a\u0631 \u0627\u0644\u0645\u062e\u0632\u0648\u0646'

    def set_stock_ten(self, request, queryset):
        queryset.update(stock=10)
        self.message_user(request, '\u062a\u0645 \u0636\u0628\u0637 \u0627\u0644\u0645\u062e\u0632\u0648\u0646 \u0639\u0644\u0649 10', messages.SUCCESS)
    set_stock_ten.short_description = '\u0636\u0628\u0637 \u0627\u0644\u0645\u062e\u0632\u0648\u0646 \u0639\u0644\u0649 10'


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
                '<span style="display:inline-block;width:16px;height:16px;background:{};'                'border-radius:50%;border:1px solid #ccc;margin-left:5px;vertical-align:middle;"></span> {}',
                obj.color.code, obj.color.name
            )
        return obj.color.name
    color_badge.short_description = '\u0627\u0644\u0644\u0648\u0646'


@admin.register(ProductSize)
class ProductSizeAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['product', 'size', 'price_display', 'order']
    list_display_links = ['product']
    list_editable = []
    list_filter = ['size', 'product__category', ProductSizePriceRangeFilter]
    search_fields = ['product__name', 'size__name']
    autocomplete_fields = ['product', 'size']
    list_per_page = 30
    list_select_related = ['product', 'size']

    def price_display(self, obj):
        return format_html('<b style="color:#28a745;">{} \u062c.\u0645</b>', obj.price)
    price_display.short_description = '\u0627\u0644\u0633\u0639\u0631'


@admin.register(ProductType)
class ProductTypeAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['preview', 'product', 'type', 'price_display', 'order']
    list_display_links = ['product']
    list_editable = []
    list_filter = ['type', 'product__category', ProductTypePriceRangeFilter]
    search_fields = ['product__name', 'type__name', 'description']
    autocomplete_fields = ['product', 'type']
    list_per_page = 30
    list_select_related = ['product', 'type']
    inlines = [ProductTypeColorInline, ProductTypeImageInline]

    fieldsets = (
        ('معلومات النوع', {'fields': ('product', 'type', 'image', 'price', 'description', 'order')}),
    )

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:6px;" />',
                obj.image.url
            )
        return '\u2014'
    preview.short_description = ''

    def price_display(self, obj):
        return format_html('<b style="color:#28a745;">{} \u062c.\u0645</b>', obj.price)
    price_display.short_description = '\u0627\u0644\u0633\u0639\u0631'


@admin.register(ProductTypeColor)
class ProductTypeColorAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['product_type', 'color_badge', 'order']
    list_display_links = ['product_type']
    list_filter = ['color', 'product_type__product__category', 'product_type__type']
    search_fields = ['product_type__product__name', 'product_type__type__name', 'color__name']
    autocomplete_fields = ['product_type', 'color']
    list_per_page = 30
    list_select_related = ['product_type', 'product_type__product', 'product_type__type', 'color']

    def color_badge(self, obj):
        if obj.color and obj.color.code:
            return format_html(
                '<span style="display:inline-block;width:16px;height:16px;background:{};'
                'border-radius:50%;border:1px solid #ccc;margin-left:5px;vertical-align:middle;"></span> {}',
                obj.color.code, obj.color.name
            )
        return obj.color.name if obj.color else '—'
    color_badge.short_description = 'اللون'


@admin.register(ProductTypeImage)
class ProductTypeImageAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['preview', 'product_type', 'color_badge', 'order']
    list_display_links = ['product_type']
    list_filter = ['product_type__product__category', 'product_type__type', 'color']
    search_fields = ['product_type__product__name', 'product_type__type__name', 'color__name']
    autocomplete_fields = ['product_type', 'color']
    list_per_page = 40
    list_select_related = ['product_type', 'product_type__product', 'product_type__type', 'color']

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
                '<span style="display:inline-block;width:14px;height:14px;background:{};'
                'border-radius:50%;border:1px solid #ccc;margin-left:4px;vertical-align:middle;"></span> {}',
                obj.color.code, obj.color.name
            )
        return obj.color.name if obj.color else '—'
    color_badge.short_description = 'اللون'


@admin.register(PatternSize)
class PatternSizeAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['pattern', 'size', 'price_display', 'stock_badge', 'order']
    list_display_links = ['pattern']
    list_editable = []
    list_filter = ['pattern__product__category', 'size', PatternSizePriceRangeFilter]
    search_fields = ['pattern__name', 'pattern__product__name', 'size__name']
    autocomplete_fields = ['pattern', 'size']
    list_per_page = 40
    list_select_related = ['pattern', 'pattern__product', 'size']

    fieldsets = (
        ('\u0627\u0644\u0631\u0628\u0637', {'fields': ('pattern', 'size', 'order')}),
        ('\u0627\u0644\u0633\u0639\u0631 \u0648\u0627\u0644\u0645\u062e\u0632\u0648\u0646', {'fields': ('price', 'stock')}),
    )

    def price_display(self, obj):
        return format_html('<b style="color:#28a745;">{} \u062c.\u0645</b>', obj.price)
    price_display.short_description = '\u0627\u0644\u0633\u0639\u0631'

    def stock_badge(self, obj):
        if obj.stock > 0:
            return format_html('<span style="color:#28a745;font-weight:bold;">\u2713 {}</span>', obj.stock)
        return format_html('<span style="color:#dc3545;font-weight:bold;">{} {}</span>', '\u2717', '\u0646\u0641\u062f')
    stock_badge.short_description = '\u0627\u0644\u0645\u062e\u0632\u0648\u0646'


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
        return '\u2014'
    preview.short_description = ''

    def color_badge(self, obj):
        if obj.color and obj.color.code:
            return format_html(
                '<span style="display:inline-block;width:14px;height:14px;background:{};'                'border-radius:50%;border:1px solid #ccc;margin-left:4px;vertical-align:middle;"></span> {}',
                obj.color.code, obj.color.name
            )
        return obj.color.name if obj.color else '\u2014'
    color_badge.short_description = '\u0627\u0644\u0644\u0648\u0646'


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
                '<span style="display:inline-block;width:16px;height:16px;background:{};'
                'border-radius:50%;border:1px solid #ccc;margin-left:5px;vertical-align:middle;"></span> {}',
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
                '<span style="display:inline-block;width:14px;height:14px;background:{};'
                'border-radius:50%;border:1px solid #ccc;margin-left:4px;vertical-align:middle;"></span> {}',
                obj.color.code, obj.color.name
            )
        return obj.color.name if obj.color else '—'
    color_badge.short_description = 'اللون'
