# API RESPONSE EXAMPLES - FLEXIBLE VARIANT SYSTEM
================================================

## Scenario 1: Simple Product (No Variants)

**Product:** كتاب Python للمبتدئين

### GET `/api/product-config/1/`

```json
{
  "success": true,
  "product_id": 1,
  "product_name": "كتاب Python للمبتدئين",
  "configuration_type": "simple",
  "base_price": "50.00",
  "has_patterns": false,
  "has_product_level_sizes": false,
  "requires_size": false,
  "patterns": [],
  "product_sizes": [],
  "colors": []
}
```

### GET `/api/variant-price/?product_id=1`

```json
{
  "success": true,
  "price": "50.00",
  "available": true,
  "stock": 100,
  "variant_id": 1,
  "requires_size": false,
  "validation": {
    "valid": true,
    "message": null
  }
}
```

---

## Scenario 2: Size-Based Product (No Patterns)

**Product:** قميص قطن بسيط

### GET `/api/product-config/2/`

```json
{
  "success": true,
  "product_id": 2,
  "product_name": "قميص قطن بسيط",
  "configuration_type": "size_based",
  "base_price": "100.00",
  "has_patterns": false,
  "has_product_level_sizes": true,
  "requires_size": true,
  "patterns": [],
  "product_sizes": [
    {"id": 1, "name": "S", "price": "100.00"},
    {"id": 2, "name": "M", "price": "120.00"},
    {"id": 3, "name": "L", "price": "140.00"},
    {"id": 4, "name": "XL", "price": "160.00"}
  ],
  "colors": [
    {"id": 1, "name": "أبيض", "code": "#FFFFFF"},
    {"id": 2, "name": "أسود", "code": "#000000"}
  ]
}
```

### GET `/api/variant-price/?product_id=2&size_id=2&color_id=1`

```json
{
  "success": true,
  "price": "120.00",
  "available": true,
  "stock": 25,
  "variant_id": 5,
  "requires_size": false,
  "validation": {
    "valid": true,
    "message": null
  }
}
```

### GET `/api/variant-price/?product_id=2` (Missing Size)

```json
{
  "success": true,
  "price": null,
  "available": false,
  "stock": 0,
  "variant_id": null,
  "requires_size": true,
  "validation": {
    "valid": false,
    "message": "يجب اختيار مقاس"
  }
}
```

---

## Scenario 3: Pattern-Based (Patterns WITHOUT Sizes)

**Product:** حقيبة يد

### GET `/api/product-config/3/`

```json
{
  "success": true,
  "product_id": 3,
  "product_name": "حقيبة يد",
  "configuration_type": "pattern_based",
  "base_price": "200.00",
  "has_patterns": true,
  "has_product_level_sizes": false,
  "requires_size": false,
  "patterns": [
    {
      "id": 1,
      "name": "جلد طبيعي",
      "has_sizes": false,
      "requires_size": false,
      "base_price": "500.00",
      "sizes": []
    },
    {
      "id": 2,
      "name": "قماش",
      "has_sizes": false,
      "requires_size": false,
      "base_price": "300.00",
      "sizes": []
    }
  ],
  "product_sizes": [],
  "colors": [
    {"id": 3, "name": "بني", "code": "#8B4513"},
    {"id": 4, "name": "أسود", "code": "#000000"}
  ]
}
```

### GET `/api/variant-price/?product_id=3&pattern_id=1&color_id=3`

```json
{
  "success": true,
  "price": "500.00",
  "available": true,
  "stock": 15,
  "variant_id": 10,
  "requires_size": false,
  "validation": {
    "valid": true,
    "message": null
  }
}
```

---

## Scenario 4: Pattern-Based (Patterns WITH Sizes)

**Product:** حذاء رياضي

### GET `/api/product-config/4/`

```json
{
  "success": true,
  "product_id": 4,
  "product_name": "حذاء رياضي",
  "configuration_type": "pattern_based",
  "base_price": "300.00",
  "has_patterns": true,
  "has_product_level_sizes": false,
  "requires_size": false,
  "patterns": [
    {
      "id": 3,
      "name": "كلاسيك",
      "has_sizes": true,
      "requires_size": true,
      "base_price": null,
      "sizes": [
        {"id": 5, "name": "40", "price": "400.00", "stock": 10},
        {"id": 6, "name": "41", "price": "420.00", "stock": 15},
        {"id": 7, "name": "42", "price": "440.00", "stock": 8},
        {"id": 8, "name": "43", "price": "460.00", "stock": 5}
      ]
    },
    {
      "id": 4,
      "name": "رياضي",
      "has_sizes": true,
      "requires_size": true,
      "base_price": null,
      "sizes": [
        {"id": 5, "name": "40", "price": "450.00", "stock": 12},
        {"id": 6, "name": "41", "price": "470.00", "stock": 20},
        {"id": 7, "name": "42", "price": "490.00", "stock": 10}
      ]
    }
  ],
  "product_sizes": [],
  "colors": [
    {"id": 5, "name": "أبيض", "code": "#FFFFFF"},
    {"id": 6, "name": "أسود", "code": "#000000"},
    {"id": 7, "name": "أزرق", "code": "#0000FF"}
  ]
}
```

### GET `/api/variant-price/?product_id=4&pattern_id=3&size_id=6&color_id=5`

