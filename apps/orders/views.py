import json
import logging
import time
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView

from apps.core.crud.mixins import FilterMixin, PaginationMixin
from apps.orders.stripe_client import get_stripe
from apps.products.models import ProductVariant
from apps.users.models import User

from .cart import Cart
from .email import send_order_confirmation_email
from .forms import (
    CheckoutOrderForm, OrderAssignDeliveryForm, OrderCancelForm,
    OrderConfirmForm, OrderCreateForm, OrderItemCreateForm,
    OrderItemDeleteForm, OrderItemUpdateForm, OrderMarkAsDeliveredForm,
    OrderUpdateForm
)
from .models import Order, OrderItem


# =============================================================================
# CONSTANTS
# =============================================================================

# Route names
DELIVERY_DASHBOARD_ROUTE = 'orders:delivery_dashboard'
ORDER_LIST_ROUTE = 'orders:order_list'
ORDER_DETAIL_ROUTE = 'orders:order_detail'
ORDER_CONFIRMATION_ROUTE = 'orders:order_confirmation'
CART_DETAIL_ROUTE = 'orders:cart_detail'
PRODUCTS_CATALOG_ROUTE = 'products:catalog'
CHECKOUT_ROUTE = 'orders:checkout'
CREATE_STRIPE_SESSION_ROUTE = 'orders:create_stripe_checkout_session'

# Order statuses
STATUS_PENDING = 'pendiente'
STATUS_CONFIRMED = 'confirmado'
STATUS_PREPARING = 'preparando'
STATUS_READY = 'listo'
STATUS_ON_THE_WAY = 'en_camino'
STATUS_DELIVERED = 'entregado'
STATUS_CANCELLED = 'cancelado'

# Status progression
STATUS_PROGRESSION = [
    STATUS_PENDING, STATUS_CONFIRMED, STATUS_PREPARING,
    STATUS_READY, STATUS_ON_THE_WAY, STATUS_DELIVERED
]

# Status badge mapping
STATUS_BADGE_MAP = {
    STATUS_PENDING: ('Pendiente', 'bg-yellow-100 text-yellow-700'),
    STATUS_CONFIRMED: ('Confirmado', 'bg-blue-100 text-blue-700'),
    STATUS_PREPARING: ('Preparando', 'bg-purple-100 text-purple-700'),
    STATUS_READY: ('Listo', 'bg-indigo-100 text-indigo-700'),
    STATUS_ON_THE_WAY: ('En camino', 'bg-orange-100 text-orange-700'),
    STATUS_DELIVERED: ('Entregado', 'bg-green-100 text-green-700'),
}
STATUS_BADGE_DEFAULT = ('Cancelado', 'bg-red-100 text-red-700')

# Webhook settings
WEBHOOK_MAX_RETRIES = 20
WEBHOOK_RETRY_DELAY = 0.5

# Template paths
TEMPLATE_DELIVERY_DASHBOARD = 'orders/delivery_dashboard.html'
TEMPLATE_CART_DETAIL = 'orders/cart_detail.html'
TEMPLATE_CHECKOUT = 'orders/checkout.html'
TEMPLATE_ORDER_CONFIRMATION = 'orders/order_confirmation.html'
TEMPLATE_TRACKING = 'orders/tracking.html'
TEMPLATE_ORDER_LIST = 'backoffice/orders/order_list.html'
TEMPLATE_ORDER_FORM = 'backoffice/orders/order_form.html'
TEMPLATE_ORDER_DETAIL = 'backoffice/orders/order_detail.html'
TEMPLATE_ORDER_CONFIRM = 'backoffice/orders/order_confirm.html'
TEMPLATE_ORDER_CANCEL = 'backoffice/orders/order_cancel.html'
TEMPLATE_ORDER_ASSIGN_DELIVERY = 'backoffice/orders/order_assign_delivery.html'
TEMPLATE_ORDER_MARK_DELIVERED = 'backoffice/orders/order_mark_delivered.html'
TEMPLATE_ORDER_ITEM_FORM = 'backoffice/orders/orderitem_form.html'
TEMPLATE_ORDER_ITEM_CONFIRM_DELETE = 'backoffice/orders/orderitem_confirm_delete.html'

