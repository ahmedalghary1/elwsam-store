import json
import re

from django.conf import settings
from django.db import models
from django.utils.html import strip_tags
from django.utils.text import Truncator, slugify
from accounts.models import User


def clean_slug(value, fallback):
    raw_value = (value or fallback or "").strip()
    raw_value = re.sub(r"[\\/%?#]+", "-", raw_value)
    raw_value = re.sub(r"\s+", " ", raw_value)
    return slugify(raw_value, allow_unicode=True) or fallback


def build_unique_slug(model_class, instance, value, fallback):
    base_slug = clean_slug(value, fallback)
    candidate = base_slug
    counter = 1
    while model_class.objects.filter(slug=candidate).exclude(pk=instance.pk).exists():
        candidate = f"{base_slug}-{counter}"
        counter += 1
    return candidate


def canonical_site_url(path="/"):
    base_url = getattr(settings, "CANONICAL_BASE_URL", "https://elwsamshop.com").rstrip("/")
    return f"{base_url}/{str(path).lstrip('/')}"
# =========================
# Category (ترتيب الأقسام)
# =========================
class Category(models.Model):

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    seo_title = models.CharField(max_length=255, blank=True, help_text='Custom SEO title for category pages')
    meta_description = models.CharField(max_length=320, blank=True, help_text='Custom meta description for category pages')
    seo_intro = models.TextField(blank=True, help_text='Intro content displayed on category pages')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    slug = models.CharField(max_length=255, unique=True, blank=True, db_index=True)
    icon = models.CharField(max_length=50, default='📁', help_text='أيقونة Emoji أو نص قصير')
    is_hot = models.BooleanField(default=False, help_text='هل هذا القسم من الأقسام المشهورة؟')
    is_active = models.BooleanField(default=True, help_text='Active visibility flag for categories')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'قسم'
        verbose_name_plural = 'الأقسام'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        cleaned_slug = clean_slug(self.slug or self.name, "category")
        if cleaned_slug != self.slug:
            self.slug = build_unique_slug(Category, self, cleaned_slug, "category")
        super().save(*args, **kwargs)
    
    def get_product_count(self):
        """حساب عدد المنتجات في هذا القسم"""
        return self.product_set.filter(is_active=True).count()
    
    def get_absolute_url(self):
        """الحصول على رابط القسم"""
        from django.urls import reverse
        return reverse('category_products', kwargs={'id': self.id, 'slug': self.slug})

