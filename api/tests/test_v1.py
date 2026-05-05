import json
from decimal import Decimal

from django.test import Client, TestCase

from orders.models import Order
from products.models import Category, Product


class ApiV1CatalogTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Switches', is_active=True)
        self.product = Product.objects.create(
            name='Wall Switch',
            category=self.category,
            description='A simple wall switch',
            price=Decimal('120.00'),
            stock=10,
            is_active=True,
        )

    def test_health_endpoint(self):
        response = self.client.get('/api/v1/health/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['version'], 'v1')
        self.assertEqual(data['data']['status'], 'ok')

    def test_product_list_uses_consistent_envelope_and_pagination(self):
        response = self.client.get('/api/v1/catalog/products/?q=wall&page_size=10')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['meta']['total'], 1)
        self.assertEqual(data['data']['items'][0]['name'], 'Wall Switch')

    def test_product_detail_returns_catalog_payload(self):
        response = self.client.get(f'/api/v1/catalog/products/{self.product.id}/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['id'], self.product.id)
        self.assertEqual(data['data']['category']['id'], self.category.id)


class ApiV1GuestOrderTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Lighting', is_active=True)
        self.product = Product.objects.create(
            name='LED Lamp',
            category=self.category,
            description='A simple LED lamp',
            price=Decimal('85.00'),
            stock=20,
            is_active=True,
        )

    def test_create_guest_order(self):
        payload = {
            'customer': {
                'name': 'Ahmed Ali',
                'phone': '01000000000',
                'city': 'Cairo',
                'address': 'Street 1',
                'contact_method': 'whatsapp',
            },
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 2,
                }
            ],
        }

        response = self.client.post(
            '/api/v1/orders/guest/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        order = Order.objects.get(id=data['data']['order']['id'])
        self.assertEqual(order.total_price, Decimal('170.00'))
        self.assertEqual(order.get_total_items(), 2)

    def test_guest_order_validates_required_customer_fields(self):
        response = self.client.post(
            '/api/v1/orders/guest/',
            data=json.dumps({'customer': {}, 'items': []}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('customer', data['error']['details'])
