import logging
import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

stripe.api_version = getattr(settings, 'STRIPE_API_VERSION', '2023-10-16')

def get_stripe():
    secret_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
    if not secret_key:
        raise ImproperlyConfigured('STRIPE_SECRET_KEY no está configurada.')

    if secret_key.startswith('sk_test_') and not settings.DEBUG:
        logger.warning('Usando clave de prueba (sk_test_) en un entorno que no es de desarrollo (DEBUG=False).')
    elif secret_key.startswith('sk_live_') and settings.DEBUG:
        logger.warning('Usando clave de producción (sk_live_) en un entorno de desarrollo (DEBUG=True).')

    stripe.api_key = secret_key
    return stripe