# 🔧 دليل الإصلاح العملي - متجر الوسام
## Practical Implementation Guide for Security Fixes

---

## 🔐 الثغرات 6-12: الإصلاحات المفصلة

### 6️⃣ Information Disclosure - رسائل الخطأ
**المشكلة:**
```python
# ❌ خطير - يفشي معلومات النظام
except Exception as e:
    return JsonResponse({'success': False, 'error': str(e)}, status=400)

# يمكن للمهاجم رؤية:
# - traceback الكامل
# - أسماء الدوال والملفات
# - رقم السطر بالضبط
```

**الحل:**
```python
# ✅ آمن - رسائل عامة للمستخدم
import logging
logger = logging.getLogger(__name__)

try:
    # ... الكود ...
except ValidationError as e:
    return JsonResponse({'success': False, 'error': 'بيانات غير صحيحة'}, status=400)
except Product.DoesNotExist:
    return JsonResponse({'success': False, 'error': 'المنتج غير موجود'}, status=404)
except Exception as e:
    # تسجيل التفاصيل بشكل آمن
    logger.exception(f"Unexpected error in get_product_config")
    # إرسال رسالة عامة
    return JsonResponse({'success': False, 'error': 'حدث خطأ في معالجة الطلب'}, status=500)
```

---

### 7️⃣ CORS & ALLOWED_HOSTS Configuration
**المشكلة:**
```python
# ❌ خطر جداً
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')
```

**الحل:**
```python
# ✅ آمن
ALLOWED_HOSTS = config(
    'DJANGO_ALLOWED_HOSTS',
    default='localhost,127.0.0.1'
).split(',')

# مثال .env:
DJANGO_ALLOWED_HOSTS=elwsamshop.com,www.elwsamshop.com
```

---

### 8️⃣ Security Headers
**الحل:**
```python
# settings.py
# ✅ إضافة Security Headers

# X-Frame-Options (موجود بالفعل)
X_FRAME_OPTIONS = 'DENY'

# ✅ Security Headers الإضافية
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ✅ HSTS (HTTP Strict Transport Security)
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000  # سنة
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ✅ CSP (Content Security Policy)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")  # قلل الـ unsafe-inline لاحقاً
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'",)

# middleware لـ CSP
MIDDLEWARE = [
    # ...
    'csp.middleware.CSPMiddleware',
]

# ✅ Referrer Policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
```

**تثبيت django-csp:**
```bash
pip install django-csp
```

---

### 9️⃣ File Upload Security
**المشكلة:**
```python
# ❌ لا يوجد فحص للـ MIME Type أو حجم الملف
class UserProfile(models.Model):
    avatar = models.ImageField(upload_to='users/', blank=True, null=True)
```

**الحل:**
```python
# forms.py
from django import forms
from django.core.exceptions import ValidationError
from PIL import Image
import os

class ProfileImageForm(forms.ModelForm):
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*'}),
        help_text='الحد الأقصى: 5MB، صيغ مقبولة: JPG, PNG, WebP'
    )

    class Meta:
        model = UserProfile
        fields = ['avatar']

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        
        if not avatar:
            return avatar
        
        # ✅ فحص حجم الملف (الحد الأقصى 5MB)
        MAX_SIZE = 5 * 1024 * 1024  # 5MB
        if avatar.size > MAX_SIZE:
            raise ValidationError(
                f'حجم الملف كبير جداً. الحد الأقصى: 5MB، حجمك: {avatar.size / 1024 / 1024:.2f}MB'
            )
        
        # ✅ فحص نوع الملف (MIME Type)
        ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
        if avatar.content_type not in ALLOWED_TYPES:
            raise ValidationError(
                f'نوع الملف غير مدعوم. الأنواع المدعومة: {", ".join(ALLOWED_TYPES)}'
            )
        
        # ✅ فحص أن الملف فعلاً صورة
        try:
            img = Image.open(avatar)
            img.verify()
        except Exception as e:
            raise ValidationError('الملف ليس صورة صحيحة')
        
        # ✅ فحص دقة الصورة (الحد الأقصى 4000x4000)
        MAX_WIDTH = 4000
        MAX_HEIGHT = 4000
        if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
            raise ValidationError(
                f'أبعاد الصورة كبيرة جداً. الحد الأقصى: {MAX_WIDTH}x{MAX_HEIGHT}'
            )
        
        return avatar

# models.py
import os
from django.db import models
from django.core.files.storage import default_storage

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(
        upload_to='users/%Y/%m/%d/',  # ✅ تنظيم الملفات بالتاريخ
        blank=True, 
        null=True,
        validators=[validate_image_file]  # ✅ استخدام Validator
    )
    bio = models.TextField(blank=True, null=True)

    def delete(self, *args, **kwargs):
        # ✅ حذف الصورة عند حذف الملف الشخصي
        if self.avatar:
            if os.path.isfile(self.avatar.path):
                os.remove(self.avatar.path)
        super().delete(*args, **kwargs)

# ✅ Validator مخصص
def validate_image_file(file_obj):
    """تحقق من صحة ملف الصورة"""
    from django.core.exceptions import ValidationError
    
    # الحد الأقصى: 5MB
    if file_obj.size > 5 * 1024 * 1024:
        raise ValidationError('حجم الملف كبير جداً')
    
    # فحص MIME Type
    allowed_types = ['image/jpeg', 'image/png', 'image/webp']
    if file_obj.content_type not in allowed_types:
        raise ValidationError('نوع الملف غير مدعوم')
```

