# Integration tests for variant API endpoints

from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
import json

from products.models import (
    Product, Category, Pattern, Size, Type, ProductSize, ProductType,
    PatternSize, ProductVariant, Color, ProductColor
)


class ProductConfigAPITestCase(TestCase):
    """Test /api/product-config/ endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=Decimal('100.00'),
            is_active=True
        )
    
    def test_simple_product_config(self):
        """Test configuration for simple product (no variants)"""
        url = f'/api/product-config/{self.product.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['configuration_type'], 'simple')
        self.assertEqual(len(data['patterns']), 0)
        self.assertEqual(len(data['product_sizes']), 0)
        self.assertFalse(data['has_patterns'])
        self.assertFalse(data['has_product_level_sizes'])
    
    def test_size_based_product_config(self):
        """Test configuration for size-based product"""
        size_s = Size.objects.create(name='S')
        size_m = Size.objects.create(name='M')
        
        ProductSize.objects.create(
            product=self.product,
            size=size_s,
            price=Decimal('100.00')
        )
        ProductSize.objects.create(
            product=self.product,
            size=size_m,
            price=Decimal('120.00')
        )
        
        url = f'/api/product-config/{self.product.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['configuration_type'], 'size_based')
        self.assertEqual(len(data['product_sizes']), 2)
        self.assertTrue(data['has_product_level_sizes'])

    def test_product_types_are_included_in_config(self):
        """Test product types are returned by product config endpoint"""
        product_type = Type.objects.create(name='Classic')
        ProductType.objects.create(
            product=self.product,
            type=product_type,
            price=Decimal('140.00'),
            description='Classic type description',
            image='product-types/classic.png'
        )

        url = f'/api/product-config/{self.product.id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data['has_product_types'])
        self.assertEqual(len(data['product_types']), 1)
        self.assertEqual(data['product_types'][0]['name'], 'Classic')
        self.assertEqual(data['product_types'][0]['price'], '140.00')
        self.assertEqual(data['product_types'][0]['description'], 'Classic type description')
    
    def test_pattern_based_product_config(self):
        """Test configuration for pattern-based product"""
        pattern1 = Pattern.objects.create(
            product=self.product,
            name='Pattern 1',
            has_sizes=True
        )
        pattern2 = Pattern.objects.create(
            product=self.product,
            name='Pattern 2',
            has_sizes=False,
            base_price=Decimal('150.00')
        )
        
        size_m = Size.objects.create(name='M')
        PatternSize.objects.create(
            pattern=pattern1,
            size=size_m,
            price=Decimal('180.00'),
            stock=10
        )
        
        url = f'/api/product-config/{self.product.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['configuration_type'], 'pattern_based')
        self.assertEqual(len(data['patterns']), 2)
        self.assertTrue(data['has_patterns'])
        
        # Check pattern 1 (with sizes)
        p1_data = next(p for p in data['patterns'] if p['id'] == pattern1.id)
        self.assertTrue(p1_data['has_sizes'])
        self.assertEqual(len(p1_data['sizes']), 1)
        
        # Check pattern 2 (without sizes)
        p2_data = next(p for p in data['patterns'] if p['id'] == pattern2.id)
        self.assertFalse(p2_data['has_sizes'])
        self.assertEqual(p2_data['base_price'], '150.00')
    
    def test_config_caching(self):
        """Test that config is cached"""
        url = f'/api/product-config/{self.product.id}/'
        
        # First request
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, 200)
        
        # Second request (should be cached)
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, 200)
        
        # Both should return same data
        self.assertEqual(response1.json(), response2.json())


class VariantOptionsAPITestCase(TestCase):
    """Test /api/variant-options/ endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=Decimal('100.00'),
            is_active=True
        )
        
        self.pattern = Pattern.objects.create(
            product=self.product,
            name='Test Pattern',
            has_sizes=True
        )
        
        self.size_m = Size.objects.create(name='M')
        self.size_l = Size.objects.create(name='L')
        
        self.color_red = Color.objects.create(name='Red', code='#ff0000')
        self.color_blue = Color.objects.create(name='Blue', code='#0000ff')
        
        # Create pattern sizes
        PatternSize.objects.create(
            pattern=self.pattern,
            size=self.size_m,
            price=Decimal('180.00'),
            stock=10
        )
        PatternSize.objects.create(
            pattern=self.pattern,
            size=self.size_l,
            price=Decimal('190.00'),
            stock=0  # Out of stock
        )
        
        # Create variants
        ProductVariant.objects.create(
            product=self.product,
            pattern=self.pattern,
            color=self.color_red,
            size=self.size_m,
            price=Decimal('180.00'),
            stock=5
        )
        ProductVariant.objects.create(
            product=self.product,
            pattern=self.pattern,
            color=self.color_blue,
            size=self.size_m,
            price=Decimal('180.00'),
            stock=0  # Out of stock
        )
    
    def test_returns_all_options_with_availability(self):
        """Test that endpoint returns ALL options with available flag"""
        url = f'/api/variant-options/{self.product.id}/?pattern_id={self.pattern.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        
        # Should return both sizes (in-stock and out-of-stock)
        self.assertEqual(len(data['sizes']), 2)
        
        # Check availability flags
        size_m_data = next(s for s in data['sizes'] if s['id'] == self.size_m.id)
        size_l_data = next(s for s in data['sizes'] if s['id'] == self.size_l.id)
        
        self.assertTrue(size_m_data['available'])
        self.assertFalse(size_l_data['available'])
    
    def test_requires_size_flag(self):
        """Test that requires_size flag is set correctly"""
        # Pattern with sizes
        url = f'/api/variant-options/{self.product.id}/?pattern_id={self.pattern.id}'
        response = self.client.get(url)
        data = response.json()
        
        self.assertTrue(data['requires_size'])
        
        # Pattern without sizes
        pattern_no_sizes = Pattern.objects.create(
            product=self.product,
            name='No Sizes Pattern',
            has_sizes=False,
            base_price=Decimal('150.00')
        )
        
        url = f'/api/variant-options/{self.product.id}/?pattern_id={pattern_no_sizes.id}'
        response = self.client.get(url)
        data = response.json()
        
        self.assertFalse(data['requires_size'])
    
    def test_color_availability_filtering(self):
        """Test that colors are marked unavailable when out of stock"""
        url = f'/api/variant-options/{self.product.id}/?pattern_id={self.pattern.id}'
        response = self.client.get(url)
        data = response.json()
        
        # Red should be available (has stock)
        red_data = next(c for c in data['colors'] if c['id'] == self.color_red.id)
        self.assertTrue(red_data['available'])
        
        # Blue should be unavailable (no stock)
        blue_data = next(c for c in data['colors'] if c['id'] == self.color_blue.id)
        self.assertFalse(blue_data['available'])


