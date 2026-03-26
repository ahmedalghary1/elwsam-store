from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, Address, UserOTP


# =========================
# Inline: UserProfile
# =========================
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0


# =========================
# Inline: Address
# =========================
class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ('full_name', 'phone', 'city', 'street', 'is_default')
    show_change_link = True


# =========================
# Custom User Admin
# =========================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    # عرض القائمة
    list_display = ('email', 'username', 'phone', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')

    # البحث
    search_fields = ('email', 'username', 'phone')
    ordering = ('-id',)

    # تنظيم الفورم
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('معلومات شخصية', {'fields': ('username', 'phone')}),
        ('الصلاحيات', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تواريخ مهمة', {'fields': ('last_login', 'date_joined')}),
    )

    # عند إنشاء مستخدم
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    # Inline Models
    inlines = [UserProfileInline, AddressInline]


# =========================
# UserProfile Admin (اختياري)
# =========================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio')
    search_fields = ('user__email',)


# =========================
# Address Admin
# =========================
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'street', 'is_default')
    list_filter = ('city', 'is_default')
    search_fields = ('user__email', 'city', 'street')

    def save_model(self, request, obj, form, change):
        # ضمان عنوان افتراضي واحد فقط
        if obj.is_default:
            Address.objects.filter(user=obj.user, is_default=True).exclude(pk=obj.pk).update(is_default=False)
        super().save_model(request, obj, form, change)


# =========================
# OTP Admin
# =========================
@admin.register(UserOTP)
class UserOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'is_used', 'created_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'code')
    readonly_fields = ('created_at',)