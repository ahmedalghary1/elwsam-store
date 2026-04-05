from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product, ProductVariant

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
