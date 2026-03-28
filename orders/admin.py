from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Cart, CartItem, Order, OrderItem


# ================================================
# Inline: OrderItem
# ================================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'variant', 'quantity', 'price', 'item_total')
    fields = ('product', 'variant', 'quantity', 'price', 'item_total')
    can_delete = False
    verbose_name = 'منتج'
    verbose_name_plural = 'المنتجات في الطلب'

    def item_total(self, obj):
        total = obj.get_total_price()
        return format_html('<strong>{} ج.م</strong>', total)
    item_total.short_description = 'الإجمالي'

    def has_add_permission(self, request, obj=None):
        return False


# ================================================
# Inline: CartItem
# ================================================
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'variant', 'quantity', 'item_total', 'added_at')
    fields = ('product', 'variant', 'quantity', 'item_total', 'added_at')
    can_delete = True
    verbose_name = 'منتج في السلة'
    verbose_name_plural = 'منتجات السلة'

    def item_total(self, obj):
        total = obj.get_total_price()
        return format_html('<strong>{} ج.م</strong>', total)
    item_total.short_description = 'الإجمالي'


# ================================================
# Order Admin
# ================================================

STATUS_COLORS = {
    'pending':    ('#ffc107', '#000', 'في انتظار الدفع'),
    'paid':       ('#28a745', '#fff', 'مدفوع'),
    'processing': ('#17a2b8', '#fff', 'قيد المعالجة'),
    'shipped':    ('#007bff', '#fff', 'تم الشحن'),
    'delivered':  ('#6f42c1', '#fff', 'تم التسليم'),
    'cancelled':  ('#dc3545', '#fff', 'ملغي'),
}

PAYMENT_LABELS = {
    'cash_on_delivery': '💵 الدفع عند الاستلام',
    'credit_card':      '💳 بطاقة ائتمان',
    'bank_transfer':    '🏦 تحويل بنكي',
}


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_id', 'customer_display', 'status_badge',
        'payment_display', 'total_display', 'items_count',
        'shipping_city', 'created_at'
    ]
    list_display_links = ['order_id']
    list_filter = ['status', 'payment_method', 'created_at', 'shipping_city']
    search_fields = [
        'id', 'user__email', 'shipping_name', 'shipping_phone',
        'shipping_address', 'guest_email'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'created_at', 'updated_at', 'order_summary_display',
        'customer_info_display'
    ]
    date_hierarchy = 'created_at'
    list_per_page = 20
    inlines = [OrderItemInline]

    fieldsets = (
        ('📋 معلومات الطلب', {
            'fields': ('order_summary_display', 'status', 'payment_method')
        }),
        ('👤 بيانات العميل', {
            'fields': ('user', 'guest_email', 'customer_info_display')
        }),
        ('🚚 معلومات الشحن', {
            'fields': (
                'shipping_name', 'shipping_phone',
                'shipping_city', 'shipping_address', 'shipping_notes'
            )
        }),
        ('💰 المالية', {
            'fields': ('total_price',)
        }),
        ('📅 التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'mark_as_paid', 'mark_as_processing',
        'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled'
    ]

    def order_id(self, obj):
        return format_html('<strong style="font-size:1em;">#️⃣ {}</strong>', obj.id)
    order_id.short_description = 'رقم الطلب'
    order_id.admin_order_field = 'id'

    def customer_display(self, obj):
        if obj.user:
            return format_html(
                '<div><strong>{}</strong><br>'
                '<small style="color:#6c757d;">{}</small></div>',
                obj.shipping_name or obj.user.get_full_name() or obj.user.username,
                obj.user.email
            )
        return format_html(
            '<div><strong>{}</strong><br>'
            '<small style="color:#fd7e14;">👤 ضيف — {}</small></div>',
            obj.shipping_name or '—',
            obj.guest_email or '—'
        )
    customer_display.short_description = 'العميل'

    def status_badge(self, obj):
        bg, fg, label = STATUS_COLORS.get(obj.status, ('#6c757d', '#fff', obj.status))
        return format_html(
            '<span style="background:{};color:{};padding:4px 12px;border-radius:20px;'
            'font-size:0.82em;font-weight:bold;white-space:nowrap;">{}</span>',
            bg, fg, label
        )
    status_badge.short_description = 'الحالة'
    status_badge.admin_order_field = 'status'

    def payment_display(self, obj):
        label = PAYMENT_LABELS.get(obj.payment_method, obj.payment_method)
        return format_html('<span style="font-size:0.9em;">{}</span>', label)
    payment_display.short_description = 'طريقة الدفع'

    def total_display(self, obj):
        return format_html('<strong style="color:#28a745;font-size:1em;">{} ج.م</strong>', obj.total_price)
    total_display.short_description = 'الإجمالي'
    total_display.admin_order_field = 'total_price'

    def items_count(self, obj):
        count = obj.get_total_items()
        return format_html('<span style="background:#e9ecef;padding:2px 8px;border-radius:10px;">{} قطعة</span>', count)
    items_count.short_description = 'العناصر'

    def order_summary_display(self, obj):
        bg, fg, label = STATUS_COLORS.get(obj.status, ('#6c757d', '#fff', obj.status))
        return format_html(
            '<div style="background:#f8f9fa;border-radius:8px;padding:12px;border-right:4px solid {};">'
            '<strong>طلب #{}</strong> — '
            '<span style="background:{};color:{};padding:2px 10px;border-radius:12px;">{}</span>'
            '<br><small style="color:#6c757d;">تاريخ الطلب: {}</small>'
            '</div>',
            bg, obj.id, bg, fg, label,
            obj.created_at.strftime('%Y-%m-%d %H:%M') if obj.created_at else '—'
        )
    order_summary_display.short_description = 'ملخص الطلب'

    def customer_info_display(self, obj):
        if obj.user:
            return format_html(
                '<div style="background:#e8f4f8;padding:10px;border-radius:6px;">'
                '📧 <strong>{}</strong><br>📱 {}'
                '</div>',
                obj.user.email, obj.user.phone or '—'
            )
        return format_html(
            '<div style="background:#fff3cd;padding:10px;border-radius:6px;">'
            '👤 ضيف<br>📧 {}'
            '</div>',
            obj.guest_email or '—'
        )
    customer_info_display.short_description = 'معلومات العميل'

    # Actions
    @admin.action(description='✅ تحديد كـ: مدفوع')
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid')
        self.message_user(request, f'تم تحديث {updated} طلب إلى "مدفوع".')

    @admin.action(description='⚙️ تحديد كـ: قيد المعالجة')
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'تم تحديث {updated} طلب إلى "قيد المعالجة".')

    @admin.action(description='🚚 تحديد كـ: تم الشحن')
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'تم تحديث {updated} طلب إلى "تم الشحن".')

    @admin.action(description='📦 تحديد كـ: تم التسليم')
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f'تم تحديث {updated} طلب إلى "تم التسليم".')

    @admin.action(description='❌ تحديد كـ: ملغي')
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'تم إلغاء {updated} طلب.')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items')