class VariantInfoAPITestCase(TestCase):
    """Test /api/variant-info/ endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=Decimal('100.00'),
            is_active=True
        )
        
        self.pattern = Pattern.objects.create(
            product=self.product,
            name='Test Pattern',
            has_sizes=True
        )
        
        self.size = Size.objects.create(name='M')
        self.color = Color.objects.create(name='Red', code='#ff0000')
        
        ProductColor.objects.create(product=self.product, color=self.color)
        
        PatternSize.objects.create(
            pattern=self.pattern,
            size=self.size,
            price=Decimal('180.00'),
            stock=10
        )
        
        self.variant = ProductVariant.objects.create(
            product=self.product,
            pattern=self.pattern,
            color=self.color,
            size=self.size,
            price=Decimal('999.99'),  # Deprecated
            stock=5
        )
    
    def test_returns_dynamic_price(self):
        """Test that endpoint returns dynamically calculated price"""
        url = f'/api/variant-info/{self.product.id}/'
        params = f'?pattern_id={self.pattern.id}&color_id={self.color.id}&size_id={self.size.id}'
        response = self.client.get(url + params)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        # Should return price from PatternSize (180.00), not deprecated field (999.99)
        self.assertEqual(data['variant']['price'], '180.00')
        self.assertNotEqual(data['variant']['price'], '999.99')
    
    def test_validation_missing_pattern(self):
        """Test validation when pattern is required but missing"""
        url = f'/api/variant-info/{self.product.id}/'
        params = f'?color_id={self.color.id}&size_id={self.size.id}'
        response = self.client.get(url + params)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertFalse(data['validation']['valid'])
        self.assertIn('نمط', data['validation']['message'].lower())
        self.assertEqual(data['validation']['field'], 'pattern')
    
    def test_validation_missing_size(self):
        """Test validation when size is required but missing"""
        url = f'/api/variant-info/{self.product.id}/'
        params = f'?pattern_id={self.pattern.id}&color_id={self.color.id}'
        response = self.client.get(url + params)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertFalse(data['validation']['valid'])
        self.assertIn('مقاس', data['validation']['message'].lower())
        self.assertEqual(data['validation']['field'], 'size')
    
    def test_validation_missing_color(self):
        """Test validation when color is required but missing"""
        url = f'/api/variant-info/{self.product.id}/'
        params = f'?pattern_id={self.pattern.id}&size_id={self.size.id}'
        response = self.client.get(url + params)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertFalse(data['validation']['valid'])
        self.assertIn('لون', data['validation']['message'].lower())
        self.assertEqual(data['validation']['field'], 'color')
    
    def test_valid_selection(self):
        """Test successful validation with all required fields"""
        url = f'/api/variant-info/{self.product.id}/'
        params = f'?pattern_id={self.pattern.id}&color_id={self.color.id}&size_id={self.size.id}'
        response = self.client.get(url + params)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertTrue(data['validation']['valid'])
        self.assertEqual(data['variant']['id'], self.variant.id)
        self.assertTrue(data['variant']['available'])

    def test_selected_type_changes_returned_price(self):
        """Test variant info uses selected product type price when provided"""
        product_type = Type.objects.create(name='Classic')
        ProductType.objects.create(
            product=self.product,
            type=product_type,
            price=Decimal('210.00'),
            description='Classic type description',
            image='product-types/classic.png'
        )

        url = f'/api/variant-info/{self.product.id}/'
        params = (
            f'?pattern_id={self.pattern.id}'
            f'&color_id={self.color.id}'
            f'&size_id={self.size.id}'
            f'&type_id={product_type.id}'
        )
        response = self.client.get(url + params)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data['success'])
        self.assertEqual(data['variant']['price'], '210.00')
    
    def test_out_of_stock_variant(self):
        """Test response for out-of-stock variant"""
        self.variant.stock = 0
        self.variant.save()
        
        url = f'/api/variant-info/{self.product.id}/'
        params = f'?pattern_id={self.pattern.id}&color_id={self.color.id}&size_id={self.size.id}'
        response = self.client.get(url + params)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertFalse(data['variant']['available'])
        self.assertEqual(data['variant']['stock'], 0)
    
    def test_nonexistent_variant(self):
        """Test response when variant combination doesn't exist"""
        other_size = Size.objects.create(name='XL')
        
        url = f'/api/variant-info/{self.product.id}/'
        params = f'?pattern_id={self.pattern.id}&color_id={self.color.id}&size_id={other_size.id}'
        response = self.client.get(url + params)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertFalse(data['validation']['valid'])


