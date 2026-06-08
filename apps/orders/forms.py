from django import forms
from django.core.exceptions import ValidationError
from .models import Order, OrderItem
from apps.products.models import ProductVariant
from .constants import (
    DEFAULT_SHIPPING_COST, 
    FREE_SHIPPING_THRESHOLD,
    MAX_QUANTITY_PER_ITEM
)
from apps.core.crud.mixins import FormStyleMixin
from apps.core.crud.widgets import DeliveryUserRadioWidget
from django.contrib.auth import get_user_model

# =============================================================================
# CONSTANTES LOCALES
# =============================================================================
ERROR_ORDER_NOT_SPECIFIED = 'Pedido no especificado.'
ERROR_CONFIRM_REQUIRED = 'Debes confirmar la acción.'
ERROR_INVALID_STATUS_TRANSITION = 'No se puede cambiar de "{from_status}" a "{to_status}". Transición no permitida.'
ERROR_INVALID_QUANTITY = 'La cantidad debe ser mayor a 0.'
ERROR_MAX_QUANTITY_EXCEEDED = f'La cantidad máxima por item es {MAX_QUANTITY_PER_ITEM}.'
ERROR_STOCK_INSUFFICIENT = 'Stock insuficiente. Solo hay {stock} unidades disponibles.'
ERROR_CANNOT_MODIFY_DELIVERED = 'No se puede modificar un pedido ya entregado.'
ERROR_PRODUCT_ALREADY_EXISTS = 'El producto "{product}" - Talla {size} ya existe en este pedido. Edita la cantidad del existente en lugar de agregar uno nuevo.'
ERROR_CONFIRM_MISMATCH = 'Debes escribir "ELIMINAR" exactamente para confirmar.'
ERROR_CANNOT_UNPAID = 'No se puede desmarcar un pedido ya pagado.'
ERROR_SHIPPING_NEGATIVE = 'El costo de envío no puede ser negativo.'
ERROR_FREE_SHIPPING_VIOLATION = 'Este pedido califica para envío gratis (subtotal >= ${threshold:,.0f}). El costo de envío debe ser 0.'
ERROR_ONLY_PENDING_CAN_CONFIRM = 'Solo se pueden confirmar pedidos en estado "Pendiente". Estado actual: {status}'
ERROR_NO_ITEMS_TO_CONFIRM = 'No se puede confirmar un pedido sin items.'
ERROR_CANNOT_CANCEL_DELIVERED = 'No se puede cancelar un pedido ya entregado.'
ERROR_CANNOT_CANCEL_ALREADY_CANCELLED = 'Este pedido ya está cancelado.'
ERROR_REASON_TOO_SHORT = 'El motivo de cancelación debe tener al menos 10 caracteres.'
ERROR_ONLY_READY_CAN_ASSIGN = 'Solo se puede asignar repartidor a pedidos en estado "Listo para envío". Estado actual: {status}'
ERROR_ONLY_ON_THE_WAY_CAN_DELIVER = 'Solo se puede entregar pedidos que están "En camino". Estado actual: {status}'
ERROR_NO_DELIVERY_ASSIGNED = 'No se puede entregar un pedido sin repartidor asignado.'
ERROR_ORDER_ALREADY_PAID = 'Este pedido ya está pagado.'
ERROR_NO_PAYMENT_METHOD = 'Debes seleccionar al menos un método de notificación (email o WhatsApp).'
ERROR_NO_EMAIL_FOR_NOTIFICATION = 'No se puede enviar por email porque el cliente no tiene correo registrado.'
ERROR_INVALID_PHONE_LENGTH = 'El número de teléfono debe tener entre 7 y 15 dígitos.'
ERROR_ONLY_PENDING_OR_CONFIRMED_CAN_ADD_ITEMS = 'Solo se pueden agregar items a pedidos pendientes o confirmados.'
ERROR_PRODUCT_ALREADY_IN_ORDER = 'El producto "{product}" - Talla {size} ya existe en este pedido. Edita la cantidad del existente en lugar de agregar uno nuevo.'
ERROR_CANNOT_MODIFY_ITEM_STATUS = 'Solo se pueden modificar items de pedidos pendientes o confirmados.'
ERROR_ONLY_PENDING_CAN_PAY = 'Solo se pueden generar links de pago para pedidos pendientes. Estado actual: {status}'

# =============================================================================
# FORMULARIOS
# =============================================================================

