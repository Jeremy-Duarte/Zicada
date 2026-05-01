import stripe
from config.settings import STRIPE_SECRET_KEY

def get_stripe():
    stripe.api_key = STRIPE_SECRET_KEY
    return stripe