# =========================
# Product (ترتيب المنتجات)
# =========================
class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True, blank=True, db_index=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    seo_title = models.CharField(max_length=255, blank=True, help_text='عنوان SEO مخصص لصفحة المنتج')
    meta_description = models.CharField(max_length=320, blank=True, help_text='وصف Meta Description مخصص')
    seo_h1 = models.CharField(max_length=255, blank=True, help_text='عنوان H1 مخصص داخل صفحة المنتج')
    seo_description = models.TextField(blank=True, help_text='وصف SEO طويل مخصص للظهور داخل صفحة المنتج')
    focus_keywords = models.TextField(blank=True, help_text='الكلمات المفتاحية الأساسية والفرعية')
    seo_faq = models.TextField(blank=True, help_text='FAQ منسق بصيغة: س: ... ثم ج: ...')
    seo_image_alt_texts = models.TextField(blank=True, help_text='اقتراحات Alt Text للصور، سطر لكل اقتراح')
    internal_linking_suggestions = models.TextField(blank=True, help_text='اقتراحات الربط الداخلي لكل منتج')
    schema_markup = models.TextField(blank=True, help_text='Product JSON-LD schema جاهز إذا توفر')
    # معلومات الأسعار
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text='السعر القديم (للخصم)')
    
    # حالة المنتج
    is_new = models.BooleanField(default=True, help_text='هل المنتج جديد؟')
    is_hot = models.BooleanField(default=False, help_text='هل المنتج مشهور/مبيع؟')
    is_active = models.BooleanField(default=True, help_text='هل المنتج متاح؟')
    
    # المخزون للمنتجات البسيطة (بدون متغيرات)
    stock = models.IntegerField(
        default=0,
        help_text='المخزون المتاح للمنتج البسيط (يُستخدم فقط إذا لم يكن للمنتج ألوان أو مقاسات أو أنماط)'
    )
    
    # Product configuration flags
    has_patterns = models.BooleanField(
        default=False,
        help_text='هل المنتج يحتوي على أنماط؟'
    )
    has_product_level_sizes = models.BooleanField(
        default=False,
        help_text='هل المنتج يحتوي على مقاسات على مستوى المنتج؟'
    )
    has_colors = models.BooleanField(
        default=False,
        help_text='هل المنتج يحتوي على ألوان فقط؟ (بدون أنماط أو مقاسات)'
    )
    
    # التقييمات والشهرة
    rating = models.FloatField(default=5.0, help_text='التقييم من 0 إلى 5')
    
    # الترتيب والتاريخ
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['order']
        verbose_name = 'منتج'
        verbose_name_plural = 'المنتجات'

    def save(self, *args, **kwargs):
        cleaned_slug = clean_slug(self.slug or self.name, "product")
        if cleaned_slug != self.slug:
            self.slug = build_unique_slug(Product, self, cleaned_slug, "product")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        """الحصول على رابط المنتج"""
        from django.urls import reverse
        return reverse('product_detail', kwargs={'id': self.id, 'slug': self.slug})
    
    def get_price_display(self):
        """عرض السعر مع الخصم إن وجد"""
        if self.old_price and self.old_price > self.price:
            discount = ((self.old_price - self.price) / self.old_price) * 100
            return f'{self.price:.2f} ج.م ({int(discount)}% خصم)'
        return f'{self.price:.2f} ج.م'
    
    def get_discount_percent(self):
        """حساب نسبة الخصم"""
        if self.old_price and self.old_price > self.price:
            return int(((self.old_price - self.price) / self.old_price) * 100)
        return 0
    
    def get_first_image(self):
        """الحصول على أول صورة للمنتج"""
        return self.images.first()
    
    def get_price(self, pattern_id=None, size_id=None, color_id=None, type_id=None):
        """
        Dynamic price resolution using hierarchy:
        0. ProductType (product + type) - highest priority
        1. PatternSize (pattern + size)
        2. ProductSize (product + size)
        3. Pattern.base_price
        4. Product.price (base price) - fallback
        
        Args:
            pattern_id: Optional pattern ID
            size_id: Optional size ID
            color_id: Optional color ID (for future use)
            type_id: Optional product type ID
        
        Returns:
            Decimal: Calculated price based on hierarchy
        """
        # Priority 0: ProductType (product + type)
        if type_id:
            try:
                product_type = ProductType.objects.get(
                    product=self,
                    type_id=type_id
                )
                return product_type.price
            except ProductType.DoesNotExist:
                pass

        # Priority 1: PatternSize (pattern + size)
        if pattern_id and size_id:
            try:
                pattern_size = PatternSize.objects.get(
                    pattern_id=pattern_id,
                    size_id=size_id
                )
                return pattern_size.price
            except PatternSize.DoesNotExist:
                pass
        
        # Priority 2: ProductSize (product + size)
        if size_id:
            try:
                product_size = ProductSize.objects.get(
                    product=self,
                    size_id=size_id
                )
                return product_size.price
            except ProductSize.DoesNotExist:
                pass
        
        # Priority 3: Pattern base price
        if pattern_id:
            try:
                pattern = Pattern.objects.get(id=pattern_id)
                if pattern.base_price:
                    return pattern.base_price
            except Pattern.DoesNotExist:
                pass
        
        # Priority 4: Product base price (fallback)
        return self.price
    
    def has_variants(self):
        """Check if product has any variants"""
        return self.variants.exists()
    
    def check_if_has_patterns(self):
        """Check if product has patterns"""
        return self.patterns.exists()
    
    def check_if_has_product_level_sizes(self):
        """Check if product has product-level sizes"""
        return self.product_sizes.exists()

    def check_if_has_product_types(self):
        """Check if product has product-level types"""
        return self.product_types.exists()
    
    def get_configuration_type(self):
        """
        Returns product configuration type for frontend logic
        Priority: pattern_based > size_based > color_only > simple
        """
        if self.check_if_has_patterns():
            return 'pattern_based'
        elif self.check_if_has_product_level_sizes():
            return 'size_based'
        elif self.has_colors:
            return 'color_only'
        else:
            return 'simple'
    
    def requires_color_selection(self):
        """
        Determines if color selection is required
        """
        return self.has_colors
    
    def requires_size_selection(self):
        """
        Determines if size selection is required at product level
        """
        return self.check_if_has_product_level_sizes()
    
    def is_simple_product(self):
        """
        Check if this is a simple product (no patterns, no sizes, no colors)
        """
        return (not self.check_if_has_patterns() and 
                not self.check_if_has_product_level_sizes() and 
                not self.has_colors)
    
    def is_available(self):
        """
        Check if product is available in stock
        For simple products: check product.stock
        For configurable products: prefer variant stock when variants exist,
        otherwise treat configured options as available when they exist.
        """
        if self.is_simple_product():
            return self.stock > 0

        if self.variants.exists():
            return self.variants.filter(stock__gt=0).exists()

        if self.product_types.exists():
            return True

        if self.product_sizes.exists():
            return True

        if self.patterns.filter(pattern_sizes__stock__gt=0).exists():
            return True

        if self.product_colors.exists():
            return True

        return False
    
    def get_stock(self):
        """
        Get stock for simple products
        """
        if self.is_simple_product():
            return self.stock
        return None

    def _plain_text_description(self):
        """Normalize long descriptions for SEO fallbacks."""
        text = strip_tags(self.description or "")
        return " ".join(text.split())

    def get_seo_title(self):
        """Return the SEO title with a sensible fallback."""
        if self.seo_title:
            return self.seo_title
        return f"{self.name} | متجر الوسام"

    def get_meta_description(self):
        """Return a concise meta description suitable for search results."""
        if self.meta_description:
            return self.meta_description
        text = self._plain_text_description()
        if not text:
            text = f"اشترِ {self.name} من متجر الوسام مع تفاصيل واضحة وسعر مناسب."
        return Truncator(text).chars(160)

    def get_seo_h1(self):
        """Return the H1 used inside the product page."""
        return self.seo_h1 or self.name

    def get_seo_description(self):
        """Return rich SEO content for the product page body."""
        return self.seo_description or self.description

    def get_focus_keywords_list(self):
        """Split stored keywords into a clean list for admin or future templates."""
        if not self.focus_keywords:
            return []
        raw_keywords = self.focus_keywords.replace("\r", "\n").replace("|", "\n")
        return [item.strip() for item in raw_keywords.splitlines() if item.strip()]

    def get_seo_image_alt_texts(self):
        """Return image alt suggestions as a list, one item per line."""
        if not self.seo_image_alt_texts:
            return []
        return [item.strip() for item in self.seo_image_alt_texts.splitlines() if item.strip()]

    def get_primary_image_alt(self):
        """Fallback alt text for product images."""
        alt_texts = self.get_seo_image_alt_texts()
        if alt_texts:
            return alt_texts[0]
        return self.get_seo_h1()

    def get_faq_items(self):
        """Parse the stored FAQ text into question/answer pairs."""
        if not self.seo_faq:
            return []

        items = []
        question = ""
        answer_lines = []

        for line in self.seo_faq.splitlines():
            stripped = line.strip()
            if not stripped:
                if question and answer_lines:
                    items.append({
                        "question": question,
                        "answer": " ".join(answer_lines).strip(),
                    })
                    question = ""
                    answer_lines = []
                continue

            if stripped.startswith("س:"):
                if question and answer_lines:
                    items.append({
                        "question": question,
                        "answer": " ".join(answer_lines).strip(),
                    })
                    answer_lines = []
                question = stripped[2:].strip()
            elif stripped.startswith("ج:"):
                answer_lines.append(stripped[2:].strip())
            else:
                answer_lines.append(stripped)

        if question and answer_lines:
            items.append({
                "question": question,
                "answer": " ".join(answer_lines).strip(),
            })

        return items

    def build_product_schema(self, url=None, image_url=None):
        """Generate a Product schema fallback when custom markup is unavailable."""
        category_name = ""
        if self.category_id:
            try:
                category_name = self.category.name
            except Exception:
                category_name = ""

        schema = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": self.get_seo_h1(),
            "description": self.get_meta_description(),
            "category": category_name,
            "sku": self.slug,
            "brand": {
                "@type": "Brand",
                "name": "الوسام",
            },
            "offers": {
                "@type": "Offer",
                "priceCurrency": "EGP",
                "price": str(self.price),
                "availability": "https://schema.org/InStock" if self.is_available() else "https://schema.org/OutOfStock",
            },
        }
        if image_url:
            schema["image"] = [image_url]
        if url:
            schema["url"] = url
            schema["offers"]["url"] = url
        return schema

    def get_schema_markup(self, url=None, image_url=None):
        """Return a controlled Product schema without unsupported custom fields."""
        return json.dumps(self.build_product_schema(url=url, image_url=image_url), ensure_ascii=False)

    def get_breadcrumb_schema(self, category_url=None, product_url=None):
        """Generate breadcrumb schema for richer search appearance."""
        category_name = "المنتجات"
        if self.category_id:
            try:
                category_name = self.category.name
            except Exception:
                category_name = "المنتجات"

        breadcrumb = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "item": canonical_site_url("/"),
                    "name": "الرئيسية",
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": category_name,
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": self.get_seo_h1(),
                },
            ],
        }
        if category_url:
            breadcrumb["itemListElement"][1]["item"] = category_url
        if product_url:
            breadcrumb["itemListElement"][2]["item"] = product_url
        return json.dumps(breadcrumb, ensure_ascii=False)

    def get_faq_schema(self):
        """Generate FAQ schema from stored FAQ content."""
        faq_items = self.get_faq_items()
        if not faq_items:
            return ""
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["question"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": item["answer"],
                    },
                }
                for item in faq_items
            ],
        }
        return json.dumps(schema, ensure_ascii=False)

    
