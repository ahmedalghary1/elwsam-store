# 💻 **أمثلة عملية من الكود**

---

## 📌 **محتويات الأمثلة**

### 1️⃣ **Templates - استخدام البيانات**
### 2️⃣ **Views - معالجة البيانات**
### 3️⃣ **Models - إنشاء وحفظ البيانات**
### 4️⃣ **URLs - توجيه الطلبات**

---

## 1️⃣ **Templates - استخدام البيانات**

### **مثال 1: عرض قائمة الأقسام**

#### ❌ الطريقة الخاطئة (Hardcoded):
```html
<div class="categories-grid">
  <a href="/categories/electronics/" class="category-card">
    <span>📱 الإلكترونيات</span>
    <span>50 منتج</span>
  </a>
  <a href="/categories/fashion/" class="category-card">
    <span>👔 الملابس</span>
    <span>100 منتج</span>
  </a>
</div>
```

#### ✅ الطريقة الصحيحة (Dynamic):
```django
<div class="categories-grid">
  {% for category in categories %}
  <a href="{% url 'category_products' category.slug %}" class="category-card">
    {% if category.image %}
      <img src="{{ category.image.url }}" alt="{{ category.name }}">
    {% else %}
      <span>{{ category.icon }}</span>
    {% endif %}
    <span>{{ category.name }}</span>
    <span>{{ category.get_product_count }} منتج</span>
    
    {% if category.is_hot %}
      <span class="badge">رائج</span>
    {% endif %}
  </a>
  {% empty %}
  <p>لا توجد أقسام</p>
  {% endfor %}
</div>
```

---

### **مثال 2: عرض تفاصيل المنتج**

#### ❌ خاطئ:
```html
<h1>مشترك يوما 6A</h1>
<p>السعر: 600 ج.م</p>
<p>السعر السابق: 700 ج.م</p>
<img src="./image/3.png" alt="صورة">
```

#### ✅ صحيح:
```django
<h1>{{ product.name }}</h1>
<p>{{ product.description }}</p>

<div class="price-section">
  <span class="price">{{ product.price }} ج.م</span>
  {% if product.old_price %}
    <span class="old-price">{{ product.old_price }} ج.م</span>
    <span class="discount">
      خصم {{ product.get_discount_percent }}%
    </span>
  {% endif %}
</div>

<!-- معرض الصور -->
<div class="gallery">
  {% for image in images %}
    <div class="gallery-item">
      <img src="{{ image.image.url }}" alt="{{ product.name }}">
    </div>
  {% endfor %}
</div>

<!-- المواصفات -->
<table class="specs">
  <tbody>
    {% for spec in specs %}
    <tr>
      <td>{{ spec.key }}</td>
      <td>{{ spec.value }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>

<!-- التقييم -->
<div class="rating">
  <span class="stars">
    {% for i in "12345" %}
      {% if forloop.counter <= product.rating %}★{% else %}☆{% endif %}
    {% endfor %}
  </span>
  <span>{{ product.rating }}/5</span>
</div>

<!-- الحالة -->
{% if product.is_active %}
  <span class="badge badge-success">متوفر</span>
{% else %}
  <span class="badge badge-danger">غير متوفر</span>
{% endif %}
```

---

### **مثال 3: فرز وتصفية المنتجات**

```django
<!-- شريط الفرز -->
<div class="sort-controls">
  <form method="GET">
    <select name="sort" onchange="this.form.submit()">
      <option value="order" {% if sort_by == 'order' %}selected{% endif %}>
        الأحدث
      </option>
      <option value="price" {% if sort_by == 'price' %}selected{% endif %}>
        السعر: من الأقل للأعلى
      </option>
      <option value="price_desc" {% if sort_by == 'price_desc' %}selected{% endif %}>
        السعر: من الأعلى للأقل
      </option>
      <option value="rating" {% if sort_by == 'rating' %}selected{% endif %}>
        الأعلى تقييماً
      </option>
    </select>
  </form>

  <form method="GET" class="search-box">
    <input type="text" name="q" placeholder="ابحث..." value="{{ search_query }}">
    <button type="submit">🔍</button>
  </form>
</div>

<!-- قائمة المنتجات -->
<div class="products-grid">
  {% for product in products %}
    <div class="product-card">
      <!-- نفس الكود أعلاه -->
    </div>
  {% empty %}
    <p>لا توجد نتائج</p>
  {% endfor %}
</div>

<!-- عدد النتائج -->
<p class="results-count">
  {% if search_query %}
    تم العثور على {{ products_count }} منتج بـ "{{ search_query }}"
  {% endif %}
</p>
```

