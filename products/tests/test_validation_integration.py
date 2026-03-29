"""
Integration Tests for Validation System
Tests end-to-end validation flow including AJAX endpoints
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import json

from products.models import (
    Category, Product, Pattern, PatternSize, Color, Size,
    ProductColor, ProductSize, ProductVariant
)


class VariantValidationIntegrationTest(TestCase):
    """Test variant validation through AJAX endpoints"""
    
    def setUp(self):
        """Set up test data and client"""
        self.client = Client()
        
        # Create test data
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=100.00,
            is_active=True
        )
        
        self.pattern = Pattern.objects.create(
            product=self.product,
            name='Pattern 1',
            has_sizes=True,
            order=1
        )
        
        self.size_s = Size.objects.create(name='S')
        self.size_m = Size.objects.create(name='M')
        
        self.pattern_size_s = PatternSize.objects.create(
            pattern=self.pattern,
            size=self.size_s,
            price=120.00,
            stock=10
        )
        
        self.color_red = Color.objects.create(name='Red', code='#FF0000')
        ProductColor.objects.create(product=self.product, color=self.color_red)
        
        self.variant = ProductVariant.objects.create(
            product=self.product,
            pattern=self.pattern,
            color=self.color_red,
            size=self.size_s,
            price=120.00,
            stock=10
        )
    
    def test_get_variant_info_missing_pattern(self):
        """Test variant info endpoint with missing pattern"""
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url, {
            'color_id': self.color_red.id,
            'size_id': self.size_s.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertIn('validation', data)
        self.assertFalse(data['validation']['valid'])
        self.assertEqual(data['validation']['field'], 'pattern')
        self.assertIn('pattern', data['validation']['errors'])
    
    def test_get_variant_info_missing_size(self):
        """Test variant info endpoint with missing size for pattern"""
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url, {
            'pattern_id': self.pattern.id,
            'color_id': self.color_red.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertIn('validation', data)
        self.assertFalse(data['validation']['valid'])
        self.assertEqual(data['validation']['field'], 'size')
        self.assertIn('size', data['validation']['errors'])
    
    def test_get_variant_info_missing_color(self):
        """Test variant info endpoint with missing color"""
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url, {
            'pattern_id': self.pattern.id,
            'size_id': self.size_s.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertIn('validation', data)
        self.assertFalse(data['validation']['valid'])
        self.assertEqual(data['validation']['field'], 'color')
        self.assertIn('color', data['validation']['errors'])
    
    def test_get_variant_info_valid_selection(self):
        """Test variant info endpoint with valid selection"""
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url, {
            'pattern_id': self.pattern.id,
            'color_id': self.color_red.id,
            'size_id': self.size_s.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertIn('variant', data)
        self.assertEqual(data['variant']['id'], self.variant.id)
        self.assertTrue(data['variant']['available'])
        self.assertEqual(data['variant']['stock'], 10)
        self.assertTrue(data['validation']['valid'])
    
    def test_get_variant_info_out_of_stock(self):
        """Test variant info endpoint with out of stock variant"""
        self.variant.stock = 0
        self.variant.save()
        
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url, {
            'pattern_id': self.pattern.id,
            'color_id': self.color_red.id,
            'size_id': self.size_s.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertIn('validation', data)
        self.assertFalse(data['validation']['valid'])
    
    def test_get_variant_info_invalid_product(self):
        """Test variant info endpoint with non-existent product"""
        url = '/api/variant-info/9999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_get_product_config(self):
        """Test product config endpoint"""
        url = f'/api/product-config/{self.product.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['configuration_type'], 'pattern_based')
        self.assertTrue(data['has_patterns'])
        self.assertTrue(data['has_colors'])
        self.assertGreater(len(data['patterns']), 0)
        self.assertGreater(len(data['colors']), 0)
    
    def test_get_variant_options_with_pattern(self):
        """Test variant options endpoint with pattern selected"""
        url = f'/api/variant-options/{self.product.id}/'
        response = self.client.get(url, {
            'pattern_id': self.pattern.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertTrue(data['requires_size'])
        self.assertGreater(len(data['sizes']), 0)
        self.assertGreater(len(data['colors']), 0)


class SizeBasedProductValidationTest(TestCase):
    """Test validation for size-based products"""
    
    def setUp(self):
        """Set up size-based product"""
        self.client = Client()
        
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Size Product',
            slug='size-product',
            category=self.category,
            price=100.00,
            is_active=True
        )
        
        self.size_s = Size.objects.create(name='S')
        ProductSize.objects.create(product=self.product, size=self.size_s, price=100.00)
        
        self.color = Color.objects.create(name='Blue', code='#0000FF')
        ProductColor.objects.create(product=self.product, color=self.color)
        
        self.variant = ProductVariant.objects.create(
            product=self.product,
            color=self.color,
            size=self.size_s,
            price=100.00,
            stock=5
        )
    
    def test_size_required_for_size_based_product(self):
        """Test that size is required for size-based products"""
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url, {
            'color_id': self.color.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertIn('size', data['validation']['errors'])
    
    def test_valid_size_based_selection(self):
        """Test valid selection for size-based product"""
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url, {
            'color_id': self.color.id,
            'size_id': self.size_s.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['variant']['id'], self.variant.id)


class SimpleProductValidationTest(TestCase):
    """Test validation for simple products"""
    
    def setUp(self):
        """Set up simple product"""
        self.client = Client()
        
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Simple Product',
            slug='simple-product',
            category=self.category,
            price=50.00,
            is_active=True
        )
        
        self.variant = ProductVariant.objects.create(
            product=self.product,
            price=50.00,
            stock=20
        )
    
    def test_simple_product_no_validation_required(self):
        """Test that simple products don't require selections"""
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Should succeed with no parameters
        self.assertTrue(data['success'])
        self.assertEqual(data['variant']['id'], self.variant.id)