class CheckoutOrderForm(FormStyleMixin, forms.Form):
    """Formulario para la creación de un pedido en el checkout."""
    
    customer_name = forms.CharField(
        max_length=200,
        min_length=3,
        required=True,
        label='Nombre completo',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: María Gómez Rodríguez',
            'id': 'customer_name'
        }),
        error_messages={
            'required': 'Por favor ingresa tu nombre completo.',
            'min_length': 'El nombre debe tener al menos 3 caracteres.',
            'max_length': 'El nombre no puede exceder los 200 caracteres.'
        }
    )
    
    customer_phone = forms.CharField(
        max_length=20,
        required=True,
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: 3001234567',
            'id': 'customer_phone'
        }),
        error_messages={
            'required': 'Por favor ingresa tu número de teléfono.'
        }
    )
    
    customer_email = forms.EmailField(
        required=False,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'placeholder': 'Ej: maria@correo.com',
            'id': 'customer_email'
        }),
        error_messages={
            'invalid': 'Ingresa un correo electrónico válido.'
        }
    )
    
    shipping_address = forms.CharField(
        required=True,
        label='Dirección de envío',
        min_length=5,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Calle, número, barrio, ciudad, referencia',
            'id': 'shipping_address'
        }),
        error_messages={
            'required': 'Por favor ingresa tu dirección de envío completa.'
        }
    )
    
    delivery_notes = forms.CharField(
        required=False,
        label='Notas adicionales',
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Ej: Dejar con el portero, llamar antes de llegar...',
            'id': 'delivery_notes'
        })
    )
    
    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone', '')
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) < 7 or len(digits) > 15:
            raise ValidationError(ERROR_INVALID_PHONE_LENGTH)
        return digits


class OrderCreateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para crear pedidos manuales desde backoffice."""
    
    class Meta:
        model = Order
        fields = [
            'customer_name',
            'customer_phone',
            'customer_email',
            'shipping_address',
            'delivery_notes',
            'shipping_cost',
            'is_paid',
        ]
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
            'delivery_notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['shipping_cost'].initial = DEFAULT_SHIPPING_COST
        self.fields['is_paid'].initial = False
        self.fields['is_paid'].help_text = 'Marcar como pagado si el cliente ya pagó (ej: contraentrega, transferencia)'
    
    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone', '')
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) < 7:
            raise ValidationError('El teléfono debe tener al menos 7 dígitos.')
        if len(digits) > 15:
            raise ValidationError('El teléfono es demasiado largo (máximo 15 dígitos).')
        return digits
    
    def clean_shipping_cost(self):
        cost = self.cleaned_data.get('shipping_cost', 0)
        if cost < 0:
            raise ValidationError(ERROR_SHIPPING_NEGATIVE)
        return cost


class OrderUpdateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para actualizar pedidos existentes desde backoffice."""
    
    class Meta:
        model = Order
        fields = [
            'customer_name',
            'customer_phone',
            'customer_email',
            'shipping_address',
            'delivery_notes',
            'shipping_cost',
            'is_paid',
            'status',
            'assigned_delivery_user',
        ]
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
            'delivery_notes': forms.Textarea(attrs={'rows': 2}),
            'status': forms.Select(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            user_model = get_user_model()
            self.fields['assigned_delivery_user'].queryset = user_model.objects.filter(
                is_delivery=True
            ).order_by('username')
            
            if self.instance.status in ['entregado', 'cancelado']:
                self.fields['status'].disabled = True
                self.fields['assigned_delivery_user'].disabled = True
                self.fields['shipping_cost'].disabled = True
                
            if self.instance.is_paid:
                self.fields['is_paid'].disabled = True
                self.fields['is_paid'].help_text = 'Este pedido ya está pagado y no puede modificarse.'
    
    def clean_status(self):
        new_status = self.cleaned_data.get('status')
        
        if self.instance and self.instance.pk:
            if new_status != self.instance.status:
                if not self.instance.can_transition_to(new_status):
                    from_status = self.instance.get_status_display()
                    to_status = dict(Order.STATUS_CHOICES).get(new_status, new_status)
                    raise ValidationError(ERROR_INVALID_STATUS_TRANSITION.format(
                        from_status=from_status, to_status=to_status
                    ))
        return new_status
    
    def clean_is_paid(self):
        is_paid = self.cleaned_data.get('is_paid')
        status = self.cleaned_data.get('status', self.instance.status if self.instance else 'pendiente')
        
        if status == 'entregado' and not is_paid:
            raise ValidationError('Un pedido entregado debe estar marcado como pagado.')
        
        if self.instance and self.instance.is_paid and not is_paid:
            raise ValidationError(ERROR_CANNOT_UNPAID)
        
        return is_paid
    
    def clean_shipping_cost(self):
        new_cost = self.cleaned_data.get('shipping_cost')
        subtotal = self.instance.subtotal if self.instance else 0
        
        if new_cost < 0:
            raise ValidationError(ERROR_SHIPPING_NEGATIVE)
        
        if subtotal >= FREE_SHIPPING_THRESHOLD and new_cost > 0:
            raise ValidationError(ERROR_FREE_SHIPPING_VIOLATION.format(threshold=FREE_SHIPPING_THRESHOLD))
        
        return new_cost


class OrderConfirmForm(FormStyleMixin, forms.Form):
    """Formulario específico para confirmar un pedido manualmente."""
    
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que deseo confirmar este pedido',
        help_text='Esta acción reducirá el stock de los productos asociados.'
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.order:
            raise ValidationError(ERROR_ORDER_NOT_SPECIFIED)
        
        if self.order.status != 'pendiente':
            raise ValidationError(ERROR_ONLY_PENDING_CAN_CONFIRM.format(status=self.order.get_status_display()))
        
        if not self.order.items.exists():
            raise ValidationError(ERROR_NO_ITEMS_TO_CONFIRM)
        
        stock_errors = []
        for item in self.order.items.all():
            if item.variant and item.quantity > item.variant.stock:
                stock_errors.append(
                    f'{item.product_name_snapshot} ({item.size_snapshot}): '
                    f'solicitado {item.quantity}, disponible {item.variant.stock}'
                )
        
        if stock_errors:
            raise ValidationError(
                'Stock insuficiente para continuar:\n- ' + '\n- '.join(stock_errors)
            )
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError(ERROR_CONFIRM_REQUIRED)
        
        return cleaned_data


class OrderCancelForm(FormStyleMixin, forms.Form):
    """Formulario específico para cancelar pedidos."""
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ej: Cliente solicitó cancelación, producto agotado, error en dirección...'}),
        label='Motivo de cancelación',
        required=True,
        max_length=500
    )
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que deseo cancelar este pedido',
        help_text='Esta acción liberará el stock de los productos asociados (si ya estaba confirmado).'
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
    
    def clean_reason(self):
        reason = self.cleaned_data.get('reason', '').strip()
        if len(reason) < 10:
            raise ValidationError(ERROR_REASON_TOO_SHORT)
        return reason
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.order:
            raise ValidationError(ERROR_ORDER_NOT_SPECIFIED)
        
        if self.order.status == 'entregado':
            raise ValidationError(ERROR_CANNOT_CANCEL_DELIVERED)
        
        if self.order.status == 'cancelado':
            raise ValidationError(ERROR_CANNOT_CANCEL_ALREADY_CANCELLED)
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError(ERROR_CONFIRM_REQUIRED)
        
        return cleaned_data