# Messages
MESSAGE_CART_EMPTY = 'Tu carrito está vacío. Agrega productos antes de continuar.'
MESSAGE_CART_CLEARED = 'Carrito vaciado correctamente'
MESSAGE_ORDER_NOT_FOUND = 'Pedido no encontrado.'
MESSAGE_PAYMENT_PROCESSING = 'Tu pago está siendo procesado. Se actualizará automáticamente en breve.'
MESSAGE_NO_SHIPPING_DATA = 'No se encontraron datos de envío. Por favor, vuelve a intentarlo.'
MESSAGE_STOCK_INSUFFICIENT = 'stock insuficiente'

# Context keys
CONTEXT_ORDER = 'order'
CONTEXT_ITEMS = 'items'
CONTEXT_CANCEL_URL = 'cancel_url'
CONTEXT_CANCEL_ARGS = 'cancel_args'
CONTEXT_TITLE = 'title'
CONTEXT_ROWS = 'rows'
CONTEXT_HEADERS = 'headers'
CONTEXT_SHOW_ACTIONS = 'show_actions'
CONTEXT_EDIT_URL_NAME = 'edit_url_name'
CONTEXT_STATUS_CHOICES = 'status_choices'
CONTEXT_DELIVERY_USERS = 'delivery_users'
CONTEXT_CAN_ASSIGN = 'can_assign'
CONTEXT_CAN_ADD_ITEMS = 'can_add_items'
CONTEXT_ITEMS_ROWS = 'items_rows'
CONTEXT_ITEMS_HEADERS = 'items_headers'

# Table headers
HEADERS_ORDER_LIST = ['Pedido', 'Cliente', 'Total', 'Estado', 'Fecha']
HEADERS_ORDER_ITEMS = ['Producto', 'Talla', 'Cantidad', 'Precio unit.', 'Subtotal']

# Allowed statuses for adding items
ALLOWED_ADD_ITEMS_STATUSES = [STATUS_PENDING, STATUS_CONFIRMED]

# Date format
DATE_FORMAT_DISPLAY = '%d/%m/%Y %H:%M'


# =============================================================================
# DELIVERY VIEWS
# =============================================================================

@staff_member_required
@require_GET
def delivery_dashboard(request):
    """Dashboard for delivery staff."""
    pedidos_listos = Order.objects.filter(status=STATUS_READY)
    pedidos_asignados = Order.objects.filter(
        assigned_delivery_user=request.user,
        status=STATUS_ON_THE_WAY
    )

    context = {
        'pedidos_listos': pedidos_listos,
        'pedidos_asignados': pedidos_asignados,
    }
    return render(request, TEMPLATE_DELIVERY_DASHBOARD, context)


@staff_member_required
@require_POST
def take_order(request, order_id):
    """Assign order to current delivery user."""
    order = get_object_or_404(Order, id=order_id)

    if order.status != STATUS_READY:
        messages.error(
            request,
            f'El pedido {order.order_number} no está listo para entregar '
            f'(estado actual: {order.get_status_display()}).'
        )
        return redirect(DELIVERY_DASHBOARD_ROUTE)

    order.assigned_delivery_user = request.user
    order.status = STATUS_ON_THE_WAY
    order.save(update_fields=['assigned_delivery_user', 'status'])
    messages.success(request, f'Pedido {order.order_number} asignado correctamente.')
    return redirect(DELIVERY_DASHBOARD_ROUTE)


@staff_member_required
@require_POST
def deliver_order(request, order_id):
    """Mark order as delivered."""
    order = get_object_or_404(Order, id=order_id, assigned_delivery_user=request.user)
    order.mark_as_delivered(user=request.user)
    messages.success(request, f'Pedido {order.order_number} entregado y pagado.')
    return redirect(DELIVERY_DASHBOARD_ROUTE)


# =============================================================================
# CART API VIEWS
# =============================================================================

