import logging
from typing import Any, Dict

from apps.orders.email import send_order_confirmation_email, send_order_cancellation_email
from apps.orders.models import Order

logger = logging.getLogger(__name__)


def _notify_payment_result(order_id: int, status: str) -> None:
    """Notifica por correo el resultado del pago de un pedido."""
    order = Order.objects.filter(id=order_id).first()
    if not order:
        logger.warning(f'Pedido {order_id} no encontrado para notificación.')
        return
    if not order.customer_email:
        return

    try:
        if status == 'approved':
            send_order_confirmation_email(order)
        else:
            send_order_cancellation_email(order)
    except Exception:
        logger.exception(f'Fallo al notificar pedido {order.order_number}')


def _process_payment_event_task(gateway_name: str, event: Dict[str, Any]) -> None:
    """Procesa un evento de webhook normalizado y verificado."""
    from apps.orders.use_cases import process_payment_event

    process_payment_event(gateway_name, event)


try:
    from celery import shared_task
    notify_payment_result = shared_task(_notify_payment_result)
    process_payment_event_task = shared_task(_process_payment_event_task)
except ImportError:
    notify_payment_result = _notify_payment_result
    process_payment_event_task = _process_payment_event_task