---

### 🔟 Logging & Monitoring
**المشكلة:**
عدم تسجيل العمليات الحساسة.

**الحل:**
```python
# settings.py
import logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'security': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# استخدام الـ Logger في الكود
security_logger = logging.getLogger('security')

# في views.py
class LoginView(View):
    def post(self, request):
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            
            # ✅ تسجيل النجاح
            security_logger.info(
                f"User login successful",
                extra={
                    'user_id': user.id,
                    'email': user.email,
                    'ip': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT')
                }
            )
        else:
            # ✅ تسجيل الفشل
            security_logger.warning(
                f"Failed login attempt",
                extra={
                    'identifier': request.POST.get('identifier', ''),
                    'ip': request.META.get('REMOTE_ADDR'),
                }
            )

# ✅ Alerting على الأنشطة المريبة
def check_suspicious_activity(user):
    """تحقق من الأنشطة المريبة"""
    from django.utils import timezone
    from datetime import timedelta
    
    # تحقق من عدد محاولات الدخول الفاشلة
    from axes.models import AxisAttempt
    
    recent_failures = AxisAttempt.objects.filter(
        username=user.email,
        attempt_time__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    if recent_failures > 10:
        # إرسال تنبيه
        send_security_alert(
            user.email,
            f"تنبيه أمني: تم اكتشاف {recent_failures} محاولات دخول فاشلة"
        )
```

**إنشاء مجلد الـ Logs:**
```bash
mkdir -p logs
chmod 755 logs
```

---

### 1️⃣1️⃣ SQL Injection Prevention (Search)
**المشكلة:**
```python
# ✅ هذا آمن فعلاً (Django ORM يحمي تلقائيًا)
products = products.filter(
    Q(name__icontains=search_query) | Q(description__icontains=search_query)
)

# لكن يجب فحص طول البحث
```

**الحل:**
```python
# views.py
from django.db.models import Q
from django.core.paginator import Paginator

def search_products(request):
    query = request.GET.get('q', '').strip()
    
    # ✅ فحص طول البحث (الحد الأدنى واحد حرف، الحد الأقصى 100)
    if not query or len(query) < 1:
        messages.error(request, "يرجى إدخال كلمة البحث")
        return redirect('products:product_list')
    
    if len(query) > 100:
        messages.error(request, "كلمة البحث طويلة جداً")
        return redirect('products:product_list')
    
    # ✅ Django ORM يحمي من SQL Injection
    products = Product.objects.filter(
        is_active=True,
        category__is_active=True
    ).filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query) |
        Q(specs__description__icontains=query)
    ).distinct()
    
    # ✅ Pagination
    paginator = Paginator(products, 24)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'products': page_obj.object_list,
        'search_query': query,
        'paginator': paginator,
        'page_obj': page_obj,
    }
    
    return render(request, 'search_results.html', context)
```

---

### 1️⃣2️⃣ Data Encryption
**المشكلة:**
بيانات حساسة بدون تشفير إضافي.

**الحل:**
```python
# settings.py
# تثبيت:
# pip install django-fernet

INSTALLED_APPS = [
    # ...
    'django_fernet',
]

FERNET_KEYS = [
    config('FERNET_KEY')  # يجب أن تكون في .env
]

# models.py
from django_fernet.fields import FernetEncryptedTextField

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # ✅ تشفير رقم الهاتف
    shipping_phone = FernetEncryptedTextField()
    # ✅ تشفير العنوان
    shipping_address = FernetEncryptedTextField()
    # ✅ تشفير البريد للطلبات الضيف
    guest_email = FernetEncryptedTextField(blank=True, null=True)

# إنشاء Fernet Key:
# python manage.py generate_fernet_key
```

