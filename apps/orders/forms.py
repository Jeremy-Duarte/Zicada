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
# HU-023: CHECKOUT ORDER FORM
# =============================================================================

class CheckoutOrderForm(FormStyleMixin, forms.Form):
    """
    HU-023: Completar formulario de envío
    Escenarios: H (todos los campos válidos), A (campos obligatorios vacíos), E (teléfono inválido)
    """
    
    # HU-023 | ESCENARIO 1 | H | Nombre completo válido (min 3, max 200)
    # HU-023 | ESCENARIO 2 | A | Nombre vacío → error 'required'
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
    
    # HU-023 | ESCENARIO 1 | H | Teléfono válido (7-15 dígitos)
    # HU-023 | ESCENARIO 3 | E | Teléfono inválido (formato incorrecto) → error en clean_customer_phone
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
    
    # HU-023 | ESCENARIO 4 | A | Email opcional, si se ingresa debe ser válido
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
    
    # HU-023 | ESCENARIO 1 | H | Dirección válida (min 5)
    # HU-023 | ESCENARIO 2 | A | Dirección vacía → error 'required'
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
    
    # HU-023 | ESCENARIO 1 | H | Notas adicionales opcionales
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
        """
        HU-023 | ESCENARIO 3 | E | Teléfono con menos de 7 o más de 15 dígitos → error
        HU-023 | ESCENARIO 1 | H | Teléfono válido (7-15 dígitos)
        """
        phone = self.cleaned_data.get('customer_phone', '')
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) < 7 or len(digits) > 15:
            raise ValidationError(ERROR_INVALID_PHONE_LENGTH)
        return digits


# =============================================================================
# HU-031: ORDER CREATE FORM (pedido manual)
# =============================================================================

class OrderCreateForm(FormStyleMixin, forms.ModelForm):
    """
    HU-031: Crear pedido manual (admin)
    Escenarios: H (datos válidos), A (teléfono inválido, costo envío negativo), E (sin permisos)
    """
    
    class Meta:
        model = Order
        fields = [
            'customer_name',
            'customer_phone',
            'customer_email',
            'shipping_address',
            'delivery_notes',
            'shipping_cost',
        ]
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
            'delivery_notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['shipping_cost'].initial = DEFAULT_SHIPPING_COST
    
    def clean_customer_phone(self):
        """
        HU-031 | ESCENARIO 1 | H | Teléfono válido (7-15 dígitos)
        HU-031 | ESCENARIO 2 | A | Teléfono inválido → error
        """
        phone = self.cleaned_data.get('customer_phone', '')
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) < 7:
            raise ValidationError('El teléfono debe tener al menos 7 dígitos.')
        if len(digits) > 15:
            raise ValidationError('El teléfono es demasiado largo (máximo 15 dígitos).')
        return digits
    
    def clean_shipping_cost(self):
        """
        HU-031 | ESCENARIO 1 | H | Costo de envío ≥ 0
        HU-031 | ESCENARIO 2 | A | Costo de envío negativo → error
        """
        cost = self.cleaned_data.get('shipping_cost', 0)
        if cost < 0:
            raise ValidationError(ERROR_SHIPPING_NEGATIVE)
        return cost


# =============================================================================
# HU-031 (PARTE): ORDER UPDATE FORM
# =============================================================================

class OrderUpdateForm(FormStyleMixin, forms.ModelForm):
    """
    HU-031 (parte): Editar pedido manual (admin)
    Escenarios: H (datos válidos), A (transición inválida, envío gratis violado, etc.), E (sin permisos)
    """
    
    class Meta:
        model = Order
        fields = [
            'customer_name',
            'customer_phone',
            'customer_email',
            'shipping_address',
            'delivery_notes',
            'shipping_cost',
        ]
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
            'delivery_notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            # HU-031 | ESCENARIO 4 | A | Pedido entregado o cancelado → campos deshabilitados
            if self.instance.status in ['entregado', 'cancelado']:
                self.fields['shipping_cost'].disabled = True
    
    def clean_shipping_cost(self):
        """
        HU-031 | ESCENARIO 2 | A | Envío gratis para subtotal >= FREE_SHIPPING_THRESHOLD
        HU-031 | ESCENARIO 2 | A | Costo de envío negativo → error
        """
        new_cost = self.cleaned_data.get('shipping_cost')
        subtotal = self.instance.subtotal if self.instance else 0        
        if new_cost < 0:
            raise ValidationError(ERROR_SHIPPING_NEGATIVE)
        
        if subtotal >= FREE_SHIPPING_THRESHOLD and new_cost > 0:
            raise ValidationError(ERROR_FREE_SHIPPING_VIOLATION.format(threshold=FREE_SHIPPING_THRESHOLD))
        
        return new_cost


