import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

stripe.api_version = getattr(settings, 'STRIPE_API_VERSION', '2023-10-16')

def get_stripe():
    secret_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
    if not secret_key:
        raise ImproperlyConfigured('STRIPE_SECRET_KEY no está configurada.')
    stripe.api_key = secret_key
    return stripe