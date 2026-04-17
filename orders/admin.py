from django.contrib import admin
from django.utils.html import format_html

from .models import Cart, CartItem, Order, OrderItem


STATUS_COLORS = {
    "pending": ("#ffc107", "#000", "في انتظار الدفع"),
    "paid": ("#28a745", "#fff", "مدفوع"),
    "processing": ("#17a2b8", "#fff", "قيد المعالجة"),
    "shipped": ("#007bff", "#fff", "تم الشحن"),
    "delivered": ("#6f42c1", "#fff", "تم التسليم"),
    "cancelled": ("#dc3545", "#fff", "ملغي"),
}

PAYMENT_LABELS = {
    "cash_on_delivery": "الدفع عند الاستلام",
    "credit_card": "بطاقة ائتمان",
    "bank_transfer": "تحويل بنكي",
    "card": "بطاقة ائتمان",
}


def _selection_badges(obj, compact=False):
    parts = []
    gap_style = "font-size:0.85em;" if compact else "margin:2px;"

    if getattr(obj, "type_name", None):
        parts.append(
            format_html(
                '<span style="background:#ede9fe;padding:2px 6px;border-radius:3px;{}">🏷️ {}</span>',
                gap_style,
                obj.type_name,
            )
        )
    if getattr(obj, "pattern_name", None):
        parts.append(
            format_html(
                '<span style="background:#e3f2fd;padding:2px 6px;border-radius:3px;{}">📐 {}</span>',
                gap_style,
                obj.pattern_name,
            )
        )
    if getattr(obj, "color_name", None):
        color_style = f"background:{obj.color_code};color:white;" if getattr(obj, "color_code", None) else "background:#f5f5f5;"
        parts.append(
            format_html(
                '<span style="{}padding:2px 6px;border-radius:3px;{}border:1px solid #ddd;">🎨 {}</span>',
                color_style,
                gap_style,
                obj.color_name,
            )
        )
    if getattr(obj, "size_name", None):
        parts.append(
            format_html(
                '<span style="background:#fff3e0;padding:2px 6px;border-radius:3px;{}">📏 {}</span>',
                gap_style,
                obj.size_name,
            )
        )
    return parts


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "variant_details_display", "quantity", "price", "item_total")
    fields = ("product", "variant_details_display", "quantity", "price", "item_total")
    can_delete = False
    verbose_name = "منتج"
    verbose_name_plural = "المنتجات في الطلب"

    def variant_details_display(self, obj):
        parts = _selection_badges(obj, compact=False)
        if parts:
            return format_html('<div style="display:flex;flex-wrap:wrap;gap:4px;">{}</div>', format_html("".join(str(p) for p in parts)))
        return obj.get_variant_display() or "—"

    variant_details_display.short_description = "التفاصيل"

    def item_total(self, obj):
        return format_html("<strong>{} ج.م</strong>", obj.get_total_price())

    item_total.short_description = "الإجمالي"

    def has_add_permission(self, request, obj=None):
        return False


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("product", "selection_display", "quantity", "item_total", "added_at")
    fields = ("product", "selection_display", "quantity", "item_total", "added_at")
    can_delete = True
    verbose_name = "منتج في السلة"
    verbose_name_plural = "منتجات السلة"

    def selection_display(self, obj):
        return obj.get_variant_display() or "—"

    selection_display.short_description = "الاختيار"

    def item_total(self, obj):
        return format_html("<strong>{} ج.م</strong>", obj.get_total_price())

    item_total.short_description = "الإجمالي"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_id",
        "customer_display",
        "status_badge",
        "payment_display",
        "total_display",
        "items_count",
        "shipping_city",
        "contact_method",
        "created_at",
    ]
    list_display_links = ["order_id"]
    list_filter = ["status", "payment_method", "contact_method", "created_at", "shipping_city"]
    search_fields = ["id", "user__email", "shipping_name", "shipping_phone", "shipping_address", "guest_email", "order_notes"]
    readonly_fields = ["created_at", "updated_at", "total_price"]
    ordering = ["-created_at"]
    inlines = [OrderItemInline]

    fieldsets = (
        ("معلومات الطلب", {"fields": ("status", "payment_method", "contact_method", "total_price")}),
        ("بيانات العميل", {"fields": ("user", "guest_email", "shipping_name", "shipping_phone")}),
        ("الشحن", {"fields": ("shipping_city", "shipping_address", "shipping_notes")}),
        ("ملاحظات", {"fields": ("order_notes",), "classes": ("collapse",)}),
        ("التواريخ", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    actions = ["mark_as_paid", "mark_as_processing", "mark_as_shipped", "mark_as_delivered", "mark_as_cancelled"]

    def order_id(self, obj):
        return format_html("<strong>#{}</strong>", obj.id)

    order_id.short_description = "رقم الطلب"
    order_id.admin_order_field = "id"

    def customer_display(self, obj):
        if obj.user:
            return format_html(
                "<div><strong>{}</strong><br><small style=\"color:#6c757d;\">{}</small></div>",
                obj.shipping_name or obj.user.get_full_name() or getattr(obj.user, "username", "—"),
                obj.user.email,
            )
        return format_html(
            "<div><strong>{}</strong><br><small style=\"color:#fd7e14;\">ضيف — {}</small></div>",
            obj.shipping_name or "—",
            obj.guest_email or "—",
        )

    customer_display.short_description = "العميل"

    def status_badge(self, obj):
        bg, fg, label = STATUS_COLORS.get(obj.status, ("#6c757d", "#fff", obj.status))
        return format_html(
            '<span style="background:{};color:{};padding:4px 12px;border-radius:20px;font-size:0.82em;font-weight:bold;">{}</span>',
            bg,
            fg,
            label,
        )

    status_badge.short_description = "الحالة"
    status_badge.admin_order_field = "status"

    def payment_display(self, obj):
        return PAYMENT_LABELS.get(obj.payment_method, obj.payment_method)

    payment_display.short_description = "الدفع"

    def total_display(self, obj):
        return format_html("<strong style=\"color:#28a745;\">{} ج.م</strong>", obj.total_price)

    total_display.short_description = "الإجمالي"
    total_display.admin_order_field = "total_price"

    def items_count(self, obj):
        return obj.get_total_items()

    items_count.short_description = "العناصر"

    @admin.action(description="تحديد كمدفوع")
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status="paid")
        self.message_user(request, f"تم تحديث {updated} طلب إلى مدفوع.")

    @admin.action(description="تحديد كقيد المعالجة")
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status="processing")
        self.message_user(request, f"تم تحديث {updated} طلب إلى قيد المعالجة.")

    @admin.action(description="تحديد كمشحون")
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status="shipped")
        self.message_user(request, f"تم تحديث {updated} طلب إلى تم الشحن.")

    @admin.action(description="تحديد كمسلم")
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status="delivered")
        self.message_user(request, f"تم تحديث {updated} طلب إلى تم التسليم.")

    @admin.action(description="تحديد كملغي")
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status="cancelled")
        self.message_user(request, f"تم إلغاء {updated} طلب.")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["order_link", "product", "variant_details_display", "quantity", "price", "total_display"]
    list_filter = ["product__category", "order__status", "type_name", "pattern_name", "color_name", "size_name"]
    search_fields = ["product__name", "order__id", "order__user__email", "type_name", "pattern_name", "color_name", "size_name"]
    readonly_fields = ["order", "product", "variant", "product_type", "quantity", "price", "type_name", "pattern_name", "color_name", "color_code", "size_name"]
    ordering = ["-order__created_at"]

    fieldsets = (
        ("معلومات الطلب", {"fields": ("order", "product", "quantity", "price")}),
        ("تفاصيل الاختيار", {"fields": ("variant", "product_type", "type_name", "pattern_name", "color_name", "color_code", "size_name"), "classes": ("collapse",)}),
    )

    def order_link(self, obj):
        return format_html("<strong>#{}</strong>", obj.order.id)

    order_link.short_description = "رقم الطلب"
    order_link.admin_order_field = "order__id"

    def variant_details_display(self, obj):
        parts = _selection_badges(obj, compact=True)
        if parts:
            return format_html(" ".join(str(p) for p in parts))
        return obj.get_variant_display() or "—"

    variant_details_display.short_description = "الاختيار"

    def total_display(self, obj):
        return format_html("<strong>{} ج.م</strong>", obj.get_total_price())

    total_display.short_description = "الإجمالي"

    def has_add_permission(self, request):
        return False


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["user", "items_count", "cart_total", "created_at", "updated_at"]
    search_fields = ["user__email", "user__username"]
    readonly_fields = ["created_at", "updated_at", "cart_total"]
    ordering = ["-updated_at"]
    inlines = [CartItemInline]

    def items_count(self, obj):
        return obj.get_total_items()

    items_count.short_description = "عدد القطع"

    def cart_total(self, obj):
        return format_html("<strong style=\"color:#28a745;\">{} ج.م</strong>", obj.get_total_price())

    cart_total.short_description = "إجمالي السلة"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["cart_user", "product", "selection_display", "quantity", "item_total", "added_at"]
    list_filter = ["product__category", "added_at"]
    search_fields = ["cart__user__email", "product__name"]
    readonly_fields = ["product_type", "added_at"]
    ordering = ["-added_at"]

    def cart_user(self, obj):
        return obj.cart.user.email

    cart_user.short_description = "المستخدم"
    cart_user.admin_order_field = "cart__user__email"

    def selection_display(self, obj):
        return obj.get_variant_display() or "—"

    selection_display.short_description = "الاختيار"

    def item_total(self, obj):
        return format_html("<strong>{} ج.م</strong>", obj.get_total_price())

    item_total.short_description = "الإجمالي"
