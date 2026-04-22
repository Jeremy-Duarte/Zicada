from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from .models import OrderItem


@receiver(post_save, sender=OrderItem)
def update_order_totals(sender, instance, created, **kwargs):
    order = instance.order
    subtotal = order.items.aggregate(total=models.Sum('subtotal'))['total'] or 0
    order.subtotal = subtotal
    order.total_amount = subtotal + (order.shipping_cost or 0)
    order.save(update_fields=['subtotal', 'total_amount'])