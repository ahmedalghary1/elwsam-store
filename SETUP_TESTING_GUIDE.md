# 🛠️ **دليل التثبيت والاختبار الشامل**

---

## 📋 **المحتويات**
1. ✅ تطبيق التغييرات
2. ✅ إضافة البيانات
3. ✅ الاختبار
4. ✅ استكشاف الأخطاء

---

## ✅ **Step 1: تطبيق التغييرات**

### **أ. التحقق من requirements**
```bash
pip list  # تأكد أن لديك Django 6.0+
```

### **ب. تطبيق Migrations**
```bash
# في مجلد المشروع
cd c:\Users\m\Documents\website\src

# إنشاء Migration جديد
python manage.py makemigrations products

# تطبيق جميع Migrations
python manage.py migrate
```

### **ج. التحقق من التغييرات**
```bash
# فتح Django Shell
python manage.py shell

# اختبار الـ Models
from products.models import Category, Product

# التحقق من أن الحقول الجديدة موجودة
c = Category()
print(c._meta.get_fields())  # يجب أن تشمل is_hot, icon, etc.

exit()
```

---

## 📊 **Step 2: إضافة البيانات الأساسية**

### **الطريقة 1️⃣: عبر Django Admin (الأسهل)**

#### **أ. إنشاء Superuser**
```bash
python manage.py createsuperuser
# نموذج التعبئة:
# Username: admin
# Email: admin@example.com
# Password: admin123
```

#### **ب. تشغيل الخادم**
```bash
python manage.py runserver
# الرابط: http://localhost:8000/admin
```

#### **ج. إضافة البيانات في Admin:**

**1. إضافة Categories:**
- الذهاب إلى: Admin → Categories → Add Category
- ملء البيانات:
  ```
  Name: المشتركات
  Description: أجهزة لتوزيع الكهرباء والتوصيل
  Icon: 🔌
  Slug: (تملأ تلقائياً)
  Is Hot: ✓ (اختياري)
  Order: 1
  Image: (اختياري)
  ```
- حفظ وتكرار لـ 3-4 أقسام أخرى

**2. إضافة Products:**
- الذهاب إلى: Admin → Products → Add Product
- ملء البيانات:
  ```
  Name: مشترك يوما 6A
  Description: شاحن متعدد المنافذ WS3341 – آمن وعملي...
  Category: المشتركات
  Price: 600
  Old Price: 700
  Is New: ✓
  Is Hot: ✓
  Is Active: ✓
  Rating: 4.8
  Order: 1
  Image: (اختياري)
  ```

**3. إضافة ProductImages:**
- الذهاب إلى: Admin → Product Images → Add Product Image
- ملء البيانات:
  ```
  Product: مشترك يوما 6A
  Image: (اختر صورة)
  Order: 1
  Color: (اختياري)
  ```

**4. إضافة ProductSpecification:**
- الذهاب إلى: Admin → Product Specifications → Add Specification
- ملء البيانات:
  ```
  Product: مشترك يوما 6A
  Key: الاتصال
  Value: USB Type-A ×6
  Order: 1
  ```

---

### **الطريقة 2️⃣: عبر Django Shell (للـ Bulk Data)**

```python
# فتح Shell
python manage.py shell

# استيراد Models
from products.models import Category, Product, ProductSpecification, ProductImage
import os
from django.core.files.base import ContentFile

# إضافة Categories
cat1 = Category.objects.create(
    name="المشتركات",
    description="أجهزة لتوزيع الكهرباء",
    icon="🔌",
    is_hot=True,
    order=1
)

cat2 = Category.objects.create(
    name="الفيشة",
    description="مقابس كهربائية",
    icon="🔌",
    order=2
)

cat3 = Category.objects.create(
    name="اللمبات",
    description="مصادر إضاءة",
    icon="💡",
    order=3
)

# إضافة Products
prod1 = Product.objects.create(
    name="مشترك يوما 6A",
    description="شاحن متعدد المنافذ WS3341 – آمن وعملي للاستخدام اليومي",
    category=cat1,
    price=600,
    old_price=700,
    is_new=True,
    is_hot=True,
    is_active=True,
    rating=4.8,
    order=1
)

prod2 = Product.objects.create(
    name="فيشة دكر صاروخ",
    description="فيشة كهربائية آمنة وموثوقة",
    category=cat2,
    price=50,
    old_price=60,
    is_new=False,
    is_hot=False,
    is_active=True,
    rating=4.5,
    order=1
)

# إضافة Specifications
ProductSpecification.objects.create(
    product=prod1,
    key="عدد المخارج",
    value="6 مخارج",
    order=1
)

ProductSpecification.objects.create(
    product=prod1,
    key="نوع التوصيل",
    value="USB Type-A",
    order=2
)

exit()
```