---

## 2️⃣ **Views - معالجة البيانات**

### **مثال 1: الحصول على بيانات المنتج مع التحسينات**

#### ❌ خاطئ:
```python
def product_detail(request, slug):
    product = Product.objects.get(slug=slug)  # قد يرفع خطأ 500
    images = ProductImage.objects.filter(product=product)
    # ... الكثير من الـ Queries
    return render(request, 'product.html', {'product': product})
```

#### ✅ صحيح:
```python
class ProductDetailView(View):
    template_name = "product.html"

    def get(self, request, slug):
        # استخدام get_object_or_404 بدل get()
        product = get_object_or_404(Product, slug=slug, is_active=True)
        
        # استخدام prefetch_related لتقليل الـ Queries
        images = ProductImage.objects.filter(product=product).order_by('order')
        colors = ProductColor.objects.filter(product=product).order_by('order')
        sizes = ProductSize.objects.filter(product=product).order_by('order')
        patterns = Pattern.objects.filter(product=product).order_by('order')
        
        # استخدام select_related للـ Foreign Keys
        variants = ProductVariant.objects.filter(product=product).select_related(
            'color', 'size', 'pattern'
        ).order_by('order')
        
        # ترتيب المواصفات
        specs = product.specs.all().order_by('order')
        
        # منتجات مشابهة
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id).order_by('-rating')[:6]
        
        context = {
            'product': product,
            'images': images,
            'colors': colors,
            'sizes': sizes,
            'patterns': patterns,
            'variants': variants,
            'specs': specs,
            'related_products': related_products,
        }
        
        return render(request, self.template_name, context)
```

---

### **مثال 2: فرز وتصفية المتقدم**

```python
def category_products(request, slug):
    """
    عرض المنتجات مع فرز وتصفية وبحث
    """
    category = get_object_or_404(Category, slug=slug)
    
    # البيانات الأساسية
    products = Product.objects.filter(
        category=category,
        is_active=True
    ).prefetch_related('images', 'variants', 'specs')
    
    # استخراج معاملات البحث من Request
    sort_by = request.GET.get('sort', 'order')
    search_query = request.GET.get('q', '').strip()
    
    # البحث
    if search_query:
        from django.db.models import Q
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # الفرز
    if sort_by == 'price':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    else:  # 'order' (الافتراضي)
        products = products.order_by('order')
    
    context = {
        'category': category,
        'products': products,
        'search_query': search_query,
        'sort_by': sort_by,
        'products_count': products.count(),
    }
    
    return render(request, 'category-products.html', context)
```

---

### **مثال 3: البحث الشامل**

```python
def search_products(request):
    """بحث شامل عن المنتجات والأقسام"""
    from django.db.models import Q
    
    query = request.GET.get('q', '').strip()
    products = Product.objects.none()
    
    if query and len(query) >= 2:  # حد أدنى لطول البحث
        # البحث في المنتجات
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True
        ).select_related('category').prefetch_related('images').order_by('-created_at')
    
    context = {
        'products': products,
        'query': query,
        'results_count': products.count(),
    }
    
    return render(request, 'search_results.html', context)
```

---

### **مثال 4: الصفحة الرئيسية**

```python
def index(request):
    """الصفحة الرئيسية - عرض الأقسام والمنتجات المميزة"""
    
    # الأقسام المرتبة
    categories = Category.objects.all().order_by('order')
    
    # المنتجات المميزة
    featured_products = Product.objects.filter(
        is_hot=True,
        is_active=True
    ).order_by('order').prefetch_related('images')[:10]
    
    # أحدث المنتجات
    latest_products = Product.objects.filter(
        is_active=True
    ).order_by('-created_at').prefetch_related('images')[:10]
    
    # الأقسام المشهورة
    hot_categories = Category.objects.filter(
        is_hot=True
    ).order_by('order')
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'latest_products': latest_products,
        'hot_categories': hot_categories,
    }
    
    return render(request, 'index.html', context)
```