# =============================================================================
# HU-029 (PARTE): ORDER CONFIRM FORM
# =============================================================================

class OrderConfirmForm(FormStyleMixin, forms.Form):
    """
    HU-029: Confirmar pedido (cambiar estado de pendiente a confirmado)
    Escenarios: H (confirmación válida y stock suficiente), A (sin items, stock insuficiente), E (estado incorrecto)
    """
    
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que deseo confirmar este pedido',
        help_text='Esta acción reducirá el stock de los productos asociados.'
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        """
        HU-029 | ESCENARIO 1 | H | Confirmación válida (stock suficiente, items presentes, estado pendiente)
        HU-029 | ESCENARIO 3 | E | Estado no es pendiente → error
        HU-029 | ESCENARIO 3 | E | Sin items en el pedido → error
        HU-029 | ESCENARIO 3 | E | Stock insuficiente → error
        """
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


# =============================================================================
# HU-030 & HU-035: ORDER CANCEL FORM
# =============================================================================

class OrderCancelForm(FormStyleMixin, forms.Form):
    """
    HU-030: Cancelar pedido (admin)
    HU-035: Registrar incidencia (el motivo de cancelación actúa como incidencia)
    Escenarios: H (motivo válido y confirmación), A (motivo demasiado corto), E (pedido entregado o ya cancelado)
    """
    
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
        """
        HU-030 | ESCENARIO 3 | H | Motivo de cancelación (incidencia) válido
        HU-035 | ESCENARIO 1 | H | Incidencia registrada con motivo
        HU-035 | ESCENARIO 2 | H | Tipos de incidencia disponibles (campo libre)
        HU-030 | ESCENARIO 2 | E | Motivo demasiado corto (< 10 caracteres) → error
        """
        reason = self.cleaned_data.get('reason', '').strip()
        if len(reason) < 10:
            raise ValidationError(ERROR_REASON_TOO_SHORT)
        return reason
    
    def clean(self):
        """
        HU-030 | ESCENARIO 1 | H | Cancelación válida
        HU-030 | ESCENARIO 2 | E | Pedido ya entregado → error
        HU-030 | ESCENARIO 4 | E | Pedido ya cancelado → error
        HU-030 | ESCENARIO 3 | A | Confirmación no marcada → error
        """
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


# =============================================================================
# HU-029 (PARTE): ORDER CHANGE STATUS FORM (cambios rápidos de estado)
# =============================================================================

class OrderChangeStatusForm(FormStyleMixin, forms.Form):
    """
    HU-029: Cambiar estado de pedido (cambios rápidos)
    Escenarios: H (transición válida), E (transición inválida)
    """
    
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
            # HU-029 | ESCENARIO 2 | H | Muestra solo estados permitidos desde el estado actual
            choices = [
                (status, label) for status, label in Order.STATUS_CHOICES
                if self.order.can_transition_to(status)
            ]
            self.fields['new_status'].choices = choices
            
            if not choices:
                self.fields['new_status'].disabled = True
                self.fields['new_status'].help_text = 'No hay transiciones disponibles para este estado.'
    
    def clean(self):
        """
        HU-029 | ESCENARIO 1 | H | Transición válida
        HU-029 | ESCENARIO 3 | E | Transición no permitida → error
        """
        cleaned_data = super().clean()
        
        # Mover la validación del pedido aquí
        if not self.order:
            raise ValidationError(ERROR_ORDER_NOT_SPECIFIED)
        
        new_status = cleaned_data.get('new_status')
        
        if new_status and not self.order.can_transition_to(new_status):
            from_status = self.order.get_status_display()
            to_status = dict(Order.STATUS_CHOICES).get(new_status, new_status)
            raise ValidationError(ERROR_INVALID_STATUS_TRANSITION.format(
                from_status=from_status, to_status=to_status
            ))
        
        return cleaned_data