class OrderChangeStatusForm(FormStyleMixin, forms.Form):
    """Formulario para cambios rápidos de estado."""
    
    new_status = forms.ChoiceField(
        choices=[],
        label='Nuevo estado',
        widget=forms.Select()
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label='Notas (opcional)',
        help_text='Notas internas sobre este cambio de estado'
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        if self.order:
            choices = [
                (status, label) for status, label in Order.STATUS_CHOICES
                if self.order.can_transition_to(status)
            ]
            self.fields['new_status'].choices = choices
            
            if not choices:
                self.fields['new_status'].disabled = True
                self.fields['new_status'].help_text = 'No hay transiciones disponibles para este estado.'
    
    def clean_new_status(self):
        new_status = self.cleaned_data.get('new_status')
        
        if not self.order:
            raise ValidationError(ERROR_ORDER_NOT_SPECIFIED)
        
        if not self.order.can_transition_to(new_status):
            from_status = self.order.get_status_display()
            to_status = dict(Order.STATUS_CHOICES).get(new_status, new_status)
            raise ValidationError(ERROR_INVALID_STATUS_TRANSITION.format(
                from_status=from_status, to_status=to_status
            ))
        
        return new_status


class OrderAssignDeliveryForm(FormStyleMixin, forms.Form):
    """Formulario para asignar repartidor desde backoffice."""
    
    delivery_user = forms.ModelChoiceField(
        queryset=None,
        label='Repartidor asignado',
        required=True,
        widget=DeliveryUserRadioWidget()
    )
    confirm = forms.BooleanField(
        required=True,
        label='Confirmar asignación',
        help_text='Esto cambiará el estado del pedido a "En camino"',
        widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-zicada-accent rounded'})
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        user_model = get_user_model()
        self.fields['delivery_user'].queryset = user_model.objects.filter(
            is_delivery=True, 
            is_active=True
        ).only('id', 'first_name', 'last_name', 'username', 'phone').order_by('first_name', 'last_name')
        
        self.fields['delivery_user'].label_from_instance = lambda u: f"{u.get_full_name()} - {u.phone or 'Sin teléfono'}"
        
        if self.order and self.order.assigned_delivery_user:
            self.fields['delivery_user'].initial = self.order.assigned_delivery_user
        
        self.fields['delivery_user'].help_text = "Selecciona el repartidor que realizará la entrega"
    
    def clean_delivery_user(self):
        delivery_user = self.cleaned_data.get('delivery_user')
        
        if delivery_user and not delivery_user.is_active:
            raise ValidationError('Este repartidor no está activo actualmente.')
        
        if delivery_user and not delivery_user.is_delivery:
            raise ValidationError('Este usuario no es un repartidor válido.')
        
        return delivery_user
    
    def clean_confirm(self):
        confirm = self.cleaned_data.get('confirm')
        
        if not confirm:
            raise ValidationError(ERROR_CONFIRM_REQUIRED)
        
        return confirm
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.order:
            raise ValidationError(ERROR_ORDER_NOT_SPECIFIED)
        
        if self.order.status != 'listo':
            raise ValidationError(ERROR_ONLY_READY_CAN_ASSIGN.format(status=self.order.get_status_display()))
        
        return cleaned_data


class OrderMarkAsDeliveredForm(FormStyleMixin, forms.Form):
    """Formulario para marcar pedido como entregado."""
    
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que el pedido ha sido entregado al cliente',
        help_text='Esto marcará el pedido como pagado también.'
    )
    delivery_evidence = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ej: Recibido por [nombre], firma digital, etc.'}),
        label='Evidencia o comentario de entrega',
        help_text='Opcional: información sobre la entrega'
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.order:
            raise ValidationError(ERROR_ORDER_NOT_SPECIFIED)
        
        if self.order.status != 'en_camino':
            raise ValidationError(ERROR_ONLY_ON_THE_WAY_CAN_DELIVER.format(status=self.order.get_status_display()))
        
        if not self.order.assigned_delivery_user:
            raise ValidationError(ERROR_NO_DELIVERY_ASSIGNED)
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError(ERROR_CONFIRM_REQUIRED)
        
        return cleaned_data


class OrderPaymentForm(FormStyleMixin, forms.Form):
    """Formulario para generar un link de pago Stripe para pedidos pendientes."""
    
    send_email = forms.BooleanField(
        required=False,
        initial=True,
        label='Enviar link de pago al cliente por email',
        help_text='Si está activado, se enviará un correo con el enlace de pago al cliente.'
    )
    
    send_whatsapp = forms.BooleanField(
        required=False,
        initial=False,
        label='Enviar link de pago por WhatsApp',
        help_text='El cliente recibirá un mensaje con el enlace de pago (requiere integración con WhatsApp API).'
    )
    
    notify_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Notas adicionales para el cliente...'}),
        label='Notas para el cliente (opcional)',
        help_text='Estas notas se incluirán en el mensaje al cliente.'
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        if self.order and not self.order.customer_email:
            self.fields['send_email'].disabled = True
            self.fields['send_email'].initial = False
            self.fields['send_email'].help_text = 'El cliente no tiene email registrado.'
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.order:
            raise ValidationError(ERROR_ORDER_NOT_SPECIFIED)
        
        if self.order.status != 'pendiente':
            raise ValidationError(ERROR_ONLY_PENDING_CAN_PAY.format(status=self.order.get_status_display()))
        
        if self.order.is_paid:
            raise ValidationError(ERROR_ORDER_ALREADY_PAID)
        
        send_email = cleaned_data.get('send_email')
        send_whatsapp = cleaned_data.get('send_whatsapp')
        
        if not send_email and not send_whatsapp:
            raise ValidationError(ERROR_NO_PAYMENT_METHOD)
        
        if send_email and not self.order.customer_email:
            raise ValidationError(ERROR_NO_EMAIL_FOR_NOTIFICATION)
        
        return cleaned_data


class OrderItemCreateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para agregar items a un pedido existente."""
    
    class Meta:
        model = OrderItem
        fields = ['variant', 'quantity']
        widgets = {
            'variant': forms.Select(),
            'quantity': forms.NumberInput(attrs={'min': 1, 'max': MAX_QUANTITY_PER_ITEM}),
        }
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        if self.order:
            self.fields['variant'].queryset = ProductVariant.objects.filter(
                is_active=True,
                product__is_active=True
            ).select_related('product', 'size', 'product_color__color')
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        
        if quantity <= 0:
            raise ValidationError(ERROR_INVALID_QUANTITY)
        
        if quantity > MAX_QUANTITY_PER_ITEM:
            raise ValidationError(ERROR_MAX_QUANTITY_EXCEEDED)
        
        variant = self.cleaned_data.get('variant')
        if variant and quantity > variant.stock:
            raise ValidationError(ERROR_STOCK_INSUFFICIENT.format(stock=variant.stock))
        
        return quantity
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.order:
            raise ValidationError(ERROR_ORDER_NOT_SPECIFIED)
        
        variant = cleaned_data.get('variant')
        if variant and self.order.items.filter(variant=variant).exists():
            raise ValidationError(ERROR_PRODUCT_ALREADY_IN_ORDER.format(
                product=variant.product.name, size=variant.size.name
            ))
        
        if self.order.status not in ['pendiente', 'confirmado']:
            raise ValidationError(ERROR_ONLY_PENDING_OR_CONFIRMED_CAN_ADD_ITEMS)
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.order = self.order
        if commit:
            instance.save()
        return instance


class OrderItemUpdateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para actualizar cantidad de un item."""
    
    class Meta:
        model = OrderItem
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1, 'max': MAX_QUANTITY_PER_ITEM}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_quantity = self.instance.quantity if self.instance else 0
    
    def clean_quantity(self):
        new_quantity = self.cleaned_data.get('quantity')
        
        if new_quantity <= 0:
            raise ValidationError(ERROR_INVALID_QUANTITY)
        
        if new_quantity > MAX_QUANTITY_PER_ITEM:
            raise ValidationError(ERROR_MAX_QUANTITY_EXCEEDED)
        
        if self.instance and self.instance.variant:
            if new_quantity > self.original_quantity:
                increase = new_quantity - self.original_quantity
                if increase > self.instance.variant.stock:
                    raise ValidationError(ERROR_STOCK_INSUFFICIENT.format(stock=self.instance.variant.stock))
        
        return new_quantity
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.instance and self.instance.order:
            if self.instance.order.status not in ['pendiente', 'confirmado']:
                raise ValidationError(ERROR_CANNOT_MODIFY_ITEM_STATUS)
        
        return cleaned_data


