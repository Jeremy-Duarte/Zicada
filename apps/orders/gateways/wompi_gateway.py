import hashlib
import hmac
import json
import logging
from decimal import Decimal
from typing import Any, Dict, Optional

import requests
from django.conf import settings

from apps.orders.gateways.base import PaymentGateway
from apps.orders.gateways.registry import register_gateway
from apps.orders.models import Order, Payment

logger = logging.getLogger(__name__)

WOMPI_STATUS_MAP = {
    'PENDING': 'pending',
    'APPROVED': 'approved',
    'DECLINED': 'rejected',
    'VOIDED': 'refunded',
    'ERROR': 'error',
}


@register_gateway
class WompiGateway(PaymentGateway):
    """Pasarela Wompi (Bancolombia) para pesos colombianos (amount_in_cents)."""

    name = 'wompi'

    def _get_settings(self):
        public_key = getattr(settings, 'WOMPI_PUBLIC_KEY', '')
        private_key = getattr(settings, 'WOMPI_PRIVATE_KEY', '')
        events_secret = getattr(settings, 'WOMPI_EVENTS_SECRET', '')
        integrity_secret = getattr(settings, 'WOMPI_INTEGRITY_SECRET', '')
        api_url = getattr(settings, 'WOMPI_API_URL', 'https://sandbox.wompi.co/v1')
        return public_key, private_key, events_secret, integrity_secret, api_url

    def to_gateway_amount(self, amount: Decimal) -> int:
        return int(amount * 100)

    def from_gateway_amount(self, amount: int) -> Decimal:
        return Decimal(amount) / 100

    def build_integrity_signature(self, reference: str, amount_in_cents: int, currency: str) -> str:
        _, _, _, integrity_secret, _ = self._get_settings()
        if not integrity_secret:
            raise ValueError('WOMPI_INTEGRITY_SECRET no está configurada.')
        raw = f'{reference}{amount_in_cents}{currency}{integrity_secret}'
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def create_intent(
        self,
        order: Order,
        payment: Payment,
        success_url: str,
        cancel_url: str,
        request_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        public_key, _, _, _, _ = self._get_settings()
        if not public_key:
            raise ValueError('WOMPI_PUBLIC_KEY no está configurada.')
        reference = f'{order.order_number}-{payment.id}'
        amount_in_cents = self.to_gateway_amount(order.total_amount)
        signature = self.build_integrity_signature(reference, amount_in_cents, 'COP')
        return {
            'gateway_session_id': reference,
            'redirect_url': success_url,
            'raw_response': {
                'public_key': public_key,
                'currency': 'COP',
                'amount_in_cents': amount_in_cents,
                'reference': reference,
                'signature': signature,
            },
        }

    def verify_signature(self, request_body: bytes, signature: str, secret: str) -> bool:
        if not signature:
            return False
        expected = hmac.new(
            secret.encode('utf-8'),
            request_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def parse_event(self, request_body: bytes, signature: str) -> Dict[str, Any]:
        payload = json.loads(request_body.decode('utf-8'))
        event_type = payload.get('event', '')
        transaction = payload.get('data', {}).get('transaction', {})

        raw_status = transaction.get('status', '')
        status = WOMPI_STATUS_MAP.get(raw_status, 'error')

        return {
            'event_id': f"{transaction.get('id', '')}-{raw_status}",
            'event_type': event_type,
            'gateway_session_id': transaction.get('reference', ''),
            'gateway_transaction_id': str(transaction.get('id', '')),
            'amount': transaction.get('amount_in_cents', 0),
            'currency': transaction.get('currency', 'COP'),
            'status': status,
            'metadata': transaction,
            'raw': payload,
        }

    def get_event_id(self, event: Dict[str, Any]) -> str:
        return event['event_id']

    def refund(self, payment: Payment) -> Dict[str, Any]:
        _, private_key, _, _, api_url = self._get_settings()
        if not private_key:
            raise ValueError('WOMPI_PRIVATE_KEY no está configurada.')
        if not payment.gateway_transaction_id:
            raise ValueError('No hay transacción que reembolsar.')
        url = f'{api_url}/transactions/{payment.gateway_transaction_id}/refund'
        response = requests.post(
            url,
            headers={'Authorization': f'Bearer {private_key}'},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
