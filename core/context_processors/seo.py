NOINDEX_ROUTES = {
    (None, "search_products"),
    ("orders", "cart"),
    ("orders", "checkout"),
    ("orders", "order_success"),
    ("orders", "guest_order_success"),
    ("orders", "order_list"),
    ("orders", "order_detail"),
    ("orders", "wishlist"),
}

NOINDEX_NAMESPACES = {"accounts"}


def seo_context(request):
    match = getattr(request, "resolver_match", None)
    namespace = getattr(match, "namespace", None)
    url_name = getattr(match, "url_name", None)

    meta_robots = "index,follow"
    request_path = request.path or ""
    if (
        namespace in NOINDEX_NAMESPACES
        or (namespace, url_name) in NOINDEX_ROUTES
        or request_path.startswith("/search/")
    ):
        meta_robots = "noindex,follow"

    return {
        "meta_robots": meta_robots,
        "seo_site_name": "متجر الوسام",
    }