class HomeProductCollectionItem(models.Model):
    COLLECTION_OFFERS = "offers"
    COLLECTION_BEST_SELLERS = "best-sellers"
    COLLECTION_LATEST = "latest"
    LEGACY_COLLECTION_ALIASES = {
        "1": COLLECTION_OFFERS,
        "2": COLLECTION_BEST_SELLERS,
        "3": COLLECTION_LATEST,
    }

    COLLECTION_CHOICES = (
        (COLLECTION_OFFERS, "العروض"),
        (COLLECTION_BEST_SELLERS, "الأفضل مبيعا"),
        (COLLECTION_LATEST, "حديثا"),
    )

    collection_type = models.CharField(
        max_length=32,
        choices=COLLECTION_CHOICES,
        db_index=True,
        verbose_name="تبويب الصفحة الرئيسية",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="home_collection_items",
        verbose_name="المنتج",
    )
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["collection_type", "order", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["collection_type", "product"],
                name="unique_home_collection_product",
            ),
        ]
        indexes = [
            models.Index(fields=["collection_type", "is_active", "order"]),
        ]
        verbose_name = "عنصر تبويب الصفحة الرئيسية"
        verbose_name_plural = "عناصر تبويبات الصفحة الرئيسية"

    def __str__(self):
        return f"{self.get_collection_type_display()} - {self.product.name}"

    def save(self, *args, **kwargs):
        self.collection_type = self.LEGACY_COLLECTION_ALIASES.get(
            str(self.collection_type),
            self.collection_type,
        )
        super().save(*args, **kwargs)


