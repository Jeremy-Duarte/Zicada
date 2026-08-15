"""
Django settings for Zicada project.
"""

import environ
from pathlib import Path

env = environ.Env()

BASE_DIR = Path(__file__).resolve().parent.parent

if (BASE_DIR / '.env').exists():
    environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env.bool('DJANGO_DEBUG', default=False)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1', 'testserver', '[::1]','.trycloudflare.com'])

# =============================================================================
# SEGURIDAD HTTP — solo activo en producción (DEBUG=False)
# En desarrollo local estas configuraciones permanecen desactivadas.
# Referencia: https://docs.djangoproject.com/en/stable/topics/security/
# =============================================================================

# Redirigir todas las peticiones HTTP a HTTPS
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=not DEBUG)

# Protección contra ataques de sesión por red
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=not DEBUG)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF solo sobre HTTPS
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=not DEBUG)
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# HTTP Strict Transport Security (HSTS)
# 1 año en producción; 0 en desarrollo para no bloquear HTTP local
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0 if DEBUG else 31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=not DEBUG)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=not DEBUG)

# Protección adicional de cabeceras
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'

# django-axes: proteccion contra fuerza bruta
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 0.5
AXES_LOCKOUT_PARAMETERS = [['username']]
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_CALLABLE = None

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Vendor Apps
    'rest_framework',
    'django.contrib.humanize',
    'cloudinary',
    'cloudinary_storage',
    'django_crontab',
    'axes',
    # Zicada Apps
    'apps.core',
    'apps.users',
    'apps.products',
    'apps.orders',
    'apps.backoffice',
    'apps.delivery',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

SITE_URL = 'http://localhost:8000'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.cart_context',
                'apps.core.context_processors.breadcrumbs',
                'apps.core.context_processors.is_home',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': env.db(default='sqlite:///db.sqlite3')
}

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/core/staff/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/core/staff/login/'

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

FROM_EMAIL_NO_REPLY = env('FROM_EMAIL_NO_REPLY', default=DEFAULT_FROM_EMAIL)
FROM_EMAIL_ORDERS = env('FROM_EMAIL_ORDERS', default=DEFAULT_FROM_EMAIL)
FROM_EMAIL_SUPPORT = env('FROM_EMAIL_SUPPORT', default=DEFAULT_FROM_EMAIL)
# Configuracion de API cloudinary
import cloudinary

cloudinary.config(
    cloud_name=env('CLOUDINARY_CLOUD_NAME'),
    api_key=env('CLOUDINARY_API_KEY'),
    api_secret=env('CLOUDINARY_API_SECRET'),
    secure=True
)

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': env('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': env('CLOUDINARY_API_KEY'),
    'API_SECRET': env('CLOUDINARY_API_SECRET'),
}

STORAGES = {
    'default': {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

CRONJOBS = [
    # Actualizar colecciones: cada domingo a las 2:00 AM
    ('0 2 * * 0', 'django.core.management.call_command', ['update_collections_status']),
    # Expirar pedidos pendientes sin pago: todos los días a las 3:00 AM
    ('0 3 * * *', 'django.core.management.call_command', ['expire_pending_orders']),
]

CRONTAB_LOCK_JOBS = True

CRONTAB_COMMAND_PREFIX = 'TZ=America/Bogota'

CRONTAB_DJANGO_SETTINGS_MODULE = 'config.settings'

# Configuración API stripe pasarela de pagos
STRIPE_PUBLISHABLE_KEY= env("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_KEY= env("STRIPE_WEBHOOK_KEY")

# Configuración API wompi pasarela de pagos
WOMPI_PUBLIC_KEY = env("WOMPI_PUBLIC_KEY", default="")
WOMPI_PRIVATE_KEY = env("WOMPI_PRIVATE_KEY", default="")
WOMPI_EVENTS_SECRET = env("WOMPI_EVENTS_SECRET", default="")
WOMPI_INTEGRITY_SECRET = env("WOMPI_INTEGRITY_SECRET", default="")
WOMPI_API_URL = env("WOMPI_API_URL", default="https://sandbox.wompi.co/v1")

# Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="memory://")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="django-db")
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=True)

# PWA Metadata
PWA_NAME = "Zicada Delivery"
PWA_SHORT_NAME = "Zicada"
PWA_DESCRIPTION = "App de entregas para repartidores Zicada"
PWA_START_URL = "/delivery/login/"
PWA_DISPLAY = "standalone"
PWA_THEME_COLOR = "#000000"
PWA_BACKGROUND_COLOR = "#ffffff"
PWA_ORIENTATION = "portrait"
PWA_SCOPE = "/delivery/"

# Icons PWA
PWA_ICONS = {
    "72": "delivery/icons/icon-72x72.png",
    "96": "delivery/icons/icon-96x96.png",
    "128": "delivery/icons/icon-128x128.png",
    "144": "delivery/icons/icon-144x144.png",
    "152": "delivery/icons/icon-152x152.png",
    "192": "delivery/icons/icon-192x192.png",
    "384": "delivery/icons/icon-384x384.png",
    "512": "delivery/icons/icon-512x512.png",
}

# Service Worker Cache
SW_CACHE_NAME = "zicada-delivery-v1.1.2"
PWA_VERSION = "1.1.2"
SW_PRECACHE_URLS = [
    "/delivery/offline/",
    "/delivery/login/",
    "/delivery/dashboard/",
    "/delivery/orders/",
    "/delivery/summary/",
    "/static/css/delivery/main.css",
    "/static/js/delivery/base.js",
    "/static/js/delivery/orders.js",
]

# Offline fallback
OFFLINE_PAGE = "/delivery/offline/"