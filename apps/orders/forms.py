from django import forms
from django.core.exceptions import ValidationError
from .models import Order, OrderItem
from apps.products.models import ProductVariant
from .constants import (
    DEFAULT_SHIPPING_COST, 
    FREE_SHIPPING_THRESHOLD,
    MAX_QUANTITY_PER_ITEM
)

class CheckoutOrderForm(forms.Form):
    # Formulario para la creación de un pedido en el checkout.
    
    # Nombre completo
    customer_name = forms.CharField(
        max_length=200,
        min_length=3,
        required=True,
        label='Nombre completo',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-zicada-accent focus:outline-none transition',
            'placeholder': 'Ej: María Gómez Rodríguez',
            'id': 'customer_name'
        }),
        error_messages={
            'required': 'Por favor ingresa tu nombre completo.',
            'min_length': 'El nombre debe tener al menos 3 caracteres.',
            'max_length': 'El nombre no puede exceder los 200 caracteres.'
        }
    )
    
    # Teléfono
    customer_phone = forms.CharField(
        max_length=20,
        required=True,
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-zicada-accent focus:outline-none transition',
            'placeholder': 'Ej: 3001234567',
            'id': 'customer_phone'
        }),
        error_messages={
            'required': 'Por favor ingresa tu número de teléfono.'
        }
    )
    
    # Correo electrónico
    customer_email = forms.EmailField(
        required=False,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-zicada-accent focus:outline-none transition',
            'placeholder': 'Ej: maria@correo.com',
            'id': 'customer_email'
        }),
        error_messages={
            'invalid': 'Ingresa un correo electrónico válido.'
        }
    )
    
    # Dirección de envío
    shipping_address = forms.CharField(
        required=True,
        label='Dirección de envío',
        min_length=5,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-zicada-accent focus:outline-none transition resize-none',
            'rows': 3,
            'placeholder': 'Calle, número, barrio, ciudad, referencia',
            'id': 'shipping_address'
        }),
        error_messages={
            'required': 'Por favor ingresa tu dirección de envío completa.'
        }
    )
    
    # Notas adicionales
    delivery_notes = forms.CharField(
        required=False,
        label='Notas adicionales',
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-zicada-accent focus:outline-none transition resize-none',
            'rows': 2,
            'placeholder': 'Ej: Dejar con el portero, llamar antes de llegar...',
            'id': 'delivery_notes'
        })
    )
    
    def clean_customer_phone(self):
        """Limpia y normaliza el teléfono eliminando caracteres no numéricos."""
        phone = self.cleaned_data.get('customer_phone', '')
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) < 7 or len(digits) > 15:
            raise ValidationError('El número de teléfono debe tener entre 7 y 15 dígitos.')
        return digits


