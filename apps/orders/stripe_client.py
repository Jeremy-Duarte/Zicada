import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

stripe.api_version = getattr(settings, 'STRIPE_API_VERSION', '2023-10-16')

def get_stripe():
    secret_key = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_mock')
    if not secret_key or secret_key == 'sk_test_mock':
        raise ImproperlyConfigured('STRIPE_SECRET_KEY no está configurada.')
    if not settings.DEBUG and not secret_key.startswith('sk_live_'):
        raise ImproperlyConfigured('En producción se requiere una key live de Stripe.')
    stripe.api_key = secret_key
    return stripe