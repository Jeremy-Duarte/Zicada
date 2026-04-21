from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
import uuid


class Order(models.Model):
    # Pedido de cliente
    
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('preparando', 'Preparando'),
        ('listo', 'Listo para envío'),
        ('en_camino', 'En camino'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    # Identificación
    order_number = models.CharField(
        max_length=8,
        unique=True,
        verbose_name='Número de pedido',
        help_text='Formato: ZCD-0001, ZCD-0002, ZCE-0001...'
    )
    tracking_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Token de seguimiento'
    )
    
    # Datos del cliente
    customer_name = models.CharField(
        max_length=200,
        verbose_name='Nombre completo'
    )
    customer_phone = models.CharField(
        max_length=20,
        verbose_name='Teléfono de contacto'
    )
    customer_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Correo electrónico',
        help_text='Para enviar confirmación y seguimiento'
    )
    
    # Dirección y envío
    shipping_address = models.TextField(
        verbose_name='Dirección de envío'
    )
    delivery_notes = models.TextField(
        blank=True,
        verbose_name='Notas adicionales',
        help_text='Ej: Dejar con el portero, llamar antes de llegar'
    )
    
    # Financiero
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Subtotal',
        help_text='Suma de productos sin envío'
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Costo de envío'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Total',
        help_text='subtotal + shipping_cost'
    )
    is_paid = models.BooleanField(
        default=False,
        verbose_name='Pagado',
        help_text='Indica si el cliente pagó contraentrega'
    )
    
    # Estado
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendiente',
        verbose_name='Estado'
    )
    cancelled_reason = models.TextField(
        blank=True,
        verbose_name='Motivo de cancelación'
    )
    
    assigned_delivery_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_orders',
        verbose_name='Entregador asignado',
        limit_choices_to={'is_delivery': True}
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creado el'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Actualizado el'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders_created',
        verbose_name='Creado por'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders_updated',
        verbose_name='Actualizado por'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
    
    def can_transition_to(self, new_status):
        allowed = {
            'pendiente': ['confirmado', 'cancelado'],
            'confirmado': ['preparando', 'cancelado'],
            'preparando': ['listo', 'cancelado'],
            'listo': ['en_camino', 'cancelado'],
            'en_camino': ['entregado', 'cancelado'],
            'entregado': [],
            'cancelado': [],
        }
        return new_status in allowed.get(self.status, [])

    def confirm(self, user=None):
        """Cambia a confirmado y reduce stock."""
        if not self.can_transition_to('confirmado'):
            raise ValidationError(f'No se puede confirmar un pedido en estado {self.status}.')
        self.status = 'confirmado'
        self.save()
        # Reducir stock de cada variante
        for item in self.items.all():
            if item.variant:
                if item.variant.stock < item.quantity:
                    raise ValidationError(f'Stock insuficiente para {item.product_name_snapshot}')
                item.variant.stock -= item.quantity
                item.variant.save()
        if user:
            self.updated_by = user
            self.save(update_fields=['updated_by'])

    def cancel(self, reason, user=None):
        # Cancela el pedido y libera stock
        if self.status == 'entregado':
            raise ValidationError('No se puede cancelar un pedido ya entregado.')
        if not reason:
            raise ValidationError('Debe indicar un motivo de cancelación.')
        self.status = 'cancelado'
        self.cancelled_reason = reason
        self.save()
        # Liberar stock
        for item in self.items.all():
            if item.variant:
                item.variant.stock += item.quantity
                item.variant.save()
        if user:
            self.updated_by = user
            self.save(update_fields=['updated_by'])

    def mark_as_ready(self, user=None):
        if not self.can_transition_to('listo'):
            raise ValidationError(f'No se puede marcar como listo un pedido en estado {self.status}.')
        self.status = 'listo'
        self.save()
        if user:
            self.updated_by = user
            self.save(update_fields=['updated_by'])

    def mark_as_preparing(self, user=None):
        if not self.can_transition_to('preparando'):
            raise ValidationError(f'No se puede marcar como preparando un pedido en estado {self.status}.')
        self.status = 'preparando'
        self.save()
        if user:
            self.updated_by = user
            self.save(update_fields=['updated_by'])

    def assign_delivery(self, delivery_user, user=None):
        if self.status != 'listo':
            raise ValidationError('Solo se puede asignar un repartidor a pedidos listos.')
        self.assigned_delivery_user = delivery_user
        self.status = 'en_camino'
        self.save()
        if user:
            self.updated_by = user
            self.save(update_fields=['updated_by'])

    def mark_as_delivered(self, user=None):
        if self.status != 'en_camino':
            raise ValidationError('Solo se puede entregar un pedido que está en camino.')
        self.status = 'entregado'
        self.is_paid = True
        self.save()
        if user:
            self.updated_by = user
            self.save(update_fields=['updated_by'])

    def __str__(self):
        return f"{self.order_number} - {self.customer_name}"
    
    def clean(self):
            if self.subtotal < 0:
                raise ValidationError({'subtotal': 'El subtotal no puede ser negativo.'})
            
            if self.shipping_cost < 0:
                raise ValidationError({'shipping_cost': 'El costo de envío no puede ser negativo.'})
            
            if self.total_amount < 0:
                raise ValidationError({'total_amount': 'El total no puede ser negativo.'})
            
            if self.status == 'entregado' and not self.is_paid:
                raise ValidationError({'is_paid': 'Un pedido entregado debe estar marcado como pagado.'})
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            last_order = Order.objects.order_by('-id').first()
            if last_order and last_order.order_number:
                try:
                    num = int(last_order.order_number.split('-')[1])
                    self.order_number = f"ZCD-{str(num + 1).zfill(4)}"
                except (IndexError, ValueError):
                    self.order_number = "ZCD-0001"
            else:
                self.order_number = "ZCD-0001"
        
        self.total_amount = self.subtotal + self.shipping_cost
        self.full_clean()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    # Productos dentro de un pedido (relacionado con la variante)

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Pedido'
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items',
        verbose_name='Variante',
        help_text='Producto + talla al momento de la compra'
    )
    product_name_snapshot = models.CharField(
        max_length=200,
        verbose_name='Nombre del producto'
    )
    size_snapshot = models.CharField(
        max_length=10,
        verbose_name='Talla'
    )
    quantity = models.PositiveIntegerField(
        verbose_name='Cantidad'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio unitario'
    )
    stock_snapshot = models.PositiveIntegerField(
        verbose_name='Stock en el momento',
        help_text='Para auditoría'
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Subtotal',
        help_text='unit_price * quantity'
    )
    
    class Meta:
        ordering = ['id']
        verbose_name = 'Item del pedido'
        verbose_name_plural = 'Items del pedido'
    
    def __str__(self):
        return f"{self.order.order_number} - {self.product_name_snapshot} x{self.quantity}"
    
    def clean(self):
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError({'quantity': 'La cantidad debe ser mayor a 0.'})
        
        if self.unit_price is not None and self.unit_price < 0:
            raise ValidationError({'unit_price': 'El precio unitario no puede ser negativo.'})
        
        if self.stock_snapshot is not None and self.stock_snapshot < 0:
            raise ValidationError({'stock_snapshot': 'El stock snapshot no puede ser negativo.'})
    
    def save(self, *args, **kwargs):
        if self.variant:
            if not self.product_name_snapshot:
                self.product_name_snapshot = self.variant.product.name
            if not self.size_snapshot:
                self.size_snapshot = self.variant.size.name
            if not self.unit_price:
                self.unit_price = self.variant.product.price
            if not self.stock_snapshot:
                self.stock_snapshot = self.variant.stock
        
        self.unit_price = self.unit_price or 0
        self.quantity = self.quantity or 0
        self.subtotal = self.unit_price * self.quantity
        
        self.full_clean()
        super().save(*args, **kwargs)