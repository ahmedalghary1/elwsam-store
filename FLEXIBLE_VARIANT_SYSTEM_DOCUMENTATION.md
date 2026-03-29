# FLEXIBLE PRODUCT VARIANT SYSTEM - COMPLETE DOCUMENTATION
=========================================================

## 🎯 EXECUTIVE SUMMARY

This document describes a **production-ready, flexible variant system** that supports:
- ✅ Multi-level pricing (Product → Pattern → Size)
- ✅ Conditional size requirements (pattern-dependent)
- ✅ Mixed product configurations
- ✅ Stock-aware filtering
- ✅ Clean architecture with no data duplication

---

## 📐 ARCHITECTURE DECISIONS

### 1. **Data Model Design**

**Core Principle:** Price resolution hierarchy with single source of truth

```
Priority 1: PatternSize.price (pattern + size)
Priority 2: ProductSize.price (product + size)
Priority 3: Pattern.base_price (pattern only)
Priority 4: Product.base_price (fallback)
```

**Key Models:**

1. **`Product`**
   - `base_price`: Fallback price
   - `has_patterns`: Configuration flag
   - `has_product_level_sizes`: Configuration flag
   - Method: `get_price(pattern_id, size_id)` - Implements price resolution

2. **`Pattern`**
   - `base_price`: Optional pattern-level price
   - `has_sizes`: Flag indicating if pattern requires size selection
   - Method: `requires_size_selection()` - Returns True if has_sizes=True

3. **`ProductSize`**
   - Product-level size with individual `price`
   - Used when product has sizes but no patterns

4. **`PatternSize`**
   - Pattern-level size with individual `price` and `stock`
   - Takes priority over ProductSize
   - Used when pattern has its own sizes

5. **`ProductVariant`**
   - Stock tracking only (no price field)
   - Price calculated dynamically via `Product.get_price()`
   - Unique constraint: (product, pattern, color, size)

### 2. **Business Logic Rules**

**Validation Hierarchy:**

```python
if product.has_patterns:
    if pattern not selected:
        → INVALID: "يجب اختيار نمط"
    
    if pattern.has_sizes and size not selected:
        → INVALID: "يجب اختيار مقاس للنمط {pattern.name}"
    
    if pattern.has_sizes == False:
        → VALID (no size needed)

elif product.has_product_level_sizes:
    if size not selected:
        → INVALID: "يجب اختيار مقاس"

else:  # Simple product
    → VALID (no selection needed)
```

---

## 🗄️ DATABASE SCHEMA

### New/Modified Models

```python
# products/models_new.py

class Product(models.Model):
    base_price = DecimalField()  # Fallback price
    has_patterns = BooleanField(default=False)
    has_product_level_sizes = BooleanField(default=False)
    
    def get_price(self, pattern_id=None, size_id=None):
        # Price resolution logic
        pass

class Pattern(models.Model):
    product = ForeignKey(Product)
    base_price = DecimalField(null=True, blank=True)
    has_sizes = BooleanField(default=False)

class ProductSize(models.Model):
    product = ForeignKey(Product)
    size = ForeignKey(Size)
    price = DecimalField()  # Product-level size price

class PatternSize(models.Model):
    pattern = ForeignKey(Pattern)
    size = ForeignKey(Size)
    price = DecimalField()  # Pattern-level size price
    stock = IntegerField()  # Stock for this combination

class ProductVariant(models.Model):
    product = ForeignKey(Product)
    pattern = ForeignKey(Pattern, null=True)
    size = ForeignKey(Size, null=True)
    color = ForeignKey(Color, null=True)
    stock = IntegerField()  # Stock only, no price
    
    def get_price(self):
        return self.product.get_price(self.pattern_id, self.size_id)
```

### Indexes for Performance

```python
class Meta:
    indexes = [
        models.Index(fields=['product', 'pattern', 'size']),
        models.Index(fields=['product', 'size']),
    ]
```

---

## 🔌 API ENDPOINTS

### 1. GET `/api/product-config/<product_id>/`

**Purpose:** Returns complete product configuration

**Response:**
```json
{
  "success": true,
  "product_id": 1,
  "product_name": "قميص رياضي",
  "configuration_type": "pattern_based",
  "base_price": "299.99",
  "has_patterns": true,
  "has_product_level_sizes": false,
  "requires_size": false,
  "patterns": [
    {
      "id": 1,
      "name": "كلاسيك",
      "has_sizes": true,
      "requires_size": true,
      "base_price": "299.99",
      "sizes": [
        {"id": 1, "name": "S", "price": "299.99", "stock": 10},
        {"id": 2, "name": "M", "price": "319.99", "stock": 15}
      ]
    },
    {
      "id": 2,
      "name": "رياضي",
      "has_sizes": false,
      "requires_size": false,
      "base_price": "349.99",
      "sizes": []
    }
  ],
  "product_sizes": [],
  "colors": [
    {"id": 1, "name": "أحمر", "code": "#FF0000"}
  ]
}
```

