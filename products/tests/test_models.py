# Unit tests for multi-level pricing and validation

from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from products.models import (
    Product, Category, Pattern, Size, Type, ProductSize, ProductType,
    PatternSize, ProductVariant, Color
)


class ProductPriceResolutionTestCase(TestCase):
    """Test multi-level price resolution hierarchy"""
    
    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=Decimal('100.00')
        )
        self.pattern = Pattern.objects.create(
            product=self.product,
            name='Test Pattern',
            has_sizes=True
        )
        self.size = Size.objects.create(name='M')
    
    def test_base_price_fallback(self):
        """Test that product base price is returned when no other prices exist"""
        price = self.product.get_price()
        self.assertEqual(price, Decimal('100.00'))
    
    def test_pattern_base_price(self):
        """Test that pattern base price overrides product base price"""
        self.pattern.base_price = Decimal('150.00')
        self.pattern.save()
        
        price = self.product.get_price(pattern_id=self.pattern.id)
        self.assertEqual(price, Decimal('150.00'))
    
    def test_product_size_price(self):
        """Test that product-level size price overrides pattern base price"""
        self.pattern.base_price = Decimal('150.00')
        self.pattern.save()
        
        product_size = ProductSize.objects.create(
            product=self.product,
            size=self.size,
            price=Decimal('120.00')
        )
        
        price = self.product.get_price(size_id=self.size.id)
        self.assertEqual(price, Decimal('120.00'))
    
    def test_pattern_size_price_highest_priority(self):
        """Test that pattern-size price has highest priority"""
        self.pattern.base_price = Decimal('150.00')
        self.pattern.save()
        
        ProductSize.objects.create(
            product=self.product,
            size=self.size,
            price=Decimal('120.00')
        )
        
        pattern_size = PatternSize.objects.create(
            pattern=self.pattern,
            size=self.size,
            price=Decimal('180.00'),
            stock=10
        )
        
        price = self.product.get_price(
            pattern_id=self.pattern.id,
            size_id=self.size.id
        )
        self.assertEqual(price, Decimal('180.00'))
    
    def test_price_hierarchy_complete(self):
        """Test complete price hierarchy with all levels"""
        # Set up all price levels
        self.pattern.base_price = Decimal('150.00')
        self.pattern.save()
        
        ProductSize.objects.create(
            product=self.product,
            size=self.size,
            price=Decimal('120.00')
        )
        
        PatternSize.objects.create(
            pattern=self.pattern,
            size=self.size,
            price=Decimal('180.00'),
            stock=10
        )
        
        # Test each level
        self.assertEqual(
            self.product.get_price(),
            Decimal('100.00'),
            "Base price should be 100"
        )
        
        self.assertEqual(
            self.product.get_price(pattern_id=self.pattern.id),
            Decimal('150.00'),
            "Pattern base price should be 150"
        )
        
        self.assertEqual(
            self.product.get_price(size_id=self.size.id),
            Decimal('120.00'),
            "Product size price should be 120"
        )
        
        self.assertEqual(
            self.product.get_price(
                pattern_id=self.pattern.id,
                size_id=self.size.id
            ),
            Decimal('180.00'),
            "Pattern size price should be 180 (highest priority)"
        )


class PatternValidationTestCase(TestCase):
    """Test pattern validation rules"""
    
    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=Decimal('100.00')
        )
    
    def test_pattern_requires_size_or_base_price(self):
        """Test that pattern must have either sizes or base price"""
        pattern = Pattern(
            product=self.product,
            name='Invalid Pattern',
            has_sizes=False,
            base_price=None
        )
        
        with self.assertRaises(ValidationError):
            pattern.clean()
    
    def test_pattern_with_sizes_valid(self):
        """Test that pattern with sizes is valid without base price"""
        pattern = Pattern(
            product=self.product,
            name='Valid Pattern',
            has_sizes=True,
            base_price=None
        )
        
        # Should not raise ValidationError
        pattern.clean()
    
    def test_pattern_with_base_price_valid(self):
        """Test that pattern with base price is valid without sizes"""
        pattern = Pattern(
            product=self.product,
            name='Valid Pattern',
            has_sizes=False,
            base_price=Decimal('150.00')
        )
        
        # Should not raise ValidationError
        pattern.clean()
    
    def test_pattern_requires_size_selection(self):
        """Test requires_size_selection method"""
        pattern_with_sizes = Pattern.objects.create(
            product=self.product,
            name='Pattern With Sizes',
            has_sizes=True
        )
        
        pattern_without_sizes = Pattern.objects.create(
            product=self.product,
            name='Pattern Without Sizes',
            has_sizes=False,
            base_price=Decimal('150.00')
        )
        
        self.assertTrue(pattern_with_sizes.requires_size_selection())
        self.assertFalse(pattern_without_sizes.requires_size_selection())