# =========================
# HeroSlide (سلايدر الصفحة الرئيسية)
# =========================
class HeroSlide(models.Model):
    title = models.CharField(max_length=180, blank=True, verbose_name="عنوان الشريحة")
    image = models.ImageField(upload_to="home/slides/", verbose_name="صورة السلايدر")
    link_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="رابط الشريحة",
        help_text="يمكن استخدام رابط داخلي مثل /products/ أو رابط كامل يبدأ بـ https://",
    )
    alt_text = models.CharField(max_length=220, blank=True, verbose_name="النص البديل للصورة")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-created_at"]
        indexes = [
            models.Index(fields=["is_active", "order"]),
        ]
        verbose_name = "شريحة السلايدر"
        verbose_name_plural = "شرائح السلايدر"

    def __str__(self):
        return self.title or f"شريحة رقم {self.pk or ''}".strip()

    @property
    def image_url(self):
        return self.image.url if self.image else ""

    @property
    def effective_alt_text(self):
        return self.alt_text or self.title or "عرض من متجر الوسام"


# =========================
# Pattern (ترتيب الأنماط)
# =========================
class Pattern(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="patterns")
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    
    # Multi-level pricing support
    has_sizes = models.BooleanField(
        default=False,
        help_text='هل هذا النمط يتطلب اختيار مقاس؟'
    )
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='السعر الأساسي للنمط (إذا لم يكن له مقاسات)'
    )

    class Meta:
        ordering = ['order']
        verbose_name = 'نمط'
        verbose_name_plural = 'الأنماط'

    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    def requires_size_selection(self):
        """Check if this pattern requires size selection"""
        return self.has_sizes
    
    def clean(self):
        """Validate that pattern has either sizes or base_price"""
        from django.core.exceptions import ValidationError
        if not self.has_sizes and not self.base_price:
            raise ValidationError(
                'يجب تحديد سعر أساسي للنمط إذا لم يكن له مقاسات'
            )