**Configuration Types:**
- `simple`: No patterns, no sizes
- `size_based`: Product-level sizes, no patterns
- `pattern_based`: Has patterns (may/may not have sizes)

---

### 2. GET `/api/variant-price/`

**Purpose:** Validates selection and returns price

**Parameters:**
- `product_id` (required)
- `pattern_id` (optional)
- `size_id` (optional)
- `color_id` (optional)

**Response (Valid):**
```json
{
  "success": true,
  "price": "319.99",
  "available": true,
  "stock": 15,
  "variant_id": 42,
  "requires_size": false,
  "validation": {
    "valid": true,
    "message": null
  }
}
```

**Response (Invalid - Missing Size):**
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

### 3. GET `/api/variant-options/<product_id>/`

**Purpose:** Returns available options (stock-aware)

**Parameters:**
- `pattern_id` (optional)
- `color_id` (optional)

**Response:**
```json
{
  "success": true,
  "patterns": [
    {"id": 1, "name": "كلاسيك", "has_sizes": true}
  ],
  "sizes": [
    {"id": 1, "name": "S", "price": "299.99"},
    {"id": 2, "name": "M", "price": "319.99"}
  ],
  "colors": [
    {"id": 1, "name": "أحمر", "code": "#FF0000"}
  ],
  "requires_size": true
}
```

---

## 💻 FRONTEND IMPLEMENTATION

### JavaScript Architecture

**File:** `static/js/flexible-variant-selector.js`

**Class:** `FlexibleVariantSelector`

**Key Features:**
1. **Configuration-driven UI**
   - Loads product config via AJAX
   - Renders UI based on `configuration_type`

2. **Dynamic validation**
   - Backend validates every selection
   - Shows/hides size selector based on pattern

3. **Conditional requirements**
   - Red asterisk (*) for required fields
   - Disabled "Add to Cart" until valid

4. **Price updates**
   - Real-time price calculation via API
   - Shows size-specific prices

**Flow:**

```javascript
1. Load product config
   ↓
2. Render UI based on type:
   - pattern_based → Show patterns
   - size_based → Show sizes
   - simple → No selectors
   ↓
3. User selects pattern
   ↓
4. If pattern.has_sizes:
   → Render size selector (required)
   Else:
   → Remove size selector
   ↓
5. User selects size (if required)
   ↓
6. Validate via API
   ↓
7. Update price and enable cart button
```

---

## 🎨 UX REQUIREMENTS

### Visual Indicators

1. **Required Fields:**
   ```html
   <div class="variant-label">
     <i class="fas fa-ruler"></i> اختر المقاس 
     <span style="color: red;">*</span>
   </div>
   ```

2. **Button States:**
   - Valid selection: `أضف إلى السلة` (enabled)
   - Missing size: `اختر المقاس` (disabled)
   - Invalid combo: `غير متاح` (disabled)

3. **Price Display:**
   - Show size-specific price in parentheses
   - Update main price on selection

4. **Messages:**
   - Warning (yellow): "يجب اختيار مقاس"
   - Error (red): "هذا التركيب غير متوفر"
   - Info (blue): General information

---

## 📊 SUPPORTED SCENARIOS

### Scenario 1: Simple Product
```
Product: كتاب
- No patterns
- No sizes
- base_price: 50.00 ج.م

User Flow:
1. Page loads → Price: 50.00 ج.م
2. Add to Cart enabled immediately
```

### Scenario 2: Size-Based Product
```
Product: قميص بسيط
- No patterns
- has_product_level_sizes: true
- ProductSize:
  - S: 100.00 ج.م
  - M: 120.00 ج.م
  - L: 140.00 ج.م

User Flow:
1. Page loads → Shows size selector (required)
2. User selects M → Price: 120.00 ج.م
3. Add to Cart enabled
```

### Scenario 3: Pattern Without Sizes
```
Product: حقيبة
- has_patterns: true
- Pattern "جلد": base_price: 500.00 ج.م, has_sizes: false
- Pattern "قماش": base_price: 300.00 ج.م, has_sizes: false

User Flow:
1. Page loads → Shows pattern selector
2. User selects "جلد" → Price: 500.00 ج.م
3. No size selector shown
4. Add to Cart enabled
```

