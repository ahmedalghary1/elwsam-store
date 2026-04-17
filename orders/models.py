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
        variant_info = self.get_variant_display()
        if variant_info:
            return f"{self.quantity} x {self.product.name} ({variant_info})"
        return f"{self.quantity} x {self.product.name}"

    def get_unit_price(self):
        """Return the effective unit price for the current selection."""
        if self.variant:
            return self.variant.get_price()
        return self.product.price

    def get_total_price(self):
        """حساب السعر الإجمالي لهذا العنصر"""
        return self.get_unit_price() * self.quantity
    
    def get_variant_display(self):
        """
        Get formatted variant details from the linked variant
        Returns: "Pattern: X | Color: Y | Size: Z" or empty string
        """
        if not self.variant:
            return ""
        
        parts = []
        if self.variant.pattern:
            parts.append(f"النمط: {self.variant.pattern.name}")
        if self.variant.color:
            parts.append(f"اللون: {self.variant.color.name}")
        if self.variant.size:
            parts.append(f"المقاس: {self.variant.size.name}")
        return " | ".join(parts)
    
    def get_variant_display_short(self):
        """
        Get short variant display (values only)
        Returns: "X, Y, Z" or empty string
        """
        if not self.variant:
            return ""
        
        parts = []
        if self.variant.pattern:
            parts.append(self.variant.pattern.name)
        if self.variant.color:
            parts.append(self.variant.color.name)
        if self.variant.size:
            parts.append(self.variant.size.name)
        return ", ".join(parts)
    
    def get_variant_details_dict(self):
        """
        Get variant details as dictionary for JSON serialization
        Returns: dict with pattern, color, size info
        """
        if not self.variant:
            return {}
        
        details = {}
        if self.variant.pattern:
            details['pattern'] = {
                'id': self.variant.pattern.id,
                'name': self.variant.pattern.name
            }
        if self.variant.color:
            details['color'] = {
                'id': self.variant.color.id,
                'name': self.variant.color.name,
                'code': self.variant.color.code
            }
        if self.variant.size:
            details['size'] = {
                'id': self.variant.size.id,
                'name': self.variant.size.name
            }
        return details


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
    
    CONTACT_METHOD_CHOICES = [
        ('whatsapp', 'واتساب'),
        ('call', 'مكالمة هاتفية'),
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

    # طريقة التواصل المفضلة
    contact_method = models.CharField(
        max_length=20, 
        choices=CONTACT_METHOD_CHOICES, 
        default='whatsapp',
        verbose_name='طريقة التواصل المفضلة'
    )
    
    # ملاحظات الطلب
    order_notes = models.TextField(
        blank=True, 
        null=True,
        verbose_name='ملاحظات الطلب',
        help_text='أي ملاحظات إضافية للطلب'
    )

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
    
    # Variant details stored as text for permanent record (even if variant is deleted)
    pattern_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='النمط')
    color_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='اللون')
    color_code = models.CharField(max_length=20, blank=True, null=True, verbose_name='كود اللون')
    size_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='المقاس')

    class Meta:
        verbose_name = 'عنصر طلب'
        verbose_name_plural = 'عناصر الطلبات'

    def __str__(self):
        variant_info = self.get_variant_display()
        if variant_info:
            return f"{self.quantity} x {self.product.name} ({variant_info})"
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        """حساب السعر الإجمالي"""
        return self.price * self.quantity
    
    def get_variant_display(self):
        """
        Get formatted variant details for display
        Returns: "Pattern: X | Color: Y | Size: Z" or empty string
        """
        parts = []
        if self.pattern_name:
            parts.append(f"النمط: {self.pattern_name}")
        if self.color_name:
            parts.append(f"اللون: {self.color_name}")
        if self.size_name:
            parts.append(f"المقاس: {self.size_name}")
        return " | ".join(parts)
    
    def get_variant_display_short(self):
        """
        Get short variant display (values only)
        Returns: "X, Y, Z" or empty string
        """
        parts = []
        if self.pattern_name:
            parts.append(self.pattern_name)
        if self.color_name:
            parts.append(self.color_name)
        if self.size_name:
            parts.append(self.size_name)
        return ", ".join(parts)
