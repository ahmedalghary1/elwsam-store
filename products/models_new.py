"""
REDESIGNED PRODUCT VARIANT SYSTEM
==================================

Architecture Decisions:
1. PatternSize model: Enables pattern-level size pricing
2. ProductSize model: Enables product-level size pricing  
3. Price resolution hierarchy: PatternSize > ProductSize > Product base price
4. Conditional logic: Pattern.has_sizes flag determines if size is required
5. Normalized structure: No price duplication, single source of truth

Supported Scenarios:
- Product with only sizes (no patterns)
- Product with patterns (each pattern may/may not have sizes)
- Mixed: Product-level sizes + Pattern-level sizes (pattern takes priority)
"""

from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, default='📁')
    is_hot = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'قسم'
        verbose_name_plural = 'الأقسام'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    # Base price (fallback if no size/pattern pricing exists)
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text='السعر الأساسي (يُستخدم إذا لم يتم تحديد سعر للمقاس أو النمط)'
    )
    old_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text='السعر القديم للعرض فقط'
    )
    
    # Product configuration flags
    has_patterns = models.BooleanField(
        default=False,
        help_text='هل المنتج يحتوي على أنماط (Patterns)؟'
    )
    has_product_level_sizes = models.BooleanField(
        default=False,
        help_text='هل المنتج يحتوي على مقاسات على مستوى المنتج؟'
    )
    
    # Status flags
    is_new = models.BooleanField(default=True)
    is_hot = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    rating = models.FloatField(default=5.0)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'منتج'
        verbose_name_plural = 'المنتجات'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    def get_configuration_type(self):
        """
        Returns product configuration type for frontend logic
        """
        if self.has_patterns:
            return 'pattern_based'
        elif self.has_product_level_sizes:
            return 'size_based'
        else:
            return 'simple'
    
    def requires_size_selection(self):
        """
        Determines if size selection is required at product level
        """
        return self.has_product_level_sizes
    
    def get_price(self, pattern_id=None, size_id=None):
        """
        Price resolution with priority hierarchy:
        1. PatternSize (if pattern and size provided)
        2. ProductSize (if only size provided)
        3. Pattern base price (if only pattern provided)
        4. Product base price (fallback)
        """
        # Priority 1: Pattern + Size
        if pattern_id and size_id:
            pattern_size = PatternSize.objects.filter(
                pattern_id=pattern_id,
                size_id=size_id
            ).first()
            if pattern_size:
                return pattern_size.price
        
        # Priority 2: Product-level Size
        if size_id and self.has_product_level_sizes:
            product_size = ProductSize.objects.filter(
                product=self,
                size_id=size_id
            ).first()
            if product_size:
                return product_size.price
        
        # Priority 3: Pattern base price
        if pattern_id:
            pattern = Pattern.objects.filter(id=pattern_id).first()
            if pattern and pattern.base_price:
                return pattern.base_price
        
        # Priority 4: Product base price
        return self.base_price
    
    def get_stock(self, pattern_id=None, size_id=None, color_id=None):
        """
        Get stock for specific combination
        """
        variant = ProductVariant.objects.filter(
            product=self,
            pattern_id=pattern_id,
            size_id=size_id,
            color_id=color_id
        ).first()
        
        return variant.stock if variant else 0


class Pattern(models.Model):
    """
    Pattern can optionally have its own sizes with individual pricing
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="patterns")
    name = models.CharField(max_length=100)
    
    # Pattern-level pricing (optional, used if no sizes defined)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='السعر الأساسي للنمط (إذا لم يكن له مقاسات)'
    )
    
    # Configuration flag
    has_sizes = models.BooleanField(
        default=False,
        help_text='هل هذا النمط يحتوي على مقاسات خاصة به؟'
    )
    
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'نمط'
        verbose_name_plural = 'الأنماط'

    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    def requires_size_selection(self):
        """
        If pattern has sizes, size selection is REQUIRED
        """
        return self.has_sizes
    
    def get_available_sizes(self):
        """
        Get sizes available for this pattern
        """
        return PatternSize.objects.filter(pattern=self).select_related('size')
    
    def clean(self):
        """
        Validation: If has_sizes=True, must have at least one PatternSize
        """
        super().clean()
        if self.pk and self.has_sizes:
            if not PatternSize.objects.filter(pattern=self).exists():
                raise ValidationError(
                    'يجب إضافة مقاس واحد على الأقل للنمط الذي يحتوي على مقاسات'
                )


class Size(models.Model):
    """
    Global size catalog
    """
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'مقاس'
        verbose_name_plural = 'المقاسات'

    def __str__(self):
        return self.name


class ProductSize(models.Model):
    """
    Product-level size with individual pricing
    Used when product has sizes but no patterns
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_sizes")
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='سعر هذا المقاس على مستوى المنتج'
    )
    
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('product', 'size')
        verbose_name = 'مقاس منتج'
        verbose_name_plural = 'مقاسات المنتجات'

    def __str__(self):
        return f"{self.product.name} - {self.size.name} ({self.price} ج.م)"


