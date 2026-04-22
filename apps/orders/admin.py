from django.contrib import admin
from django import forms
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.db.models import Sum
from .models import Order, OrderItem
from apps.products.models import ProductVariant


class OrderForm(forms.ModelForm):
    """Formulario personalizado para Order."""
    class Meta:
        model = Order
        fields = '__all__'
        widgets = {
            'cancelled_reason': forms.Textarea(attrs={'rows': 2}),
            'delivery_notes': forms.Textarea(attrs={'rows': 2}),
            'shipping_address': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'total_amount' in self.fields:
            self.fields['total_amount'].widget.attrs['readonly'] = True
            self.fields['total_amount'].required = False


class OrderItemForm(forms.ModelForm):
    """Formulario personalizado para OrderItem"""
    
    class Meta:
        model = OrderItem
        fields = ('variant', 'quantity')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['variant'].label_from_instance = lambda v: (
            f"{v.product.name} - {v.size.name} "
            f"(Stock: {v.stock} | Precio: ${v.product.price:,.0f} COP)"
        )
        self.fields['variant'].queryset = ProductVariant.objects.filter(
            is_active=True
        ).select_related('product', 'size')
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        variant = self.cleaned_data.get('variant')
        
        if quantity and variant and quantity > variant.stock:
            raise ValidationError(
                f'Stock insuficiente. Solo hay {variant.stock} unidades disponibles.'
            )
        return quantity


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    form = OrderItemForm
    extra = 1
    fields = ('variant', 'quantity', 'unit_price_display', 'subtotal_display')
    readonly_fields = ('unit_price_display', 'subtotal_display')
    can_delete = True
    
    def unit_price_display(self, obj):
        if obj.variant:
            return f"${obj.variant.product.price:,.0f} COP"
        return "-"
    unit_price_display.short_description = 'Precio unitario'
    
    def subtotal_display(self, obj):
        if obj.variant and obj.quantity:
            total = obj.variant.product.price * obj.quantity
            return f"${total:,.0f} COP"
        return "-"
    subtotal_display.short_description = 'Subtotal'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderForm
    list_display = (
        'order_number', 
        'customer_name', 
        'customer_phone', 
        'total_display', 
        'status_badge', 
        'payment_badge', 
        'created_at'
    )
    list_filter = ('status', 'is_paid', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_phone', 'customer_email')
    readonly_fields = (
        'order_number', 
        'tracking_token', 
        'created_at', 
        'updated_at',
        'subtotal_display',
        'total_display_readonly'
    )
    inlines = [OrderItemInline]
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Identificación del pedido', {
            'fields': ('order_number', 'tracking_token')
        }),
        ('Datos del cliente', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('Dirección de envío', {
            'fields': ('shipping_address', 'delivery_notes')
        }),
        ('Resumen financiero', {
            'fields': ('shipping_cost', 'subtotal_display', 'total_display_readonly', 'is_paid'),
            'description': 'Los totales se calculan automáticamente al guardar'
        }),
        ('Estado del pedido', {
            'fields': ('status', 'cancelled_reason', 'assigned_delivery_user')
        }),
    )
    
    def subtotal_display(self, obj):
        if obj.id:
            total = obj.items.aggregate(s=Sum('subtotal'))['s'] or 0
            return f"${total:,.0f} COP"
        return "$0 COP"
    subtotal_display.short_description = 'Subtotal'
    
    def total_display(self, obj):
        if obj.id:
            subtotal = obj.items.aggregate(s=Sum('subtotal'))['s'] or 0
            total = subtotal + (obj.shipping_cost or 0)
            return f"${total:,.0f} COP"
        return "$0 COP"
    total_display.short_description = 'Total'
    
    def total_display_readonly(self, obj):
        return self.total_display(obj)
    total_display_readonly.short_description = 'Total'
    
    def status_badge(self, obj):
        colors = {
            'pendiente': '#ffc107',
            'confirmado': '#17a2b8',
            'preparando': '#fd7e14',
            'listo': '#6c757d',
            'en_camino': '#007bff',
            'entregado': '#28a745',
            'cancelado': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        status_names = dict(Order.STATUS_CHOICES)
        return mark_safe(
            f'<span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">'
            f'{status_names.get(obj.status, obj.status)}</span>'
        )
    status_badge.short_description = 'Estado'
    
    def payment_badge(self, obj):
        if obj.is_paid:
            return mark_safe('<span style="color: green;">✓ Pagado</span>')
        return mark_safe('<span style="color: red;">✗ Pendiente</span>')
    payment_badge.short_description = 'Pago'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            if not obj.order_number:
                last_order = Order.objects.order_by('-id').first()
                if last_order and last_order.order_number:
                    try:
                        num = int(last_order.order_number.split('-')[1])
                        obj.order_number = f"ZCD-{str(num + 1).zfill(4)}"
                    except (IndexError, ValueError):
                        obj.order_number = "ZCD-0001"
                else:
                    obj.order_number = "ZCD-0001"
                
                import uuid
                obj.tracking_token = uuid.uuid4()
        
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        order = form.instance
        subtotal = order.items.aggregate(s=Sum('subtotal'))['s'] or 0
        order.subtotal = subtotal
        order.total_amount = subtotal + (order.shipping_cost or 0)
        order.save(update_fields=['subtotal', 'total_amount'])

    actions = ['confirm_orders', 'mark_as_preparing_orders', 'mark_as_ready_orders', 'mark_as_delivered_orders', 'cancel_orders']

    def confirm_orders(self, request, queryset):
        """Confirmar pedidos seleccionados (reduce stock)."""
        success_count = 0
        error_count = 0
        for order in queryset:
            try:
                order.confirm(user=request.user)
                success_count += 1
            except ValidationError as e:
                error_count += 1
                self.message_user(request, f'Error en {order.order_number}: {e}', level='ERROR')
        self.message_user(request, f'{success_count} pedido(s) confirmado(s). {error_count} error(es).')
    confirm_orders.short_description = 'Confirmar pedidos seleccionados'
    
    def mark_as_ready_orders(self, request, queryset):
        success_count = 0
        error_count = 0
        for order in queryset:
            try:
                order.mark_as_ready(user=request.user)
                success_count += 1
            except ValidationError as e:
                error_count += 1
                self.message_user(request, f'Error en {order.order_number}: {e}', level='ERROR')
        self.message_user(request, f'{success_count} pedido(s) marcado(s) como listos.')
    mark_as_ready_orders.short_description = 'Marcar seleccionados como listos para envío'

    def mark_as_preparing_orders(self, request, queryset):
        success_count = 0
        error_count = 0
        for order in queryset:
            try:
                order.mark_as_preparing(user=request.user)
                success_count += 1
            except ValidationError as e:
                error_count += 1
                self.message_user(request, f'Error en {order.order_number}: {e}', level='ERROR')
        self.message_user(request, f'{success_count} pedido(s) marcado(s) como en preparación.')
    mark_as_preparing_orders.short_description = 'Marcar seleccionados como en preparación'

    def mark_as_delivered_orders(self, request, queryset):
        """Marcar pedidos como entregados."""
        success_count = 0
        error_count = 0
        for order in queryset:
            try:
                order.mark_as_delivered(user=request.user)
                success_count += 1
            except ValidationError as e:
                error_count += 1
                self.message_user(request, f'Error en {order.order_number}: {e}', level='ERROR')
        self.message_user(request, f'{success_count} pedido(s) marcado(s) como entregados.')
    mark_as_delivered_orders.short_description = 'Marcar seleccionados como entregados'
    
    def cancel_orders(self, request, queryset):
        """Cancelar pedidos seleccionados (libera stock)."""
        # Mostrar un formulario para ingresar el motivo de cancelación
        from django.shortcuts import render
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        from django.contrib import messages
        
        if 'cancel' in request.POST:
            reason = request.POST.get('cancelled_reason', '')
            if not reason:
                self.message_user(request, 'Debe ingresar un motivo de cancelación.', level='ERROR')
                return HttpResponseRedirect(request.get_full_path())
            
            success_count = 0
            error_count = 0
            for order in queryset:
                try:
                    order.cancel(reason=reason, user=request.user)
                    success_count += 1
                except ValidationError as e:
                    error_count += 1
                    self.message_user(request, f'Error en {order.order_number}: {e}', level='ERROR')
            self.message_user(request, f'{success_count} pedido(s) cancelado(s). {error_count} error(es).')
            return HttpResponseRedirect(reverse('admin:orders_order_changelist'))
        
        context = {
            'orders': queryset,
            'title': 'Cancelar pedidos',
            'action': 'cancel_orders',
        }
        return render(request, 'admin/cancel_orders_confirmation.html', context)
    cancel_orders.short_description = 'Cancelar pedidos seleccionados'

    def get_urls(self):
        from django.urls import path
        from apps.orders.views import delivery_dashboard, take_order, deliver_order
        
        url = super().get_urls()
        custom_urls = [
            path('delivery/', delivery_dashboard, name='delivery_dashboard'),
            path('delivery/take/<int:order_id>/', take_order, name='take_order'),
            path('delivery/deliver/<int:order_id>/', deliver_order, name='deliver_order'),
        ]
        return custom_urls + url

    def app_index(self, request, extra_context=None):        
        context = {
            'pending_count': Order.objects.filter(status='pendiente').count(),
            'confirmed_count': Order.objects.filter(status='confirmado').count(),
            'preparing_count': Order.objects.filter(status='preparando').count(),
            'ready_count': Order.objects.filter(status='listo').count(),
            'en_camino_count': Order.objects.filter(status='en_camino').count(),
            'delivered_count': Order.objects.filter(status='entregado').count(),
            'cancelled_count': Order.objects.filter(status='cancelado').count(),
        }
        return super().app_index(request, extra_context=context)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_link', 'product_display', 'quantity', 'unit_price_display', 'subtotal_display')
    list_filter = ('order__status',)
    search_fields = ('order__order_number', 'product_name_snapshot')
    readonly_fields = ('product_name_snapshot', 'size_snapshot', 'unit_price', 'stock_snapshot', 'subtotal')
    list_per_page = 30
    
    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Pedido'
    
    def product_display(self, obj):
        if obj.variant:
            return f"{obj.variant.product.name} - {obj.variant.size.name}"
        return f"{obj.product_name_snapshot} - {obj.size_snapshot}"
    product_display.short_description = 'Producto'
    
    def unit_price_display(self, obj):
        return f"${obj.unit_price:,.0f} COP" if obj.unit_price else "-"
    unit_price_display.short_description = 'Precio unitario'
    
    def subtotal_display(self, obj):
        return f"${obj.subtotal:,.0f} COP" if obj.subtotal else "-"
    subtotal_display.short_description = 'Subtotal'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False