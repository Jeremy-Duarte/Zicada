import stripe

def get_stripe():
    from django.conf import settings
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_mock')
    return stripe