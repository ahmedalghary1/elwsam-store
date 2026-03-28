from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import User, UserProfile, Address, UserOTP


# ================================================
# Inline: UserProfile
# ================================================
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0
    verbose_name = 'الملف الشخصي'
    verbose_name_plural = 'الملف الشخصي'
    fields = ('avatar', 'bio')


# ================================================
# Inline: Address
# ================================================
class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ('full_name', 'phone', 'city', 'street', 'is_default', 'order')
    show_change_link = True
    verbose_name = 'عنوان'
    verbose_name_plural = 'العناوين'


# ================================================
# User Admin
# ================================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = ('avatar_display', 'email', 'username', 'phone', 'account_type', 'is_active_badge', 'date_joined')
    list_display_links = ('email',)
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'username', 'phone')
    ordering = ('-date_joined',)
    list_per_page = 25
    date_hierarchy = 'date_joined'

    fieldsets = (
        ('🔐 بيانات الدخول', {
            'fields': ('email', 'password')
        }),
        ('👤 المعلومات الشخصية', {
            'fields': ('username', 'first_name', 'last_name', 'phone')
        }),
        ('🛡️ الصلاحيات', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('📅 التواريخ', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        ('➕ إنشاء حساب جديد', {
            'classes': ('wide',),
            'fields': ('email', 'username', 'phone', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    inlines = [UserProfileInline, AddressInline]
    readonly_fields = ('last_login', 'date_joined')

    def avatar_display(self, obj):
        try:
            if obj.profile and obj.profile.avatar:
                return format_html('<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;border:2px solid #ddd;" />', obj.profile.avatar.url)
        except Exception:
            pass
        initials = (obj.email[0] if obj.email else '?').upper()
        return format_html(
            '<div style="width:36px;height:36px;border-radius:50%;background:#4CAF50;color:white;'
            'display:flex;align-items:center;justify-content:center;font-weight:bold;">{}</div>',
            initials
        )
    avatar_display.short_description = ''

    def account_type(self, obj):
        if obj.is_superuser:
            return format_html('<span style="background:#6f42c1;color:white;padding:2px 8px;border-radius:12px;font-size:0.8em;">مشرف عام</span>')
        elif obj.is_staff:
            return format_html('<span style="background:#fd7e14;color:white;padding:2px 8px;border-radius:12px;font-size:0.8em;">موظف</span>')
        return format_html('<span style="background:#17a2b8;color:white;padding:2px 8px;border-radius:12px;font-size:0.8em;">عميل</span>')
    account_type.short_description = 'نوع الحساب'

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#28a745;font-weight:bold;">✓ مفعّل</span>')
        return format_html('<span style="color:#dc3545;font-weight:bold;">✗ موقوف</span>')
    is_active_badge.short_description = 'الحالة'
    is_active_badge.admin_order_field = 'is_active'


# ================================================
# UserProfile Admin
# ================================================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('avatar_display', 'user', 'bio_short')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('avatar_preview',)

    fieldsets = (
        ('👤 الملف الشخصي', {
            'fields': ('user', 'avatar', 'avatar_preview', 'bio')
        }),
    )

    def avatar_display(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;" />', obj.avatar.url)
        return '—'
    avatar_display.short_description = 'الصورة'

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="max-width:150px;border-radius:8px;" />', obj.avatar.url)
        return 'لا توجد صورة'
    avatar_preview.short_description = 'معاينة الصورة'

    def bio_short(self, obj):
        if obj.bio:
            return obj.bio[:60] + '...' if len(obj.bio) > 60 else obj.bio
        return '—'
    bio_short.short_description = 'النبذة'


# ================================================
# Address Admin
# ================================================
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'street_short', 'phone', 'is_default_badge', 'order')
    list_display_links = ('full_name',)
    list_editable = ('order',)
    list_filter = ('city', 'is_default', 'country')
    search_fields = ('user__email', 'full_name', 'city', 'street', 'phone')
    ordering = ('user', 'order')

    fieldsets = (
        ('👤 معلومات المستلم', {
            'fields': ('user', 'full_name', 'phone')
        }),
        ('📍 العنوان', {
            'fields': ('country', 'city', 'street', 'postal_code')
        }),
        ('⚙️ الإعدادات', {
            'fields': ('is_default', 'order')
        }),
    )

    def street_short(self, obj):
        return obj.street[:40] + '...' if len(obj.street) > 40 else obj.street
    street_short.short_description = 'الشارع'

    def is_default_badge(self, obj):
        if obj.is_default:
            return format_html('<span style="color:#28a745;font-weight:bold;">★ افتراضي</span>')
        return '—'
    is_default_badge.short_description = 'الافتراضي'

    def save_model(self, request, obj, form, change):
        if obj.is_default:
            Address.objects.filter(user=obj.user, is_default=True).exclude(pk=obj.pk).update(is_default=False)
        super().save_model(request, obj, form, change)


# ================================================
# UserOTP Admin
# ================================================
@admin.register(UserOTP)
class UserOTPAdmin(admin.ModelAdmin):
    list_display = ('email_display', 'code', 'purpose_badge', 'status_badge', 'created_at', 'expires_at')
    list_filter = ('is_used', 'purpose', 'created_at')
    search_fields = ('user__email', 'email', 'code')
    readonly_fields = ('created_at', 'expires_at', 'code', 'email', 'user', 'purpose')
    ordering = ('-created_at',)
    list_per_page = 30
    date_hierarchy = 'created_at'

    fieldsets = (
        ('📧 معلومات الرمز', {
            'fields': ('user', 'email', 'code', 'purpose')
        }),
        ('⏱️ الصلاحية', {
            'fields': ('created_at', 'expires_at', 'is_used')
        }),
    )

    def email_display(self, obj):
        return obj.email or (obj.user.email if obj.user else '—')
    email_display.short_description = 'البريد الإلكتروني'

    def purpose_badge(self, obj):
        if obj.purpose == 'email_verification':
            return format_html('<span style="background:#17a2b8;color:white;padding:2px 8px;border-radius:12px;font-size:0.8em;">تحقق من البريد</span>')
        return format_html('<span style="background:#fd7e14;color:white;padding:2px 8px;border-radius:12px;font-size:0.8em;">إعادة كلمة المرور</span>')
    purpose_badge.short_description = 'الغرض'

    def status_badge(self, obj):
        if obj.is_used:
            return format_html('<span style="color:#6c757d;">✓ مستخدم</span>')
        if obj.expires_at and timezone.now() > obj.expires_at:
            return format_html('<span style="color:#dc3545;">✗ منتهي</span>')
        return format_html('<span style="color:#28a745;font-weight:bold;">● نشط</span>')
    status_badge.short_description = 'الحالة'