---

## 3️⃣ **Models - إنشاء وحفظ البيانات**

### **مثال 1: إنشاء منتج جديد**

```python
from products.models import Category, Product, ProductImage, ProductSpecification

# الطريقة 1: الإنشاء والحفظ منفصل
product = Product(
    name="مشترك يوما 6A",
    description="شاحن متعدد المنافذ",
    category=Category.objects.get(id=1),
    price=600,
    old_price=700,
    is_new=True,
    is_hot=True,
    rating=4.8,
)
product.save()

# الطريقة 2: الإنشاء والحفظ معاً
product = Product.objects.create(
    name="مشترك يوما 6A",
    description="شاحن متعدد المنافذ",
    category_id=1,
    price=600,
    old_price=700,
)
```

---

### **مثال 2: تحديث البيانات**

```python
# الحصول على المنتج
product = Product.objects.get(slug='smart-phone')

# تحديث حقل واحد
product.rating = 4.9
product.save()

# تحديث عدة حقول
Product.objects.filter(id=product.id).update(
    is_hot=True,
    order=1
)

# تغيير الحالة
product.is_active = False
product.save(update_fields=['is_active'])
```

---

### **مثال 3: استخدام Methods المخصصة**

```python
# استخدام get_price_display()
product = Product.objects.get(id=1)
print(product.get_price_display())
# Output: 600.00 ج.م (50% خصم)

# استخدام get_discount_percent()
print(f"خصم: {product.get_discount_percent()}%")
# Output: خصم: 50%

# استخدام get_product_count()
category = Category.objects.get(id=1)
print(f"عدد المنتجات: {category.get_product_count()}")
# Output: عدد المنتجات: 25
```

---

## 4️⃣ **URLs - توجيه الطلبات**

### **مثال: استخدام URL Reversing في Templates**

```django
<!-- ❌ الطريقة الخاطئة (Hardcoded) -->
<a href="/products/smart-phone/">تفاصيل المنتج</a>

<!-- ✅ الطريقة الصحيحة (Dynamic) -->
<a href="{% url 'product_detail' product.slug %}">
  تفاصيل المنتج
</a>

<!-- مع معاملات -->
<a href="{% url 'category_products' category.slug %}?sort=price">
  المنتجات (مرتبة حسب السعر)
</a>

<!-- في JavaScript -->
<script>
  let url = "{% url 'product_images_by_color' product.id 0 %}";
  // سيحول إلى: /api/product-images/1/0/
</script>
```

---

## 🧪 **اختبار الأمثلة**

### **تشغيل Django Shell**

```bash
python manage.py shell
```

### **اختبار نموذج**

```python
# 1. استيراد المكتبات
from products.models import Category, Product

# 2. الحصول على البيانات
categories = Category.objects.all()
for cat in categories:
    print(f"{cat.name}: {cat.get_product_count()} منتج")

# 3. البحث
products = Product.objects.filter(category__name="المشتركات")
for prod in products:
    print(f"{prod.name}: {prod.get_price_display()}")

# 4. الفرز
expensive = Product.objects.order_by('-price')[:5]
for prod in expensive:
    print(f"{prod.name}: {prod.price}")

# 5. التحديث
product = Product.objects.get(name__contains="مشترك")
product.is_hot = True
product.save()

# 6. الحذف
Product.objects.filter(is_active=False).delete()
```

---

## 📝 **ملاحظات مهمة**

1. ✅ استخدم `get_object_or_404()` لتجنب الأخطاء
2. ✅ استخدم `prefetch_related()` و `select_related()` لـ optimization
3. ✅ استخدم `{% url %}` template tag بدل hardcoded URLs
4. ✅ تحقق من البيانات قبل عرضها
5. ✅ استخدم `order_by()` دائماً للترتيب

---

**✅ الآن لديك أمثلة عملية شاملة!**