# ================================================
# OrderItem Admin
# ================================================
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order_link', 'product', 'variant', 'quantity', 'price', 'total_display']
    list_filter = ['product__category', 'order__status']
    search_fields = ['product__name', 'order__id', 'order__user__email']
    readonly_fields = ['order', 'product', 'variant', 'quantity', 'price']
    ordering = ['-order__created_at']

    def order_link(self, obj):
        return format_html('<strong>#{}</strong>', obj.order.id)
    order_link.short_description = 'رقم الطلب'
    order_link.admin_order_field = 'order__id'

    def total_display(self, obj):
        return format_html('<strong>{} ج.م</strong>', obj.get_total_price())
    total_display.short_description = 'الإجمالي'

    def has_add_permission(self, request):
        return False


# ================================================
# Cart Admin
# ================================================
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'items_count', 'cart_total', 'created_at', 'updated_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'cart_total']
    ordering = ['-updated_at']
    inlines = [CartItemInline]

    def items_count(self, obj):
        count = obj.get_total_items()
        return format_html('<span style="background:#e9ecef;padding:2px 8px;border-radius:10px;">{} قطعة</span>', count)
    items_count.short_description = 'عدد القطع'

    def cart_total(self, obj):
        total = obj.get_total_price()
        return format_html('<strong style="color:#28a745;">{} ج.م</strong>', total)
    cart_total.short_description = 'إجمالي السلة'


# ================================================
# CartItem Admin
# ================================================
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart_user', 'product', 'variant', 'quantity', 'item_total', 'added_at']
    list_filter = ['product__category', 'added_at']
    search_fields = ['cart__user__email', 'product__name']
    readonly_fields = ['added_at']
    ordering = ['-added_at']

    def cart_user(self, obj):
        return obj.cart.user.email
    cart_user.short_description = 'المستخدم'
    cart_user.admin_order_field = 'cart__user__email'

    def item_total(self, obj):
        return format_html('<strong>{} ج.م</strong>', obj.get_total_price())
    item_total.short_description = 'الإجمالي'