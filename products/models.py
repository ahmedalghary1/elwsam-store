from django.db import models
from django.utils.text import slugify
from accounts.models import User
# =========================
# Category (ترتيب الأقسام)
# =========================
class Category(models.Model):

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    slug = models.CharField(max_length=255, unique=True, blank=True, db_index=True)
    icon = models.CharField(max_length=50, default='📁', help_text='أيقونة Emoji أو نص قصير')
    is_hot = models.BooleanField(default=False, help_text='هل هذا القسم من الأقسام المشهورة؟')
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
            base_slug = slugify(self.name, allow_unicode=True)
            if not base_slug:
                base_slug = 'category'
            
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def get_product_count(self):
        """حساب عدد المنتجات في هذا القسم"""
        return self.product_set.count()
    
    def get_absolute_url(self):
        """الحصول على رابط القسم"""
        from django.urls import reverse
        return reverse('category_products', kwargs={'id': self.id, 'slug': self.slug})




# =========================
# Product (ترتيب المنتجات)
# =========================
class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True, blank=True, db_index=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    has_product_level_sizes = models.BooleanField(default=False)
    has_patterns = models.BooleanField(default=False)
    # معلومات الأسعار
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text='السعر القديم (للخصم)')
    
    # حالة المنتج
    is_new = models.BooleanField(default=True, help_text='هل المنتج جديد؟')
    is_hot = models.BooleanField(default=False, help_text='هل المنتج مشهور/مبيع؟')
    is_active = models.BooleanField(default=True, help_text='هل المنتج متاح؟')
    
    # Product configuration flags
    has_colors = models.BooleanField(
        default=False,
        help_text='هل المنتج يحتوي على ألوان فقط؟ (بدون أنماط أو مقاسات)'
    )
    
    # التقييمات والشهرة
    rating = models.FloatField(default=5.0, help_text='التقييم من 0 إلى 5')
    
    # الترتيب والتاريخ
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['order']
        verbose_name = 'منتج'
        verbose_name_plural = 'المنتجات'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            if not base_slug:
                base_slug = 'product'
            
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        """الحصول على رابط المنتج"""
        from django.urls import reverse
        return reverse('product_detail', kwargs={'id': self.id, 'slug': self.slug})
    
    def get_price_display(self):
        """عرض السعر مع الخصم إن وجد"""
        if self.old_price and self.old_price > self.price:
            discount = ((self.old_price - self.price) / self.old_price) * 100
            return f'{self.price:.2f} ج.م ({int(discount)}% خصم)'
        return f'{self.price:.2f} ج.م'
    
    def get_discount_percent(self):
        """حساب نسبة الخصم"""
        if self.old_price and self.old_price > self.price:
            return int(((self.old_price - self.price) / self.old_price) * 100)
        return 0
    
    def get_first_image(self):
        """الحصول على أول صورة للمنتج"""
        return self.images.first()
    
    def get_price(self, pattern_id=None, size_id=None, color_id=None):
        """
        Dynamic price resolution using hierarchy:
        1. PatternSize (pattern + size) - highest priority
        2. ProductSize (product + size)
        3. Pattern.base_price
        4. Product.price (base price) - fallback
        
        Args:
            pattern_id: Optional pattern ID
            size_id: Optional size ID
            color_id: Optional color ID (for future use)
        
        Returns:
            Decimal: Calculated price based on hierarchy
        """
        # Priority 1: PatternSize (pattern + size)
        if pattern_id and size_id:
            try:
                pattern_size = PatternSize.objects.get(
                    pattern_id=pattern_id,
                    size_id=size_id
                )
                return pattern_size.price
            except PatternSize.DoesNotExist:
                pass
        
        # Priority 2: ProductSize (product + size)
        if size_id:
            try:
                product_size = ProductSize.objects.get(
                    product=self,
                    size_id=size_id
                )
                return product_size.price
            except ProductSize.DoesNotExist:
                pass
        
        # Priority 3: Pattern base price
        if pattern_id:
            try:
                pattern = Pattern.objects.get(id=pattern_id)
                if pattern.base_price:
                    return pattern.base_price
            except Pattern.DoesNotExist:
                pass
        
        # Priority 4: Product base price (fallback)
        return self.price
    
    def has_variants(self):
        """Check if product has any variants"""
        return self.variants.exists()
    
    def has_patterns(self):
        """Check if product has patterns"""
        return self.patterns.exists()
    
    def has_product_level_sizes(self):
        """Check if product has product-level sizes"""
        return self.product_sizes.exists()
    
    def get_configuration_type(self):
        """
        Returns product configuration type for frontend logic
        Priority: pattern_based > size_based > color_only > simple
        """
        if self.has_patterns():
            return 'pattern_based'
        elif self.has_product_level_sizes():
            return 'size_based'
        elif self.has_colors:
            return 'color_only'
        else:
            return 'simple'
    
    def requires_color_selection(self):
        """
        Determines if color selection is required
        """
        return self.has_colors
    
    def requires_size_selection(self):
        """
        Determines if size selection is required at product level
        """
        return self.has_product_level_sizes()

    