@require_POST
def cart_add(request):
    """Add product variant to cart."""
    try:
        data = json.loads(request.body) if request.body else request.POST
        variant_id = data.get('variant_id')
        quantity = int(data.get('quantity', 1))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    cart = Cart(request)

    try:
        cart.add(variant_id, quantity)
        variant = ProductVariant.objects.select_related(
            'product', 'product_color__color', 'size'
        ).get(id=variant_id)

        mensaje = f'{quantity}x {variant.product.name} - {variant.product_color.color.name} - {variant.size.name} agregado al carrito'
        messages.success(request, mensaje)

        return JsonResponse({
            'success': True,
            'total_items': cart.get_total_items(),
            'message': mensaje
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_POST
def cart_remove(request):
    """Remove product variant from cart."""
    try:
        data = json.loads(request.body) if request.body else request.POST
        variant_id = data.get('variant_id')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    cart = Cart(request)
    cart.remove(variant_id)

    return JsonResponse({
        'success': True,
        'total_items': cart.get_total_items(),
    })


@require_POST
def cart_update(request):
    """Update product quantity in cart."""
    try:
        data = json.loads(request.body) if request.body else request.POST
        variant_id = data.get('variant_id')
        quantity = data.get('quantity')

        if isinstance(quantity, str):
            quantity = int(quantity)
        elif not isinstance(quantity, int):
            return JsonResponse({'error': 'Cantidad inválida'}, status=400)
    except (ValueError, TypeError) as e:
        return JsonResponse({'error': f'Datos inválidos: {str(e)}'}, status=400)

    cart = Cart(request)

    try:
        cart.update_quantity(variant_id, quantity)
        return JsonResponse({
            'success': True,
            'total_items': cart.get_total_items(),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_POST
def cart_clear(request):
    """Clear all items from cart."""
    cart = Cart(request)
    cart.clear()
    return JsonResponse({
        'success': True,
        'total_items': 0,
        'message': MESSAGE_CART_CLEARED
    })


@require_GET
def cart_data(request):
    """Get cart data as JSON."""
    cart = Cart(request)
    summary = cart.get_summary()

    summary['subtotal'] = float(summary['subtotal'])
    summary['shipping_cost'] = float(summary['shipping_cost'])
    summary['total'] = float(summary['total'])

    for item in summary['items']:
        item['price'] = float(item['price'])
        item['subtotal'] = float(Decimal(item['price']) * item['quantity'])

    return JsonResponse(summary)


@require_GET
def cart_detail(request):
    """Render cart detail page."""
    cart = Cart(request)
    summary = cart.get_summary()

    for item in summary['items']:
        item['total'] = item['price'] * item['quantity']

    context = {
        'items': summary['items'],
        'subtotal': summary['subtotal'],
        'shipping_cost': summary['shipping_cost'],
        'total': summary['total'],
        'is_empty': summary['is_empty'],
        'total_items': summary['total_items'],
    }
    return render(request, TEMPLATE_CART_DETAIL, context)


# =============================================================================
# CHECKOUT & PAYMENT FLOW
# =============================================================================

@require_http_methods(['GET', 'POST'])
def checkout(request):
    """Checkout page - collects customer information."""
    cart = Cart(request)

    if cart.is_empty():
        messages.warning(request, MESSAGE_CART_EMPTY)
        return redirect(PRODUCTS_CATALOG_ROUTE)

    stock_errors = cart.validate_stock()
    if stock_errors:
        for error in stock_errors:
            messages.error(
                request,
                f'"{error["name"]}" ({error["size"]}, {error["color"]}): '
                f'solicitado {error["requested"]}, disponible {error["available"]}'
            )
        return redirect(CART_DETAIL_ROUTE)

    if request.method == 'POST':
        form = CheckoutOrderForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            request.session['checkout_data'] = {
                'customer_name': cleaned_data['customer_name'],
                'customer_phone': cleaned_data['customer_phone'],
                'customer_email': cleaned_data['customer_email'],
                'shipping_address': cleaned_data['shipping_address'],
                'delivery_notes': cleaned_data['delivery_notes'],
            }
            return redirect(CREATE_STRIPE_SESSION_ROUTE)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    field_label = form.fields[field].label if field in form.fields else field
                    messages.error(request, f'{field_label}: {error}')
    else:
        form = CheckoutOrderForm()

    summary = cart.get_summary()
    context = {
        'form': form,
        'cart_summary': {
            'items': summary['items'],
            'subtotal': float(summary['subtotal']),
            'shipping_cost': float(summary['shipping_cost']),
            'total': float(summary['total']),
        },
    }
    return render(request, TEMPLATE_CHECKOUT, context)


@require_http_methods(['GET', 'POST'])
def create_stripe_checkout_session(request):
    """Create Stripe checkout session."""
    stripe = get_stripe()
    cart = Cart(request)

    if cart.is_empty():
        messages.error(request, MESSAGE_CART_EMPTY)
        return redirect(PRODUCTS_CATALOG_ROUTE)

    stock_errors = cart.validate_stock()
    if stock_errors:
        for error in stock_errors:
            messages.error(
                request,
                f'"{error["name"]}" ({error["size"]}, {error["color"]}): {MESSAGE_STOCK_INSUFFICIENT}'
            )
        return redirect(CART_DETAIL_ROUTE)

    checkout_data = request.session.get('checkout_data')
    if not checkout_data:
        messages.error(request, MESSAGE_NO_SHIPPING_DATA)
        return redirect(CHECKOUT_ROUTE)

    customer_name = checkout_data.get('customer_name')
    customer_phone = checkout_data.get('customer_phone')
    customer_email = checkout_data.get('customer_email')
    shipping_address = checkout_data.get('shipping_address')
    delivery_notes = checkout_data.get('delivery_notes', '')

    # Create order
    order = Order(
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email or None,
        shipping_address=shipping_address,
        delivery_notes=delivery_notes,
        subtotal=cart.get_subtotal(),
        shipping_cost=cart.get_shipping_cost(),
        total_amount=cart.get_total(),
        status=STATUS_PENDING,
        is_paid=False,
    )
    order.save()

    for item in cart.get_items():
        variant = ProductVariant.objects.get(id=item['variant_id'])
        OrderItem.objects.create(
            order=order,
            variant=variant,
            product_name_snapshot=item['product_name'],
            size_snapshot=item['size_name'],
            quantity=item['quantity'],
            unit_price=Decimal(item['price']),
            stock_snapshot=variant.stock,
            subtotal=Decimal(item['price']) * item['quantity']
        )

    try:
        success_url = settings.SITE_URL + reverse(
            ORDER_CONFIRMATION_ROUTE,
            kwargs={'order_number': order.order_number}
        )
        cancel_url = settings.SITE_URL + reverse(CART_DETAIL_ROUTE)

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'cop',
                    'unit_amount': int(cart.get_total() * 100),
                    'product_data': {
                        'name': f'Pedido Zicada - {customer_name}',
                        'description': f'{cart.get_total_items()} productos',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(order.order_number),
            customer_email=customer_email or None,
            metadata={
                'order_number': order.order_number,
                'session_key': request.session.session_key,
            }
        )

        order.payment_session_id = checkout_session.id
        order.save(update_fields=['payment_session_id'])
        del request.session['checkout_data']
        return redirect(checkout_session.url)

    except Exception as e:
        order.status = STATUS_CANCELLED
        order.cancelled_reason = f'Error al crear sesión de pago: {str(e)}'
        order.save()
        messages.error(request, f'Error al procesar el pago: {str(e)}')
        return redirect(CHECKOUT_ROUTE)


@require_GET
def order_confirmation(request, order_number):
    """Order confirmation page."""
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        messages.error(request, MESSAGE_ORDER_NOT_FOUND)
        return redirect(PRODUCTS_CATALOG_ROUTE)

    if not order.is_paid:
        for _ in range(WEBHOOK_MAX_RETRIES):
            if order.is_paid:
                break
            time.sleep(WEBHOOK_RETRY_DELAY)
            order.refresh_from_db()

    if order.is_paid:
        cart = Cart(request)
        if not cart.is_empty():
            cart.clear()
    else:
        messages.warning(request, MESSAGE_PAYMENT_PROCESSING)

    context = {
        CONTEXT_ORDER: order,
        CONTEXT_ITEMS: order.items.all(),
    }
    return render(request, TEMPLATE_ORDER_CONFIRMATION, context)


@require_GET
def order_tracking(request, tracking_token):
    """Public order tracking page."""
    order = get_object_or_404(Order, tracking_token=tracking_token)

    current_step = STATUS_PROGRESSION.index(order.status) if order.status in STATUS_PROGRESSION else 0
    total_steps = len(STATUS_PROGRESSION) - 1

    context = {
        CONTEXT_ORDER: order,
        CONTEXT_ITEMS: order.items.all(),
        'current_step': current_step,
        'total_steps': total_steps,
        'status_percentage': (current_step / total_steps) * 100 if total_steps > 0 else 0,
    }
    return render(request, TEMPLATE_TRACKING, context)


# =============================================================================
# STRIPE WEBHOOK
# =============================================================================

@require_POST
@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events."""
    import stripe
    logger = logging.getLogger(__name__)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_KEY
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        session_id = session['id']

        try:
            order = Order.objects.get(payment_session_id=session_id)
            logger.info(f"Webhook recibido para pedido {order.order_number}")
        except Order.DoesNotExist:
            logger.error(f"Pedido no encontrado para session_id: {session_id}")
            return HttpResponse(status=200)

        if order.is_paid:
            logger.info(f"Pedido {order.order_number} ya estaba pagado")
            return HttpResponse(status=200)

        try:
            if order.status == STATUS_PENDING:
                order.confirm(user=None)

            order.is_paid = True
            order.save(update_fields=['is_paid'])
            logger.info(f"Pedido {order.order_number} marcado como pagado")

            if order.customer_email:
                send_order_confirmation_email(order)
                logger.info(f"Correo de confirmación enviado a {order.customer_email}")
            else:
                logger.warning(f"Pedido {order.order_number} no tiene email asociado")

        except Exception as e:
            logging.exception(f"Error al procesar pedido {order.order_number}: {e}")
            return HttpResponse(status=500)

    return HttpResponse(status=200)


# =============================================================================
# BACKOFFICE ORDER VIEWS
# =============================================================================

class OrderListView(PermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    model = Order
    template_name = TEMPLATE_ORDER_LIST
    context_object_name = 'orders'
    permission_required = 'orders.view_order'
    paginate_by = 20

    filters = [
        ('status', 'status', 'exact'),
        ('customer_name', 'customer_name', 'icontains'),
        ('customer_phone', 'customer_phone', 'icontains'),
        ('order_number', 'order_number', 'icontains'),
    ]

    def get_queryset(self):
        qs = super().get_queryset().select_related('assigned_delivery_user')
        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(
                models.Q(order_number__icontains=search) |
                models.Q(customer_name__icontains=search) |
                models.Q(customer_phone__icontains=search)
            )
        return qs

    def get_status_badge(self, status):
        label, color_class = STATUS_BADGE_MAP.get(status, STATUS_BADGE_DEFAULT)
        return mark_safe(f'<span class="px-2 py-1 text-xs rounded-full {color_class}">{label}</span>')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        for order in context['orders']:
            rows.append({
                'pk': order.pk,
                'values': [
                    order.order_number,
                    order.customer_name,
                    f"${order.total_amount:,.0f}",
                    self.get_status_badge(order.status),
                    order.created_at.strftime(DATE_FORMAT_DISPLAY),
                ],
            })
        context[CONTEXT_ROWS] = rows
        context[CONTEXT_HEADERS] = HEADERS_ORDER_LIST
        context[CONTEXT_SHOW_ACTIONS] = True
        context[CONTEXT_EDIT_URL_NAME] = 'orders:order_edit'
        context[CONTEXT_STATUS_CHOICES] = Order.STATUS_CHOICES
        return context


class OrderCreateView(PermissionRequiredMixin, CreateView):
    model = Order
    form_class = OrderCreateForm
    template_name = TEMPLATE_ORDER_FORM
    permission_required = 'orders.add_order'
    success_url = reverse_lazy(ORDER_LIST_ROUTE)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = ORDER_LIST_ROUTE
        context[CONTEXT_TITLE] = 'Crear pedido manual'
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Pedido {form.instance.order_number} creado exitosamente.')
        return response


class OrderUpdateView(PermissionRequiredMixin, UpdateView):
    model = Order
    form_class = OrderUpdateForm
    template_name = TEMPLATE_ORDER_FORM
    permission_required = 'orders.change_order'
    success_url = reverse_lazy(ORDER_LIST_ROUTE)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = ORDER_LIST_ROUTE
        context[CONTEXT_TITLE] = f'Editar pedido {self.object.order_number}'
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Pedido {form.instance.order_number} actualizado exitosamente.')
        return response


class OrderDetailView(PermissionRequiredMixin, DetailView):
    model = Order
    template_name = TEMPLATE_ORDER_DETAIL
    context_object_name = CONTEXT_ORDER
    permission_required = 'orders.view_order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object

        context[CONTEXT_DELIVERY_USERS] = User.objects.filter(is_delivery=True, is_active=True)
        context[CONTEXT_CAN_ASSIGN] = order.status == STATUS_READY
        context[CONTEXT_CAN_ADD_ITEMS] = order.status in ALLOWED_ADD_ITEMS_STATUSES

        items_rows = []
        for item in order.items.all():
            items_rows.append({
                'pk': item.pk,
                'values': [
                    item.product_name_snapshot,
                    item.size_snapshot,
                    item.quantity,
                    f"${item.unit_price:,.0f}",
                    f"${item.subtotal:,.0f}",
                ],
            })
        context[CONTEXT_ITEMS_ROWS] = items_rows
        context[CONTEXT_ITEMS_HEADERS] = HEADERS_ORDER_ITEMS
        return context


class OrderConfirmView(PermissionRequiredMixin, FormView):
    form_class = OrderConfirmForm
    template_name = TEMPLATE_ORDER_CONFIRM
    permission_required = 'orders.change_order'

    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order'] = self.order
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_ORDER] = self.order
        context[CONTEXT_CANCEL_URL] = ORDER_DETAIL_ROUTE
        context[CONTEXT_CANCEL_ARGS] = [self.order.pk]
        return context

    def form_valid(self, form):
        self.order.confirm(user=self.request.user)
        messages.success(self.request, f'Pedido {self.order.order_number} confirmado exitosamente.')
        return redirect(ORDER_DETAIL_ROUTE, pk=self.order.pk)


class OrderCancelView(PermissionRequiredMixin, FormView):
    form_class = OrderCancelForm
    template_name = TEMPLATE_ORDER_CANCEL
    permission_required = 'orders.change_order'

    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order'] = self.order
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_ORDER] = self.order
        context[CONTEXT_CANCEL_URL] = ORDER_DETAIL_ROUTE
        context[CONTEXT_CANCEL_ARGS] = [self.order.pk]
        return context

    def form_valid(self, form):
        reason = form.cleaned_data['reason']
        self.order.cancel(reason=reason, user=self.request.user)
        messages.success(self.request, f'Pedido {self.order.order_number} cancelado exitosamente.')
        return redirect(ORDER_DETAIL_ROUTE, pk=self.order.pk)


class OrderMarkPreparingView(PermissionRequiredMixin, View):
    permission_required = 'orders.change_order'

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        try:
            order.mark_as_preparing(user=request.user)
            messages.success(request, f'Pedido {order.order_number} marcado como en preparación.')
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect(ORDER_DETAIL_ROUTE, pk=order.pk)


class OrderMarkReadyView(PermissionRequiredMixin, View):
    permission_required = 'orders.change_order'

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        try:
            order.mark_as_ready(user=request.user)
            messages.success(request, f'Pedido {order.order_number} marcado como listo para envío.')
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect(ORDER_DETAIL_ROUTE, pk=order.pk)


class OrderAssignDeliveryView(PermissionRequiredMixin, FormView):
    form_class = OrderAssignDeliveryForm
    template_name = TEMPLATE_ORDER_ASSIGN_DELIVERY
    permission_required = 'orders.change_order'

    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order'] = self.order
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_ORDER] = self.order
        context[CONTEXT_CANCEL_URL] = ORDER_DETAIL_ROUTE
        context[CONTEXT_CANCEL_ARGS] = [self.order.pk]
        return context

    def form_valid(self, form):
        delivery_user = form.cleaned_data['delivery_user']
        self.order.assign_delivery(delivery_user, user=self.request.user)
        messages.success(self.request, f'Repartidor asignado al pedido {self.order.order_number}.')
        return redirect(ORDER_DETAIL_ROUTE, pk=self.order.pk)


class OrderMarkAsDeliveredView(PermissionRequiredMixin, FormView):
    form_class = OrderMarkAsDeliveredForm
    template_name = TEMPLATE_ORDER_MARK_DELIVERED
    permission_required = 'orders.change_order'

    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order'] = self.order
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_ORDER] = self.order
        context[CONTEXT_CANCEL_URL] = ORDER_DETAIL_ROUTE
        context[CONTEXT_CANCEL_ARGS] = [self.order.pk]
        return context

    def form_valid(self, form):
        self.order.mark_as_delivered(user=self.request.user)
        messages.success(self.request, f'Pedido {self.order.order_number} marcado como entregado.')
        return redirect(ORDER_DETAIL_ROUTE, pk=self.order.pk)


class OrderItemCreateView(PermissionRequiredMixin, CreateView):
    model = OrderItem
    form_class = OrderItemCreateForm
    template_name = TEMPLATE_ORDER_ITEM_FORM
    permission_required = 'orders.change_order'

    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs['order_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order'] = self.order
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_ORDER] = self.order
        context[CONTEXT_CANCEL_URL] = ORDER_DETAIL_ROUTE
        context[CONTEXT_CANCEL_ARGS] = [self.order.pk] if self.order and self.order.pk else []
        return context

    def form_valid(self, form):
        form.instance.order = self.order
        self.order.save()  # Recalcula totales
        messages.success(self.request, f'Producto agregado al pedido {self.order.order_number}.')
        return redirect(ORDER_DETAIL_ROUTE, pk=self.order.pk)


class OrderItemUpdateView(PermissionRequiredMixin, UpdateView):
    model = OrderItem
    form_class = OrderItemUpdateForm
    template_name = TEMPLATE_ORDER_ITEM_FORM
    permission_required = 'orders.change_order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_ORDER] = self.object.order
        context[CONTEXT_CANCEL_URL] = ORDER_DETAIL_ROUTE
        context[CONTEXT_CANCEL_ARGS] = [self.object.order.pk] if self.object.order and self.object.order.pk else []
        context[CONTEXT_TITLE] = 'Editar cantidad'
        return context

    def get_success_url(self):
        return reverse_lazy(ORDER_DETAIL_ROUTE, kwargs={'pk': self.object.order.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.order.save()
        messages.success(self.request, f'Cantidad actualizada en pedido {self.object.order.order_number}.')
        return response


class OrderItemDeleteView(PermissionRequiredMixin, FormView):
    form_class = OrderItemDeleteForm
    template_name = TEMPLATE_ORDER_ITEM_CONFIRM_DELETE
    permission_required = 'orders.change_order'

    def dispatch(self, request, *args, **kwargs):
        self.order_item = get_object_or_404(OrderItem, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order_item'] = self.order_item
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_ORDER] = self.order_item.order
        context['order_item'] = self.order_item
        context[CONTEXT_CANCEL_URL] = ORDER_DETAIL_ROUTE
        context[CONTEXT_CANCEL_ARGS] = [self.order_item.order.pk] if self.order_item.order and self.order_item.order.pk else []
        return context

    def form_valid(self, form):
        order_pk = self.order_item.order.pk
        self.order_item.delete()
        order = Order.objects.get(pk=order_pk)
        order.save()
        messages.success(self.request, f'Producto eliminado del pedido {order.order_number}.')
        return redirect(ORDER_DETAIL_ROUTE, pk=order_pk)