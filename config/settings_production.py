"""
Django settings for Zicada project - PRODUCCIÓN en Railway.
Utiliza django-environ para la configuración segura desde variables de entorno.
"""

import environ
from pathlib import Path

env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent

# Carga .env.prod solo si existe (para pruebas locales)
if (BASE_DIR / '.env.prod').exists():
    environ.Env.read_env(BASE_DIR / '.env.prod')

# CONFIGURACIÓN BÁSICA - PRODUCCIÓN

SECRET_KEY = env('DJANGO_SECRET_KEY')

DEBUG = False

# Railway asigna un dominio automáticamente
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['.railway.app'])

# SEGURIDAD CSRF
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    'https://*.railway.app',
    'https://zicada.up.railway.app',
])

# APPS INSTALADAS
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
    'anymail',
    # Zicada Apps
    'apps.core',
    'apps.users',
    'apps.products',
    'apps.orders',
    'apps.backoffice',
    'apps.delivery',
]

# MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Requisito Railway
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URLS Y TEMPLATES
ROOT_URLCONF = 'config.urls'
SITE_URL = env('SITE_URL', default='https://zicada-production.up.railway.app')

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

# ============================================
# BASE DE DATOS
# ============================================
# Railway inyecta automáticamente la variable DATABASE_URL
# Usamos django-environ para parsear la URL de forma nativa

DATABASE_URL = env('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL no está configurada. Asegúrate de que Railway la haya inyectado.")

DATABASES = {
    'default': env.db(),
}

# Forzar SSL para conexiones seguras a PostgreSQL en producción
if 'postgres' in DATABASE_URL or 'postgresql' in DATABASE_URL:
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',
    }

# AUTENTICACIÓN Y SEGURIDAD
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

# INTERNACIONALIZACIÓN
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# ARCHIVOS ESTÁTICOS Y MEDIA
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Requisito de despliegue para railway [Servir archivos estaticos]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST FRAMEWORK
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# EMAIL
ANYMAIL = {
    "RESEND_API_KEY": env('RESEND_API_KEY'),
}
EMAIL_BACKEND = 'anymail.backends.resend.EmailBackend'
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='Zicada <noreply@zicada.com>')
FROM_EMAIL_NO_REPLY = env('FROM_EMAIL_NO_REPLY', default=DEFAULT_FROM_EMAIL)
FROM_EMAIL_ORDERS = env('FROM_EMAIL_ORDERS', default=DEFAULT_FROM_EMAIL)
FROM_EMAIL_SUPPORT = env('FROM_EMAIL_SUPPORT', default=DEFAULT_FROM_EMAIL)

# CLOUDINARY
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

# STRIPE
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_KEY = env("STRIPE_WEBHOOK_KEY")

# CRON TASKS
CRONJOBS = [
    ('0 2 * * 0', 'django.core.management.call_command', ['update_collections_status']),
]
CRONTAB_LOCK_JOBS = True
CRONTAB_COMMAND_PREFIX = 'TZ=America/Bogota'
CRONTAB_DJANGO_SETTINGS_MODULE = 'config.settings_production'

# CONFIGURACIONES DE SEGURIDAD PARA PRODUCCIÓN
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# LOGGING PARA PRODUCCIÓN
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

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