# =========================
# Pattern (ترتيب الأنماط)
# =========================
class Pattern(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="patterns")
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    
    # Multi-level pricing support
    has_sizes = models.BooleanField(
        default=False,
        help_text='هل هذا النمط يتطلب اختيار مقاس؟'
    )
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='السعر الأساسي للنمط (إذا لم يكن له مقاسات)'
    )

    class Meta:
        ordering = ['order']
        verbose_name = 'نمط'
        verbose_name_plural = 'الأنماط'

    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    def requires_size_selection(self):
        """Check if this pattern requires size selection"""
        return self.has_sizes
    
    def clean(self):
        """Validate that pattern has either sizes or base_price"""
        from django.core.exceptions import ValidationError
        if not self.has_sizes and not self.base_price:
            raise ValidationError(
                'يجب تحديد سعر أساسي للنمط إذا لم يكن له مقاسات'
            )


# =========================
# Color (عام)
# =========================
class Color(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=7, blank=True)

    class Meta:
        verbose_name = 'لون'
        verbose_name_plural = 'الألوان'

    def __str__(self):
        return self.name


# =========================
# ProductColor (ترتيب الألوان لكل منتج)
# =========================
class ProductColor(models.Model):
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
    
    
    def create_variants_for_pattern_sizes(self):
        """Create ProductVariant for all pattern-size combinations"""
        from .models import Pattern, PatternSize, ProductVariant
        
        product = self.product
        color = self.color
        
        # Get all patterns with sizes
        patterns = Pattern.objects.filter(product=product, has_sizes=True)
        
        created_count = 0
        for pattern in patterns:
            # Get all sizes for this pattern
            pattern_sizes = PatternSize.objects.filter(pattern=pattern).select_related('size')
            
            for ps in pattern_sizes:
                # Check if variant already exists
                if not ProductVariant.objects.filter(
                    product=product,
                    pattern=pattern,
                    color=color,
                    size=ps.size
                ).exists():
                    # Create variant
                    ProductVariant.objects.create(
                        product=product,
                        pattern=pattern,
                        color=color,
                        size=ps.size,
                        price=ps.price,
                        stock=ps.stock,
                        order=0
                    )
                    created_count += 1
        
        return created_count