---

## 🧪 **Step 3: الاختبار**

### **أ. اختبار الصفحات**

#### **1. الصفحة الرئيسية**
```
URL: http://localhost:8000/
✓ عرض الأقسام (من Loop)
✓ عرض المنتجات المميزة (من Loop)
✓ عرض الأسعار والخصم
```

#### **2. صفحة الأقسام**
```
URL: http://localhost:8000/categories/
✓ قائمة جميع الأقسام
✓ كل قسم يعرض الأيقونة وعدد المنتجات
✓ الرابط يذهب للمنتجات الصحيحة
```

#### **3. صفحة منتجات القسم**
```
URL: http://localhost:8000/categories/electronics/
✓ عرض المنتجات من القسم الصحيح
✓ عرض الصور والأسعار
✓ إمكانية الفرز والبحث
```

#### **4. صفحة تفاصيل المنتج**
```
URL: http://localhost:8000/products/smart-phone/
✓ عرض المنتج الصحيح من Database
✓ عرض جميع الصور
✓ عرض المواصفات
✓ عرض التقييم والسعر والخصم
```

### **ب. اختبار البحث والفرز**

```
URL: http://localhost:8000/categories/electronics/?sort=price
✓ فرز حسب السعر

URL: http://localhost:8000/search/?q=مشترك
✓ البحث عن المنتجات
```

---

## 🔧 **استكشاف الأخطاء الشائعة**

### **❌ خطأ: `TemplateDoesNotExist`**
```
حل: تأكد من أن جميع Template files موجودة في:
- c:\Users\m\Documents\website\src\templates\
```

### **❌ خطأ: `No such table: products_product`**
```
حل: تأكد من تطبيق Migrations:
python manage.py migrate
```

### **❌ خطأ: `AttributeError: 'Category' object has no attribute 'get_product_count'`**
```
حل: الطريقة لم تُحفظ في Model، أضفها يدوياً:

def get_product_count(self):
    return self.product_set.count()
```

### **❌ خطأ: صور المنتج لا تظهر**
```
حل: 
1. تأكد من تحميل الصور إلى المشروع
2. تأكد من أن Media Files محفوظة في مجلد media/
3. تحقق من رابط الـ Media في settings:
   MEDIA_URL='/media/'
   MEDIA_ROOT=BASE_DIR / "media"
```

### **❌ خطأ: `ModuleNotFoundError: No module named 'products.models'`**
```
حل: تأكد من وجود __init__.py في مجلد products/
```

---

## 📊 **Checklist للتحقق**

- [ ] جميع الـ Models محدثة بـ الحقول الجديدة
- [ ] جميع الـ Migrations تم تطبيقها بنجاح
- [ ] Django Admin يعمل بشكل صحيح
- [ ] هناك بيانات في Database
- [ ] الصفحة الرئيسية تعرض الأقسام بشكل ديناميكي
- [ ] صفحة الأقسام تعرض جميع الأقسام
- [ ] صفحة تفاصيل المنتج تعرض البيانات بشكل صحيح
- [ ] البحث والفرز يعملان بشكل صحيح
- [ ] الصور تظهر بشكل صحيح
- [ ] الأسعار والخصم يظهران بشكل صحيح

---

## 🚀 **تشغيل الخادم النهائي**

```bash
# الانتقال للمجلد
cd c:\Users\m\Documents\website\src

# تشغيل الخادم
python manage.py runserver

# الوصول للموقع
http://localhost:8000/
```

---

## 📝 **ملاحظات مهمة**

1. **استخدام الـ Static Files:**
   - CSS و JS في `static/css/` و `static/js/`
   - تأكد من استخدام `{% static 'path/to/file' %}`

2. **الصور:**
   - يجب أن تكون الصور في `media/` folder
   - استخدم `{{ image.url }}` في Templates

3. **الـ URLs:**
   - استخدم دائماً `{% url 'name' %}` بدل hardcoded URLs
   - هذا يسهل التعديل لاحقاً

4. **Database:**
   - تأكد من تطبيق جميع Migrations
   - إذا حدثت مشاكل، يمكن حذف DB وإعادة الإنشاء

5. **Performance:**
   - استخدم `Django Debug Toolbar` لـ optimization
   - استخدم `select_related()` و `prefetch_related()`

---

**✅ تم الانتهاء من دليل التثبيت والاختبار!**
