import logging

from celery import shared_task

from apps.orders.email import send_order_confirmation_email, send_order_cancellation_email
from apps.orders.models import Order

logger = logging.getLogger(__name__)


@shared_task
def notify_payment_result(order_id: int, status: str) -> None:
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