class StockValidationTest(TestCase):
    """Test stock availability validation"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=100.00,
            is_active=True
        )
        
        self.variant = ProductVariant.objects.create(
            product=self.product,
            price=100.00,
            stock=5
        )
    
    def test_variant_available_with_stock(self):
        """Test variant shows as available when in stock"""
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url)
        
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertTrue(data['variant']['available'])
        self.assertEqual(data['variant']['stock'], 5)
    
    def test_variant_unavailable_without_stock(self):
        """Test variant shows as unavailable when out of stock"""
        self.variant.stock = 0
        self.variant.save()
        
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url)
        
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertIn('stock', data['validation']['errors'])


class ErrorMessageLocalizationTest(TestCase):
    """Test that all error messages are in Arabic"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=100.00,
            is_active=True
        )
        
        self.pattern = Pattern.objects.create(
            product=self.product,
            name='Pattern 1',
            has_sizes=True
        )
        
        self.color = Color.objects.create(name='Red', code='#FF0000')
        ProductColor.objects.create(product=self.product, color=self.color)
    
    def test_pattern_required_message_in_arabic(self):
        """Test pattern required message is in Arabic"""
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url, {'color_id': self.color.id})
        
        data = json.loads(response.content)
        
        self.assertIn('النمط', data['validation']['errors']['pattern'])
    
    def test_size_required_message_in_arabic(self):
        """Test size required message is in Arabic"""
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url, {
            'pattern_id': self.pattern.id,
            'color_id': self.color.id
        })
        
        data = json.loads(response.content)
        
        self.assertIn('المقاس', data['validation']['errors']['size'])
    
    def test_color_required_message_in_arabic(self):
        """Test color required message is in Arabic"""
        size = Size.objects.create(name='S')
        
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url, {
            'pattern_id': self.pattern.id,
            'size_id': size.id
        })
        
        data = json.loads(response.content)
        
        self.assertIn('اللون', data['validation']['errors']['color'])


class EdgeCaseValidationTest(TestCase):
    """Test edge cases and race conditions"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=100.00,
            is_active=True
        )
    
    def test_invalid_pattern_id(self):
        """Test with non-existent pattern ID"""
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url, {'pattern_id': 9999})
        
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertIn('pattern', data['validation']['errors'])
    
    def test_invalid_color_id(self):
        """Test with non-existent color ID"""
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url, {'color_id': 9999})
        
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertIn('color', data['validation']['errors'])
    
    def test_non_numeric_ids(self):
        """Test with non-numeric IDs"""
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url, {'pattern_id': 'abc'})
        
        # Should handle gracefully
        self.assertEqual(response.status_code, 400)
    
    def test_inactive_product(self):
        """Test with inactive product"""
        self.product.is_active = False
        self.product.save()
        
        url = f'/api/variant-info/{self.product.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
