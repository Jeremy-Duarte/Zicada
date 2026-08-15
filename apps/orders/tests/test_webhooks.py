import hashlib
import hmac
import json
from decimal import Decimal
from unittest import mock

import pytest
from django.urls import reverse

from apps.orders.models import Order, Payment


@pytest.mark.django_db
class TestStripeWebhook:
    def _payload(self, session_id='cs_1', amount=10000, order_number='ZCD-8001', payment_id='1'):
        return json.dumps({
            'id': 'evt_1',
            'type': 'checkout.session.completed',
            'data': {'object': {
                'id': session_id,
                'payment_intent': 'pi_1',
                'amount_total': amount,
                'currency': 'cop',
                'metadata': {'order_number': order_number, 'payment_id': payment_id},
            }},
        })

    def test_valid_signature_processes_event(self, client, order_factory, order_item_factory, product_with_stock):
        product, variant = product_with_stock(stock=5, price=Decimal('10000.00'))
        order = order_factory(
            status='pendiente',
            order_number='ZCD-8001',
            customer_email='a@b.com',
        )
        order.payment_session_id = 'cs_1'
        order.save(update_fields=['payment_session_id'])
        order_item_factory(order=order, variant=variant, quantity=1, price=Decimal('10000.00'))
        order.refresh_from_db()

        payload = self._payload(amount=int(order.total_amount * 100), order_number='ZCD-8001')

        event_obj = json.loads(payload)
        with mock.patch('stripe.Webhook.construct_event', return_value=event_obj):
            response = client.post(
                reverse('orders:stripe_webhook'),
                data=payload,
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='t=1,v1=sig',
            )

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.is_paid is True
        assert Payment.objects.filter(order=order, status='approved').exists()

    def test_invalid_signature_returns_400(self, client, order_factory):
        order_factory(status='pendiente', order_number='ZCD-8002')
        import stripe

        with mock.patch('stripe.Webhook.construct_event', side_effect=stripe.error.SignatureVerificationError('bad sig', 'raw')):
            response = client.post(
                reverse('orders:stripe_webhook'),
                data=self._payload(order_number='ZCD-8002'),
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='t=1,v1=bad',
            )

        assert response.status_code == 400


@pytest.mark.django_db
class TestWompiWebhook:
    def _payload(self, transaction_id='txn_1', reference='ZCD-8003-1', amount=5000000, status='APPROVED'):
        return json.dumps({
            'event': 'transaction.updated',
            'data': {'transaction': {
                'id': transaction_id,
                'reference': reference,
                'amount_in_cents': amount,
                'currency': 'COP',
                'status': status,
            }},
        })

    def _valid_signature(self, payload):
        return hmac.new(
            b'wompi_events_mock_secret',
            payload.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

    def test_valid_checksum_processes_event(self, client, order_factory, order_item_factory, product_with_stock):
        product, variant = product_with_stock(stock=5, price=Decimal('10000.00'))
        order = order_factory(
            status='pendiente',
            order_number='ZCD-8003',
            customer_email='a@b.com',
        )
        order.payment_session_id = 'ZCD-8003-1'
        order.save(update_fields=['payment_session_id'])
        order_item_factory(order=order, variant=variant, quantity=1, price=Decimal('10000.00'))
        order.refresh_from_db()

        payload = self._payload(amount=int(order.total_amount * 100), reference='ZCD-8003-1')
        signature = self._valid_signature(payload)

        response = client.post(
            reverse('orders:wompi_webhook'),
            data=payload,
            content_type='application/json',
            HTTP_X_EVENT_CHECKSUM=signature,
        )

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.is_paid is True

    def test_invalid_checksum_returns_400(self, client, order_factory):
        order_factory(status='pendiente', order_number='ZCD-8004')

        response = client.post(
            reverse('orders:wompi_webhook'),
            data=self._payload(reference='ZCD-8004-1'),
            content_type='application/json',
            HTTP_X_EVENT_CHECKSUM='wrong-checksum',
        )

        assert response.status_code == 400
        assert not Payment.objects.filter(order__order_number='ZCD-8004').exists()

    def test_missing_checksum_returns_400(self, client, order_factory):
        order_factory(status='pendiente', order_number='ZCD-8005')

        response = client.post(
            reverse('orders:wompi_webhook'),
            data=self._payload(reference='ZCD-8005-1'),
            content_type='application/json',
        )

        assert response.status_code == 400
