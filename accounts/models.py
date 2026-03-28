from django.contrib.auth.models import AbstractUser
from django.db import models

# =========================
# 1️⃣ Custom User Model
# =========================
class User(AbstractUser):
    """
    نموذج المستخدم المخصص.
    يدعم:
    - تسجيل الدخول بواسطة البريد الإلكتروني
    - إضافة رقم الهاتف بسهولة
    - قابل للتوسع لاحقًا لأي حقل إضافي
    """
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    # اجعل البريد هو الحقل الأساسي لتسجيل الدخول
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


# =========================
# 2️⃣ User Profile (اختياري)
# =========================
class UserProfile(models.Model):
    """
    بيانات إضافية لكل مستخدم.
    يمكن استخدامه للصور، العناوين الافتراضية، أو أي معلومات إضافية.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to='users/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)  # نبذة عن المستخدم

    def __str__(self):
        return f"Profile of {self.user.email}"


# =========================
# 3️⃣ Address Model
# =========================
class Address(models.Model):
    """
    نموذج العناوين المتعددة لكل مستخدم.
    يمكن تعيين عنوان افتراضي لكل مستخدم.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    
    # بيانات العنوان الأساسية
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20, blank=True, null=True)

    # تعيين العنوان الافتراضي
    is_default = models.BooleanField(default=False)

    order = models.PositiveIntegerField(default=0)  # ترتيب العناوين في لوحة التحكم

    class Meta:
        ordering = ['order']
        verbose_name = 'عنوان'
        verbose_name_plural = 'العناوين'

    def __str__(self):
        return f"{self.user.email} - {self.city}, {self.street}"


# =========================
# 4️⃣ Wishlist Model (اختياري)
# =========================
# class Wishlist(models.Model):
#     """
#     قائمة الرغبات لكل مستخدم.
#     """
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
#     product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
#     added_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('user', 'product')  # لا يمكن إضافة نفس المنتج مرتين
#         verbose_name = 'قائمة الرغبات'
#         verbose_name_plural = 'قوائم الرغبات'

#     def __str__(self):
#         return f"{self.user.email} → {self.product.name}"


# =========================
# 5️⃣ User OTP / Verification
# =========================
class UserOTP(models.Model):
    """
    لتخزين رموز التحقق المؤقتة (Email) لكل مستخدم
    """
    PURPOSE_CHOICES = [
        ('email_verification', 'التحقق من البريد الإلكتروني'),
        ('password_reset', 'إعادة تعيين كلمة المرور'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps", null=True, blank=True)
    email = models.EmailField(blank=True,null=True) 
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='email_verification')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True,null=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'رمز تحقق OTP'
        verbose_name_plural = 'رموز التحقق'

    def __str__(self):
        return f"OTP for {self.email}: {self.code} ({self.purpose})"
    
    def is_valid(self):
        """التحقق من صلاحية OTP"""
        from django.utils import timezone
        return not self.is_used and timezone.now() < self.expires_at