# =============================================================================
# HU-032: ORDER ASSIGN DELIVERY FORM
# =============================================================================

class OrderAssignDeliveryForm(FormStyleMixin, forms.Form):
    """
    HU-032: Asignar repartidor (admin)
    Escenarios: H (repartidor asignado y confirmación), A (sin entregadores disponibles), E (pedido no está listo)
    """
    
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
        # HU-032 | ESCENARIO 2 | A | Sin entregadores disponibles → queryset vacío
        self.fields['delivery_user'].queryset = user_model.objects.filter(
            is_delivery=True, 
            is_active=True
        ).only('id', 'first_name', 'last_name', 'username', 'phone').order_by('first_name', 'last_name')
        
        self.fields['delivery_user'].label_from_instance = lambda u: f"{u.get_full_name()} - {u.phone or 'Sin teléfono'}"
        
        if self.order and self.order.assigned_delivery_user:
            self.fields['delivery_user'].initial = self.order.assigned_delivery_user
        
        self.fields['delivery_user'].help_text = "Selecciona el repartidor que realizará la entrega"
    
    def clean_delivery_user(self):
        """
        HU-032 | ESCENARIO 1 | H | Repartidor válido (activo y con rol de entregador)
        HU-032 | ESCENARIO 2 | A | Repartidor inactivo → error
        """
        delivery_user = self.cleaned_data.get('delivery_user')
        
        if delivery_user and not delivery_user.is_active:
            raise ValidationError('Este repartidor no está activo actualmente.')
        
        if delivery_user and not delivery_user.is_delivery:
            raise ValidationError('Este usuario no es un repartidor válido.')
        
        return delivery_user
    
    def clean_confirm(self):
        """
        HU-032 | ESCENARIO 1 | H | Confirmación marcada
        HU-032 | ESCENARIO 3 | A | Confirmación no marcada → error
        """
        confirm = self.cleaned_data.get('confirm')
        
        if not confirm:
            raise ValidationError(ERROR_CONFIRM_REQUIRED)
        
        return confirm
    
    def clean(self):
        """
        HU-032 | ESCENARIO 1 | H | Pedido en estado 'listo'
        HU-032 | ESCENARIO 3 | E | Pedido no está listo → error
        """
        cleaned_data = super().clean()
        
        if not self.order:
            raise ValidationError(ERROR_ORDER_NOT_SPECIFIED)
        
        if self.order.status != 'listo':
            raise ValidationError(ERROR_ONLY_READY_CAN_ASSIGN.format(status=self.order.get_status_display()))
        
        return cleaned_data


# =============================================================================
# HU-034: ORDER MARK AS DELIVERED FORM
# =============================================================================

class OrderMarkAsDeliveredForm(FormStyleMixin, forms.Form):
    """
    HU-034: Marcar pedido como pagado/entregado
    Escenarios: H (confirmación válida), A (confirmación no marcada), E (pedido no está en camino, sin repartidor)
    """
    
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
        """
        HU-034 | ESCENARIO 1 | H | Entrega válida (pedido en camino, repartidor asignado)
        HU-034 | ESCENARIO 2 | H | Confirmación requerida
        HU-034 | ESCENARIO 3 | E | Pedido no está en camino → error
        HU-034 | ESCENARIO 3 | E | Sin repartidor asignado → error
        """
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


# =============================================================================
# HU-024 (PARTE): ORDER PAYMENT FORM (generar link de pago)
# =============================================================================

class OrderPaymentForm(FormStyleMixin, forms.Form):
    """
    HU-024 (parte): Generar link de pago Stripe para pedidos pendientes
    Escenarios: H (método de pago seleccionado), A (sin método seleccionado), E (pedido pagado o no pendiente)
    """
    
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
        """
        HU-024 | ESCENARIO 1 | H | Método de pago seleccionado (email o WhatsApp)
        HU-024 | ESCENARIO 2 | E | Pedido no está pendiente → error
        HU-024 | ESCENARIO 2 | E | Pedido ya pagado → error
        HU-024 | ESCENARIO 2 | A | Sin método de pago seleccionado → error
        """
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