class OrderCreateForm(forms.ModelForm):
    """
    Formulario para crear pedidos manuales desde backoffice.
    Estos pedidos se crean en estado 'pendiente' y requieren pago o marcado manual.
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
            'is_paid',
        ]
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'delivery_notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['shipping_cost'].initial = DEFAULT_SHIPPING_COST
        self.fields['is_paid'].initial = False
        self.fields['is_paid'].help_text = 'Marcar como pagado si el cliente ya pagó (ej: contraentrega, transferencia)'
    
    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone', '')
        # Normaliza eliminando todo carácter no numérico (consistente con CheckoutOrderForm)
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) < 7:
            raise ValidationError('El teléfono debe tener al menos 7 dígitos.')
        if len(digits) > 15:
            raise ValidationError('El teléfono es demasiado largo (máximo 15 dígitos).')
        return digits
    
    def clean_shipping_cost(self):
        cost = self.cleaned_data.get('shipping_cost', 0)
        if cost < 0:
            raise ValidationError('El costo de envío no puede ser negativo.')
        # Para pedidos nuevos (sin subtotal), solo validamos que no sea negativo.
        # La validación de envío gratis vs subtotal se hace en OrderUpdateForm.
        return cost


class OrderUpdateForm(forms.ModelForm):
    """
    Formulario para actualizar pedidos existentes desde backoffice.
    Respeta la máquina de estados.
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
            'is_paid',
            'status',
            'assigned_delivery_user',
        ]
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'delivery_notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.fields['assigned_delivery_user'].queryset = User.objects.filter(
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
                    raise ValidationError(
                        f'No se puede cambiar de "{self.instance.get_status_display()}" '
                        f'a "{dict(Order.STATUS_CHOICES).get(new_status, new_status)}". '
                        f'Transición no permitida.'
                    )
        return new_status
    
    def clean_is_paid(self):
        is_paid = self.cleaned_data.get('is_paid')
        status = self.cleaned_data.get('status', self.instance.status if self.instance else 'pendiente')
        
        if status == 'entregado' and not is_paid:
            raise ValidationError('Un pedido entregado debe estar marcado como pagado.')
        
        if self.instance and self.instance.is_paid and not is_paid:
            raise ValidationError('No se puede desmarcar un pedido ya pagado.')
        
        return is_paid
    
    def clean_shipping_cost(self):
        new_cost = self.cleaned_data.get('shipping_cost')
        subtotal = self.instance.subtotal if self.instance else 0
        
        if new_cost < 0:
            raise ValidationError('El costo de envío no puede ser negativo.')
        
        if subtotal >= FREE_SHIPPING_THRESHOLD and new_cost > 0:
            raise ValidationError(
                f'Este pedido califica para envío gratis (subtotal >= ${FREE_SHIPPING_THRESHOLD:,.0f}). '
                f'El costo de envío debe ser 0.'
            )
        
        return new_cost


