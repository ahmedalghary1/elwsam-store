from django.db import models
from django.conf import settings
from products.models import Product, ProductVariant

from django.db.models import Sum
# =========================
# Cart Model (سلة التسوق)
# =========================
class Cart(models.Model):
    """
    سلة التسوق للمستخدمين المسجلين
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'سلة تسوق'
        verbose_name_plural = 'سلات التسوق'

    def __str__(self):
        return f'سلة {self.user.email}'

    def get_total_price(self):
        """حساب إجمالي السعر"""
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_items(self):
        """حساب عدد العناصر"""
        return self.items.aggregate(total=Sum('quantity'))['total'] or 0

    def get_subtotal(self):
        """إجمالي السعر قبل الشحن"""
        return self.get_total_price()

    @property
    def subtotal(self):
        return self.get_subtotal()
# =========================
# CartItem Model (عنصر في السلة)
# =========================
class CartItem(models.Model):
    """
    عنصر في سلة التسوق
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product', 'variant')
        verbose_name = 'عنصر سلة'
        verbose_name_plural = 'عناصر السلات'

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        """حساب السعر الإجمالي لهذا العنصر"""
        if self.variant and self.variant.price:
            return self.variant.price * self.quantity
        return self.product.price * self.quantity


# =========================
# Order Model (الطلب)
# =========================
class Order(models.Model):
    """
    نموذج الطلب - للمستخدمين المسجلين والضيوف
    """
    STATUS_CHOICES = [
        ('pending', 'في انتظار الدفع'),
        ('paid', 'مدفوع'),
        ('processing', 'قيد المعالجة'),
        ('shipped', 'تم الشحن'),
        ('delivered', 'تم التسليم'),
        ('cancelled', 'ملغي'),
    ]

    class Meta:
        verbose_name = 'طلب'
        verbose_name_plural = 'الطلبات'
        ordering = ['-created_at']

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # معلومات الشحن
    shipping_address = models.TextField()
    shipping_phone = models.CharField(max_length=20)
    shipping_name = models.CharField(max_length=255, default='', blank=True)
    shipping_city = models.CharField(max_length=100, default='', blank=True)
    shipping_notes = models.TextField(blank=True, null=True)

    # معلومات الدفع
    payment_method = models.CharField(max_length=50, default='cash_on_delivery')

    # للضيوف - بريد إلكتروني اختياري
    guest_email = models.EmailField(blank=True, null=True)

    # التواريخ
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f'طلب #{self.id} - {self.user.email}'
        return f'طلب #{self.id} - ضيف ({self.shipping_name})'

    def get_total_items(self):
        """حساب عدد العناصر في الطلب"""
        return sum(item.quantity for item in self.items.all())

    def get_subtotal(self):
        return sum(item.price * item.quantity for item in self.items.all())

    @property
    def is_guest_order(self):
        """التحقق من كون الطلب لضيف"""
        return self.user is None
# =========================
# OrderItem Model (عنصر في الطلب)
# =========================
class OrderItem(models.Model):
    """
    عنصر في الطلب
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # السعر وقت الشراء

    class Meta:
        verbose_name = 'عنصر طلب'
        verbose_name_plural = 'عناصر الطلبات'

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        """حساب السعر الإجمالي"""
        return self.price * self.quantity