# =========================
# Color (عام)
# =========================
class Color(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=7, blank=True)

    class Meta:
        verbose_name = 'لون'
        verbose_name_plural = 'الألوان'

    def __str__(self):
        return self.name


# =========================
# ProductColor (ترتيب الألوان لكل منتج)
# =========================
class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_colors")
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('product', 'color')
        verbose_name = 'لون منتج'
        verbose_name_plural = 'ألوان المنتجات'

    def __str__(self):
        return f"{self.product.name} - {self.color.name}"
    
    
    def create_variants_for_pattern_sizes(self):
        """Create ProductVariant for all pattern-size combinations"""
        from .models import Pattern, PatternSize, ProductVariant
        
        product = self.product
        color = self.color
        
        # Get all patterns with sizes
        patterns = Pattern.objects.filter(product=product, has_sizes=True)
        
        created_count = 0
        for pattern in patterns:
            # Get all sizes for this pattern
            pattern_sizes = PatternSize.objects.filter(pattern=pattern).select_related('size')
            
            for ps in pattern_sizes:
                # Check if variant already exists
                if not ProductVariant.objects.filter(
                    product=product,
                    pattern=pattern,
                    color=color,
                    size=ps.size
                ).exists():
                    # Create variant
                    ProductVariant.objects.create(
                        product=product,
                        pattern=pattern,
                        color=color,
                        size=ps.size,
                        price=ps.price,
                        stock=ps.stock,
                        order=0
                    )
                    created_count += 1
        
        return created_count


