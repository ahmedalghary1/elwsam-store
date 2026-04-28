# 📊 مصفوفة الأولويات والخطة التنفيذية
## Security Issues Priority Matrix & Implementation Plan

---

## 📈 مصفوفة الأولويات (CVSS Scoring)

| ID | الثغرة | CVSS | الخطورة | الجهد | الأولوية | الحالة |
|----|--------|------|--------|------|---------|--------|
| 1 | Hardcoded Credentials | 9.8 | 🔴 Critical | منخفض | 1 | ⏳ جاهز للإصلاح |
| 2 | Weak Password Reset | 9.1 | 🔴 Critical | متوسط | 2 | ⏳ جاهز للإصلاح |
| 3 | Missing Rate Limiting | 8.9 | 🔴 Critical | منخفض | 3 | ⏳ جاهز للإصلاح |
| 4 | IDOR - Cart/Orders | 8.7 | 🔴 Critical | منخفض | 4 | ⏳ جاهز للإصلاح |
| 5 | Input Validation | 7.5 | 🟠 High | متوسط | 5 | ⏳ جاهز للإصلاح |
| 6 | File Upload | 7.2 | 🟠 High | متوسط | 6 | ⏳ جاهز للإصلاح |
| 7 | CORS Config | 6.8 | 🟠 High | منخفض | 7 | ⏳ جاهز للإصلاح |
| 8 | Security Headers | 6.5 | 🟠 High | منخفض | 8 | ⏳ جاهز للإصلاح |
| 9 | Info Disclosure | 5.3 | 🟡 Medium | منخفض | 9 | ⏳ جاهز للإصلاح |
| 10 | Logging Gaps | 5.0 | 🟡 Medium | متوسط | 10 | ⏳ جاهز للإصلاح |

---

## 🗓️ خطة التنفيذ بالمراحل

### 🚨 **المرحلة 1: الحرجة (24 ساعة)**

**الهدف:** معالجة جميع ثغرات Critical لمنع الاستغلال الفوري

#### المهام:

**1. نقل البيانات الحساسة إلى `.env`** (1 ساعة)
```bash
# الوقت المقدر: 1 ساعة
# الجهد: منخفض
# المخاطر: لا تنسَ تحديث الـ CI/CD

# الخطوات:
1. تثبيت python-decouple
   pip install python-decouple

2. إنشاء ملف .env
   DJANGO_SECRET_KEY=your-long-random-secret-here
   DJANGO_DB_PASSWORD=your_password_here
   EMAIL_HOST_PASSWORD=your_app_password_here

3. تحديث settings.py
   - استبدل جميع hard-coded values بـ config()

4. إضافة .env للـ .gitignore
   echo ".env" >> .gitignore

5. التحقق:
   python manage.py shell
   from django.conf import settings
   print(len(settings.SECRET_KEY))  # يجب أن تكون > 50
```

**2. تطبيق Rate Limiting** (1 ساعة)
```bash
# الوقت المقدر: 1 ساعة
# الجهد: منخفض

# الخطوات:
1. تثبيت django-axes
   pip install django-axes

2. إضافة إلى INSTALLED_APPS و MIDDLEWARE
   
3. تشغيل Migrations
   python manage.py migrate

4. الاختبار:
   - حاول تسجيل دخول خاطئ 5 مرات
   - تحقق من الحجب
```

**3. إصلاح IDOR في Cart/Orders** (1 ساعة)
```bash
# الوقت المقدر: 1 ساعة
# الجهد: منخفض

# الخطوات:
1. تحديث views.py
   - أضف تحقق إضافي من الملكية
   
2. الاختبار:
   pytest tests/test_access_control.py
```

**4. إصلاح Password Reset** (2 ساعات)
```bash
# الوقت المقدر: 2 ساعة
# الجهد: متوسط

# الخطوات:
1. إنشاء نموذج PasswordResetToken
2. تحديث views.py
3. تشغيل Migration
   python manage.py makemigrations
   python manage.py migrate
4. الاختبار الشامل
```

