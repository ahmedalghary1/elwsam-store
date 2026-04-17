from django.conf import settings
from django.db import models
from django.db.models import Sum

from products.models import Product, ProductType, ProductVariant


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "سلة تسوق"
        verbose_name_plural = "سلات التسوق"

    def __str__(self):
        return f"سلة {self.user.email}"

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_items(self):
        return self.items.aggregate(total=Sum("quantity"))["total"] or 0

    def get_subtotal(self):
        return self.get_total_price()

    @property
    def subtotal(self):
        return self.get_subtotal()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "product", "variant", "product_type")
        verbose_name = "عنصر سلة"
        verbose_name_plural = "عناصر السلات"

    def __str__(self):
        selection_info = self.get_variant_display()
        if selection_info:
            return f"{self.quantity} x {self.product.name} ({selection_info})"
        return f"{self.quantity} x {self.product.name}"

    def get_selected_type_id(self):
        return self.product_type.type_id if self.product_type_id else None

    def get_selected_type_name(self):
        if self.product_type_id:
            return self.product_type.type.name
        return None

    def get_unit_price(self):
        if self.variant_id or self.product_type_id:
            return self.product.get_price(
                pattern_id=self.variant.pattern_id if self.variant_id else None,
                size_id=self.variant.size_id if self.variant_id else None,
                color_id=self.variant.color_id if self.variant_id else None,
                type_id=self.get_selected_type_id(),
            )
        return self.product.price

    def get_total_price(self):
        return self.get_unit_price() * self.quantity

    def get_variant_display(self):
        parts = []
        if self.product_type_id:
            parts.append(f"النوع: {self.product_type.type.name}")
        if self.variant and self.variant.pattern:
            parts.append(f"النمط: {self.variant.pattern.name}")
        if self.variant and self.variant.color:
            parts.append(f"اللون: {self.variant.color.name}")
        if self.variant and self.variant.size:
            parts.append(f"المقاس: {self.variant.size.name}")
        return " | ".join(parts)

    def get_variant_display_short(self):
        parts = []
        if self.product_type_id:
            parts.append(self.product_type.type.name)
        if self.variant and self.variant.pattern:
            parts.append(self.variant.pattern.name)
        if self.variant and self.variant.color:
            parts.append(self.variant.color.name)
        if self.variant and self.variant.size:
            parts.append(self.variant.size.name)
        return ", ".join(parts)

    def get_variant_details_dict(self):
        if not self.variant and not self.product_type_id:
            return {}

        details = {}
        if self.product_type_id:
            details["type"] = {
                "id": self.product_type.id,
                "name": self.product_type.type.name,
            }
        if self.variant and self.variant.pattern:
            details["pattern"] = {
                "id": self.variant.pattern.id,
                "name": self.variant.pattern.name,
            }
        if self.variant and self.variant.color:
            details["color"] = {
                "id": self.variant.color.id,
                "name": self.variant.color.name,
                "code": self.variant.color.code,
            }
        if self.variant and self.variant.size:
            details["size"] = {
                "id": self.variant.size.id,
                "name": self.variant.size.name,
            }
        return details


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "في انتظار الدفع"),
        ("paid", "مدفوع"),
        ("processing", "قيد المعالجة"),
        ("shipped", "تم الشحن"),
        ("delivered", "تم التسليم"),
        ("cancelled", "ملغي"),
    ]

    CONTACT_METHOD_CHOICES = [
        ("whatsapp", "واتساب"),
        ("call", "مكالمة هاتفية"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    shipping_address = models.TextField()
    shipping_phone = models.CharField(max_length=20)
    shipping_name = models.CharField(max_length=255, default="", blank=True)
    shipping_city = models.CharField(max_length=100, default="", blank=True)
    shipping_notes = models.TextField(blank=True, null=True)

    payment_method = models.CharField(max_length=50, default="cash_on_delivery")
    contact_method = models.CharField(
        max_length=20,
        choices=CONTACT_METHOD_CHOICES,
        default="whatsapp",
        verbose_name="طريقة التواصل المفضلة",
    )
    order_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات الطلب",
        help_text="أي ملاحظات إضافية للطلب",
    )

    guest_email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"
        ordering = ["-created_at"]

    def __str__(self):
        if self.user:
            return f"طلب #{self.id} - {self.user.email}"
        return f"طلب #{self.id} - ضيف ({self.shipping_name})"

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())

    def get_subtotal(self):
        return sum(item.price * item.quantity for item in self.items.all())

    @property
    def is_guest_order(self):
        return self.user is None


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    type_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="النوع")
    pattern_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="النمط")
    color_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="اللون")
    color_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="كود اللون")
    size_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="المقاس")

    class Meta:
        verbose_name = "عنصر طلب"
        verbose_name_plural = "عناصر الطلبات"

    def __str__(self):
        selection_info = self.get_variant_display()
        if selection_info:
            return f"{self.quantity} x {self.product.name} ({selection_info})"
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        return self.price * self.quantity

    def get_variant_display(self):
        parts = []
        if self.type_name:
            parts.append(f"النوع: {self.type_name}")
        if self.pattern_name:
            parts.append(f"النمط: {self.pattern_name}")
        if self.color_name:
            parts.append(f"اللون: {self.color_name}")
        if self.size_name:
            parts.append(f"المقاس: {self.size_name}")
        return " | ".join(parts)

    def get_variant_display_short(self):
        parts = []
        if self.type_name:
            parts.append(self.type_name)
        if self.pattern_name:
            parts.append(self.pattern_name)
        if self.color_name:
            parts.append(self.color_name)
        if self.size_name:
            parts.append(self.size_name)
        return ", ".join(parts)
