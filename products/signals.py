from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import (
    Pattern,
    PatternColor,
    PatternImage,
    PatternSize,
    Product,
    ProductColor,
    ProductImage,
    ProductSize,
    ProductType,
    ProductTypeColor,
    ProductTypeImage,
    ProductVariant,
)


def _delete_product_config_cache(product_id):
    if product_id:
        cache.delete(f'product_config_{product_id}')

@receiver(post_save, sender=Product)
def create_or_update_simple_product_variant(sender, instance, created, **kwargs):
    """
    Ensure that a simple product (without patterns, sizes, or colors)
    has a default ProductVariant record for cart operations.
    """
    # Use the product's method to determine its configuration type
    config_type = instance.get_configuration_type()

    if config_type == 'simple':
        # Check if a default variant already exists
        # A simple product's variant has NULL for pattern, color, and size
        default_variant, variant_created = ProductVariant.objects.get_or_create(
            product=instance,
            pattern__isnull=True,
            color__isnull=True,
            size__isnull=True,
            defaults={
                'price': instance.price, # Set price from parent product
                'stock': 100, # Default stock, can be adjusted
            }
        )

        # If the variant was not just created, check if its price needs updating
        if not variant_created:
            if default_variant.price != instance.price:
                default_variant.price = instance.price
                default_variant.save()

    _delete_product_config_cache(instance.pk)


@receiver(post_delete, sender=Product)
def delete_product_config_cache(sender, instance, **kwargs):
    _delete_product_config_cache(instance.pk)


def _related_product_id(instance):
    if hasattr(instance, 'product_id'):
        return instance.product_id
    if hasattr(instance, 'pattern_id'):
        return instance.pattern.product_id
    if hasattr(instance, 'product_type_id'):
        return instance.product_type.product_id
    return None


def _invalidate_related_product_config(sender, instance, **kwargs):
    _delete_product_config_cache(_related_product_id(instance))


for related_model in (
    Pattern,
    PatternColor,
    PatternImage,
    PatternSize,
    ProductColor,
    ProductImage,
    ProductSize,
    ProductType,
    ProductTypeColor,
    ProductTypeImage,
    ProductVariant,
):
    post_save.connect(
        _invalidate_related_product_config,
        sender=related_model,
        dispatch_uid=f'invalidate_product_config_on_{related_model.__name__}_save',
    )
    post_delete.connect(
        _invalidate_related_product_config,
        sender=related_model,
        dispatch_uid=f'invalidate_product_config_on_{related_model.__name__}_delete',
    )
