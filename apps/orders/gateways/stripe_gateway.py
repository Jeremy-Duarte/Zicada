import logging
from decimal import Decimal
from typing import Any, Dict, Optional

import stripe
from django.conf import settings

from apps.orders.gateways.base import PaymentGateway
from apps.orders.gateways.registry import register_gateway
from apps.orders.models import Order, Payment

logger = logging.getLogger(__name__)

stripe.api_version = getattr(settings, 'STRIPE_API_VERSION', '2023-10-16')


@register_gateway
class StripeGateway(PaymentGateway):
    """Pasarela Stripe Checkout para pesos colombianos (centavos)."""

    name = 'stripe'

    def _get_client(self):
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError('STRIPE_SECRET_KEY no está configurada.')
        stripe.api_key = settings.STRIPE_SECRET_KEY
        return stripe

    def to_gateway_amount(self, amount: Decimal) -> int:
        return int(amount * 100)

    def from_gateway_amount(self, amount: int) -> Decimal:
        return Decimal(amount) / 100

    def create_intent(
        self,
        order: Order,
        payment: Payment,
        success_url: str,
        cancel_url: str,
        request_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        client = self._get_client()
        cart_items_count = order.items.count()
        checkout_session = client.checkout.Session.create(
            idempotency_key=f'{order.order_number}:{payment.id}',
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'cop',
                    'unit_amount': self.to_gateway_amount(order.total_amount),
                    'product_data': {
                        'name': f'Pedido Zicada - {order.customer_name}',
                        'description': f'{cart_items_count} productos',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(order.order_number),
            customer_email=order.customer_email or None,
            metadata={
                'order_number': order.order_number,
                'payment_id': str(payment.id),
            },
        )
        return {
            'gateway_session_id': checkout_session.id,
            'redirect_url': checkout_session.url,
            'raw_response': dict(checkout_session),
        }

    def verify_signature(self, request_body: bytes, signature: str, secret: str) -> bool:
        try:
            stripe.Webhook.construct_event(request_body, signature, secret)
            return True
        except (ValueError, stripe.error.SignatureVerificationError):
            return False

    def parse_event(self, request_body: bytes, signature: str) -> Dict[str, Any]:
        event = stripe.Webhook.construct_event(
            request_body,
            signature,
            settings.STRIPE_WEBHOOK_KEY,
        )
        session = event['data']['object']
        amount_total = session.get('amount_total', 0)
        event_type = event['type']

        if event_type == 'checkout.session.completed':
            status = 'approved'
        elif event_type == 'checkout.session.expired':
            status = 'cancelled'
        elif event_type == 'charge.refunded':
            status = 'refunded'
        else:
            status = 'pending'

        return {
            'event_id': event['id'],
            'event_type': event_type,
            'gateway_session_id': session.get('id', ''),
            'gateway_transaction_id': str(session.get('payment_intent', '')),
            'amount': amount_total,
            'currency': session.get('currency', 'cop'),
            'status': status,
            'metadata': session.get('metadata', {}),
            'raw': event,
        }

    def get_event_id(self, event: Dict[str, Any]) -> str:
        return event['event_id']

    def refund(self, payment: Payment) -> Dict[str, Any]:
        client = self._get_client()
        if not payment.gateway_transaction_id:
            raise ValueError('No hay transacción que reembolsar.')
        refund = client.Refund.create(
            payment_intent=payment.gateway_transaction_id,
        )
        return dict(refund)
