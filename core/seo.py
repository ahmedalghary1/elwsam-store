import json

from django.conf import settings
from django.templatetags.static import static


SITE_NAME = "متجر الوسام"
SITE_DESCRIPTION = "متجر إلكتروني عربي لبيع المشترك الكهربائي ومستلزمات الكهرباء المنزلية داخل مصر والدول العربية."


def build_absolute_uri(request, path_or_url):
    if not path_or_url:
        return ""
    if path_or_url.startswith(("http://", "https://")):
        return canonicalize_url(path_or_url)
    return f"{get_canonical_base_url()}/{path_or_url.lstrip('/')}"


def get_canonical_base_url():
    return getattr(settings, "CANONICAL_BASE_URL", "https://elwsamshop.com").rstrip("/")


def canonicalize_url(url):
    from urllib.parse import urlsplit, urlunsplit

    parsed = urlsplit(url)
    return urlunsplit((
        "https",
        getattr(settings, "CANONICAL_DOMAIN", "elwsamshop.com"),
        parsed.path or "/",
        parsed.query,
        "",
    ))


def serialize_schema(schema):
    return json.dumps(schema, ensure_ascii=False)


def build_breadcrumb_schema(items):
    item_list = []
    for position, item in enumerate(items, start=1):
        name, url = item
        data = {
            "@type": "ListItem",
            "position": position,
            "name": name,
        }
        if url:
            data["item"] = url
        item_list.append(data)

    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": item_list,
    }


def build_collection_page_schema(name, description, url):
    return {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": name,
        "description": description,
        "url": url,
        "inLanguage": "ar",
    }


def build_item_list_schema(name, url, items):
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": name,
        "url": url,
        "numberOfItems": len(items),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": position,
                "url": item_url,
                "name": item_name,
            }
            for position, (item_name, item_url) in enumerate(items, start=1)
        ],
    }


def build_store_schema(request):
    home_url = build_absolute_uri(request, "/")
    return {
        "@context": "https://schema.org",
        "@type": "Store",
        "name": SITE_NAME,
        "description": SITE_DESCRIPTION,
        "url": home_url,
        "logo": build_absolute_uri(request, static("image/ELWSAM-LOGO2020.webp")),
        "image": build_absolute_uri(request, static("image/ELWSAM-LOGO2020.webp")),
        "currenciesAccepted": "EGP",
        "paymentAccepted": "Cash, Credit Card",
        "areaServed": ["EG", "SA", "AE"],
        "inLanguage": "ar",
    }


def build_website_schema(request):
    home_url = build_absolute_uri(request, "/")
    search_url = build_absolute_uri(request, "/search/?q={search_term_string}")
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": home_url,
        "inLanguage": "ar",
        "potentialAction": {
            "@type": "SearchAction",
            "target": search_url,
            "query-input": "required name=search_term_string",
        },
    }
