from django.db.models import F

from .models import Product


PRODUCT_COLLECTION_TYPES = {"offers", "best-sellers", "latest"}


def get_product_collection_queryset(collection_type):
    """Return product collections used by the home tabs and product API."""
    queryset = Product.objects.filter(
        is_active=True,
        category__is_active=True,
    ).select_related('category').prefetch_related('images')

    if collection_type == "offers":
        return queryset.filter(
            old_price__isnull=False,
            old_price__gt=F('price'),
        ).order_by('order', '-updated_at', '-created_at')

    if collection_type == "best-sellers":
        return queryset.filter(is_hot=True).order_by('order', '-rating', '-created_at')

    if collection_type == "latest":
        return queryset.order_by('-created_at')

    return Product.objects.none()


def serialize_product_card(product):
    """Serialize the fields needed to render a product card on the frontend."""
    image_url = product.image.url if product.image else ""
    old_price = product.old_price if product.old_price and product.old_price > product.price else None

    return {
        "id": product.id,
        "name": product.name,
        "category": product.category.name if product.category_id else "",
        "price": str(product.price),
        "old_price": str(old_price) if old_price else "",
        "discount_percent": product.get_discount_percent(),
        "image": image_url,
        "image_alt": product.get_primary_image_alt(),
        "url": product.get_absolute_url(),
        "is_hot": product.is_hot,
        "is_new": product.is_new,
        "has_offer": bool(old_price),
        "rating": product.rating,
    }