class OrderConfirmForm(forms.Form):
    """
    Formulario específico para confirmar un pedido manualmente (sin Stripe).
    Esto ejecuta la misma lógica que confirm() del modelo + reduce stock.
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
        cleaned_data = super().clean()
        
        if not self.order:
            raise ValidationError('Pedido no especificado.')
        
        if self.order.status != 'pendiente':
            raise ValidationError(f'Solo se pueden confirmar pedidos en estado "Pendiente". Estado actual: {self.order.get_status_display()}')
        
        if not self.order.items.exists():
            raise ValidationError('No se puede confirmar un pedido sin items.')
        
        stock_errors = []
        for item in self.order.items.all():
            if item.variant and item.quantity > item.variant.stock:
                stock_errors.append(
                    f'{item.product_name_snapshot} ({item.size_snapshot}): '
                    f'solicitado {item.quantity}, disponible {item.variant.stock}'
                )
        
        if stock_errors:
            raise ValidationError(
                f'Stock insuficiente para continuar:\n- ' + '\n- '.join(stock_errors)
            )
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError('Debes confirmar la acción.')
        
        return cleaned_data


class OrderCancelForm(forms.Form):
    """Formulario específico para cancelar pedidos (libera stock si estaba confirmado)"""
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ej: Cliente solicitó cancelación, producto agotado, error en dirección...', 'class': 'form-control'}),
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
            raise ValidationError('El motivo de cancelación debe tener al menos 10 caracteres.')
        return reason
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.order:
            raise ValidationError('Pedido no especificado.')
        
        if self.order.status == 'entregado':
            raise ValidationError('No se puede cancelar un pedido ya entregado.')
        
        if self.order.status == 'cancelado':
            raise ValidationError('Este pedido ya está cancelado.')
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError('Debes confirmar la cancelación.')
        
        return cleaned_data


class OrderChangeStatusForm(forms.Form):
    """
    Formulario para cambios rápidos de estado (con validación de transiciones).
    Útil para botones de acción en el panel de administración.
    """
    
    new_status = forms.ChoiceField(
        choices=[],
        label='Nuevo estado',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        label='Notas (opcional)',
        help_text='Notas internas sobre este cambio de estado'
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        if self.order:
            # Delega en el modelo para mantener una única fuente de verdad
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
            raise ValidationError('Pedido no especificado.')
        
        if not self.order.can_transition_to(new_status):
            raise ValidationError(
                f'No se puede cambiar de "{self.order.get_status_display()}" '
                f'a "{dict(Order.STATUS_CHOICES).get(new_status, new_status)}".'
            )
        
        return new_status


class OrderAssignDeliveryForm(forms.Form):
    """Formulario para asignar repartidor desde backoffice"""
    
    delivery_user = forms.ModelChoiceField(
        queryset=None,
        label='Repartidor asignado',
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    confirm = forms.BooleanField(
        required=True,
        label='Confirmar asignación',
        help_text='Esto cambiará el estado del pedido a "En camino"'
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Mostrar solo usuarios marcados como repartidores y activos
        self.fields['delivery_user'].queryset = User.objects.filter(
            is_delivery=True, is_active=True
        ).order_by('username')
        
        if self.order and self.order.assigned_delivery_user:
            self.fields['delivery_user'].initial = self.order.assigned_delivery_user
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.order:
            raise ValidationError('Pedido no especificado.')
        
        if self.order.status != 'listo':
            raise ValidationError(
                f'Solo se puede asignar repartidor a pedidos en estado "Listo para envío". '
                f'Estado actual: {self.order.get_status_display()}'
            )
        
        delivery_user = cleaned_data.get('delivery_user')
        confirm = cleaned_data.get('confirm')
        
        if delivery_user and not confirm:
            raise ValidationError('Debes confirmar la asignación.')
        
        return cleaned_data


class OrderMarkAsDeliveredForm(forms.Form):
    """Formulario para marcar pedido como entregado"""
    
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que el pedido ha sido entregado al cliente',
        help_text='Esto marcará el pedido como pagado también.'
    )
    delivery_evidence = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Ej: Recibido por [nombre], firma digital, etc.'}),
        label='Evidencia o comentario de entrega',
        help_text='Opcional: información sobre la entrega'
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.order:
            raise ValidationError('Pedido no especificado.')
        
        if self.order.status != 'en_camino':
            raise ValidationError(
                f'Solo se puede entregar pedidos que están "En camino". '
                f'Estado actual: {self.order.get_status_display()}'
            )
        
        if not self.order.assigned_delivery_user:
            raise ValidationError('No se puede entregar un pedido sin repartidor asignado.')
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError('Debes confirmar la entrega.')
        
        return cleaned_data

class OrderPaymentForm(forms.Form):
    """
    Formulario para generar un link de pago Stripe para pedidos pendientes.
    Útil para pedidos creados manualmente en backoffice que requieren pago en línea.
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
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Notas adicionales para el cliente...'}),
        label='Notas para el cliente (opcional)',
        help_text='Estas notas se incluirán en el mensaje al cliente.'
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        if self.order:
            # Si el cliente no tiene email, deshabilitar opción de email
            if not self.order.customer_email:
                self.fields['send_email'].disabled = True
                self.fields['send_email'].initial = False
                self.fields['send_email'].help_text = 'El cliente no tiene email registrado.'
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.order:
            raise ValidationError('Pedido no especificado.')
        
        if self.order.status != 'pendiente':
            raise ValidationError(
                f'Solo se pueden generar links de pago para pedidos pendientes. '
                f'Estado actual: {self.order.get_status_display()}'
            )
        
        if self.order.is_paid:
            raise ValidationError('Este pedido ya está pagado.')
        
        send_email = cleaned_data.get('send_email')
        send_whatsapp = cleaned_data.get('send_whatsapp')
        
        if not send_email and not send_whatsapp:
            raise ValidationError('Debes seleccionar al menos un método de notificación (email o WhatsApp).')
        
        if send_email and not self.order.customer_email:
            raise ValidationError('No se puede enviar por email porque el cliente no tiene correo registrado.')
        
        return cleaned_data


