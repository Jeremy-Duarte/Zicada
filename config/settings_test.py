import environ
from pathlib import Path
import tempfile
import logging

env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent

if (BASE_DIR / '.env').exists():
    environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = 'django-insecure-test-key-for-ci-only-2024'
DEBUG = False
ALLOWED_HOSTS = ['*']

# Seguridad HTTPS — desactivada en tests para que el cliente de prueba funcione sin SSL
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django.contrib.humanize',
    'cloudinary',
    'cloudinary_storage',
    'django_crontab',
    # 'axes',  # Instalar django-axes: pip install django-axes==7.2.0
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
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
SITE_URL = 'http://testserver'

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
AUTH_USER_MODEL = 'users.User'
AUTH_PASSWORD_VALIDATORS = []

LOGIN_URL = '/core/staff/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/core/staff/login/'

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
STATIC_ROOT = tempfile.mkdtemp()
MEDIA_URL = '/media/'
MEDIA_ROOT = tempfile.mkdtemp()
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
DEFAULT_FROM_EMAIL = 'test@zicada.com'
FROM_EMAIL_NO_REPLY = 'noreply@test.zicada.com'
FROM_EMAIL_ORDERS = 'orders@test.zicada.com'
FROM_EMAIL_SUPPORT = 'support@test.zicada.com'

import cloudinary
cloudinary.config(
    cloud_name='test_cloud_name',
    api_key='test_key',
    api_secret='test_secret',
    secure=True
)

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'test_cloud_name',
    'API_KEY': 'test_key',
    'API_SECRET': 'test_secret',
}

STORAGES = {
    'default': {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

STRIPE_PUBLISHABLE_KEY = 'pk_test_mock_key'
STRIPE_SECRET_KEY = 'sk_test_mock_key'
STRIPE_WEBHOOK_KEY = 'whsec_mock_key'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

logging.disable(logging.ERROR)

CRONJOBS = []
CRONTAB_LOCK_JOBS = False