**5. تحسين Input Validation** (1 ساعة)
```bash
# الوقت المقدر: 1 ساعة
# الجهد: منخفض

# الخطوات:
1. إضافة GuestCheckoutForm
2. تحديث views.py
3. الاختبار
```

**الإجمالي: 6 ساعات** ✅

---

### 🔧 **المرحلة 2: العالية (48 ساعة)**

**الهدف:** إغلاق جميع ثغرات High والتأكد من الامتثال OWASP

#### المهام:

**1. File Upload Validation** (2 ساعات)
```bash
# الخطوات:
1. تحديث UserProfile model
2. إضافة validators
3. تحديث forms
4. الاختبار الشامل
```

**2. تحسين Error Handling** (1 ساعة)
```bash
# الخطوات:
1. إضافة logging مخصص
2. إزالة stack traces من الـ Responses
3. الاختبار
```

**3. إضافة Security Headers** (1 ساعة)
```bash
# الخطوات:
1. تثبيت django-csp
   pip install django-csp
2. تحديث settings.py
3. الاختبار
```

**4. تحسين CORS** (1 ساعة)
```bash
# الخطوات:
1. إصلاح ALLOWED_HOSTS
2. إضافة CORS headers
3. الاختبار
```

**الإجمالي: 5 ساعات** ✅

---

### 📊 **المرحلة 3: المتوسطة (أسبوع)**

**الهدف:** تحسين المراقبة والتسجيل والامتثال طويل الأمد

#### المهام:

**1. Logging & Monitoring Setup** (3 ساعات)
```bash
# الخطوات:
1. إعداد Logging
2. إضافة Security Events
3. تحديث Database
```

**2. Encryption Setup** (2 ساعات)
```bash
# الخطوات:
1. تثبيت django-fernet
2. تطبيق على البيانات الحساسة
3. Migrations
```

**3. Security Testing** (4 ساعات)
```bash
# الخطوات:
1. كتابة tests شاملة
2. تشغيل OWASP tests
3. إصلاح الفشل
```

**الإجمالي: 9 ساعات** ✅

---

## 📋 قائمة التحقق بالتفصيل

### 🔴 Critical Issues Checklist

- [ ] **Issue #1: Hardcoded Credentials**
  - [ ] إنشاء ملف `.env`
  - [ ] تثبيت `python-decouple`
  - [ ] تحديث `settings.py`
  - [ ] اختبار البيئة المحلية
  - [ ] التحقق من عدم الـ hard-coded secrets
  - [ ] إضافة `.env` للـ `.gitignore`
  - [ ] توثيق الـ `.env` variables
  - [ ] ✅ تم
  
- [ ] **Issue #2: Weak Password Reset**
  - [ ] إنشاء نموذج `PasswordResetToken`
  - [ ] تحديث `ForgotPasswordView`
  - [ ] تحديث `ResetPasswordView`
  - [ ] كتابة tests
  - [ ] اختبار انتهاء الصلاحية
  - [ ] اختبار استخدام مرة واحدة
  - [ ] ✅ تم

- [ ] **Issue #3: Rate Limiting**
  - [ ] تثبيت `django-axes`
  - [ ] تطبيق على جميع authentication endpoints
  - [ ] تكوين timeout و attempts
  - [ ] اختبار الحجب
  - [ ] اختبار الإفراج بعد انقضاء المدة
  - [ ] ✅ تم

- [ ] **Issue #4: IDOR**
  - [ ] فحص جميع endpoints
  - [ ] إضافة تحقق الملكية
  - [ ] إضافة tests IDOR
  - [ ] اختبار access control
  - [ ] ✅ تم

- [ ] **Issue #5: Input Validation**
  - [ ] إنشاء `GuestCheckoutForm`
  - [ ] إضافة validators
  - [ ] تحديث checkout view
  - [ ] كتابة tests شاملة
  - [ ] ✅ تم

### 🟠 High Priority Checklist

- [ ] **Issue #6: File Upload**
  - [ ] فحص MIME Type
  - [ ] فحص حجم الملف
  - [ ] فحص أبعاد الصورة
  - [ ] إضافة validators
  - [ ] اختبار الملفات الضارة
  - [ ] ✅ تم

