import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.orders.gateways.registry import get_gateway
from apps.orders.models import Order, Payment, PaymentEvent

logger = logging.getLogger(__name__)

PENDING_ORDER_EXPIRATION_HOURS = 24

# ---------------------------------------------------------------------------
# helpers de búsqueda
# ---------------------------------------------------------------------------

def _find_order(event: Dict[str, Any]) -> Optional[Order]:
    """Localiza el pedido asociado a un evento normalizado."""
    metadata = event.get('metadata') or {}
    order_number = metadata.get('order_number')
    if order_number:
        order = Order.objects.filter(order_number=order_number).first()
        if order:
            return order

    session_id = event.get('gateway_session_id')
    if session_id:
        order = Order.objects.filter(payment_session_id=session_id).first()
        if order:
            return order
        payment = Payment.objects.filter(gateway_session_id=session_id).select_related('order').first()
        if payment:
            return payment.order
    return None


def _get_or_create_payment(order: Order, gateway_name: str, event: Dict[str, Any]) -> Payment:
    """Recupera o crea el registro de pago asociado a un pedido y evento."""
    payment = (
        Payment.objects.filter(order=order, gateway=gateway_name)
        .order_by('-created_at')
        .first()
    )
    if payment:
        return payment
    gateway = get_gateway(gateway_name)
    amount = gateway.from_gateway_amount(event.get('amount', 0))
    return Payment.objects.create(
        order=order,
        gateway=gateway_name,
        status='pending',
        amount=amount,
        currency=event.get('currency', 'COP').upper(),
    )


# ---------------------------------------------------------------------------
# acciones de negocio
# ---------------------------------------------------------------------------

def _confirm_order(order: Order) -> None:
    """Confirma el pedido (verifica y descuenta stock) y lo marca pagado."""
    with transaction.atomic():
        if order.status == 'pendiente':
            order.confirm(user=None)
        order.is_paid = True
        order.payment_method = order.payment_method or 'sin_registrar'
        order.save(update_fields=['is_paid', 'payment_method', 'updated_at'])


def _refund_and_cancel(gateway, order: Order, payment: Payment, reason: str) -> None:
    """Reembolsa el pago y cancela el pedido liberando stock."""
    try:
        result = gateway.refund(payment)
        payment.raw_response = result
        payment.status = 'refunded'
    except Exception as exc:
        logger.exception(f'Reembolso fallido para pago {payment.id}: {exc}')
        payment.status = 'error'
        payment.error_message = str(exc)
    payment.save()

    if order.status == 'pendiente':
        try:
            order.cancel(reason=reason, user=None)
        except ValidationError as exc:
            logger.warning(f'No se pudo cancelar el pedido {order.order_number}: {exc}')


def _handle_approved(gateway, order: Order, payment: Payment, event: Dict[str, Any]) -> None:
    """Procesa un evento de pago aprobado: confirma stock o reembolsa."""
    gateway_amount = gateway.from_gateway_amount(event.get('amount', 0))
    if gateway_amount != order.total_amount:
        payment.status = 'error'
        payment.error_message = (
            f'Discrepancia de monto: esperado {order.total_amount}, '
            f'recibido {gateway_amount}'
        )
        payment.save()
        _refund_and_cancel(gateway, order, payment, 'Monto cobrado no coincide con el pedido.')
        return

    if order.status in ('entregado', 'cancelado'):
        payment.status = 'approved'
        payment.save()
        if order.status == 'cancelado':
            _refund_and_cancel(gateway, order, payment, 'Pago aprobado para pedido cancelado.')
        return

    try:
        _confirm_order(order)
        payment.status = 'approved'
        payment.processed_at = timezone.now()
        payment.save()
    except ValidationError:
        _refund_and_cancel(
            gateway,
            order,
            payment,
            'Stock insuficiente al confirmar el pago. Se devuelve el dinero.',
        )


def _handle_rejected(order: Order, payment: Payment, status: str) -> None:
    """Procesa un evento de pago rechazado o cancelado."""
    payment.status = status
    payment.processed_at = timezone.now()
    payment.save()
    if order.status == 'pendiente':
        try:
            order.cancel(reason=f'Pago rechazado por la pasarela ({status}).', user=None)
        except ValidationError as exc:
            logger.warning(f'No se pudo cancelar el pedido {order.order_number}: {exc}')


