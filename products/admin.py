from django.contrib import admin
from .models import (
    Category, Product, Pattern, Color, ProductColor, Size, ProductSize,
    ProductImage, ProductVariant, ProductSpecification
)


# =========================
# Inlines
# =========================

class PatternInline(admin.TabularInline):
    model = Pattern
    extra = 1
    fields = ['name', 'order']
    ordering = ['order']


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    fields = ['color', 'order']
    ordering = ['order']


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1
    fields = ['size', 'order']
    ordering = ['order']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['color', 'image', 'order']
    ordering = ['order']


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1
    fields = ['key', 'value', 'order']
    ordering = ['order']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['pattern', 'color', 'size', 'price', 'stock', 'sku']
    ordering = ['product', 'pattern', 'color', 'size']


# =========================
# ModelAdmins
# =========================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'image']
    list_editable = ['order']
    search_fields = ['name']
    ordering = ['order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'order']
    list_editable = ['order']
    list_filter = ['category']
    search_fields = ['name', 'description']
    ordering = ['order']
    inlines = [
        PatternInline,
        ProductColorInline,
        ProductSizeInline,
        ProductImageInline,
        ProductSpecificationInline,
        ProductVariantInline,
    ]


@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'order']
    list_editable = ['order']
    list_filter = ['product']
    search_fields = ['name']
    ordering = ['order']


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name']


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['product', 'color', 'order']
    list_editable = ['order']
    list_filter = ['product', 'color']
    ordering = ['order']


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ['product', 'size', 'order']
    list_editable = ['order']
    list_filter = ['product', 'size']
    ordering = ['order']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'color', 'image', 'order']
    list_editable = ['order']
    list_filter = ['product', 'color']
    ordering = ['order']


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'pattern', 'color', 'size', 'price', 'stock', 'sku']
    list_filter = ['product', 'pattern', 'color', 'size']
    search_fields = ['sku']
    ordering = ['product', 'pattern', 'color', 'size']


@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ['product', 'key', 'value', 'order']
    list_editable = ['order']
    list_filter = ['product']
    search_fields = ['key', 'value']
    ordering = ['order']