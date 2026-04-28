from django import template

from products.image_utils import get_thumbnail_url


register = template.Library()


@register.filter
def thumbnail_url(image_field, spec="400x400:cover"):
    return get_thumbnail_url(image_field, spec)