### Scenario 4: Pattern With Sizes
```
Product: حذاء رياضي
- has_patterns: true
- Pattern "كلاسيك":
  - has_sizes: true
  - PatternSize:
    - 40: 400.00 ج.م
    - 41: 420.00 ج.م
    - 42: 440.00 ج.م

User Flow:
1. Page loads → Shows pattern selector
2. User selects "كلاسيك" → Size selector appears (required)
3. User selects 41 → Price: 420.00 ج.م
4. Add to Cart enabled
```

### Scenario 5: Mixed Patterns
```
Product: جاكيت
- has_patterns: true
- Pattern "شتوي": has_sizes: true (S, M, L with prices)
- Pattern "صيفي": has_sizes: false, base_price: 200.00 ج.م

User Flow A (شتوي):
1. Select "شتوي" → Size selector appears
2. Select M → Price from PatternSize
3. Add to Cart enabled

User Flow B (صيفي):
1. Select "صيفي" → No size selector
2. Price: 200.00 ج.م
3. Add to Cart enabled
```

---

## 🔄 MIGRATION STRATEGY

### Phase 1: Add New Fields (Non-Breaking)

```python
# Migration 1: Add new fields to existing models
python manage.py makemigrations

# Generated migration:
class Migration:
    operations = [
        migrations.AddField('Product', 'base_price', default=0),
        migrations.AddField('Product', 'has_patterns', default=False),
        migrations.AddField('Product', 'has_product_level_sizes', default=False),
        migrations.AddField('Pattern', 'base_price', null=True),
        migrations.AddField('Pattern', 'has_sizes', default=False),
    ]
```

### Phase 2: Create New Models

```python
# Migration 2: Create ProductSize and PatternSize
class Migration:
    operations = [
        migrations.CreateModel('ProductSize', ...),
        migrations.CreateModel('PatternSize', ...),
    ]
```

### Phase 3: Data Migration

```python
# Migration 3: Migrate existing data
def migrate_existing_variants(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    ProductVariant = apps.get_model('products', 'ProductVariant')
    
    for product in Product.objects.all():
        # Analyze existing variants
        variants = ProductVariant.objects.filter(product=product)
        
        # Set configuration flags
        has_patterns = variants.filter(pattern__isnull=False).exists()
        has_sizes = variants.filter(size__isnull=False).exists()
        
        product.has_patterns = has_patterns
        product.has_product_level_sizes = has_sizes and not has_patterns
        product.base_price = product.price  # Migrate old price field
        product.save()
```

### Phase 4: Remove Old Price Field from ProductVariant

```python
# Migration 4: Remove price from ProductVariant
class Migration:
    operations = [
        migrations.RemoveField('ProductVariant', 'price'),
    ]
```

### Rollback Plan

Keep old `ProductVariant.price` field for 2 weeks:
1. Deploy new system
2. Monitor for issues
3. If stable → run Migration 4
4. If issues → revert and fix

---

## ⚠️ EDGE CASES HANDLING

### 1. Pattern Without Sizes Selected
```python
# Backend validation
if pattern.has_sizes and not size_id:
    return {
        'valid': False,
        'message': f'يجب اختيار مقاس للنمط {pattern.name}'
    }
```

### 2. Size Without Pattern (Invalid)
```python
# Frontend prevents this
if config.has_patterns and !selection.pattern:
    // Don't show size selector
```

### 3. Out of Stock
```python
# API returns available=False
{
    "available": false,
    "stock": 0,
    "message": "هذا المقاس غير متوفر حالياً"
}
```

### 4. Invalid Combination
```python
# No variant exists
variant = ProductVariant.objects.filter(...).first()
if not variant:
    return {'available': False}
```

### 5. Missing Required Selection
```python
# Frontend disables button
if validation.requiresSize and !selection.size:
    addToCartBtn.disabled = true
    addToCartBtn.innerHTML = 'اختر المقاس'
```

---

## 🧪 TESTING CHECKLIST

### Unit Tests