# =========================
# Size (عام)
# =========================
class Size(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'مقاس'
        verbose_name_plural = 'المقاسات'

    def __str__(self):
        return self.name


# =========================
# ProductSize (ترتيب المقاسات لكل منتج)
# =========================
class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_sizes")
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    
    # Multi-level pricing: product-level size pricing
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text='السعر لهذا المقاس على مستوى المنتج'
    )

    class Meta:
        ordering = ['order']
        unique_together = ('product', 'size')
        verbose_name = 'مقاس منتج'
        verbose_name_plural = 'مقاسات المنتجات'
        indexes = [
            models.Index(fields=['product', 'size']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.size.name} ({self.price} ج.م)"


# =========================
# PatternSize (مقاسات النمط مع الأسعار)
# =========================
class PatternSize(models.Model):
    """Pattern-specific size pricing (highest priority in price hierarchy)"""
    pattern = models.ForeignKey(Pattern, on_delete=models.CASCADE, related_name="pattern_sizes")
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text='السعر لهذا المقاس في هذا النمط'
    )
    stock = models.IntegerField(
        default=0,
        help_text='المخزون المتاح لهذا المقاس في هذا النمط'
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('pattern', 'size')
        verbose_name = 'مقاس نمط'
        verbose_name_plural = 'مقاسات الأنماط'
        indexes = [
            models.Index(fields=['pattern', 'size']),
            models.Index(fields=['pattern', 'stock']),
        ]

    def __str__(self):
        return f"{self.pattern.name} - {self.size.name} ({self.price} ج.م)"
    
    def is_available(self):
        """Check if this pattern-size combination is in stock"""
        return self.stock > 0
    
    
    def create_variants_for_colors(self):
        """Create ProductVariant for all colors of this product"""
        from .models import ProductColor, ProductVariant
        
        product = self.pattern.product
        pattern = self.pattern
        size = self.size
        
        # Get all colors for this product
        product_colors = ProductColor.objects.filter(product=product).select_related('color')
        
        created_count = 0
        for pc in product_colors:
            # Check if variant already exists
            if not ProductVariant.objects.filter(
                product=product,
                pattern=pattern,
                color=pc.color,
                size=size
            ).exists():
                # Create variant
                ProductVariant.objects.create(
                    product=product,
                    pattern=pattern,
                    color=pc.color,
                    size=size,
                    price=self.price,
                    stock=self.stock,
                    order=0
                )
                created_count += 1
        
        return created_count


# =========================
# Product Images (ترتيب الصور لكل لون)
# =========================
class ProductImage(models.Model):
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


# =========================
# Variant (التركيبة النهائية)
# =========================
class ProductVariant(models.Model):
    """
    Product variant for stock tracking only.
    Price is calculated dynamically using Product.get_price() method.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")

    pattern = models.ForeignKey(Pattern, on_delete=models.SET_NULL, null=True, blank=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    # DEPRECATED: Will be removed in future migration
    # Price is now calculated dynamically via Product.get_price()
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text='DEPRECATED: Use Product.get_price() instead'
    )
    
    stock = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('product', 'pattern', 'color', 'size')
        ordering = ['order']
        verbose_name = 'متغير منتج'
        verbose_name_plural = 'متغيرات المنتجات'
        indexes = [
            models.Index(fields=['product', 'pattern', 'size']),
            models.Index(fields=['product', 'stock']),
            models.Index(fields=['product', 'pattern', 'color', 'size']),
        ]

    def __str__(self):
        parts = [self.product.name]
        if self.pattern:
            parts.append(self.pattern.name)
        if self.color:
            parts.append(self.color.name)
        if self.size:
            parts.append(self.size.name)
        return ' - '.join(parts)
    
    def get_price(self):
        """Get dynamic price using Product.get_price() hierarchy"""
        return self.product.get_price(
            pattern_id=self.pattern_id,
            size_id=self.size_id,
            color_id=self.color_id
        )
    
    def is_available(self):
        """Check if variant is in stock"""
        return self.stock > 0
    
    def clean(self):
        """Validate variant configuration"""
        from django.core.exceptions import ValidationError
        
        # If pattern has sizes, size must be selected
        if self.pattern and self.pattern.has_sizes and not self.size:
            raise ValidationError(
                'يجب اختيار مقاس لهذا النمط'
            )
        
        # If product is color_only (no patterns, no sizes, has colors), color is required
        if (not self.product.has_patterns() and 
            not self.product.has_product_level_sizes() and 
            self.product.has_colors and 
            not self.color):
            raise ValidationError('يجب اختيار لون لهذا المنتج')


# =========================
# Specifications (ترتيب المواصفات)
# =========================
class ProductSpecification(models.Model):
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



