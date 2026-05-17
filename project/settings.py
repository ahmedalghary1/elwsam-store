import pymysql
# Override the version reported to Django
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(path):
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


load_env_file(BASE_DIR / ".env")


SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-rl17&5ecdx1h131wc@wy!^r-*7zh(q@!+#4jy2*%tw=z@4dv2i')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')
CANONICAL_DOMAIN = os.environ.get('CANONICAL_DOMAIN', 'elwsamshop.com')
CANONICAL_BASE_URL = f'https://{CANONICAL_DOMAIN}'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:51281',
    'https://elwsamshop.com',
    'https://www.elwsamshop.com',
]


# Application definition

INSTALLED_APPS = [
    'accounts',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',

    # third-party apps
    'adminsortable2',

    # local apps
    'core',
    'orders',
    'products',
    'payments',
    'staff_dashboard',
    'api',
]

MIDDLEWARE = [
    'core.middleware.CanonicalDomainMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.PublicCacheMiddleware',
]

ROOT_URLCONF = 'project.urls'

FORCE_SCRIPT_NAME = '/'
TEMPLATE_DIR = BASE_DIR / 'templates'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.cart.cart_processor',
                'core.context_processors.seo.seo_context',
                # 'core.context_processors.wishlist.wishlist_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DJANGO_DB_ENGINE', 'django.db.backends.mysql'),
        'NAME': os.environ.get('DJANGO_DB_NAME', 'elwsamst_shop'),
        'USER': os.environ.get('DJANGO_DB_USER', 'elwsamst_usershop'),
        'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD', 'elwsam@100'),
        'HOST': os.environ.get('DJANGO_DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DJANGO_DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET NAMES 'utf8mb4'"
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/shop_media/'
MEDIA_ROOT = '/home/elwsamst/media'
ASSET_VERSION = os.environ.get('ASSET_VERSION', '20260503-hero-slide-dots')


AUTH_USER_MODEL = 'accounts.User'
DEFAULT_CHARSET = 'utf-8'
# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email Configuration
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', "mail.elwsamshop.com")
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '465'))
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', False)
EMAIL_USE_SSL = env_bool('EMAIL_USE_SSL', True)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'support@elwsamshop.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'info@100')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'ELWSAM Shop <support@elwsamshop.com>')

# OTP Settings
OTP_EXPIRY_MINUTES = 10  # مدة صلاحية OTP بالدقائق

# Security Settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