class ProductVariantTestCase(TestCase):
    """Test product variant functionality"""
    
    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=Decimal('100.00')
        )
        self.pattern = Pattern.objects.create(
            product=self.product,
            name='Test Pattern',
            has_sizes=True
        )
        self.size = Size.objects.create(name='M')
        self.color = Color.objects.create(name='Red', code='#ff0000')
        
        PatternSize.objects.create(
            pattern=self.pattern,
            size=self.size,
            price=Decimal('180.00'),
            stock=10
        )
    
    def test_variant_get_price_uses_hierarchy(self):
        """Test that variant.get_price() uses Product.get_price() hierarchy"""
        variant = ProductVariant.objects.create(
            product=self.product,
            pattern=self.pattern,
            color=self.color,
            size=self.size,
            price=Decimal('999.99'),  # Deprecated field
            stock=5
        )
        
        # Should return price from hierarchy, not deprecated field
        price = variant.get_price()
        self.assertEqual(price, Decimal('180.00'))
        self.assertNotEqual(price, Decimal('999.99'))
    
    def test_variant_is_available(self):
        """Test variant availability check"""
        variant_in_stock = ProductVariant.objects.create(
            product=self.product,
            pattern=self.pattern,
            color=self.color,
            size=self.size,
            price=Decimal('180.00'),
            stock=5
        )
        
        variant_out_of_stock = ProductVariant.objects.create(
            product=self.product,
            pattern=self.pattern,
            size=self.size,
            price=Decimal('180.00'),
            stock=0
        )
        
        self.assertTrue(variant_in_stock.is_available())
        self.assertFalse(variant_out_of_stock.is_available())
    
    def test_variant_validation_pattern_requires_size(self):
        """Test that variant validation enforces pattern size requirement"""
        variant = ProductVariant(
            product=self.product,
            pattern=self.pattern,  # has_sizes=True
            color=self.color,
            size=None,  # Missing required size
            price=Decimal('180.00'),
            stock=5
        )
        
        with self.assertRaises(ValidationError):
            variant.clean()
    
    def test_variant_str_representation(self):
        """Test variant string representation"""
        variant = ProductVariant.objects.create(
            product=self.product,
            pattern=self.pattern,
            color=self.color,
            size=self.size,
            price=Decimal('180.00'),
            stock=5
        )
        
        expected = f"{self.product.name} - {self.pattern.name} - {self.color.name} - {self.size.name}"
        self.assertEqual(str(variant), expected)


class PatternSizeTestCase(TestCase):
    """Test PatternSize model"""
    
    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=Decimal('100.00')
        )
        self.pattern = Pattern.objects.create(
            product=self.product,
            name='Test Pattern',
            has_sizes=True
        )
        self.size = Size.objects.create(name='M')
    
    def test_pattern_size_is_available(self):
        """Test PatternSize availability check"""
        ps_in_stock = PatternSize.objects.create(
            pattern=self.pattern,
            size=self.size,
            price=Decimal('180.00'),
            stock=10
        )
        
        ps_out_of_stock = PatternSize.objects.create(
            pattern=self.pattern,
            size=Size.objects.create(name='L'),
            price=Decimal('190.00'),
            stock=0
        )
        
        self.assertTrue(ps_in_stock.is_available())
        self.assertFalse(ps_out_of_stock.is_available())
    
    def test_pattern_size_unique_constraint(self):
        """Test that pattern-size combination is unique"""
        PatternSize.objects.create(
            pattern=self.pattern,
            size=self.size,
            price=Decimal('180.00'),
            stock=10
        )
        
        # Attempting to create duplicate should raise error
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            PatternSize.objects.create(
                pattern=self.pattern,
                size=self.size,
                price=Decimal('190.00'),
                stock=5
            )


class ProductTypeTestCase(TestCase):
    """Test ProductType model and price resolution"""

    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Typed Product',
            category=self.category,
            price=Decimal('100.00')
        )
        self.type = Type.objects.create(name='Classic')

    def test_product_type_overrides_base_price(self):
        """Selected product type should override the base product price"""
        product_type = ProductType.objects.create(
            product=self.product,
            type=self.type,
            price=Decimal('145.00'),
            description='Classic product type',
            image='product-types/classic.png'
        )

        price = self.product.get_price(type_id=self.type.id)
        self.assertEqual(price, Decimal('145.00'))
        self.assertEqual(product_type.type.name, 'Classic')

    def test_product_type_relation_check(self):
        """Product should detect related product types"""
        self.assertFalse(self.product.check_if_has_product_types())

        ProductType.objects.create(
            product=self.product,
            type=self.type,
            price=Decimal('145.00'),
            description='Classic product type',
            image='product-types/classic.png'
        )

        self.assertTrue(self.product.check_if_has_product_types())
