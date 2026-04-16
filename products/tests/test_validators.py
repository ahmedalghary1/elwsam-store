"""
Unit Tests for Product Validation System
Tests all validation logic for variants, cart operations, and authentication.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from products.models import (
    Category, Product, Pattern, PatternSize, Color, Size,
    Type, ProductColor, ProductSize, ProductType, ProductTypeColor, ProductVariant
)
from products.validators import VariantValidator, CartValidator, AuthValidator


class VariantValidatorTestCase(TestCase):
    """Test VariantValidator class"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=100.00
        )
        
        # Create pattern
        self.pattern = Pattern.objects.create(
            product=self.product,
            name='Pattern 1',
            has_sizes=True,
            order=1
        )
        
        # Create sizes
        self.size_s = Size.objects.create(name='S')
        self.size_m = Size.objects.create(name='M')
        
        # Create pattern sizes
        self.pattern_size_s = PatternSize.objects.create(
            pattern=self.pattern,
            size=self.size_s,
            price=120.00,
            stock=10
        )
        
        # Create color
        self.color = Color.objects.create(name='Red', code='#FF0000')
        ProductColor.objects.create(product=self.product, color=self.color)
        
        # Create variant
        self.variant = ProductVariant.objects.create(
            product=self.product,
            pattern=self.pattern,
            color=self.color,
            size=self.size_s,
            price=120.00,
            stock=10
        )
    
    def test_validate_pattern_required(self):
        """Test that pattern is required when product has patterns"""
        result = VariantValidator.validate_variant_selection(
            self.product,
            pattern_id=None,
            color_id=self.color.id,
            size_id=self.size_s.id
        )
        
        self.assertFalse(result['valid'])
        self.assertEqual(result['field'], 'pattern')
        self.assertIn('pattern', result['errors'])
        self.assertEqual(result['errors']['pattern'], 'يجب اختيار النمط أولاً')
    
    def test_validate_size_required_for_pattern(self):
        """Test that size is required when pattern has sizes"""
        result = VariantValidator.validate_variant_selection(
            self.product,
            pattern_id=self.pattern.id,
            color_id=self.color.id,
            size_id=None
        )
        
        self.assertFalse(result['valid'])
        self.assertEqual(result['field'], 'size')
        self.assertIn('size', result['errors'])
        self.assertEqual(result['errors']['size'], 'يجب اختيار المقاس لهذا النمط')
    
    def test_validate_color_required(self):
        """Test that color is required when product has colors"""
        result = VariantValidator.validate_variant_selection(
            self.product,
            pattern_id=self.pattern.id,
            color_id=None,
            size_id=self.size_s.id
        )
        
        self.assertFalse(result['valid'])
        self.assertEqual(result['field'], 'color')
        self.assertIn('color', result['errors'])
        self.assertEqual(result['errors']['color'], 'يجب اختيار اللون')
    
    def test_validate_valid_selection(self):
        """Test valid selection passes validation"""
        result = VariantValidator.validate_variant_selection(
            self.product,
            pattern_id=self.pattern.id,
            color_id=self.color.id,
            size_id=self.size_s.id
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['message'], '')
        self.assertIsNone(result['field'])
        self.assertEqual(result['errors'], {})
    
    def test_validate_invalid_pattern(self):
        """Test validation fails for non-existent pattern"""
        result = VariantValidator.validate_variant_selection(
            self.product,
            pattern_id=9999,
            color_id=self.color.id,
            size_id=self.size_s.id
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('pattern', result['errors'])
        self.assertEqual(result['errors']['pattern'], 'النمط المحدد غير موجود')
    
    def test_validate_invalid_color(self):
        """Test validation fails for color not belonging to product"""
        other_color = Color.objects.create(name='Blue', code='#0000FF')
        
        result = VariantValidator.validate_variant_selection(
            self.product,
            pattern_id=self.pattern.id,
            color_id=other_color.id,
            size_id=self.size_s.id
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('color', result['errors'])
        self.assertEqual(result['errors']['color'], 'اللون المحدد غير متوفر لهذا المنتج')
    
    def test_validate_invalid_type(self):
        """Test validation fails for type not belonging to product"""
        product_type = Type.objects.create(name='Classic')
        other_product = Product.objects.create(
            name='Other Product',
            slug='other-product',
            category=self.category,
            price=120.00
        )
        ProductType.objects.create(
            product=other_product,
            type=product_type,
            price=150.00,
            description='Classic type',
            image='product-types/classic.png'
        )

        result = VariantValidator.validate_variant_selection(
            self.product,
            pattern_id=self.pattern.id,
            color_id=self.color.id,
            size_id=self.size_s.id,
            type_id=product_type.id
        )

        self.assertFalse(result['valid'])
        self.assertIn('type', result['errors'])

    def test_validate_color_must_belong_to_selected_type(self):
        """Test validation fails when color is not linked to selected product type."""
        product_type = Type.objects.create(name='Classic')
        ProductType.objects.create(
            product=self.product,
            type=product_type,
            price=150.00,
            description='Classic type',
            image='product-types/classic.png'
        )
        allowed_color = Color.objects.create(name='Black', code='#111111')
        ProductTypeColor.objects.create(
            product_type=ProductType.objects.get(product=self.product, type=product_type),
            color=allowed_color
        )

        result = VariantValidator.validate_variant_selection(
            self.product,
            pattern_id=self.pattern.id,
            color_id=self.color.id,
            size_id=self.size_s.id,
            type_id=product_type.id
        )

        self.assertFalse(result['valid'])
        self.assertIn('color', result['errors'])

    def test_validate_stock_availability_in_stock(self):
        """Test stock validation for available variant"""
        result = VariantValidator.validate_stock_availability(self.variant.id, quantity=5)
        
        self.assertTrue(result['available'])
        self.assertEqual(result['stock'], 10)
        self.assertEqual(result['message'], 'متوفر')
    
    def test_validate_stock_availability_out_of_stock(self):
        """Test stock validation for out of stock variant"""
        self.variant.stock = 0
        self.variant.save()
        
        result = VariantValidator.validate_stock_availability(self.variant.id, quantity=1)
        
        self.assertFalse(result['available'])
        self.assertEqual(result['stock'], 0)
        self.assertEqual(result['message'], 'المنتج غير متوفر حالياً')
    
    def test_validate_stock_availability_insufficient(self):
        """Test stock validation for insufficient stock"""
        result = VariantValidator.validate_stock_availability(self.variant.id, quantity=15)
        
        self.assertFalse(result['available'])
        self.assertEqual(result['stock'], 10)
        self.assertIn('10 قطعة', result['message'])
    
    def test_get_variant_or_validate_success(self):
        """Test getting variant with valid selection"""
        variant, validation = VariantValidator.get_variant_or_validate(
            self.product.id,
            pattern_id=self.pattern.id,
            color_id=self.color.id,
            size_id=self.size_s.id
        )
        
        self.assertIsNotNone(variant)
        self.assertEqual(variant.id, self.variant.id)
        self.assertTrue(validation['valid'])
    
    def test_get_variant_or_validate_invalid_selection(self):
        """Test getting variant with invalid selection"""
        variant, validation = VariantValidator.get_variant_or_validate(
            self.product.id,
            pattern_id=None,
            color_id=self.color.id,
            size_id=self.size_s.id
        )
        
        self.assertIsNone(variant)
        self.assertFalse(validation['valid'])
        self.assertIn('pattern', validation['errors'])
    
    def test_get_variant_or_validate_out_of_stock(self):
        """Test getting variant that is out of stock"""
        self.variant.stock = 0
        self.variant.save()
        
        variant, validation = VariantValidator.get_variant_or_validate(
            self.product.id,
            pattern_id=self.pattern.id,
            color_id=self.color.id,
            size_id=self.size_s.id
        )
        
        self.assertIsNone(variant)
        self.assertFalse(validation['valid'])
        self.assertIn('stock', validation['errors'])

    def test_get_variant_or_validate_allows_type_color_without_variant_row(self):
        """Type/color selections should stay valid even without a dedicated ProductVariant row."""
        product = Product.objects.create(
            name='Typed Only Product',
            slug='typed-only-product',
            category=self.category,
            price=90.00
        )
        product_type = Type.objects.create(name='Modern')
        ProductType.objects.create(
            product=product,
            type=product_type,
            price=110.00,
            description='Modern type',
            image='product-types/modern.png'
        )
        color = Color.objects.create(name='Olive', code='#556b2f')
        ProductTypeColor.objects.create(
            product_type=ProductType.objects.get(product=product, type=product_type),
            color=color
        )

        variant, validation = VariantValidator.get_variant_or_validate(
            product.id,
            pattern_id=None,
            color_id=color.id,
            size_id=None,
            type_id=product_type.id
        )

        self.assertIsNone(variant)
        self.assertTrue(validation['valid'])

    def test_get_variant_or_validate_ignores_legacy_color_variant_for_type_selection(self):
        """Type/color selections should not be rejected by old color-only ProductVariant rows."""
        product = Product.objects.create(
            name='Typed Variant Product',
            slug='typed-variant-product',
            category=self.category,
            price=90.00,
            is_active=True
        )
        type_catalog = Type.objects.create(name='Classic')
        product_type = ProductType.objects.create(
            product=product,
            type=type_catalog,
            price=110.00,
            description='Classic type',
            image='product-types/classic.png'
        )
        color = Color.objects.create(name='Black', code='#111111')
        ProductTypeColor.objects.create(product_type=product_type, color=color)
        ProductVariant.objects.create(
            product=product,
            color=color,
            price=90.00,
            stock=0
        )

        variant, validation = VariantValidator.get_variant_or_validate(
            product.id,
            color_id=color.id,
            type_id=type_catalog.id
        )

        self.assertIsNone(variant)
        self.assertTrue(validation['valid'])


class CartValidatorTestCase(TestCase):
    """Test CartValidator class"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=100.00
        )
        
        self.pattern = Pattern.objects.create(
            product=self.product,
            name='Pattern 1',
            has_sizes=False,
            base_price=100.00
        )
        
        self.color = Color.objects.create(name='Red', code='#FF0000')
        ProductColor.objects.create(product=self.product, color=self.color)
        
        self.variant = ProductVariant.objects.create(
            product=self.product,
            pattern=self.pattern,
            color=self.color,
            price=100.00,
            stock=10
        )
    
    def test_validate_add_to_cart_valid(self):
        """Test valid add to cart"""
        result = CartValidator.validate_add_to_cart(
            self.product.id,
            variant_id=self.variant.id,
            quantity=2
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['errors'], {})
    
    def test_validate_add_to_cart_invalid_quantity(self):
        """Test add to cart with invalid quantity"""
        result = CartValidator.validate_add_to_cart(
            self.product.id,
            variant_id=self.variant.id,
            quantity=0
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('quantity', result['errors'])
    
    def test_validate_add_to_cart_excessive_quantity(self):
        """Test add to cart with quantity > 100"""
        result = CartValidator.validate_add_to_cart(
            self.product.id,
            variant_id=self.variant.id,
            quantity=150
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('quantity', result['errors'])
        self.assertIn('100', result['errors']['quantity'])
    
    def test_validate_add_to_cart_missing_variant(self):
        """Test add to cart without variant when required"""
        result = CartValidator.validate_add_to_cart(
            self.product.id,
            variant_id=None,
            quantity=1
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('variant', result['errors'])
    
    def test_validate_add_to_cart_insufficient_stock(self):
        """Test add to cart with insufficient stock"""
        result = CartValidator.validate_add_to_cart(
            self.product.id,
            variant_id=self.variant.id,
            quantity=15
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('stock', result['errors'])
    
    def test_validate_add_to_cart_invalid_product(self):
        """Test add to cart with non-existent product"""
        result = CartValidator.validate_add_to_cart(
            product_id=9999,
            variant_id=self.variant.id,
            quantity=1
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('product', result['errors'])


class AuthValidatorTestCase(TestCase):
    """Test AuthValidator class"""
    
    def test_validate_login_valid(self):
        """Test valid login credentials"""
        result = AuthValidator.validate_login_credentials('testuser', 'password123')
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['errors'], {})
    
    def test_validate_login_missing_username(self):
        """Test login with missing username"""
        result = AuthValidator.validate_login_credentials('', 'password123')
        
        self.assertFalse(result['valid'])
        self.assertIn('username', result['errors'])
    
    def test_validate_login_missing_password(self):
        """Test login with missing password"""
        result = AuthValidator.validate_login_credentials('testuser', '')
        
        self.assertFalse(result['valid'])
        self.assertIn('password', result['errors'])
    
    def test_validate_login_username_too_long(self):
        """Test login with username > 150 chars"""
        long_username = 'a' * 151
        result = AuthValidator.validate_login_credentials(long_username, 'password123')
        
        self.assertFalse(result['valid'])
        self.assertIn('username', result['errors'])
    
    def test_validate_registration_valid(self):
        """Test valid registration data"""
        result = AuthValidator.validate_registration(
            'testuser',
            'test@example.com',
            'password123',
            'password123'
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['errors'], {})
    
    def test_validate_registration_short_username(self):
        """Test registration with username < 3 chars"""
        result = AuthValidator.validate_registration(
            'ab',
            'test@example.com',
            'password123',
            'password123'
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('username', result['errors'])
    
    def test_validate_registration_invalid_email(self):
        """Test registration with invalid email"""
        result = AuthValidator.validate_registration(
            'testuser',
            'invalid-email',
            'password123',
            'password123'
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('email', result['errors'])
    
    def test_validate_registration_short_password(self):
        """Test registration with password < 8 chars"""
        result = AuthValidator.validate_registration(
            'testuser',
            'test@example.com',
            'pass',
            'pass'
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('password', result['errors'])
    
    def test_validate_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        result = AuthValidator.validate_registration(
            'testuser',
            'test@example.com',
            'password123',
            'password456'
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('password_confirm', result['errors'])


class ProductSizeBasedValidationTestCase(TestCase):
    """Test validation for size-based products (no patterns)"""
    
    def setUp(self):
        """Set up size-based product"""
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Size Product',
            slug='size-product',
            category=self.category,
            price=100.00
        )
        
        # Create product-level sizes
        self.size_s = Size.objects.create(name='S')
        self.size_m = Size.objects.create(name='M')
        
        ProductSize.objects.create(product=self.product, size=self.size_s, price=100.00)
        ProductSize.objects.create(product=self.product, size=self.size_m, price=110.00)
        
        # Create color
        self.color = Color.objects.create(name='Blue', code='#0000FF')
        ProductColor.objects.create(product=self.product, color=self.color)
        
        # Create variant
        self.variant = ProductVariant.objects.create(
            product=self.product,
            color=self.color,
            size=self.size_s,
            price=100.00,
            stock=5
        )
    
    def test_validate_size_required_for_size_based_product(self):
        """Test that size is required for size-based products"""
        result = VariantValidator.validate_variant_selection(
            self.product,
            pattern_id=None,
            color_id=self.color.id,
            size_id=None
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('size', result['errors'])
        self.assertEqual(result['errors']['size'], 'يجب اختيار المقاس')
    
    def test_validate_valid_size_based_selection(self):
        """Test valid selection for size-based product"""
        result = VariantValidator.validate_variant_selection(
            self.product,
            pattern_id=None,
            color_id=self.color.id,
            size_id=self.size_s.id
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['errors'], {})


class SimpleProductValidationTestCase(TestCase):
    """Test validation for simple products (no patterns, no sizes)"""
    
    def setUp(self):
        """Set up simple product"""
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Simple Product',
            slug='simple-product',
            category=self.category,
            price=50.00
        )
        
        # Create variant without pattern or size
        self.variant = ProductVariant.objects.create(
            product=self.product,
            price=50.00,
            stock=20
        )
    
    def test_validate_simple_product(self):
        """Test validation for simple product"""
        result = VariantValidator.validate_variant_selection(
            self.product,
            pattern_id=None,
            color_id=None,
            size_id=None
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['errors'], {})
