# Elwsam Store Endpoints README

هذا الملف يوثق جميع المسارات المهمة في مشروع متجر الوسام، مع التركيز على API الجديدة تحت `/api/v1/`، ثم نقاط AJAX القديمة، ثم صفحات المتجر ولوحة التحكم.

## معلومات عامة

- Framework: Django
- API base URL: `/api/v1/`
- Legacy AJAX API base URL: `/api/`
- تنسيق البيانات في API الجديدة: JSON
- ترميز JSON: UTF-8
- أغلب مسارات الكتالوج عامة ولا تحتاج تسجيل دخول.
- مسار إنشاء طلب ضيف لا يحتاج تسجيل دخول.
- مسارات الحسابات والسلة ولوحة التحكم تعتمد على جلسة Django و CSRF في نماذج HTML.

## تنسيق رد API v1

كل endpoints الجديدة ترجع envelope موحد:

```json
{
  "success": true,
  "version": "v1",
  "message": "",
  "data": {},
  "meta": {}
}
```

عند الخطأ:

```json
{
  "success": false,
  "version": "v1",
  "message": "رسالة الخطأ",
  "error": {
    "code": "validation_error",
    "details": {}
  }
}
```

## Pagination في API v1

المسارات التي ترجع قوائم تدعم:

| Query parameter | النوع | الافتراضي | الوصف |
| --- | --- | --- | --- |
| `page` | integer | `1` | رقم الصفحة |
| `page_size` | integer | حسب endpoint | عدد العناصر في الصفحة |

مثال `meta`:

```json
{
  "page": 1,
  "page_size": 24,
  "total": 100,
  "total_pages": 5,
  "has_next": true,
  "has_previous": false
}
```

# API v1 Endpoints

## 1. Health Check

### `GET /api/v1/health/`

يتأكد أن API تعمل.

Response 200:

```json
{
  "success": true,
  "version": "v1",
  "message": "",
  "data": {
    "service": "elwsam-store-api",
    "status": "ok"
  }
}
```

## 2. Home Data

### `GET /api/v1/home/`

يرجع بيانات الصفحة الرئيسية: الأقسام النشطة، شرائح السلايدر، ومجموعات المنتجات المختارة.

Response data:

```json
{
  "categories": [],
  "hero_slides": [],
  "collections": [
    {
      "type": "offers",
      "products": []
    }
  ]
}
```

## 3. Categories

### `GET /api/v1/catalog/categories/`

يرجع كل الأقسام النشطة.

Response data:

```json
{
  "items": [
    {
      "id": 1,
      "name": "Category name",
      "slug": "category-slug",
      "description": "",
      "image": "",
      "icon": "",
      "is_hot": false,
      "is_active": true,
      "order": 0,
      "url": "/categories/1/category-slug/",
      "absolute_url": "http://example.com/categories/1/category-slug/",
      "product_count": 12
    }
  ]
}
```

### `GET /api/v1/catalog/categories/{category_id}/`

يرجع قسمًا محددًا مع منتجاته.

Path parameters:

| Parameter | النوع | الوصف |
| --- | --- | --- |
| `category_id` | integer | رقم القسم |

Query parameters:

| Parameter | النوع | الوصف |
| --- | --- | --- |
| `page` | integer | رقم الصفحة |
| `page_size` | integer | عدد المنتجات |

Response data:

```json
{
  "category": {},
  "products": []
}
```

Errors:

| Status | السبب |
| --- | --- |
| 404 | القسم غير موجود أو غير نشط |

## 4. Products List

### `GET /api/v1/catalog/products/`

يرجع قائمة المنتجات النشطة.

Query parameters:

| Parameter | النوع | مثال | الوصف |
| --- | --- | --- | --- |
| `q` | string | `lamp` | بحث في اسم ووصف المنتج |
| `category` | string/integer | `switches` أو `3` | فلترة بالقسم عن طريق slug أو id |
| `sort` | string | `price_desc` | ترتيب النتائج |
| `collection` | string | `offers` | مجموعة منتجات الصفحة الرئيسية |
| `page` | integer | `1` | رقم الصفحة |
| `page_size` | integer | `24` | عدد المنتجات |

