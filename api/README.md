# Elwsam Store API v1

Base path: `/api/v1/`

All endpoints return a consistent envelope:

```json
{
  "success": true,
  "version": "v1",
  "message": "",
  "data": {},
  "meta": {}
}
```

## Public Catalog

- `GET /api/v1/health/`
- `GET /api/v1/home/`
- `GET /api/v1/catalog/categories/`
- `GET /api/v1/catalog/categories/{id}/?page=1&page_size=24`
- `GET /api/v1/catalog/products/?q=&category=&sort=order&page=1&page_size=24`
- `GET /api/v1/catalog/products/?collection=offers`
- `GET /api/v1/catalog/products/{id}/`
- `GET /api/v1/catalog/products/{id}/configuration/`
- `GET /api/v1/catalog/products/{id}/variant-options/?pattern_id=&color_id=&type_id=`
- `GET /api/v1/catalog/products/{id}/variant-info/?pattern_id=&color_id=&size_id=&type_id=`
- `GET /api/v1/catalog/products/{id}/images/?color_id=&pattern_id=&type_id=`

Supported sort values: `order`, `price`, `price_desc`, `newest`, `rating`.

Supported collection values are driven by `HomeProductCollectionItem.COLLECTION_CHOICES`.

## Guest Orders

`POST /api/v1/orders/guest/`

```json
{
  "customer": {
    "name": "Ahmed Ali",
    "phone": "01000000000",
    "city": "Cairo",
    "address": "Street 1",
    "email": "ahmed@example.com",
    "contact_method": "whatsapp",
    "notes": ""
  },
  "items": [
    {
      "product_id": 1,
      "variant_id": null,
      "product_type_id": null,
      "quantity": 2
    }
  ],
  "notes": ""
}
```

`variant_id` is the stock-tracked `ProductVariant` row. `product_type_id` is the `ProductType` row id used by cart and checkout.