def _handle_refunded(order: Order, payment: Payment) -> None:
    """Procesa un evento de reembolso manual o automático."""
    payment.status = 'refunded'
    payment.processed_at = timezone.now()
    payment.save()
    if order.status not in ('entregado', 'cancelado'):
        try:
            order.cancel(reason='Pago reembolsado por la pasarela.', user=None)
        except ValidationError as exc:
            logger.warning(f'No se pudo cancelar el pedido {order.order_number}: {exc}')


# ---------------------------------------------------------------------------
# casos de uso públicos
# ---------------------------------------------------------------------------

def create_payment_intent(
    order: Order,
    gateway_name: str,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Crea un Payment y la intención de pago en la pasarela.
    Actualiza payment_method y payment_session_id del pedido.
    """
    gateway = get_gateway(gateway_name)
    payment = Payment.objects.create(
        order=order,
        gateway=gateway_name,
        status='pending',
        amount=order.total_amount,
        currency='COP',
    )

    base_url = settings.SITE_URL
    success_url = success_url or f'{base_url}{reverse("orders:order_confirmation", kwargs={"order_number": order.order_number})}'
    cancel_url = cancel_url or f'{base_url}{reverse("orders:cart_detail")}'

    result = gateway.create_intent(order, payment, success_url, cancel_url)

    payment.gateway_session_id = result['gateway_session_id']
    payment.raw_response = result.get('raw_response', {})
    payment.save(update_fields=['gateway_session_id', 'raw_response', 'updated_at'])

    order.payment_method = gateway_name
    order.payment_session_id = result['gateway_session_id']
    order.save(update_fields=['payment_method', 'payment_session_id', 'updated_at'])

    return result


def process_payment_event(gateway_name: str, event: Dict[str, Any]) -> None:
    """
    Procesa un evento de webhook ya normalizado y verificado.
    Garantiza idempotencia mediante PaymentEvent.
    """
    gateway = get_gateway(gateway_name)
    event_id = gateway.get_event_id(event)

    if PaymentEvent.objects.filter(gateway=gateway_name, event_id=event_id).exists():
        logger.info(f'Evento duplicado ignorado: {gateway_name} {event_id}')
        return

    order = _find_order(event)
    if order is None:
        logger.error(f'Pedido no encontrado para evento {event_id} ({gateway_name})')
        return

    payment = _get_or_create_payment(order, gateway_name, event)
    payment.gateway_transaction_id = event.get('gateway_transaction_id', '') or payment.gateway_transaction_id
    payment.raw_request = event.get('raw', {})
    payment.save(update_fields=['gateway_transaction_id', 'raw_request', 'updated_at'])

    with transaction.atomic():
        PaymentEvent.objects.create(
            payment=payment,
            gateway=gateway_name,
            event_id=event_id,
            event_type=event.get('event_type', ''),
        )

    status = event.get('status')
    if status == 'approved':
        _handle_approved(gateway, order, payment, event)
    elif status in ('rejected', 'cancelled'):
        _handle_rejected(order, payment, status)
    elif status == 'refunded':
        _handle_refunded(order, payment)
    else:
        payment.status = 'error'
        payment.error_message = f'Estado desconocido del evento: {status}'
        payment.save()

    _notify_result(order, status)


def cancel_expired_pending_orders() -> int:
    """Cancela pedidos pendientes sin pago aprobado tras el periodo configurado."""
    threshold = timezone.now() - timedelta(hours=PENDING_ORDER_EXPIRATION_HOURS)
    expired = Order.objects.filter(
        status='pendiente',
        created_at__lte=threshold,
    ).exclude(payments__status='approved')
    count = 0
    for order in expired:
        try:
            order.cancel(reason='Pedido expirado por falta de pago.', user=None)
            count += 1
        except ValidationError as exc:
            logger.warning(f'No se pudo expirar el pedido {order.order_number}: {exc}')
    return count


def _notify_result(order: Order, status: str) -> None:
    """Encola la notificación por correo según el resultado del pago."""
    from apps.orders.tasks import notify_payment_result

    notify_payment_result.delay(order.id, status)