# =========================
# Size (عام)
# =========================
class Size(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'مقاس'
        verbose_name_plural = 'المقاسات'

    def __str__(self):
        return self.name


class Type(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'نوع'
        verbose_name_plural = 'الأنواع'

    def __str__(self):
        return self.name


# =========================
# ProductSize (ترتيب المقاسات لكل منتج)
# =========================
class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_sizes")
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    
    # Multi-level pricing: product-level size pricing
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text='السعر لهذا المقاس على مستوى المنتج'
    )

    class Meta:
        ordering = ['order']
        unique_together = ('product', 'size')
        verbose_name = 'مقاس منتج'
        verbose_name_plural = 'مقاسات المنتجات'
        indexes = [
            models.Index(fields=['product', 'size']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.size.name} ({self.price} ج.م)"


# =========================
# PatternSize (مقاسات النمط مع الأسعار)
# =========================
class ProductType(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_types")
    type = models.ForeignKey(Type, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='product-types/',null=True, blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='السعر لهذا النوع على مستوى المنتج'
    )
    description = models.TextField(
        help_text='الوصف الخاص بهذا النوع', null=True, blank=True
    )

    class Meta:
        ordering = ['order']
        unique_together = ('product', 'type')
        verbose_name = 'نوع منتج'
        verbose_name_plural = 'أنواع المنتجات'
        indexes = [
            models.Index(fields=['product', 'type']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.type.name} ({self.price} ج.م)"


class ProductTypeColor(models.Model):
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.CASCADE,
        related_name="type_colors"
    )
    color = models.ForeignKey(
        Color,
        on_delete=models.CASCADE,
        related_name="product_type_colors"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('product_type', 'color')
        verbose_name = 'لون نوع المنتج'
        verbose_name_plural = 'ألوان أنواع المنتجات'
        indexes = [
            models.Index(fields=['product_type', 'color']),
        ]

    def __str__(self):
        return f"{self.product_type.product.name} - {self.product_type.type.name} - {self.color.name}"


class ProductTypeImage(models.Model):
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.CASCADE,
        related_name="type_images"
    )
    color = models.ForeignKey(
        Color,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_type_images",
        help_text='اختياري: اربط الصورة بلون معين لهذا النوع'
    )
    image = models.ImageField(upload_to='product-types/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'صورة نوع المنتج'
        verbose_name_plural = 'صور أنواع المنتجات'

    def __str__(self):
        color_part = f" - {self.color.name}" if self.color else ""
        return f"صورة {self.product_type.product.name} - {self.product_type.type.name}{color_part}"


class PatternSize(models.Model):
    """Pattern-specific size pricing (highest priority in price hierarchy)"""
    pattern = models.ForeignKey(Pattern, on_delete=models.CASCADE, related_name="pattern_sizes")
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text='السعر لهذا المقاس في هذا النمط'
    )
    stock = models.IntegerField(
        default=0,
        help_text='المخزون المتاح لهذا المقاس في هذا النمط'
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('pattern', 'size')
        verbose_name = 'مقاس نمط'
        verbose_name_plural = 'مقاسات الأنماط'
        indexes = [
            models.Index(fields=['pattern', 'size']),
            models.Index(fields=['pattern', 'stock']),
        ]

    def __str__(self):
        return f"{self.pattern.name} - {self.size.name} ({self.price} ج.م)"
    
    def is_available(self):
        """Check if this pattern-size combination is in stock"""
        return self.stock > 0
    
    
    def create_variants_for_colors(self):
        """Create ProductVariant for all colors of this product"""
        from .models import ProductColor, ProductVariant
        
        product = self.pattern.product
        pattern = self.pattern
        size = self.size
        
        # Get all colors for this product
        product_colors = ProductColor.objects.filter(product=product).select_related('color')
        
        created_count = 0
        for pc in product_colors:
            # Check if variant already exists
            if not ProductVariant.objects.filter(
                product=product,
                pattern=pattern,
                color=pc.color,
                size=size
            ).exists():
                # Create variant
                ProductVariant.objects.create(
                    product=product,
                    pattern=pattern,
                    color=pc.color,
                    size=size,
                    price=self.price,
                    stock=self.stock,
                    order=0
                )
                created_count += 1
        
        return created_count


# =========================
# PatternColor (ألوان خاصة بكل نمط)
# =========================
class PatternColor(models.Model):
    pattern = models.ForeignKey(Pattern, on_delete=models.CASCADE, related_name="pattern_colors")
    color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name="pattern_colors")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('pattern', 'color')
        verbose_name = 'لون النمط'
        verbose_name_plural = 'ألوان الأنماط'

    def __str__(self):
        return f"{self.pattern.name} - {self.color.name}"


# =========================
# PatternImage (صور خاصة بكل نمط ولون)
# =========================
class PatternImage(models.Model):
    pattern = models.ForeignKey(Pattern, on_delete=models.CASCADE, related_name="pattern_images")
    color = models.ForeignKey(
        Color, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="pattern_images",
        help_text='اختياري: اربط الصورة بلون معين لعرضها عند اختياره'
    )
    image = models.ImageField(upload_to='patterns/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'صورة النمط'
        verbose_name_plural = 'صور الأنماط'

    def __str__(self):
        color_part = f" - {self.color.name}" if self.color else ""
        return f"صورة {self.pattern.name}{color_part}"


# =========================
# Product Images (ترتيب الصور لكل لون)
# =========================
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='products/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'صورة منتج'
        verbose_name_plural = 'صور المنتجات'

    def __str__(self):
        return f"Image for {self.product.name}"


# =========================
# Variant (التركيبة النهائية)
# =========================
class ProductVariant(models.Model):
    """
    Product variant for stock tracking only.
    Price is calculated dynamically using Product.get_price() method.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")

    pattern = models.ForeignKey(Pattern, on_delete=models.SET_NULL, null=True, blank=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    # DEPRECATED: Will be removed in future migration
    # Price is now calculated dynamically via Product.get_price()
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text='DEPRECATED: Use Product.get_price() instead'
    )
    
    stock = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('product', 'pattern', 'color', 'size')
        ordering = ['order']
        verbose_name = 'متغير منتج'
        verbose_name_plural = 'متغيرات المنتجات'
        indexes = [
            models.Index(fields=['product', 'pattern', 'size']),
            models.Index(fields=['product', 'stock']),
            models.Index(fields=['product', 'pattern', 'color', 'size']),
        ]

    def __str__(self):
        parts = [self.product.name]
        if self.pattern:
            parts.append(self.pattern.name)
        if self.color:
            parts.append(self.color.name)
        if self.size:
            parts.append(self.size.name)
        return ' - '.join(parts)
    
    def get_price(self):
        """Get dynamic price using Product.get_price() hierarchy"""
        return self.product.get_price(
            pattern_id=self.pattern_id,
            size_id=self.size_id,
            color_id=self.color_id
        )
    
    def is_available(self):
        """Check if variant is in stock"""
        return self.stock > 0
    
    def clean(self):
        """Validate variant configuration"""
        from django.core.exceptions import ValidationError
        
        # If pattern has sizes, size must be selected
        if self.pattern and self.pattern.has_sizes and not self.size:
            raise ValidationError(
                'يجب اختيار مقاس لهذا النمط'
            )
        
        # Skip relationship queries if product is not saved yet (no PK)
        if not self.product_id:
            return
        
        # If product is color_only (no patterns, no sizes, has colors), color is required
        if (not self.product.check_if_has_patterns() and 
            not self.product.check_if_has_product_level_sizes() and 
            self.product.has_colors and 
            not self.color):
            raise ValidationError('يجب اختيار لون لهذا المنتج')


# =========================
# Specifications (ترتيب المواصفات)
# =========================
class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="specs")
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'مواصفة'
        verbose_name_plural = 'مواصفات المنتجات'

    def __str__(self):
        return f"{self.key}: {self.value}"