class PatternSize(models.Model):
    """
    Pattern-level size with individual pricing
    Used when pattern has its own sizes
    Takes priority over ProductSize
    """
    pattern = models.ForeignKey(Pattern, on_delete=models.CASCADE, related_name="pattern_sizes")
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='سعر هذا المقاس لهذا النمط'
    )
    
    stock = models.IntegerField(
        default=0,
        help_text='المخزون المتاح لهذا التركيب (نمط + مقاس)'
    )
    
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('pattern', 'size')
        verbose_name = 'مقاس نمط'
        verbose_name_plural = 'مقاسات الأنماط'

    def __str__(self):
        return f"{self.pattern.name} - {self.size.name} ({self.price} ج.م)"


class Color(models.Model):
    """
    Global color catalog
    """
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=7, blank=True, help_text='كود اللون HEX (مثال: #FF0000)')

    class Meta:
        verbose_name = 'لون'
        verbose_name_plural = 'الألوان'

    def __str__(self):
        return self.name


class ProductColor(models.Model):
    """
    Colors available for a product
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_colors")
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('product', 'color')
        verbose_name = 'لون منتج'
        verbose_name_plural = 'ألوان المنتجات'

    def __str__(self):
        return f"{self.product.name} - {self.color.name}"


class ProductImage(models.Model):
    """
    Product images (can be color-specific)
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='products/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'صورة منتج'
        verbose_name_plural = 'صور المنتجات'

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductVariant(models.Model):
    """
    Final variant combination for stock tracking
    Price is calculated dynamically via Product.get_price()
    This model only tracks stock and SKU
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    pattern = models.ForeignKey(Pattern, on_delete=models.SET_NULL, null=True, blank=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    
    stock = models.IntegerField(default=0, help_text='المخزون المتاح')
    sku = models.CharField(max_length=100, blank=True, null=True, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'pattern', 'color', 'size')
        ordering = ['order']
        verbose_name = 'متغير منتج'
        verbose_name_plural = 'متغيرات المنتجات'
        indexes = [
            models.Index(fields=['product', 'pattern', 'size']),
            models.Index(fields=['product', 'size']),
        ]

    def __str__(self):
        parts = [self.product.name]
        if self.pattern:
            parts.append(self.pattern.name)
        if self.color:
            parts.append(self.color.name)
        if self.size:
            parts.append(self.size.name)
        return " - ".join(parts)
    
    def get_price(self):
        """
        Get price for this variant using product's price resolution logic
        """
        return self.product.get_price(
            pattern_id=self.pattern_id,
            size_id=self.size_id
        )
    
    def is_available(self):
        """
        Check if variant is available (has stock)
        """
        return self.stock > 0
    
    def clean(self):
        """
        Validation rules:
        1. If product has patterns, pattern is required
        2. If pattern has sizes, size is required
        3. If product has product-level sizes (no patterns), size is required
        """
        super().clean()
        
        # Rule 1: Pattern requirement
        if self.product.has_patterns and not self.pattern:
            raise ValidationError('يجب اختيار نمط لهذا المنتج')
        
        # Rule 2: Pattern-level size requirement
        if self.pattern and self.pattern.has_sizes and not self.size:
            raise ValidationError(f'يجب اختيار مقاس للنمط {self.pattern.name}')
        
        # Rule 3: Product-level size requirement
        if self.product.has_product_level_sizes and not self.pattern and not self.size:
            raise ValidationError('يجب اختيار مقاس لهذا المنتج')


class ProductSpecification(models.Model):
    """
    Product specifications/features
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="specs")
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'مواصفة'
        verbose_name_plural = 'مواصفات المنتجات'

    def __str__(self):
        return f"{self.key}: {self.value}"
