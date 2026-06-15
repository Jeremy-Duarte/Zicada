from decimal import Decimal
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import models
from .models import OrderItem, Order
from .constants import FREE_SHIPPING_THRESHOLD, DEFAULT_SHIPPING_COST


@receiver([post_save, post_delete], sender=OrderItem)
def update_order_totals(sender, instance, **kwargs):
    """
    Actualiza subtotal, costo de envío y total del pedido cuando se modifica un OrderItem.
    
    HU-024 (parte) | H | Aplica regla de envío gratis:
    - Si subtotal >= FREE_SHIPPING_THRESHOLD → envío gratis (costo = 0)
    - Si subtotal < FREE_SHIPPING_THRESHOLD → restaura costo de envío por defecto
    
    Escenarios cubiertos:
    - Agregar producto que eleva subtotal por encima del umbral → envío gratis
    - Eliminar producto que baja subtotal por debajo del umbral → envío vuelve a aplicarse
    - Modificar cantidad que cruza el umbral en cualquier dirección
    """
    order = instance.order
    
    if order.status in ['entregado', 'cancelado']:
        return
    
    subtotal = order.items.aggregate(total=models.Sum('subtotal'))['total'] or Decimal('0')
    order.subtotal = subtotal
    
    # HU-024 | ESCENARIO | Aplicar o quitar envío gratis según el subtotal
    if subtotal >= FREE_SHIPPING_THRESHOLD:
        if order.shipping_cost != 0:
            order.shipping_cost = Decimal('0')
    else:
        if order.shipping_cost == 0 and order.status != 'entregado':
            order.shipping_cost = Decimal(str(DEFAULT_SHIPPING_COST))
    
    order.total_amount = subtotal + order.shipping_cost
    
    order.save(update_fields=['subtotal', 'shipping_cost', 'total_amount', 'updated_at'])