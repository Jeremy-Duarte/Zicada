import hashlib
import hmac
import json
from decimal import Decimal
from unittest import mock

import pytest

from apps.orders.gateways.registry import get_gateway, list_gateways
from apps.orders.gateways.stripe_gateway import StripeGateway
from apps.orders.gateways.wompi_gateway import WompiGateway


@pytest.mark.django_db
class TestGatewayRegistry:
    def test_gateways_are_registered(self):
        assert set(list_gateways().keys()) == {'stripe', 'wompi'}

    def test_get_gateway_returns_instance(self):
        assert get_gateway('stripe').name == 'stripe'
        assert get_gateway('wompi').name == 'wompi'

    def test_get_unknown_gateway_raises(self):
        with pytest.raises(ValueError):
            get_gateway('nope')


@pytest.mark.django_db
class TestStripeGateway:
    def test_to_gateway_amount_converts_cop_to_cents(self):
        gateway = StripeGateway()
        assert gateway.to_gateway_amount(Decimal('50000.00')) == 5000000

    def test_from_gateway_amount_converts_cents_to_cop(self):
        gateway = StripeGateway()
        assert gateway.from_gateway_amount(5000000) == Decimal('50000.00')

    def test_verify_signature_valid(self):
        gateway = StripeGateway()
        secret = 'whsec_test'
        payload = b'{"type": "checkout.session.completed"}'
        signature = 't=123,v1=fake'
        with mock.patch('stripe.Webhook.construct_event', return_value={}):
            assert gateway.verify_signature(payload, signature, secret) is True

    def test_verify_signature_invalid(self):
        gateway = StripeGateway()
        import stripe
        with mock.patch('stripe.Webhook.construct_event', side_effect=stripe.error.SignatureVerificationError('bad', 's')):
            assert gateway.verify_signature(b'{}', 'bad-sig', 'whsec') is False

    def test_parse_event_normalizes_completed(self):
        gateway = StripeGateway()
        event = {
            'id': 'evt_123',
            'type': 'checkout.session.completed',
            'data': {'object': {
                'id': 'cs_456',
                'payment_intent': 'pi_789',
                'amount_total': 5000000,
                'currency': 'cop',
                'metadata': {'order_number': 'ZCD-0001', 'payment_id': '1'},
            }},
        }
        with mock.patch('stripe.Webhook.construct_event', return_value=event):
            normalized = gateway.parse_event(b'{}', 'sig')
        assert normalized['event_id'] == 'evt_123'
        assert normalized['event_type'] == 'checkout.session.completed'
        assert normalized['gateway_session_id'] == 'cs_456'
        assert normalized['gateway_transaction_id'] == 'pi_789'
        assert normalized['amount'] == 5000000
        assert normalized['status'] == 'approved'

    def test_parse_event_refunded(self):
        gateway = StripeGateway()
        event = {
            'id': 'evt_ref',
            'type': 'charge.refunded',
            'data': {'object': {
                'id': 'ch_1',
                'amount_total': 5000000,
                'currency': 'cop',
                'metadata': {},
            }},
        }
        with mock.patch('stripe.Webhook.construct_event', return_value=event):
            normalized = gateway.parse_event(b'{}', 'sig')
        assert normalized['status'] == 'refunded'


@pytest.mark.django_db
class TestWompiGateway:
    def test_to_gateway_amount_uses_amount_in_cents(self):
        gateway = WompiGateway()
        assert gateway.to_gateway_amount(Decimal('50000.00')) == 5000000

    def test_from_gateway_amount_converts_cents_to_cop(self):
        gateway = WompiGateway()
        assert gateway.from_gateway_amount(5000000) == Decimal('50000.00')

    def test_verify_signature_valid(self):
        gateway = WompiGateway()
        secret = 'wompi_events_mock_secret'
        body = b'{"event": "transaction.updated"}'
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        assert gateway.verify_signature(body, expected, secret) is True

    def test_verify_signature_invalid(self):
        gateway = WompiGateway()
        assert gateway.verify_signature(b'{}', 'wrong-checksum', 'secret') is False

    def test_verify_signature_empty(self):
        gateway = WompiGateway()
        assert gateway.verify_signature(b'{}', '', 'secret') is False

    def test_parse_event_approved(self):
        gateway = WompiGateway()
        payload = json.dumps({
            'event': 'transaction.updated',
            'data': {'transaction': {
                'id': 'txn_1',
                'reference': 'ZCD-0001-1',
                'amount_in_cents': 5000000,
                'currency': 'COP',
                'status': 'APPROVED',
            }},
        }).encode()
        normalized = gateway.parse_event(payload, 'sig')
        assert normalized['event_id'] == 'txn_1-APPROVED'
        assert normalized['gateway_transaction_id'] == 'txn_1'
        assert normalized['gateway_session_id'] == 'ZCD-0001-1'
        assert normalized['amount'] == 5000000
        assert normalized['status'] == 'approved'

    def test_parse_event_declined(self):
        gateway = WompiGateway()
        payload = json.dumps({
            'event': 'transaction.updated',
            'data': {'transaction': {
                'id': 'txn_2',
                'reference': 'ZCD-0002-1',
                'amount_in_cents': 10000,
                'currency': 'COP',
                'status': 'DECLINED',
            }},
        }).encode()
        normalized = gateway.parse_event(payload, 'sig')
        assert normalized['status'] == 'rejected'

    def test_build_integrity_signature_is_sha256(self):
        gateway = WompiGateway()
        signature = gateway.build_integrity_signature('ref', 5000000, 'COP')
        assert len(signature) == 64