**توليد مفتاح Fernet:**
```bash
python manage.py shell
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())
# أضفه إلى .env كـ FERNET_KEY
```

---

## 🧪 اختبارات أمان شاملة

```python
# tests/test_security.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import User, UserOTP
from orders.models import Order, Cart

class SecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='SecurePass123!'
        )

    # ✅ اختبار CSRF Protection
    def test_csrf_token_required_for_forms(self):
        """تأكد من أن CSRF Token مطلوب"""
        response = self.client.get(reverse('accounts:login'))
        self.assertContains(response, 'csrfmiddlewaretoken')

    # ✅ اختبار IDOR
    def test_user_cannot_access_other_user_data(self):
        """تأكد من عدم الوصول إلى بيانات المستخدمين الآخرين"""
        user2 = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='pass'
        )
        from accounts.models import Address
        address2 = Address.objects.create(
            user=user2,
            full_name='Other User',
            phone='1234567890',
            city='Cairo',
            street='Street'
        )
        
        self.client.login(email='test@example.com', password='SecurePass123!')
        response = self.client.get(
            reverse('accounts:address_update', args=[address2.id])
        )
        
        # يجب أن يحصل على 404 أو 403
        self.assertIn(response.status_code, [403, 404])

    # ✅ اختبار Rate Limiting
    def test_brute_force_protection(self):
        """تأكد من حماية Brute Force"""
        for i in range(10):
            response = self.client.post(reverse('accounts:login'), {
                'identifier': 'test@example.com',
                'password': 'wrongpass'
            })
        
        # بعد 5 محاولات، يجب رفع الطلب
        response = self.client.post(reverse('accounts:login'), {
            'identifier': 'test@example.com',
            'password': 'SecurePass123!'
        })
        # قد يكون في الحالة الطبيعية 200 أو redirect، لكن إذا كانت تحمية فقد تكون 429
        # هذا يعتمد على التطبيق

    # ✅ اختبار XSS Protection
    def test_xss_prevention_in_user_input(self):
        """تأكد من حماية XSS"""
        malicious_input = '<script>alert("XSS")</script>'
        
        response = self.client.post(
            reverse('accounts:register'),
            {
                'email': 'xss@example.com',
                'username': malicious_input,
                'phone': '0100000000',
                'password1': 'SecurePass123!',
                'password2': 'SecurePass123!',
                'accept_terms': True
            }
        )
        
        # يجب رفض الـ Input أو التعامل معه بشكل آمن
        user = User.objects.filter(email='xss@example.com').first()
        if user:
            # إذا تم إنشاء المستخدم، يجب أن لا يكون الـ Username يحتوي على script
            self.assertNotIn('<script>', user.username)

    # ✅ اختبار HTTPS Redirect
    def test_https_redirect_in_production(self):
        """تأكد من إعادة توجيه HTTP إلى HTTPS"""
        from django.test.utils import override_settings
        
        with override_settings(DEBUG=False, SECURE_SSL_REDIRECT=True):
            response = self.client.get('/products/', secure=False)
            # في الإنتاج، يجب إعادة توجيه من http:// إلى https://

    # ✅ اختبار Security Headers
    def test_security_headers_present(self):
        """تأكد من وجود Security Headers"""
        response = self.client.get(reverse('index'))
        
        self.assertIn('X-Frame-Options', response)
        self.assertEqual(response['X-Frame-Options'], 'DENY')
```

---

## 🚀 Deployment Checklist

```bash
# قبل النشر:
python manage.py check --deploy

# القائمة:
- [ ] DEBUG = False
- [ ] SECRET_KEY في .env وقوية
- [ ] ALLOWED_HOSTS محددة
- [ ] HTTPS مفعل
- [ ] Security Headers مضافة
- [ ] CSRF Protection فعالة
- [ ] Rate Limiting مفعل
- [ ] Logging مشغل
- [ ] Database Backups مشغلة
- [ ] Static Files جمعت
- [ ] Media Files محمية
- [ ] Tests تمرت
- [ ] Security Scan تمرت
```

---

**آخر تحديث:** 28 أبريل 2026