class OrderItemCreateForm(forms.ModelForm):
    """Formulario para agregar items a un pedido existente"""
    
    class Meta:
        model = OrderItem
        fields = ['variant', 'quantity']
        widgets = {
            'variant': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': MAX_QUANTITY_PER_ITEM}),
        }
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        if self.order:
            # Mostrar solo variantes activas y con stock (opcional: mostrar todas pero validar después)
            self.fields['variant'].queryset = ProductVariant.objects.filter(
                is_active=True,
                product__is_active=True
            ).select_related('product', 'size', 'product_color__color')
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        
        if quantity <= 0:
            raise ValidationError('La cantidad debe ser mayor a 0.')
        
        if quantity > MAX_QUANTITY_PER_ITEM:
            raise ValidationError(f'La cantidad máxima por item es {MAX_QUANTITY_PER_ITEM}.')
        
        variant = self.cleaned_data.get('variant')
        if variant and quantity > variant.stock:
            raise ValidationError(f'Stock insuficiente. Solo hay {variant.stock} unidades disponibles.')
        
        return quantity
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.order:
            raise ValidationError('Pedido no especificado.')
        
        # Verificar si ya existe el mismo producto+talla en el pedido
        variant = cleaned_data.get('variant')
        if variant and self.order.items.filter(variant=variant).exists():
            raise ValidationError(
                f'El producto "{variant.product.name}" - Talla {variant.size.name} ya existe en este pedido. '
                f'Edita la cantidad del existente en lugar de agregar uno nuevo.'
            )
        
        if self.order.status not in ['pendiente', 'confirmado']:
            raise ValidationError('Solo se pueden agregar items a pedidos pendientes o confirmados.')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.order = self.order
        
        # Los snapshots se llenan automáticamente en el save del modelo OrderItem
        if commit:
            instance.save()
        return instance


class OrderItemUpdateForm(forms.ModelForm):
    """Formulario para actualizar cantidad de un item"""
    
    class Meta:
        model = OrderItem
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': MAX_QUANTITY_PER_ITEM}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_quantity = self.instance.quantity if self.instance else 0
    
    def clean_quantity(self):
        new_quantity = self.cleaned_data.get('quantity')
        
        if new_quantity <= 0:
            raise ValidationError('La cantidad debe ser mayor a 0.')
        
        if new_quantity > MAX_QUANTITY_PER_ITEM:
            raise ValidationError(f'La cantidad máxima por item es {MAX_QUANTITY_PER_ITEM}.')
        
        # Verificar stock si la cantidad aumenta
        if self.instance and self.instance.variant:
            if new_quantity > self.original_quantity:
                increase = new_quantity - self.original_quantity
                if increase > self.instance.variant.stock:
                    raise ValidationError(
                        f'Stock insuficiente para aumentar. '
                        f'Solo hay {self.instance.variant.stock} unidades disponibles. '
                        f'Necesitas {increase} más.'
                    )
        
        return new_quantity
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.instance and self.instance.order:
            if self.instance.order.status not in ['pendiente', 'confirmado']:
                raise ValidationError('Solo se pueden modificar items de pedidos pendientes o confirmados.')
        
        return cleaned_data


class OrderItemDeleteForm(forms.Form):
    """Formulario para eliminar un item del pedido"""
    
    confirm = forms.CharField(
        required=True,
        label='Escribe "ELIMINAR" para confirmar la eliminación del producto',
        help_text='Esto liberará el stock asociado al producto si el pedido ya estaba confirmado.',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ELIMINAR'})
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
            raise ValidationError('Item no especificado.')
        
        if value.upper() != 'ELIMINAR':
            raise ValidationError('Debes escribir "ELIMINAR" exactamente para confirmar.')
        
        if self.order_item.order and self.order_item.order.status not in ['pendiente', 'confirmado']:
            raise ValidationError(
                f'Solo se pueden eliminar items de pedidos pendientes o confirmados. '
                f'Estado actual: {self.order_item.order.get_status_display()}'
            )
        
        return value