class StockAwareFilteringTestCase(TestCase):
    """Test that stock-aware filtering works correctly"""
    
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=Decimal('100.00'),
            is_active=True
        )
        
        self.pattern = Pattern.objects.create(
            product=self.product,
            name='Test Pattern',
            has_sizes=True
        )
        
        self.size_s = Size.objects.create(name='S')
        self.size_m = Size.objects.create(name='M')
        self.size_l = Size.objects.create(name='L')
        
        # S: In stock
        PatternSize.objects.create(
            pattern=self.pattern,
            size=self.size_s,
            price=Decimal('170.00'),
            stock=5
        )
        
        # M: In stock
        PatternSize.objects.create(
            pattern=self.pattern,
            size=self.size_m,
            price=Decimal('180.00'),
            stock=10
        )
        
        # L: Out of stock
        PatternSize.objects.create(
            pattern=self.pattern,
            size=self.size_l,
            price=Decimal('190.00'),
            stock=0
        )
        
        self.color = Color.objects.create(name='Red', code='#ff0000')
        
        # Create variants
        ProductVariant.objects.create(
            product=self.product,
            pattern=self.pattern,
            color=self.color,
            size=self.size_s,
            price=Decimal('170.00'),
            stock=5
        )
        ProductVariant.objects.create(
            product=self.product,
            pattern=self.pattern,
            color=self.color,
            size=self.size_m,
            price=Decimal('180.00'),
            stock=10
        )
        ProductVariant.objects.create(
            product=self.product,
            pattern=self.pattern,
            color=self.color,
            size=self.size_l,
            price=Decimal('190.00'),
            stock=0
        )
    
    def test_all_sizes_returned_with_availability(self):
        """Test that all sizes are returned, not just in-stock ones"""
        url = f'/api/variant-options/{self.product.id}/?pattern_id={self.pattern.id}'
        response = self.client.get(url)
        data = response.json()
        
        # Should return ALL 3 sizes
        self.assertEqual(len(data['sizes']), 3)
        
        # Check each size has correct availability
        sizes_dict = {s['id']: s for s in data['sizes']}
        
        self.assertTrue(sizes_dict[self.size_s.id]['available'])
        self.assertTrue(sizes_dict[self.size_m.id]['available'])
        self.assertFalse(sizes_dict[self.size_l.id]['available'])