```json
{
  "success": true,
  "price": "420.00",
  "available": true,
  "stock": 15,
  "variant_id": 25,
  "requires_size": false,
  "validation": {
    "valid": true,
    "message": null
  }
}
```

### GET `/api/variant-price/?product_id=4&pattern_id=3` (Missing Size)

```json
{
  "success": true,
  "price": null,
  "available": false,
  "stock": 0,
  "variant_id": null,
  "requires_size": true,
  "validation": {
    "valid": false,
    "message": "يجب اختيار مقاس للنمط كلاسيك"
  }
}
```

---

## Scenario 5: Mixed Patterns (Some With Sizes, Some Without)

**Product:** جاكيت

### GET `/api/product-config/5/`

```json
{
  "success": true,
  "product_id": 5,
  "product_name": "جاكيت",
  "configuration_type": "pattern_based",
  "base_price": "250.00",
  "has_patterns": true,
  "has_product_level_sizes": false,
  "requires_size": false,
  "patterns": [
    {
      "id": 5,
      "name": "شتوي",
      "has_sizes": true,
      "requires_size": true,
      "base_price": null,
      "sizes": [
        {"id": 1, "name": "S", "price": "350.00", "stock": 8},
        {"id": 2, "name": "M", "price": "370.00", "stock": 12},
        {"id": 3, "name": "L", "price": "390.00", "stock": 6}
      ]
    },
    {
      "id": 6,
      "name": "صيفي",
      "has_sizes": false,
      "requires_size": false,
      "base_price": "200.00",
      "sizes": []
    }
  ],
  "product_sizes": [],
  "colors": [
    {"id": 8, "name": "كحلي", "code": "#000080"},
    {"id": 9, "name": "رمادي", "code": "#808080"}
  ]
}
```

### GET `/api/variant-price/?product_id=5&pattern_id=5&size_id=2&color_id=8`

**Pattern "شتوي" WITH size:**
```json
{
  "success": true,
  "price": "370.00",
  "available": true,
  "stock": 12,
  "variant_id": 30,
  "requires_size": false,
  "validation": {
    "valid": true,
    "message": null
  }
}
```

### GET `/api/variant-price/?product_id=5&pattern_id=6&color_id=8`

**Pattern "صيفي" WITHOUT size:**
```json
{
  "success": true,
  "price": "200.00",
  "available": true,
  "stock": 20,
  "variant_id": 35,
  "requires_size": false,
  "validation": {
    "valid": true,
    "message": null
  }
}
```

---

## Scenario 6: Out of Stock

### GET `/api/variant-price/?product_id=4&pattern_id=3&size_id=8&color_id=5`

```json
{
  "success": true,
  "price": "460.00",
  "available": false,
  "stock": 0,
  "variant_id": 28,
  "requires_size": false,
  "validation": {
    "valid": true,
    "message": null
  }
}
```

---

## Scenario 7: Invalid Combination

### GET `/api/variant-price/?product_id=4&pattern_id=3&size_id=99&color_id=5`

**Size 99 doesn't exist for this pattern:**
```json
{
  "success": true,
  "price": null,
  "available": false,
  "stock": 0,
  "variant_id": null,
  "requires_size": false,
  "validation": {
    "valid": true,
    "message": null
  }
}
```

---

## GET `/api/variant-options/<product_id>/`

### Example 1: Initial Load (No Selection)

**GET `/api/variant-options/4/`**

```json
{
  "success": true,
  "patterns": [
    {"id": 3, "name": "كلاسيك", "has_sizes": true},
    {"id": 4, "name": "رياضي", "has_sizes": true}
  ],
  "sizes": [],
  "colors": [
    {"id": 5, "name": "أبيض", "code": "#FFFFFF"},
    {"id": 6, "name": "أسود", "code": "#000000"},
    {"id": 7, "name": "أزرق", "code": "#0000FF"}
  ],
  "requires_size": false
}
```

### Example 2: After Pattern Selection

**GET `/api/variant-options/4/?pattern_id=3`**

```json
{
  "success": true,
  "patterns": [
    {"id": 3, "name": "كلاسيك", "has_sizes": true},
    {"id": 4, "name": "رياضي", "has_sizes": true}
  ],
  "sizes": [
    {"id": 5, "name": "40", "price": "400.00"},
    {"id": 6, "name": "41", "price": "420.00"},
    {"id": 7, "name": "42", "price": "440.00"},
    {"id": 8, "name": "43", "price": "460.00"}
  ],
  "colors": [
    {"id": 5, "name": "أبيض", "code": "#FFFFFF"},
    {"id": 6, "name": "أسود", "code": "#000000"},
    {"id": 7, "name": "أزرق", "code": "#0000FF"}
  ],
  "requires_size": true
}
```

---

## Error Responses

### Missing Product ID

**GET `/api/variant-price/`**

```json
{
  "success": false,
  "error": "product_id is required"
}
```

### Product Not Found

**GET `/api/product-config/999/`**

```json
{
  "success": false,
  "error": "No Product matches the given query."
}
```

### Invalid Pattern ID

**GET `/api/variant-price/?product_id=4&pattern_id=999`**

```json
{
  "success": true,
  "price": null,
  "available": false,
  "stock": 0,
  "variant_id": null,
  "requires_size": false,
  "validation": {
    "valid": false,
    "message": "النمط المحدد غير موجود"
  }
}
```
