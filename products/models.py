from django.db import models


# =========================
# Category (ترتيب الأقسام)
# =========================
class Category(models.Model):
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


# =========================
# Product (ترتيب المنتجات)
# =========================
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


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

    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('product', 'pattern', 'color', 'size')

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



# =========================
#  Wishlist 
# =========================
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.email} → {self.product.name}"


# =========================
#  OTP Model 
# =========================
class UserOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP for {self.user.email}: {self.code}"