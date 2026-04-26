from .settings import *  # noqa: F401,F403


DEBUG = True

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.local.sqlite3",
    }
}

MIGRATION_MODULES = {
    "accounts": None,
    "core": None,
    "orders": None,
    "payments": None,
    "products": None,
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media_local"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
DEFAULT_FROM_EMAIL = "local@elwsam.test"

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_PROXY_SSL_HEADER = None

CANONICAL_DOMAIN = "local.elwsam.test"
CANONICAL_BASE_URL = "http://127.0.0.1:8000"

MIDDLEWARE = [
    item
    for item in MIDDLEWARE
    if item != "core.middleware.CanonicalDomainMiddleware"
]
