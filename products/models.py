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
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, default='📁', help_text='أيقونة Emoji أو نص قصير')
    is_hot = models.BooleanField(default=False, help_text='هل هذا القسم من الأقسام المشهورة؟')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
    
    def get_product_count(self):
        """حساب عدد المنتجات في هذا القسم"""
        return self.product_set.count()

# =========================
# Product (ترتيب المنتجات)
# =========================
class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    # معلومات الأسعار
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text='السعر القديم (للخصم)')
    
    # حالة المنتج
    is_new = models.BooleanField(default=True, help_text='هل المنتج جديد؟')
    is_hot = models.BooleanField(default=False, help_text='هل المنتج مشهور/مبيع؟')
    is_active = models.BooleanField(default=True, help_text='هل المنتج متاح؟')
    
    # التقييمات والشهرة
    rating = models.FloatField(default=5.0, help_text='التقييم من 0 إلى 5')
    
    # الترتيب والتاريخ
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
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

    
# =========================
# Pattern (ترتيب الأنماط)
# =========================
class Pattern(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="patterns")
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - {self.name}"


# =========================
# Color (عام)
# =========================
class Color(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=7, blank=True)

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

    def __str__(self):
        return f"{self.product.name} - {self.color.name}"


# =========================
# Size (عام)
# =========================
class Size(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


# =========================
# ProductSize (ترتيب المقاسات لكل منتج)
# =========================
class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_sizes")
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('product', 'size')

    def __str__(self):
        return f"{self.product.name} - {self.size.name}"


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

    def __str__(self):
        return f"Image for {self.product.name}"


# =========================
# Variant (التركيبة النهائية)
# =========================
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")

    pattern = models.ForeignKey(Pattern, on_delete=models.SET_NULL, null=True, blank=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('product', 'pattern', 'color', 'size')
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} Variant"


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

    def __str__(self):
        return f"{self.key}: {self.value}"