- [ ] **Issue #7: CORS**
  - [ ] إصلاح `ALLOWED_HOSTS`
  - [ ] إضافة CORS headers
  - [ ] اختبار cross-origin requests
  - [ ] ✅ تم

- [ ] **Issue #8: Security Headers**
  - [ ] تثبيت `django-csp`
  - [ ] إضافة CSP headers
  - [ ] إضافة HSTS
  - [ ] إضافة Referrer-Policy
  - [ ] اختبار Headers
  - [ ] ✅ تم

### 🟡 Medium Priority Checklist

- [ ] **Issue #9: Information Disclosure**
  - [ ] تحديث exception handling
  - [ ] إزالة stack traces
  - [ ] إضافة logging
  - [ ] اختبار رسائل الخطأ
  - [ ] ✅ تم

- [ ] **Issue #10: Logging**
  - [ ] إعداد logging configuration
  - [ ] إضافة security logger
  - [ ] تسجيل الأحداث المهمة
  - [ ] إنشاء log files
  - [ ] ✅ تم

---

## 🧪 Regression Testing Plan

```bash
# بعد كل إصلاح، قم بـ:

# 1. Unit Tests
pytest tests/ -v

# 2. Integration Tests
python manage.py test

# 3. Security Tests
pytest tests/test_security.py -v

# 4. Performance Tests (تأكد من عدم التأثير)
locust -f locustfile.py

# 5. Manual Testing
- [ ] اختبر جميع User Flows
- [ ] اختبر جميع API endpoints
- [ ] اختبر admin panel
```

---

## 📞 معالجة المشاكل أثناء التطبيق

| المشكلة | السبب | الحل |
|--------|------|------|
| ImportError: decouple | لم تثبت المكتبة | `pip install python-decouple` |
| Migration Conflicts | migrations قديمة | `python manage.py makemigrations --merge` |
| Tests تفشل | bugs في الكود | اتبع stack trace وأصلح |
| Performance بطيء | queries كثيرة | استخدم `select_related()` و `prefetch_related()` |
| CORS errors | headers خاطئة | تحقق من `ALLOWED_HOSTS` و CORS config |

---

## ✅ Acceptance Criteria

### للمرحلة 1 (Critical):
```
✅ لا يوجد hard-coded credentials في الكود
✅ جميع endpoints محمية من Brute Force
✅ IDOR tests تمرت بنجاح
✅ Password reset uses tokens
✅ Input validation على جميع forms
```

### للمرحلة 2 (High):
```
✅ File uploads محمية
✅ CORS مشددة
✅ Security Headers موجودة
✅ Error handling آمن
```

### للمرحلة 3 (Medium):
```
✅ Logging شامل مفعل
✅ Monitoring alerts مشغلة
✅ Encryption للبيانات الحساسة
✅ Tests شاملة + تمر بنجاح
```

---

## 🚀 Go-Live Checklist

```bash
# قبل النشر للإنتاج:

# 1. Final Security Review
./security_check.sh

# 2. All Tests Pass
pytest --cov
coverage report

# 3. Check Deployment
python manage.py check --deploy

# 4. Database Backup
pg_dump production_db > backup_$(date +%s).sql

# 5. Deploy
git push to main

# 6. Post-Deploy Verification
curl https://elwsamshop.com
# تحقق من Security Headers
curl -I https://elwsamshop.com | grep -E "X-Frame|X-Content|Strict-Transport"

# 7. Monitor Logs
tail -f logs/security.log
```

---

## 📞 Escalation Path

إذا واجهت مشكلة أثناء التنفيذ:

1. **مشاكل بسيطة:** اقرأ الـ error message و ابحث عن الحل
2. **مشاكل متوسطة:** ارجع للدليل (SECURITY_FIXES_GUIDE.md)
3. **مشاكل حرجة:** تجنب النشر واطلب مساعدة متخصص

---

**تاريخ التحديث:** 28 أبريل 2026  
**الإصدار:** 1.0 Draft  
**الحالة:** Ready for Implementation