```python
# tests/test_models.py

def test_price_resolution_hierarchy():
    """Test PatternSize > ProductSize > Pattern > Product"""
    product = Product.objects.create(base_price=100)
    pattern = Pattern.objects.create(product=product, base_price=150)
    size = Size.objects.create(name='M')
    
    # Test 1: Product base price
    assert product.get_price() == 100
    
    # Test 2: Pattern base price
    assert product.get_price(pattern_id=pattern.id) == 150
    
    # Test 3: ProductSize price
    ProductSize.objects.create(product=product, size=size, price=120)
    assert product.get_price(size_id=size.id) == 120
    
    # Test 4: PatternSize price (highest priority)
    PatternSize.objects.create(pattern=pattern, size=size, price=180)
    assert product.get_price(pattern_id=pattern.id, size_id=size.id) == 180

def test_validation_logic():
    """Test conditional size requirements"""
    product = Product.objects.create(has_patterns=True)
    pattern_with_sizes = Pattern.objects.create(
        product=product, has_sizes=True
    )
    pattern_without_sizes = Pattern.objects.create(
        product=product, has_sizes=False
    )
    
    # Test 1: Pattern with sizes requires size
    result = validate_selection(product, pattern_with_sizes.id, None)
    assert result['valid'] == False
    assert 'مقاس' in result['message']
    
    # Test 2: Pattern without sizes doesn't require size
    result = validate_selection(product, pattern_without_sizes.id, None)
    assert result['valid'] == True
```

### Integration Tests

```python
# tests/test_api.py

def test_product_config_endpoint():
    """Test /api/product-config/ returns correct structure"""
    response = client.get(f'/api/product-config/{product.id}/')
    data = response.json()
    
    assert data['success'] == True
    assert 'configuration_type' in data
    assert 'patterns' in data
    assert 'product_sizes' in data

def test_variant_price_validation():
    """Test /api/variant-price/ validates correctly"""
    # Missing required size
    response = client.get(f'/api/variant-price/?product_id={product.id}&pattern_id={pattern.id}')
    data = response.json()
    
    assert data['validation']['valid'] == False
    assert data['available'] == False
```

### Frontend Tests

```javascript
// tests/variant-selector.test.js

test('renders size selector when pattern has sizes', async () => {
    const selector = new FlexibleVariantSelector();
    await selector.loadProductConfig();
    
    // Select pattern with sizes
    await selector.handlePatternClick(patternWithSizes);
    
    const sizeGroup = document.getElementById('group-size');
    expect(sizeGroup).toBeInTheDocument();
});

test('hides size selector when pattern has no sizes', async () => {
    const selector = new FlexibleVariantSelector();
    
    // Select pattern without sizes
    await selector.handlePatternClick(patternWithoutSizes);
    
    const sizeGroup = document.getElementById('group-size');
    expect(sizeGroup).not.toBeInTheDocument();
});
```

---

## 📈 PERFORMANCE CONSIDERATIONS

### Database Queries

**Before (N+1 Problem):**
```python
for variant in variants:
    print(variant.pattern.name)  # N queries
    print(variant.size.name)      # N queries
```

**After (Optimized):**
```python
variants = ProductVariant.objects.select_related(
    'pattern', 'size', 'color'
).filter(product=product)
```

### Caching Strategy

```python
from django.core.cache import cache

def get_product_config(request, product_id):
    cache_key = f'product_config_{product_id}'
    config = cache.get(cache_key)
    
    if not config:
        # Generate config
        config = {...}
        cache.set(cache_key, config, 300)  # 5 minutes
    
    return JsonResponse(config)
```

### Frontend Optimization

```javascript
// Debounce validation calls
const debouncedValidate = debounce(
    () => this.validateAndUpdatePrice(),
    300
);
```

---

## 🚀 DEPLOYMENT CHECKLIST

- [ ] Run migrations on staging
- [ ] Test all product types
- [ ] Verify price calculations
- [ ] Test cart integration
- [ ] Check mobile responsiveness
- [ ] Load test API endpoints
- [ ] Monitor error logs
- [ ] Backup database before production deploy
- [ ] Deploy to production
- [ ] Monitor for 24 hours
- [ ] Remove old price field (after 2 weeks)

---

## 📚 URL ROUTES

```python
# project/urls.py

urlpatterns = [
    # New flexible variant endpoints
    path('api/product-config/<int:product_id>/', 
         get_product_config, 
         name='get_product_config'),
    
    path('api/variant-price/', 
         get_variant_price, 
         name='get_variant_price'),
    
    path('api/variant-options/<int:product_id>/', 
         get_variant_options, 
         name='get_variant_options'),
    
    # Existing endpoints
    path('api/product-images/<int:product_id>/<int:color_id>/', 
         product_images_by_color, 
         name='product_images_by_color'),
]
```

---

## 🎓 SUMMARY

This flexible variant system provides:

✅ **Multi-level pricing** with clear hierarchy
✅ **Conditional requirements** enforced by backend
✅ **Clean architecture** with no data duplication
✅ **Scalable design** supporting all product types
✅ **Stock-aware filtering** at all levels
✅ **Production-ready** with migration strategy

**Key Innovation:** Price calculated dynamically instead of stored redundantly, enabling flexible pricing models without schema changes.
