from decimal import Decimal
from unittest import mock

import pytest
from django.utils import timezone
from datetime import timedelta

from apps.orders.models import Order, Payment, PaymentEvent
from apps.orders import use_cases


@pytest.mark.django_db
class TestCreatePaymentIntent:
    def test_stripe_intent_updates_order_and_payment(self, order_factory):
        order = order_factory(
            status='pendiente',
            order_number='ZCD-9001',
            customer_email='a@b.com',
            subtotal=Decimal('100000.00'),
            shipping_cost=Decimal('0'),
        )
        with mock.patch('apps.orders.gateways.stripe_gateway.stripe.checkout.Session.create', return_value=mock.Mock(
            id='cs_test_1',
            url='https://checkout.stripe.com/c/pay',
            to_dict_recursive=lambda: {'id': 'cs_test_1'},
        )):
            result = use_cases.create_payment_intent(order, 'stripe')

        assert result['redirect_url'] == 'https://checkout.stripe.com/c/pay'
        order.refresh_from_db()
        assert order.payment_method == 'stripe'
        assert order.payment_session_id == 'cs_test_1'
        payment = Payment.objects.get(order=order)
        assert payment.gateway == 'stripe'
        assert payment.status == 'pending'
        assert payment.gateway_session_id == 'cs_test_1'

    def test_wompi_intent_returns_widget_data(self, order_factory):
        order = order_factory(
            status='pendiente',
            order_number='ZCD-9002',
            customer_email='a@b.com',
            subtotal=Decimal('50000.00'),
            shipping_cost=Decimal('0'),
        )
        result = use_cases.create_payment_intent(order, 'wompi')
        raw = result['raw_response']
        assert raw['currency'] == 'COP'
        assert raw['amount_in_cents'] == 5000000
        assert raw['reference'] == f'{order.order_number}-1'
        assert len(raw['signature']) == 64
        order.refresh_from_db()
        assert order.payment_method == 'wompi'

    def test_unknown_gateway_raises(self, order_factory):
        order = order_factory(status='pendiente')
        with pytest.raises(ValueError):
            use_cases.create_payment_intent(order, 'nope')


@pytest.mark.django_db
class TestProcessPaymentEvent:
    def _approved_event(self, session_id='cs_1', amount=5000000):
        return {
            'event_id': 'evt_1',
            'event_type': 'checkout.session.completed',
            'gateway_session_id': session_id,
            'gateway_transaction_id': 'pi_1',
            'amount': amount,
            'currency': 'cop',
            'status': 'approved',
            'metadata': {},
            'raw': {},
        }

    def test_approved_event_confirms_order_and_stock(self, order_factory, order_item_factory, product_with_stock):
        product, variant = product_with_stock(stock=5, price=Decimal('10000.00'))
        order = order_factory(
            status='pendiente',
            order_number='ZCD-9003',
            customer_email='a@b.com',
        )
        order.payment_session_id = 'cs_1'
        order.save(update_fields=['payment_session_id'])
        order_item_factory(order=order, variant=variant, quantity=2, price=Decimal('10000.00'))
        order.refresh_from_db()

        use_cases.process_payment_event('stripe', self._approved_event(amount=int(order.total_amount * 100)))

        order.refresh_from_db()
        assert order.status == 'confirmado'
        assert order.is_paid is True
        variant.refresh_from_db()
        assert variant.stock == 3
        payment = Payment.objects.get(order=order)
        assert payment.status == 'approved'
        assert PaymentEvent.objects.filter(gateway='stripe', event_id='evt_1').exists()

    def test_duplicate_event_is_ignored(self, order_factory, order_item_factory, product_with_stock):
        product, variant = product_with_stock(stock=5, price=Decimal('10000.00'))
        order = order_factory(
            status='pendiente',
            order_number='ZCD-9004',
            customer_email='a@b.com',
        )
        order.payment_session_id = 'cs_1'
        order.save(update_fields=['payment_session_id'])
        order_item_factory(order=order, variant=variant, quantity=2, price=Decimal('10000.00'))
        order.refresh_from_db()

        use_cases.process_payment_event('stripe', self._approved_event(amount=int(order.total_amount * 100)))
        order.refresh_from_db()
        assert order.status == 'confirmado'

        order.status = 'pendiente'
        order.is_paid = False
        order.save()
        use_cases.process_payment_event('stripe', self._approved_event(amount=int(order.total_amount * 100)))
        order.refresh_from_db()
        assert order.status == 'pendiente'

    def test_stock_shortage_triggers_refund_and_cancel(self, order_factory, order_item_factory, product_with_stock):
        product, variant = product_with_stock(stock=1, price=Decimal('10000.00'))
        order = order_factory(
            status='pendiente',
            order_number='ZCD-9005',
            customer_email='a@b.com',
        )
        order.payment_session_id = 'cs_1'
        order.save(update_fields=['payment_session_id'])
        order_item_factory(order=order, variant=variant, quantity=2, price=Decimal('10000.00'))
        order.refresh_from_db()

        with mock.patch('apps.orders.gateways.stripe_gateway.StripeGateway.refund', return_value={'id': 're_1'}):
            use_cases.process_payment_event('stripe', self._approved_event(amount=int(order.total_amount * 100)))

        order.refresh_from_db()
        assert order.status == 'cancelado'
        assert 'Stock insuficiente' in order.cancelled_reason
        variant.refresh_from_db()
        assert variant.stock == 1
        payment = Payment.objects.get(order=order)
        assert payment.status == 'refunded'

    def test_rejected_event_cancels_pending_order(self, order_factory):
        order = order_factory(
            status='pendiente',
            order_number='ZCD-9006',
            customer_email='a@b.com',
        )
        order.payment_session_id = 'cs_1'
        order.save(update_fields=['payment_session_id'])

        event = {
            'event_id': 'evt_rej',
            'event_type': 'transaction.updated',
            'gateway_session_id': 'cs_1',
            'gateway_transaction_id': 'txn_1',
            'amount': 1000000,
            'currency': 'cop',
            'status': 'rejected',
            'metadata': {},
            'raw': {},
        }
        use_cases.process_payment_event('stripe', event)

        order.refresh_from_db()
        assert order.status == 'cancelado'
        payment = Payment.objects.get(order=order)
        assert payment.status == 'rejected'


@pytest.mark.django_db
class TestCancelExpiredPendingOrders:
    def test_expires_only_old_pending_orders(self, order_factory):
        fresh = order_factory(status='pendiente', order_number='ZCD-9010')
        old = order_factory(status='pendiente', order_number='ZCD-9011')
        confirmed = order_factory(status='confirmado', order_number='ZCD-9012')

        Order.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - timedelta(hours=30)
        )

        count = use_cases.cancel_expired_pending_orders()

        assert count == 1
        fresh.refresh_from_db()
        old.refresh_from_db()
        confirmed.refresh_from_db()
        assert fresh.status == 'pendiente'
        assert old.status == 'cancelado'
        assert confirmed.status == 'confirmado'