Supported `sort` values:

| Value | الوصف |
| --- | --- |
| `order` | الترتيب اليدوي |
| `price` | السعر من الأقل للأعلى |
| `price_desc` | السعر من الأعلى للأقل |
| `newest` | الأحدث |
| `rating` | الأعلى تقييمًا |

Supported `collection` values:

القيم تأتي من `HomeProductCollectionItem.COLLECTION_CHOICES`، والقيم المستخدمة حاليًا تشمل:

| Value | الوصف |
| --- | --- |
| `offers` | العروض |
| `best-sellers` | الأكثر مبيعًا |
| `latest` | الأحدث |

Response data:

```json
{
  "items": [
    {
      "id": 1,
      "name": "Product name",
      "slug": "product-slug",
      "category": {
        "id": 1,
        "name": "Category name",
        "slug": "category-slug"
      },
      "price": "120.00",
      "old_price": "150.00",
      "discount_percent": 20,
      "rating": 5.0,
      "image": "http://example.com/media/products/image.jpg",
      "image_alt": "Product name",
      "url": "/products/1/product-slug/",
      "absolute_url": "http://example.com/products/1/product-slug/",
      "is_new": true,
      "is_hot": false,
      "is_available": true,
      "configuration_type": "simple"
    }
  ]
}
```

Errors:

| Status | السبب |
| --- | --- |
| 400 | قيمة `sort` غير مدعومة |
| 400 | قيمة `collection` غير مدعومة |

## 5. Product Detail

### `GET /api/v1/catalog/products/{product_id}/`

يرجع تفاصيل منتج واحد.

Path parameters:

| Parameter | النوع | الوصف |
| --- | --- | --- |
| `product_id` | integer | رقم المنتج |

Response data:

```json
{
  "id": 1,
  "name": "Product name",
  "description": "Full description",
  "price": "120.00",
  "stock": 10,
  "images": [
    {
      "id": 1,
      "url": "http://example.com/media/products/image.jpg",
      "color": null,
      "order": 0
    }
  ],
  "specifications": [
    {
      "key": "Power",
      "value": "15W",
      "order": 0
    }
  ],
  "seo": {
    "title": "SEO title",
    "h1": "Product H1",
    "meta_description": "Meta description",
    "focus_keywords": []
  }
}
```

Errors:

| Status | السبب |
| --- | --- |
| 404 | المنتج غير موجود أو غير نشط |

## 6. Product Configuration

### `GET /api/v1/catalog/products/{product_id}/configuration/`

يرجع إعدادات المنتج وخياراته: الأنماط، المقاسات، الألوان، الأنواع.

Response data:

```json
{
  "configuration_type": "pattern_based",
  "base_price": "100.00",
  "patterns": [
    {
      "id": 1,
      "name": "Pattern 1",
      "has_sizes": true,
      "base_price": null,
      "sizes": [
        {
          "id": 1,
          "name": "M",
          "price": "180.00",
          "stock": 10,
          "available": true
        }
      ]
    }
  ],
  "product_sizes": [],
  "colors": [
    {
      "id": 1,
      "name": "Black",
      "code": "#111111"
    }
  ],
  "product_types": [],
  "flags": {
    "has_patterns": true,
    "has_product_level_sizes": false,
    "has_product_types": false,
    "has_colors": true,
    "has_type_colors": false
  }
}
```

Possible `configuration_type` values:

| Value | الوصف |
| --- | --- |
| `simple` | منتج بسيط بدون اختيارات |
| `color_only` | منتج يعتمد على اللون فقط |
| `size_based` | منتج يعتمد على مقاس على مستوى المنتج |
| `pattern_based` | منتج يعتمد على نمط وقد يحتوي مقاسات |

### `GET /api/v1/catalog/products/{product_id}/configuration-legacy/`

يرجع نفس منطق endpoint القديم `/api/product-config/{product_id}/` لكن داخل envelope موحد لـ API v1.