# =============================================================================
# HU-031 (PARTE): ORDER ITEM CREATE FORM
# =============================================================================

class OrderItemCreateForm(FormStyleMixin, forms.ModelForm):
    """
    HU-031 (parte): Agregar producto a pedido manual (admin)
    HU-031 | ESCENARIO 1 | H | Producto agregado exitosamente
    HU-031 | ESCENARIO 2 | H | Buscar productos para agregar (formulario con variantes)
    HU-031 | ESCENARIO 3 | E | Stock insuficiente (validado en form)
    HU-031 | ESCENARIO 3 | E | Producto ya existe en el pedido (validado en form)
    HU-031 | ESCENARIO 3 | E | Pedido no está pendiente o confirmado (validado en form)
    HU-024 (parte) | H | Al agregar producto, se actualiza subtotal y se aplica regla de envío gratis
    """
    
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
        
        # HU-031 | ESCENARIO 2 | H | Filtrar variantes activas
        if self.order:
            self.fields['variant'].queryset = ProductVariant.objects.filter(
                is_active=True,
                product__is_active=True
            ).select_related('product', 'size', 'product_color__color')
            
            # Personalizar la representación de las variantes en el select
            self.fields['variant'].label_from_instance = lambda v: (
                f"{v.product.name} - {v.color_name} - {v.size.name} "
                f"(Stock: {v.stock})"
            )
    
    def clean_quantity(self):
        """
        HU-031 | ESCENARIO 1 | H | Cantidad válida (1 - MAX_QUANTITY_PER_ITEM)
        HU-031 | ESCENARIO 3 | E | Cantidad > stock disponible → error
        """
        quantity = self.cleaned_data.get('quantity')
        
        if quantity is None or quantity <= 0:
            raise ValidationError(ERROR_INVALID_QUANTITY)
        
        if quantity > MAX_QUANTITY_PER_ITEM:
            raise ValidationError(ERROR_MAX_QUANTITY_EXCEEDED)
        
        variant = self.cleaned_data.get('variant')
        if variant:
            # Obtener stock actualizado desde BD
            variant.refresh_from_db()
            if quantity > variant.stock:
                raise ValidationError(
                    f'Stock insuficiente. Solo hay {variant.stock} unidades disponibles '
                    f'de "{variant.product.name} - {variant.color_name} - {variant.size.name}".'
                )
        
        return quantity
    
    def clean(self):
        """
        HU-031 | ESCENARIO 1 | H | Producto no existente en el pedido
        HU-031 | ESCENARIO 3 | E | Producto ya existe en el pedido → error
        HU-031 | ESCENARIO 3 | E | Pedido no está pendiente o confirmado → error
        """
        cleaned_data = super().clean()
        
        if not self.order:
            raise ValidationError(ERROR_ORDER_NOT_SPECIFIED)
        
        # HU-031 | ESCENARIO 3 | E | Validar estado del pedido
        if self.order.status not in ['pendiente', 'confirmado']:
            raise ValidationError(ERROR_ONLY_PENDING_OR_CONFIRMED_CAN_ADD_ITEMS)
        
        # HU-031 | ESCENARIO 3 | E | Validar producto duplicado
        variant = cleaned_data.get('variant')
        if variant and self.order.items.filter(variant=variant).exists():
            raise ValidationError(
                ERROR_PRODUCT_ALREADY_IN_ORDER.format(
                    product=variant.product.name, 
                    size=variant.size.name
                )
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        HU-031 | ESCENARIO 1 | H | Guardar OrderItem y reducir stock automáticamente
        HU-024 (parte) | H | Actualiza subtotal del pedido (la señal se encarga del resto)
        """
        instance = super().save(commit=False)
        instance.order = self.order
        
        if commit:
            # Obtener la variante con stock actualizado
            variant = instance.variant
            if variant:
                variant.refresh_from_db()
                
                # Verificar stock nuevamente antes de guardar
                if instance.quantity > variant.stock:
                    raise ValidationError(
                        f'Stock insuficiente. Solo hay {variant.stock} unidades disponibles.'
                    )
                
                # Establecer snapshots
                instance.product_name_snapshot = variant.product.name
                instance.size_snapshot = variant.size.name
                instance.unit_price = variant.product.price
                instance.stock_snapshot = variant.stock - instance.quantity
                instance.subtotal = instance.unit_price * instance.quantity
                
                # Reducir stock
                variant.stock -= instance.quantity
                variant.save(update_fields=['stock'])
            
            instance.save()
            
            # NOTA: La señal post_save de OrderItem actualizará automáticamente:
            # - subtotal del pedido (suma de subtotales)
            # - total_amount (subtotal + shipping_cost)
            # La regla de envío gratis se aplica en la señal o en el modelo Order.save()
        
        return instance


# =============================================================================
# HU-031 (PARTE): ORDER ITEM UPDATE FORM
# =============================================================================

class OrderItemUpdateForm(FormStyleMixin, forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1, 'max': MAX_QUANTITY_PER_ITEM}),
        }

    def __init__(self, *args, **kwargs):
        self.original_quantity = kwargs.pop('original_quantity', 0)
        super().__init__(*args, **kwargs)

    def clean_quantity(self):
        new_quantity = self.cleaned_data.get('quantity')
        if new_quantity is None or new_quantity <= 0:
            raise ValidationError(ERROR_INVALID_QUANTITY)
        if new_quantity > MAX_QUANTITY_PER_ITEM:
            raise ValidationError(ERROR_MAX_QUANTITY_EXCEEDED)

        if self.instance.variant and new_quantity > self.original_quantity:
            try:
                variant = ProductVariant.objects.get(id=self.instance.variant.id)
                increase = new_quantity - self.original_quantity
                if increase > variant.stock:
                    raise ValidationError(
                        f'Stock insuficiente. Solo hay {variant.stock} unidades disponibles. '
                        f'No puedes aumentar {increase} unidades más.'
                    )
            except ProductVariant.DoesNotExist:
                raise ValidationError('El producto asociado ya no está disponible.')
        return new_quantity

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.order.status not in ['pendiente', 'confirmado']:
            raise ValidationError(ERROR_CANNOT_MODIFY_ITEM_STATUS)
        return cleaned_data

    def save(self, commit=True):
        instance = self.instance
        new_quantity = self.cleaned_data['quantity']
        old_quantity = self.original_quantity

        if new_quantity == old_quantity:
            return instance

        variant = instance.variant
        if variant:
            variant.refresh_from_db()
            if new_quantity > old_quantity:
                increase = new_quantity - old_quantity
                variant.stock -= increase
            else:
                decrease = old_quantity - new_quantity
                variant.stock += decrease
            variant.save(update_fields=['stock'])
            instance.stock_snapshot = variant.stock

        instance.quantity = new_quantity
        instance.subtotal = instance.unit_price * new_quantity

        if commit:
            instance.save(update_fields=['quantity', 'subtotal', 'stock_snapshot'])

        return instance

# =============================================================================
# HU-031 (PARTE): ORDER ITEM DELETE FORM
# =============================================================================

class OrderItemDeleteForm(FormStyleMixin, forms.Form):
    """
    HU-031 (parte): Eliminar producto de pedido manual
    Escenarios: H (confirmación "ELIMINAR"), A (confirmación incorrecta), E (pedido no editable)
    """
    
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
        """
        HU-031 | ESCENARIO 1 | H | Confirmación "ELIMINAR" correcta
        HU-031 | ESCENARIO 3 | A | Confirmación incorrecta → error
        HU-031 | ESCENARIO 3 | E | Pedido no está pendiente o confirmado → error
        """
        value = self.cleaned_data.get('confirm', '').strip()
        
        if not self.order_item:
            raise ValidationError(ERROR_ORDER_NOT_SPECIFIED)
        
        if value.upper() != 'ELIMINAR':
            raise ValidationError(ERROR_CONFIRM_MISMATCH)
        
        if self.order_item.order and self.order_item.order.status not in ['pendiente', 'confirmado']:
            raise ValidationError(ERROR_CANNOT_MODIFY_ITEM_STATUS)
        
        return value