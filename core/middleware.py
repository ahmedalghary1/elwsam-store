from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.utils.cache import patch_cache_control


class CanonicalDomainMiddleware:
    """Redirect production domain variants to https://elwsamshop.com."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.canonical_host = getattr(settings, "CANONICAL_DOMAIN", "elwsamshop.com")
        self.redirect_hosts = {self.canonical_host, f"www.{self.canonical_host}"}

    def __call__(self, request):
        host = request.get_host().split(":", 1)[0].lower()

        if host in self.redirect_hosts and (host != self.canonical_host or request.scheme != "https"):
            parsed = urlsplit(request.build_absolute_uri())
            canonical_url = urlunsplit(("https", self.canonical_host, parsed.path, parsed.query, ""))
            return HttpResponsePermanentRedirect(canonical_url)

        return self.get_response(request)


class PublicCacheMiddleware:
    """Make anonymous public pages easier to cache without touching private flows."""

    private_prefixes = (
        "/admin/",
        "/accounts/",
        "/cart/",
        "/checkout/",
        "/orders/",
        "/payments/",
        "/profile/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not self._is_public_cache_candidate(request, response):
            return response

        vary_header = response.get("Vary")
        if vary_header:
            vary_values = [
                value.strip()
                for value in vary_header.split(",")
                if value.strip().lower() != "cookie"
            ]
            if vary_values:
                response["Vary"] = ", ".join(vary_values)
            else:
                del response["Vary"]

        patch_cache_control(response, public=True, max_age=300, stale_while_revalidate=1800)
        return response

    def _is_public_cache_candidate(self, request, response):
        if request.method not in {"GET", "HEAD"}:
            return False
        if getattr(request, "user", None) is not None and request.user.is_authenticated:
            return False
        if response.status_code != 200 or response.has_header("Set-Cookie"):
            return False
        path = request.path_info or "/"
        return not path.startswith(self.private_prefixes)