يفيد عند احتياج الواجهة الجديدة لنفس structure القديم بدون كسر التوافق.

## 7. Variant Options

### `GET /api/v1/catalog/products/{product_id}/variant-options/`

يرجع الاختيارات المتاحة بعد اختيار بعض القيم.

Query parameters:

| Parameter | النوع | مطلوب | الوصف |
| --- | --- | --- | --- |
| `pattern_id` | integer | لا | النمط المختار |
| `color_id` | integer | لا | اللون المختار |
| `type_id` | integer | لا | نوع المنتج المختار |

Example:

```text
GET /api/v1/catalog/products/10/variant-options/?pattern_id=2&type_id=4
```

Response data:

```json
{
  "patterns": [],
  "colors": [
    {
      "id": 1,
      "name": "Black",
      "code": "#111111",
      "available": true
    }
  ],
  "sizes": [
    {
      "id": 1,
      "name": "M",
      "available": true,
      "price": "180.00",
      "stock": 10
    }
  ],
  "requires_size": true,
  "has_patterns": true,
  "has_colors": true,
  "has_sizes": true
}
```

## 8. Variant Info

### `GET /api/v1/catalog/products/{product_id}/variant-info/`

يتحقق من اختيار المستخدم ويرجع السعر والمخزون للتركيبة المختارة.

Query parameters:

| Parameter | النوع | مطلوب حسب المنتج | الوصف |
| --- | --- | --- | --- |
| `pattern_id` | integer | نعم إذا المنتج pattern-based | رقم النمط |
| `color_id` | integer | نعم إذا المنتج له ألوان | رقم اللون |
| `size_id` | integer | نعم إذا المنتج يحتاج مقاس | رقم المقاس |
| `type_id` | integer | لا | رقم النوع من جدول `Type` |

Example:

```text
GET /api/v1/catalog/products/10/variant-info/?pattern_id=2&color_id=5&size_id=3
```

Response data:

```json
{
  "variant": {
    "id": 15,
    "price": "180.00",
    "stock": 6,
    "available": true,
    "sku": "SKU-001",
    "pattern": {
      "id": 2,
      "name": "Pattern 1"
    },
    "color": {
      "id": 5,
      "name": "Black",
      "code": "#111111"
    },
    "size": {
      "id": 3,
      "name": "M"
    }
  },
  "validation": {
    "valid": true,
    "message": "",
    "field": null,
    "errors": {}
  }
}
```

Validation error 422:

```json
{
  "success": false,
  "version": "v1",
  "message": "يجب اختيار المقاس",
  "error": {
    "code": "invalid_selection",
    "details": {
      "valid": false,
      "message": "يجب اختيار المقاس",
      "field": "size",
      "errors": {
        "size": "يجب اختيار المقاس"
      }
    }
  }
}
```

## 9. Product Images

### `GET /api/v1/catalog/products/{product_id}/images/`

يرجع صور المنتج.

Query parameters:

| Parameter | النوع | مطلوب | الوصف |
| --- | --- | --- | --- |
| `color_id` | integer | لا | عند تمريره يرجع الصور المرتبطة بهذا اللون |
| `pattern_id` | integer | لا | يستخدم مع `color_id` لتفضيل صور النمط |
| `type_id` | integer | لا | يستخدم مع `color_id` لتفضيل صور النوع |

Examples:

```text
GET /api/v1/catalog/products/10/images/
GET /api/v1/catalog/products/10/images/?color_id=4
GET /api/v1/catalog/products/10/images/?color_id=4&type_id=2
```

Response data:

```json
{
  "images": [
    {
      "id": 1,
      "url": "http://example.com/media/products/image.jpg",
      "color_id": 4,
      "order": 0
    }
  ]
}
```

## 10. Guest Order

### `POST /api/v1/orders/guest/`

ينشئ طلبًا كضيف بدون تسجيل دخول.

Headers:

```text
Content-Type: application/json
```

Request body:

```json
{
  "customer": {
    "name": "Ahmed Ali",
    "phone": "01000000000",
    "city": "Cairo",
    "address": "Street 1",
    "email": "ahmed@example.com",
    "contact_method": "whatsapp",
    "notes": "علامة مميزة أو ملاحظات شحن"
  },
  "items": [
    {
      "product_id": 1,
      "variant_id": null,
      "product_type_id": null,
      "quantity": 2
    }
  ],
  "notes": "ملاحظات على الطلب"
}
```

Customer fields:

| Field | مطلوب | الوصف |
| --- | --- | --- |
| `name` | نعم | اسم العميل |
| `phone` | نعم | رقم الهاتف |
| `city` | نعم | المدينة |
| `address` | نعم | العنوان |
| `email` | لا | بريد الضيف |
| `contact_method` | لا | `whatsapp` أو `call` |
| `notes` | لا | ملاحظات شحن |

Item fields:

| Field | مطلوب | الوصف |
| --- | --- | --- |
| `product_id` | نعم | رقم المنتج |
| `variant_id` | حسب المنتج | رقم `ProductVariant` للمنتجات ذات المخزون المتغير |
| `product_type_id` | حسب المنتج | رقم `ProductType` عند اختيار نوع |
| `quantity` | لا | الافتراضي `1`، الحد الأقصى `100` |

Response 201:

```json
{
  "success": true,
  "version": "v1",
  "message": "تم إنشاء الطلب بنجاح",
  "data": {
    "order": {
      "id": 25,
      "status": "pending",
      "total_price": "170.00",
      "items_count": 2,
      "detail_url": "http://example.com/orders/guest-order-success/25/"
    }
  }
}
```

Validation error 422:

```json
{
  "success": false,
  "version": "v1",
  "message": "بيانات الطلب غير مكتملة",
  "error": {
    "code": "validation_error",
    "details": {
      "customer": {
        "name": "الاسم مطلوب"
      },
      "items": []
    }
  }
}
```

# Legacy AJAX API Endpoints

هذه endpoints موجودة قبل API v1 وتخدم واجهة Django الحالية. أبقيناها للتوافق.

## `GET /api/products/`

يرجع منتجات مجموعات الصفحة الرئيسية.

Query parameters:

| Parameter | الافتراضي | الوصف |
| --- | --- | --- |
| `type` | `offers` | نوع المجموعة: `offers`, `best-sellers`, `latest` |
| `limit` | `10` | عدد المنتجات، بين 1 و 24 |
| `page` | `1` | رقم الصفحة |

Response:

```json
{
  "success": true,
  "type": "offers",
  "products": [],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 0,
    "num_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

## `GET /api/product-config/{product_id}/`

يرجع إعدادات المنتج للواجهة القديمة.

Path parameters:

| Parameter | الوصف |
| --- | --- |
| `product_id` | رقم المنتج |

Response يحتوي:

- `configuration_type`
- `patterns`
- `product_sizes`
- `product_types`
- `colors`
- `base_price`
- flags مثل `has_patterns`, `has_colors`

## `GET /api/variant-options/{product_id}/`

يرجع خيارات المنتج المتاحة حسب الاختيار الحالي.

Query parameters:

| Parameter | الوصف |
| --- | --- |
| `pattern_id` | النمط المختار |
| `color_id` | اللون المختار |
| `type_id` | النوع المختار |

## `GET /api/variant-info/{product_id}/`

يرجع معلومات المتغير والسعر والتحقق.

Query parameters:

| Parameter | الوصف |
| --- | --- |
| `pattern_id` | النمط |
| `color_id` | اللون |
| `size_id` | المقاس |
| `type_id` | النوع |

Response success:

```json
{
  "success": true,
  "variant": {
    "id": 1,
    "price": "180.00",
    "stock": 10,
    "available": true
  },
  "validation": {
    "valid": true,
    "message": "",
    "field": null,
    "errors": {}
  }
}
```

## `GET /api/variant-detail/{variant_id}/`

يرجع تفاصيل متغير محدد عن طريق id.

Path parameters:

| Parameter | الوصف |
| --- | --- |
| `variant_id` | رقم `ProductVariant` |

Response:

```json
{
  "success": true,
  "variant": {
    "id": 1,
    "pattern_name": "Pattern",
    "color_name": "Black",
    "color_code": "#111111",
    "size_name": "M",
    "price": "180.00",
    "sku": "SKU",
    "stock": 10,
    "available": true
  }
}
```

## `GET /api/product-images/{product_id}/{color_id}/`

يرجع صور المنتج حسب اللون، ويمكن تمرير `pattern_id` أو `type_id`.

Query parameters:

| Parameter | الوصف |
| --- | --- |
| `pattern_id` | لتفضيل صور النمط |
| `type_id` | لتفضيل صور النوع |

## `GET /search/`

مسار البحث الحالي. يستخدمه الموقع لنتائج البحث.

# Web Page Endpoints

هذه صفحات HTML وليست API JSON.

## Core

| Method | Path | الوصف |
| --- | --- | --- |
| GET | `/` | الصفحة الرئيسية |
| GET | `/robots.txt` | ملف robots |
| GET | `/sitemap.xml` | sitemap |

## Products Pages

| Method | Path | الوصف |
| --- | --- | --- |
| GET | `/categories/` | قائمة الأقسام |
| GET | `/categories/{id}/{slug}/` | منتجات قسم |
| GET | `/products/` | كل المنتجات |
| GET | `/products/{id}/{slug}/` | تفاصيل منتج |

## Accounts Pages

Base path: `/accounts/`

| Method | Path | الاسم | الوصف |
| --- | --- | --- | --- |
| GET/POST | `/accounts/login/` | `accounts:login` | تسجيل الدخول |
| GET/POST | `/accounts/register/` | `accounts:register` | تسجيل حساب |
| GET | `/accounts/logout/` | `accounts:logout` | تسجيل الخروج |
| GET/POST | `/accounts/verify-email/` | `accounts:verify_email` | تأكيد البريد |
| GET/POST | `/accounts/resend-otp/` | `accounts:resend_otp` | إعادة إرسال OTP |
| GET/POST | `/accounts/forgot-password/` | `accounts:forgot_password` | طلب استعادة كلمة المرور |
| GET/POST | `/accounts/verify-reset-code/` | `accounts:verify_reset_code` | تأكيد كود الاستعادة |
| GET/POST | `/accounts/reset-password/` | `accounts:reset_password` | تعيين كلمة مرور جديدة |
| GET/POST | `/accounts/profile/` | `accounts:profile` | الملف الشخصي |
| GET/POST | `/accounts/addresses/add/` | `accounts:address_create` | إضافة عنوان |
| GET/POST | `/accounts/addresses/{pk}/edit/` | `accounts:address_update` | تعديل عنوان |
| POST | `/accounts/addresses/{pk}/delete/` | `accounts:address_delete` | حذف عنوان |
| POST | `/accounts/addresses/{pk}/set-default/` | `accounts:set_default_address` | تعيين عنوان افتراضي |

## Orders And Cart Pages

Base path: `/orders/`

| Method | Path | الاسم | الوصف |
| --- | --- | --- | --- |
| GET | `/orders/cart/` | `orders:cart` | عرض السلة |
| POST | `/orders/cart/add/` | `orders:add_to_cart` | إضافة منتج للسلة |
| POST | `/orders/cart/item/{item_id}/update/` | `orders:update_cart_item` | تحديث كمية عنصر |
| POST | `/orders/cart/item/{item_id}/remove/` | `orders:remove_from_cart` | حذف عنصر |
| GET/POST | `/orders/checkout/` | `orders:checkout` | الدفع وإنشاء الطلب |
| GET | `/orders/order-success/{order_id}/` | `orders:order_success` | نجاح طلب مستخدم مسجل |
| GET | `/orders/guest-order-success/{order_id}/` | `orders:guest_order_success` | نجاح طلب ضيف |
| GET | `/orders/orders/` | `orders:order_list` | طلبات المستخدم |
| GET | `/orders/orders/{order_id}/` | `orders:order_detail` | تفاصيل طلب |
| GET | `/orders/wishlist/` | `orders:wishlist` | المفضلة |
| POST/GET | `/orders/wishlist/add/{product_id}/` | `orders:add_to_wishlist` | إضافة للمفضلة |
| POST/GET | `/orders/wishlist/remove/{product_id}/` | `orders:remove_from_wishlist` | حذف من المفضلة |

## Orders AJAX

Base path: `/orders/`

| Method | Path | الوصف |
| --- | --- | --- |
| POST | `/orders/wishlist/add-ajax/{product_id}/` | إضافة للمفضلة عبر AJAX |
| POST | `/orders/wishlist/remove-ajax/{product_id}/` | حذف من المفضلة عبر AJAX |
| POST | `/orders/wishlist/sync/` | مزامنة المفضلة من localStorage |
| POST | `/orders/cart/sync/` | مزامنة السلة من localStorage |
| POST | `/orders/cart/item/{item_id}/update-ajax/` | تحديث كمية عنصر عبر AJAX |
| POST | `/orders/cart/item/{item_id}/remove-ajax/` | حذف عنصر عبر AJAX |

# Staff Dashboard Endpoints

Base path: `/control-panel/`

هذه المسارات مخصصة للإدارة الداخلية.

| Method | Path | الاسم | الوصف |
| --- | --- | --- | --- |
| GET | `/control-panel/` | `staff_dashboard:dashboard` | لوحة التحكم |
| GET | `/control-panel/products/` | `staff_dashboard:products` | قائمة المنتجات |
| GET/POST | `/control-panel/products/add/` | `staff_dashboard:product_add` | إضافة منتج |
| GET/POST | `/control-panel/products/{pk}/edit/` | `staff_dashboard:product_edit` | تعديل منتج |
| POST | `/control-panel/products/{pk}/delete/` | `staff_dashboard:product_delete` | حذف منتج |
| GET/POST | `/control-panel/products/{pk}/colors/add/` | `staff_dashboard:product_color_add` | إضافة لون لمنتج |
| POST | `/control-panel/products/{pk}/colors/{color_pk}/delete/` | `staff_dashboard:product_color_delete` | حذف لون من منتج |
| GET/POST | `/control-panel/products/{product_pk}/types/add/` | `staff_dashboard:product_type_add` | إضافة نوع منتج |
| GET/POST | `/control-panel/products/{product_pk}/types/{type_pk}/edit/` | `staff_dashboard:product_type_edit` | تعديل نوع منتج |
| POST | `/control-panel/products/{product_pk}/types/{type_pk}/delete/` | `staff_dashboard:product_type_delete` | حذف نوع منتج |
| GET/POST | `/control-panel/product-types/{type_pk}/colors/add/` | `staff_dashboard:product_type_color_add` | إضافة لون لنوع منتج |
| POST | `/control-panel/product-types/{type_pk}/colors/{color_pk}/delete/` | `staff_dashboard:product_type_color_delete` | حذف لون من نوع منتج |
| GET/POST | `/control-panel/product-types/{type_pk}/images/add/` | `staff_dashboard:product_type_image_add` | إضافة صورة لنوع منتج |
| POST | `/control-panel/product-types/{type_pk}/images/{image_pk}/delete/` | `staff_dashboard:product_type_image_delete` | حذف صورة نوع منتج |
| GET | `/control-panel/colors/` | `staff_dashboard:colors` | قائمة الألوان |
| GET/POST | `/control-panel/colors/add/` | `staff_dashboard:color_add` | إضافة لون |
| GET/POST | `/control-panel/colors/{pk}/edit/` | `staff_dashboard:color_edit` | تعديل لون |
| POST | `/control-panel/colors/{pk}/delete/` | `staff_dashboard:color_delete` | حذف لون |
| GET | `/control-panel/categories/` | `staff_dashboard:categories` | قائمة الأقسام |
| GET/POST | `/control-panel/categories/add/` | `staff_dashboard:category_add` | إضافة قسم |
| GET/POST | `/control-panel/categories/{pk}/edit/` | `staff_dashboard:category_edit` | تعديل قسم |
| POST | `/control-panel/categories/{pk}/delete/` | `staff_dashboard:category_delete` | حذف قسم |
| GET | `/control-panel/orders/` | `staff_dashboard:orders` | قائمة الطلبات |
| GET | `/control-panel/orders/{pk}/` | `staff_dashboard:order_detail` | تفاصيل طلب |
| GET | `/control-panel/customers/` | `staff_dashboard:customers` | قائمة العملاء |
| GET/POST | `/control-panel/customers/{pk}/edit/` | `staff_dashboard:customer_edit` | تعديل عميل |
| GET | `/control-panel/home-sections/` | `staff_dashboard:home_collections` | أقسام الصفحة الرئيسية |
| GET/POST | `/control-panel/home-sections/add/` | `staff_dashboard:home_collection_add` | إضافة قسم رئيسية |
| GET/POST | `/control-panel/home-sections/{pk}/edit/` | `staff_dashboard:home_collection_edit` | تعديل قسم رئيسية |
| POST | `/control-panel/home-sections/{pk}/delete/` | `staff_dashboard:home_collection_delete` | حذف قسم رئيسية |
| GET | `/control-panel/hero-slides/` | `staff_dashboard:hero_slides` | شرائح السلايدر |
| GET/POST | `/control-panel/hero-slides/add/` | `staff_dashboard:hero_slide_add` | إضافة شريحة |
| GET/POST | `/control-panel/hero-slides/{pk}/edit/` | `staff_dashboard:hero_slide_edit` | تعديل شريحة |
| POST | `/control-panel/hero-slides/{pk}/delete/` | `staff_dashboard:hero_slide_delete` | حذف شريحة |
| GET | `/control-panel/settings/` | `staff_dashboard:settings` | إعدادات عامة |

# Admin And System Endpoints

| Method | Path | الوصف |
| --- | --- | --- |
| GET/POST | `/admin/` | Django admin |
| GET/POST | `/_nested_admin/` | nested admin package routes |
| GET | `/static/...` | ملفات static أثناء التطوير حسب settings |
| GET | `/media/...` أو `/shop_media/...` | ملفات media حسب settings |

# ملاحظات مهمة للمطورين

## الفرق بين `type_id` و `product_type_id`

- في `variant-info` و `variant-options` يتم استخدام `type_id` وهو رقم السجل في جدول `Type`.
- في إنشاء الطلب والسلة يتم استخدام `product_type_id` وهو رقم السجل في جدول `ProductType`.

## اختيار المنتج قبل إضافته للطلب

للمنتجات البسيطة:

```json
{
  "product_id": 1,
  "quantity": 1
}
```

للمنتجات ذات المتغيرات:

```json
{
  "product_id": 1,
  "variant_id": 15,
  "quantity": 1
}
```

للمنتجات ذات الأنواع:

```json
{
  "product_id": 1,
  "product_type_id": 4,
  "quantity": 1
}
```

## تدفق اختيار منتج في الواجهة

1. اعرض تفاصيل المنتج:

```text
GET /api/v1/catalog/products/{product_id}/
```

2. اجلب إعدادات الاختيارات:

```text
GET /api/v1/catalog/products/{product_id}/configuration/
```

3. عند اختيار المستخدم لقيمة، اجلب الخيارات المتاحة:

```text
GET /api/v1/catalog/products/{product_id}/variant-options/?pattern_id=...
```

4. قبل الإضافة للسلة أو الطلب تحقق من السعر والمخزون:

```text
GET /api/v1/catalog/products/{product_id}/variant-info/?pattern_id=...&color_id=...&size_id=...
```

5. أنشئ طلب ضيف:

```text
POST /api/v1/orders/guest/
```

## أوامر تحقق مفيدة

```bash
python manage.py check
python manage.py test api.tests products.tests.test_api
python manage.py test
```