class OrderItemDeleteForm(FormStyleMixin, forms.Form):
    """Formulario para eliminar un item del pedido."""
    
    confirm = forms.CharField(
        required=True,
        label='Escribe "ELIMINAR" para confirmar la eliminación del producto',
        help_text='Esto liberará el stock asociado al producto si el pedido ya estaba confirmado.',
        widget=forms.TextInput(attrs={'placeholder': 'ELIMINAR'})
    )
    
    def __init__(self, *args, **kwargs):
        self.order_item = kwargs.pop('order_item', None)
        super().__init__(*args, **kwargs)
        if self.order_item:
            self.fields['confirm'].help_text = (
                f'Estás por eliminar "{self.order_item.product_name_snapshot}" '
                f'(x{self.order_item.quantity}). Esta acción liberará el stock si el pedido ya estaba confirmado.'
            )
    
    def clean_confirm(self):
        value = self.cleaned_data.get('confirm', '').strip()
        
        if not self.order_item:
            raise ValidationError(ERROR_ORDER_NOT_SPECIFIED)
        
        if value.upper() != 'ELIMINAR':
            raise ValidationError(ERROR_CONFIRM_MISMATCH)
        
        if self.order_item.order and self.order_item.order.status not in ['pendiente', 'confirmado']:
            raise ValidationError(ERROR_CANNOT_MODIFY_ITEM_STATUS)
        
        return value