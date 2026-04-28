from django.db import OperationalError, ProgrammingError
from django.db.models import Case, F, IntegerField, When

from .image_utils import get_thumbnail_url
from .models import HomeProductCollectionItem, Product


PRODUCT_COLLECTION_TYPES = {
    choice[0] for choice in HomeProductCollectionItem.COLLECTION_CHOICES
}
LEGACY_COLLECTION_TYPES = HomeProductCollectionItem.LEGACY_COLLECTION_ALIASES


def normalize_collection_type(collection_type):
    return LEGACY_COLLECTION_TYPES.get(str(collection_type), collection_type)


def collection_type_values(collection_type):
    normalized_type = normalize_collection_type(collection_type)
    aliases = [
        legacy_value
        for legacy_value, canonical_value in LEGACY_COLLECTION_TYPES.items()
        if canonical_value == normalized_type
    ]
    return [normalized_type, *aliases]


def _base_product_queryset():
    return Product.objects.filter(
        is_active=True,
        category__is_active=True,
    ).select_related('category').prefetch_related('images')


def _curated_collection_queryset(collection_type):
    collection_values = collection_type_values(collection_type)
    item_queryset = HomeProductCollectionItem.objects.filter(
        collection_type__in=collection_values,
        is_active=True,
        product__is_active=True,
        product__category__is_active=True,
    ).order_by('order', '-created_at')

    try:
        product_ids = list(item_queryset.values_list('product_id', flat=True))
    except (OperationalError, ProgrammingError):
        return Product.objects.none()
    if not product_ids:
        return Product.objects.none()

    preserved_order = Case(
        *[When(pk=product_id, then=position) for position, product_id in enumerate(product_ids)],
        output_field=IntegerField(),
    )
    return _base_product_queryset().filter(pk__in=product_ids).order_by(preserved_order)


def get_product_collection_queryset(collection_type):
    """Return product collections used by the home tabs and product API."""
    collection_type = normalize_collection_type(collection_type)
    curated_queryset = _curated_collection_queryset(collection_type)
    if curated_queryset.exists():
        return curated_queryset

    queryset = _base_product_queryset()

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
    image_url = get_thumbnail_url(product.image, "400x400:cover") if product.image else ""
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
        "is_simple": product.is_simple_product(),
        "is_available": product.is_available(),
        "rating": product.rating,
    }
