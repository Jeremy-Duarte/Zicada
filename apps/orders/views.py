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

logger = logging.getLogger(__name__)

from apps.core.url_names import (
    ORDERS_DELIVERY_DASHBOARD,
    ORDERS_LIST,
    ORDERS_DETAIL,
    ORDERS_CONFIRMATION,
    ORDERS_CART_DETAIL,
    PRODUCTS_CATALOG,
    ORDERS_CHECKOUT,
    ORDERS_CREATE_STRIPE_SESSION,
)

from .constants import (
    DEFAULT_SHIPPING_COST,
    CART_EXPIRATION_DAYS,
    MAX_QUANTITY_PER_ITEM,
    FREE_SHIPPING_THRESHOLD,
    # Order statuses
    STATUS_PENDING,
    STATUS_CONFIRMED,
    STATUS_PREPARING,
    STATUS_READY,
    STATUS_ON_THE_WAY,
    STATUS_DELIVERED,
    STATUS_CANCELLED,
    # Status progression
    STATUS_PROGRESSION,
    # Status badge mapping
    STATUS_BADGE_MAP,
    STATUS_BADGE_DEFAULT,
    # Webhook settings
    WEBHOOK_MAX_RETRIES,
    WEBHOOK_RETRY_DELAY,
    # Stock thresholds
    LOW_STOCK_THRESHOLD,
    # Pagination
    PAGINATE_BY_DEFAULT,
    # Query parameters
    QUERY_PARAM_SEARCH,
    # Template paths
    TEMPLATE_DELIVERY_DASHBOARD,
    TEMPLATE_CART_DETAIL,
    TEMPLATE_CHECKOUT,
    TEMPLATE_ORDER_CONFIRMATION,
    TEMPLATE_TRACKING,
    TEMPLATE_ORDER_LIST,
    TEMPLATE_ORDER_FORM,
    TEMPLATE_ORDER_DETAIL,
    TEMPLATE_ORDER_CONFIRM,
    TEMPLATE_ORDER_CANCEL,
    TEMPLATE_ORDER_ASSIGN_DELIVERY,
    TEMPLATE_ORDER_MARK_DELIVERED,
    TEMPLATE_ORDER_ITEM_FORM,
    TEMPLATE_ORDER_ITEM_CONFIRM_DELETE,
    # Messages
    MESSAGE_CART_EMPTY,
    MESSAGE_CART_CLEARED,
    MESSAGE_ORDER_NOT_FOUND,
    MESSAGE_PAYMENT_PROCESSING,
    MESSAGE_NO_SHIPPING_DATA,
    MESSAGE_STOCK_INSUFFICIENT,
    # Error messages
    MSG_INVALID_DATA,
    MSG_QUANTITY_MIN,
    MSG_QUANTITY_MAX,
    MSG_PRODUCT_UNAVAILABLE,
    MSG_OUT_OF_STOCK,
    MSG_INSUFFICIENT_STOCK,
    MSG_PRODUCT_NOT_FOUND,
    MSG_CART_ALREADY_EMPTY,
    MSG_PRODUCT_REMOVED_WARNING,
    MSG_UPDATE_ERROR,
    MSG_REMOVE_ERROR,
    MSG_ADD_ERROR,
    # Stock status strings
    STOCK_STATUS_OUT_OF_STOCK,
    STOCK_STATUS_LOW_STOCK,
    STOCK_STATUS_AVAILABLE,
    STOCK_STATUS_UNAVAILABLE,
    # Stripe product data templates
    STRIPE_PRODUCT_NAME_TEMPLATE,
    STRIPE_PRODUCT_DESCRIPTION_TEMPLATE,
    # Context keys
    CONTEXT_ORDER,
    CONTEXT_ITEMS,
    CONTEXT_CANCEL_URL,
    CONTEXT_CANCEL_ARGS,
    CONTEXT_TITLE,
    CONTEXT_ROWS,
    CONTEXT_HEADERS,
    CONTEXT_SHOW_ACTIONS,
    CONTEXT_EDIT_URL_NAME,
    CONTEXT_STATUS_CHOICES,
    CONTEXT_DELIVERY_USERS,
    CONTEXT_CAN_ASSIGN,
    CONTEXT_CAN_ADD_ITEMS,
    CONTEXT_ITEMS_ROWS,
    CONTEXT_ITEMS_HEADERS,
    # Table headers
    HEADERS_ORDER_LIST,
    HEADERS_ORDER_ITEMS,
    # Allowed statuses for adding items
    ALLOWED_ADD_ITEMS_STATUSES,
    # Date format
    DATE_FORMAT_DISPLAY,
    # Perms
    PERM_ORDER_VIEW,
    PERM_ORDER_ADD,
    PERM_ORDER_CHANGE,
)


# =============================================================================
# DELIVERY VIEWS (HU-033, HU-034, HU-035, HU-036)
# =============================================================================

@staff_member_required
@require_GET
def delivery_dashboard(request):
    """
    HU-033: Consultar pedidos del día (entregador)
    HU-036: Ver resumen del día (parcial - solo lista, no hay resumen)
    """
    # HU-033 | ESCENARIO 1 | H | Lista de pedidos listos y asignados
    pedidos_listos = Order.objects.filter(status=STATUS_READY)
    pedidos_asignados = Order.objects.filter(
        assigned_delivery_user=request.user,
        status=STATUS_ON_THE_WAY
    )
    # HU-033 | ESCENARIO 2 | A | Sin pedidos asignados → template muestra mensaje
    # HU-033 | ESCENARIO 3 | H | Pull-to-refresh (se recarga la página, manejado por el template)

    context = {
        'pedidos_listos': pedidos_listos,
        'pedidos_asignados': pedidos_asignados,
    }
    return render(request, TEMPLATE_DELIVERY_DASHBOARD, context)
    # HU-036 | ESCENARIO 1 | H | Resumen del día (no implementado, solo lista básica)
    # HU-036 | ESCENARIO 2 | H | Cierre de jornada (NO IMPLEMENTADO)


@staff_member_required
@require_POST
def take_order(request, order_id):
    """
    HU-033 (parte): Asignar pedido a repartidor
    HU-034: Marcar pedido como pagado (no, esto es solo asignación)
    """
    # HU-033 | ESCENARIO 1 | H | Repartidor toma un pedido listo
    order = get_object_or_404(Order, id=order_id)

    if order.status != STATUS_READY:
        messages.error(
            request,
            f'El pedido {order.order_number} no está listo para entregar '
            f'(estado actual: {order.get_status_display()}).'
        )
        return redirect(ORDERS_DELIVERY_DASHBOARD)

    order.assigned_delivery_user = request.user
    order.status = STATUS_ON_THE_WAY
    order.save(update_fields=['assigned_delivery_user', 'status'])
    messages.success(request, f'Pedido {order.order_number} asignado correctamente.')
    return redirect(ORDERS_DELIVERY_DASHBOARD)


@staff_member_required
@require_POST
def deliver_order(request, order_id):
    """
    HU-034: Marcar pedido como pagado (entregador)
    """
    # HU-034 | ESCENARIO 1 | H | Pedido marcado como pagado/entregado
    # HU-034 | ESCENARIO 2 | H | Confirmación requerida (se muestra mensaje de éxito)
    order = get_object_or_404(Order, id=order_id, assigned_delivery_user=request.user)
    order.mark_as_delivered(user=request.user)
    messages.success(request, f'Pedido {order.order_number} entregado y pagado.')
    # HU-034 | ESCENARIO 3 | E | Pedido ya pagado (no se puede marcar de nuevo, validado en modelo)
    return redirect(ORDERS_DELIVERY_DASHBOARD)

# HU-035 | Registrar incidencia (NO IMPLEMENTADO en este código)
# PENDIENTE: HU-035 - Registrar incidencia por parte del entregador.
# Motivo: No hay vista ni formulario para reportar incidencias.


# =============================================================================
# CART API VIEWS (HU-019, HU-020, HU-021, HU-022)
# =============================================================================

def _get_stock_status(stock):
    """Helper function to determine stock status."""
    if stock == 0:
        return STOCK_STATUS_OUT_OF_STOCK
    elif stock <= LOW_STOCK_THRESHOLD:
        return STOCK_STATUS_LOW_STOCK
    return STOCK_STATUS_AVAILABLE


@require_POST
def cart_add(request):
    """
    HU-019: Añadir producto al carrito
    """
    try:
        data = json.loads(request.body) if request.body else request.POST
        variant_id = data.get('variant_id')
        quantity = int(data.get('quantity', 1))
    except (ValueError, TypeError):
        return JsonResponse({'error': MSG_INVALID_DATA}, status=400)

    # HU-019 | ESCENARIO 2 | A | Sin talla seleccionada (no aplica, el frontenvía variant_id)
    if quantity < 1:
        return JsonResponse({'error': MSG_QUANTITY_MIN}, status=400)
    
    if quantity > MAX_QUANTITY_PER_ITEM:
        return JsonResponse({'error': MSG_QUANTITY_MAX.format(max_quantity=MAX_QUANTITY_PER_ITEM)}, status=400)

    cart = Cart(request)

    try:
        variant = ProductVariant.objects.select_related(
            'product', 'product_color__color', 'size'
        ).get(id=variant_id, is_active=True)
        
        if not variant.is_active:
            # HU-019 | ESCENARIO 3 | E | Producto sin stock en la talla (o inactivo)
            return JsonResponse({'error': f'❌ "{variant.product.name}" {MSG_PRODUCT_UNAVAILABLE}'}, status=400)
        
        current_qty = 0
        if hasattr(cart, 'cart') and isinstance(cart.cart, dict):
            item_data = cart.cart.get(str(variant_id))
            if item_data:
                current_qty = item_data.get('quantity', 0)
        
        new_qty = current_qty + quantity
        
        if variant.stock == 0:
            return JsonResponse({
                'error': f'❌ "{variant.product.name}" - {variant.size.name} / {variant.color_name} {MSG_OUT_OF_STOCK}'
            }, status=400)
        
        if new_qty > variant.stock:
            return JsonResponse({
                'error': MSG_INSUFFICIENT_STOCK.format(
                    product=variant.product.name,
                    size=variant.size.name,
                    color=variant.color_name,
                    stock=variant.stock
                )
            }, status=400)

        # HU-019 | ESCENARIO 1 | H | Producto añadido exitosamente
        cart.add(variant_id, quantity)

        # HU-019 | ESCENARIO 4 | H | Producto ya en carrito (misma talla) → aumenta cantidad
        return JsonResponse({
            'success': True,
            'total_items': cart.get_total_items(),
        })

    except ProductVariant.DoesNotExist:
        return JsonResponse({'error': MSG_PRODUCT_NOT_FOUND}, status=404)
    except ValidationError as e:
        return JsonResponse({'error': f'⚠️ {str(e)}'}, status=400)
    except Exception as e:
        logger.exception("Error in cart_add")
        return JsonResponse({'error': MSG_ADD_ERROR}, status=400)


@require_POST
def cart_remove(request):
    """
    HU-020: Quitar producto del carrito
    """
    try:
        data = json.loads(request.body) if request.body else request.POST
        variant_id = data.get('variant_id')
    except (ValueError, TypeError):
        return JsonResponse({'error': MSG_INVALID_DATA}, status=400)

    cart = Cart(request)

    try:
        if not cart.get_item(variant_id):
            return JsonResponse({'error': MSG_PRODUCT_NOT_FOUND}, status=404)
        
        variant = ProductVariant.objects.filter(id=variant_id).first()
        if variant:
            logger.info(f"Removing from cart: {variant.product.name} - {variant.size.name}")
        
        # HU-020 | ESCENARIO 1 | H | Producto eliminado exitosamente
        cart.remove(variant_id)
        # HU-020 | ESCENARIO 2 | A | Eliminar última unidad de producto con cantidad > 1 (el carrito maneja la eliminación completa)
        # HU-020 | ESCENARIO 3 | A | Carrito vacío después de eliminar (el template lo maneja)
        
        return JsonResponse({
            'success': True,
            'total_items': cart.get_total_items(),
        })
        
    except Exception:
        logger.exception("Error in cart_remove")
        return JsonResponse({'error': MSG_REMOVE_ERROR}, status=400)


@require_POST
def cart_update(request):
    """
    HU-021: Modificar cantidad en carrito
    """
    try:
        data = json.loads(request.body) if request.body else request.POST
        variant_id = data.get('variant_id')
        quantity = data.get('quantity')
        
        if isinstance(quantity, str):
            quantity = int(quantity)
        elif not isinstance(quantity, int):
            return JsonResponse({'error': MSG_INVALID_DATA}, status=400)
            
    except (ValueError, TypeError):
        return JsonResponse({'error': MSG_INVALID_DATA}, status=400)

    if quantity < 0:
        return JsonResponse({'error': MSG_QUANTITY_MIN}, status=400)
    
    if quantity > MAX_QUANTITY_PER_ITEM:
        return JsonResponse({'error': MSG_QUANTITY_MAX.format(max_quantity=MAX_QUANTITY_PER_ITEM)}, status=400)

    cart = Cart(request)

    if quantity == 0:
        # HU-021 | ESCENARIO 2 | H | Disminuir cantidad a 0 elimina el producto
        cart.remove(variant_id)
        return JsonResponse({
            'success': True, 
            'total_items': cart.get_total_items()
        })

    try:
        if not cart.get_item(variant_id):
            return JsonResponse({'error': MSG_PRODUCT_NOT_FOUND}, status=404)
        
        variant = ProductVariant.objects.select_related(
            'product', 'product_color__color', 'size'
        ).get(id=variant_id, is_active=True)
        
        if quantity > variant.stock:
            # HU-021 | ESCENARIO 3 | A | Límite de stock alcanzado
            if variant.stock == 0:
                return JsonResponse({
                    'error': f'❌ "{variant.product.name}" - {variant.size.name} / {variant.color_name} {MSG_OUT_OF_STOCK}. {MSG_PRODUCT_REMOVED_WARNING}'
                }, status=400)
            else:
                return JsonResponse({
                    'error': MSG_INSUFFICIENT_STOCK.format(
                        product=variant.product.name,
                        size=variant.size.name,
                        color=variant.color_name,
                        stock=variant.stock
                    )
                }, status=400)
        
        # HU-021 | ESCENARIO 1 | H | Aumentar cantidad
        # HU-021 | ESCENARIO 2 | H | Disminuir cantidad (si quantity>0)
        # HU-021 | ESCENARIO 4 | E | Cantidad no puede ser negativa (ya validado)
        cart.update_quantity(variant_id, quantity)
        
        return JsonResponse({
            'success': True,
            'total_items': cart.get_total_items(),
        })
        
    except ProductVariant.DoesNotExist:
        cart.remove(variant_id)
        return JsonResponse({
            'success': True,
            'total_items': cart.get_total_items(),
            'warning': MSG_PRODUCT_REMOVED_WARNING
        })
    except ValidationError as e:
        return JsonResponse({'error': f'⚠️ {str(e)}'}, status=400)
    except Exception as e:
        logger.exception("Error in cart_update")
        return JsonResponse({'error': MSG_UPDATE_ERROR}, status=400)


@require_POST
def cart_clear(request):
    """
    HU-020 (parte): Limpiar carrito (acción masiva)
    """
    cart = Cart(request)
    
    if cart.is_empty():
        return JsonResponse({'warning': MSG_CART_ALREADY_EMPTY})

    item_count = cart.get_total_items()
    cart.clear()
    
    logger.info(f"Cart cleared: {item_count} items removed")
    
    return JsonResponse({
        'success': True,
        'total_items': 0
    })


@require_GET
def cart_data(request):
    """
    HU-022: Consultar carrito (vía API)
    """
    # HU-022 | ESCENARIO 1 | H | Carrito con productos (retorna JSON)
    # HU-022 | ESCENARIO 2 | A | Carrito vacío (retorna is_empty=True)
    # HU-022 | ESCENARIO 3 | H | Persistencia del carrito (se maneja en el objeto Cart con sesión)
    cart = Cart(request)
    summary = cart.get_summary()

    summary['subtotal'] = float(summary['subtotal'])
    summary['shipping_cost'] = float(summary['shipping_cost'])
    summary['total'] = float(summary['total'])

    for item in summary['items']:
        item['price'] = float(item['price'])
        item['subtotal'] = float(Decimal(item['price']) * item['quantity'])

        try:
            variant = ProductVariant.objects.select_related(
                'product', 'product_color__color', 'size'
            ).get(id=item['variant_id'])
            
            item['stock_available'] = variant.stock
            item['max_quantity'] = min(variant.stock, MAX_QUANTITY_PER_ITEM)
            item['is_low_stock'] = 0 < variant.stock <= LOW_STOCK_THRESHOLD
            item['size_name'] = variant.size.name
            item['color_name'] = variant.color_name
            item['stock_status'] = _get_stock_status(variant.stock)
                
        except ProductVariant.DoesNotExist:
            item['stock_available'] = 0
            item['max_quantity'] = 0
            item['is_low_stock'] = False
            item['stock_status'] = STOCK_STATUS_UNAVAILABLE

    return JsonResponse(summary)


@require_GET
def cart_detail(request):
    """
    HU-022: Consultar carrito (vista HTML)
    """
    # HU-022 | ESCENARIO 1 | H | Carrito con productos (renderiza template)
    # HU-022 | ESCENARIO 2 | A | Carrito vacío (template muestra mensaje)
    cart = Cart(request)
    summary = cart.get_summary()

    for item in summary['items']:
        item['total'] = item['price'] * item['quantity']
        
        try:
            variant = ProductVariant.objects.select_related(
                'product', 'product_color__color', 'size'
            ).get(id=item['variant_id'])
            
            item['stock_available'] = variant.stock
            item['is_low_stock'] = 0 < variant.stock <= LOW_STOCK_THRESHOLD
            item['stock_status'] = _get_stock_status(variant.stock)
            
        except ProductVariant.DoesNotExist:
            item['stock_available'] = 0
            item['is_low_stock'] = False
            item['stock_status'] = STOCK_STATUS_UNAVAILABLE

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
# CHECKOUT & PAYMENT FLOW (HU-023, HU-024, HU-025, HU-026)
# =============================================================================

@require_http_methods(['GET', 'POST'])
def checkout(request):
    """
    HU-023: Completar formulario de envío
    HU-024: Confirmar pedido (parte inicial)
    """
    cart = Cart(request)
    
    # HU-024 | ESCENARIO 3 | E | Carrito vacío al confirmar (redirige al catálogo)
    if not _validate_cart_not_empty(request, cart):
        return redirect(PRODUCTS_CATALOG)
    
    # Validación de stock antes de mostrar checkout
    if not _validate_cart_stock(request, cart):
        return redirect(ORDERS_CART_DETAIL)
    
    if request.method == 'POST':
        return _process_checkout_form(request, cart)
    
    return _render_checkout_form(request, cart)


def _validate_cart_not_empty(request, cart):
    """Valida que el carrito no esté vacío. Retorna False si está vacío."""
    if cart.is_empty():
        messages.warning(request, MESSAGE_CART_EMPTY)
        return False
    return True


def _validate_cart_stock(request, cart):
    """Valida el stock del carrito. Retorna False si hay errores."""
    stock_errors = cart.validate_stock()
    if stock_errors:
        for error in stock_errors:
            messages.error(
                request,
                f'"{error["name"]}" ({error["size"]}, {error["color"]}): '
                f'solicitado {error["requested"]}, disponible {error["available"]}'
            )
        return False
    return True


def _process_checkout_form(request, cart):
    """Procesa el formulario de checkout enviado por POST."""
    form = CheckoutOrderForm(request.POST)
    
    if form.is_valid():
        # HU-023 | ESCENARIO 1 | H | Formulario completado exitosamente
        _save_checkout_data_to_session(request, form.cleaned_data)
        return redirect(ORDERS_CREATE_STRIPE_SESSION)
    
    # HU-023 | ESCENARIO 2,3,4 | A/E | Errores en el formulario
    _add_form_errors_to_messages(request, form)
    return _render_checkout_form(request, cart, form=form)


def _save_checkout_data_to_session(request, cleaned_data):
    """Guarda los datos del checkout en la sesión."""
    request.session['checkout_data'] = {
        'customer_name': cleaned_data['customer_name'],
        'customer_phone': cleaned_data['customer_phone'],
        'customer_email': cleaned_data['customer_email'],
        'shipping_address': cleaned_data['shipping_address'],
        'delivery_notes': cleaned_data['delivery_notes'],
    }


def _add_form_errors_to_messages(request, form):
    """Añade los errores del formulario a los mensajes de Django."""
    for field, errors in form.errors.items():
        for error in errors:
            field_label = form.fields[field].label if field in form.fields else field
            messages.error(request, f'{field_label}: {error}')


def _get_cart_summary_context(cart):
    """Obtiene el resumen del carrito para el contexto."""
    summary = cart.get_summary()
    return {
        'items': summary['items'],
        'subtotal': float(summary['subtotal']),
        'shipping_cost': float(summary['shipping_cost']),
        'total': float(summary['total']),
    }


def _render_checkout_form(request, cart, form=None):
    """Renderiza el formulario de checkout."""
    if form is None:
        form = CheckoutOrderForm()
    
    context = {
        'form': form,
        'cart_summary': _get_cart_summary_context(cart),
    }
    return render(request, TEMPLATE_CHECKOUT, context)


@require_http_methods(['GET', 'POST'])
def create_stripe_checkout_session(request):
    """
    HU-024: Confirmar pedido (creación de pedido y redirección a Stripe)
    HU-025: Recibir confirmación de pedido (después del pago)
    """
    stripe = get_stripe()
    cart = Cart(request)

    if cart.is_empty():
        messages.error(request, MESSAGE_CART_EMPTY)
        return redirect(PRODUCTS_CATALOG)

    stock_errors = cart.validate_stock()
    if stock_errors:
        for error in stock_errors:
            messages.error(
                request,
                f'"{error["name"]}" ({error["size"]}, {error["color"]}): {MESSAGE_STOCK_INSUFFICIENT}'
            )
        return redirect(ORDERS_CART_DETAIL)

    checkout_data = request.session.get('checkout_data')
    if not checkout_data:
        messages.error(request, MESSAGE_NO_SHIPPING_DATA)
        return redirect(ORDERS_CHECKOUT)

    customer_name = checkout_data.get('customer_name')
    customer_phone = checkout_data.get('customer_phone')
    customer_email = checkout_data.get('customer_email')
    shipping_address = checkout_data.get('shipping_address')
    delivery_notes = checkout_data.get('delivery_notes', '')

    # HU-024 | ESCENARIO 1 | H | Creación del pedido en estado pendiente
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

    # Crear items del pedido (snapshots)
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
            ORDERS_CONFIRMATION,
            kwargs={'order_number': order.order_number}
        )
        cancel_url = settings.SITE_URL + reverse(ORDERS_CART_DETAIL)

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'cop',
                    'unit_amount': int(cart.get_total() * 100),
                    'product_data': {
                        'name': STRIPE_PRODUCT_NAME_TEMPLATE.format(customer_name=customer_name),
                        'description': STRIPE_PRODUCT_DESCRIPTION_TEMPLATE.format(total_items=cart.get_total_items()),
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
        # HU-024 | ESCENARIO 2 | E | Stock insuficiente al confirmar (error en Stripe o validación)
        order.status = STATUS_CANCELLED
        order.cancelled_reason = f'Error al crear sesión de pago: {str(e)}'
        order.save()
        messages.error(request, f'Error al procesar el pago: {str(e)}')
        return redirect(ORDERS_CHECKOUT)


@require_GET
def order_confirmation(request, order_number):
    """
    HU-025: Recibir confirmación de pedido (pantalla y envío de correo/WhatsApp)
    """
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        messages.error(request, MESSAGE_ORDER_NOT_FOUND)
        return redirect(PRODUCTS_CATALOG)

    # Esperar a que Stripe webhook marque como pagado
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
        # HU-025 | ESCENARIO 1 | H | Confirmación en pantalla con número de pedido
        # HU-025 | ESCENARIO 2 | H | Envío de enlace por WhatsApp (se hace en el webhook? No está aquí, se usa email)
        # HU-025 | ESCENARIO 3 | H | Envío de correo opcional (se hace en webhook con send_order_confirmation_email)
    else:
        messages.warning(request, MESSAGE_PAYMENT_PROCESSING)

    context = {
        CONTEXT_ORDER: order,
        CONTEXT_ITEMS: order.items.all(),
    }
    return render(request, TEMPLATE_ORDER_CONFIRMATION, context)


@require_GET
def order_tracking(request, tracking_token):
    """
    HU-026: Consultar estado del pedido (vía token)
    """
    # HU-026 | ESCENARIO 2 | H | Consulta por enlace (token)
    order = get_object_or_404(Order, tracking_token=tracking_token)
    # HU-026 | ESCENARIO 1 | H | Consulta por número de pedido (no hay vista pública con número, solo token)
    # HU-026 | ESCENARIO 3 | E | Pedido no encontrado → 404
    # HU-026 | ESCENARIO 4 | E | Enlace expirado (no implementado, los tokens no expiran)

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
# STRIPE WEBHOOK (HU-024, HU-025)
# =============================================================================

@require_POST
@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events."""
    import stripe

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
            # HU-024 | ESCENARIO 1 | H | Confirmar pedido y reducir stock
            if order.status == STATUS_PENDING:
                order.confirm(user=None)

            order.is_paid = True
            order.save(update_fields=['is_paid'])
            logger.info(f"Pedido {order.order_number} marcado como pagado")

            # HU-025 | ESCENARIO 3 | H | Envío de correo de confirmación
            if order.customer_email:
                send_order_confirmation_email(order)
                logger.info(f"Correo de confirmación enviado a {order.customer_email}")
            else:
                logger.warning(f"Pedido {order.order_number} no tiene email asociado")

        except Exception as e:
            logger.exception(f"Error al procesar pedido {order.order_number}: {e}")
            return HttpResponse(status=500)

    return HttpResponse(status=200)


# =============================================================================
# BACKOFFICE ORDER VIEWS (HU-027, HU-028, HU-029, HU-030, HU-031, HU-032, HU-034)
# =============================================================================

class OrderListView(PermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    """
    HU-027: Listar pedidos (admin)
    """
    model = Order
    template_name = TEMPLATE_ORDER_LIST
    context_object_name = 'orders'
    permission_required = PERM_ORDER_VIEW  # HU-027 | ESCENARIO 6 | E | Sin permisos
    paginate_by = PAGINATE_BY_DEFAULT

    filters = [
        ('status', 'status', 'exact'),
        ('customer_name', 'customer_name', 'icontains'),
        ('customer_phone', 'customer_phone', 'icontains'),
        ('order_number', 'order_number', 'icontains'),
    ]

    def get_queryset(self):
        qs = super().get_queryset().select_related('assigned_delivery_user')
        search = self.request.GET.get(QUERY_PARAM_SEARCH, '')
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
        # HU-027 | ESCENARIO 1 | H | Lista de pedidos cargada
        # HU-027 | ESCENARIO 2 | H | Filtro por estado
        # HU-027 | ESCENARIO 3 | H | Filtro por fecha (no implementado en este filtro, pero se puede añadir)
        # HU-027 | ESCENARIO 4 | H | Búsqueda por número o cliente
        # HU-027 | ESCENARIO 5 | A | Sin pedidos → template muestra mensaje
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
    """
    HU-031: Crear pedido manual (admin)
    """
    model = Order
    form_class = OrderCreateForm
    template_name = TEMPLATE_ORDER_FORM
    permission_required = PERM_ORDER_ADD  # HU-031 | ESCENARIO 4 | E | Sin permisos
    success_url = reverse_lazy(ORDERS_LIST)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = ORDERS_LIST
        context[CONTEXT_TITLE] = 'Crear pedido manual'
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        # HU-031 | ESCENARIO 1 | H | Pedido manual creado exitosamente
        messages.success(self.request, f'Pedido {form.instance.order_number} creado exitosamente.')
        # HU-031 | ESCENARIO 3 | E | Stock insuficiente (validado en el modelo o en confirmación posterior)
        return response
    # HU-031 | ESCENARIO 2 | H | Buscar productos para agregar (se hace mediante OrderItemCreateView)


class OrderUpdateView(PermissionRequiredMixin, UpdateView):
    """
    HU-031 (parte): Editar pedido manual (admin)
    """
    model = Order
    form_class = OrderUpdateForm
    template_name = TEMPLATE_ORDER_FORM
    permission_required = PERM_ORDER_CHANGE  # HU-031 | ESCENARIO 4 | E | Sin permisos
    success_url = reverse_lazy(ORDERS_LIST)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = ORDERS_LIST
        context[CONTEXT_TITLE] = f'Editar pedido {self.object.order_number}'
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Pedido {form.instance.order_number} actualizado exitosamente.')
        return response


class OrderDetailView(PermissionRequiredMixin, DetailView):
    """
    HU-028: Ver detalle de pedido (admin)
    """
    model = Order
    template_name = TEMPLATE_ORDER_DETAIL
    context_object_name = CONTEXT_ORDER
    permission_required = PERM_ORDER_VIEW  # HU-028 | ESCENARIO 3 | E | Sin permisos

    def get_context_data(self, **kwargs):
        # HU-028 | ESCENARIO 1 | H | Detalle cargado exitosamente
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
        # HU-028 | ESCENARIO 2 | E | Pedido no existe → 404 (manejado por DetailView)
        return context


class BaseOrderActionView(PermissionRequiredMixin, FormView):
    """Clase base para vistas de acción sobre pedidos (confirmar, cancelar, asignar, entregar)."""
    
    permission_required = PERM_ORDER_CHANGE  # E | Sin permisos para todas
    
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
        context[CONTEXT_CANCEL_URL] = ORDERS_DETAIL
        context[CONTEXT_CANCEL_ARGS] = [self.order.pk]
        return context
    
    def get_success_message(self):
        raise NotImplementedError
    
    def perform_action(self, form):
        raise NotImplementedError
    
    def form_valid(self, form):
        self.perform_action(form)
        messages.success(self.request, self.get_success_message())
        return redirect(ORDERS_DETAIL, pk=self.order.pk)


class OrderConfirmView(BaseOrderActionView):
    """
    HU-029 (parte): Confirmar pedido (cambiar estado de pendiente a confirmado)
    """
    form_class = OrderConfirmForm
    template_name = TEMPLATE_ORDER_CONFIRM
    
    def get_success_message(self):
        return f'Pedido {self.order.order_number} confirmado exitosamente.'
    
    def perform_action(self, form):
        # HU-029 | ESCENARIO 1 | H | Cambio de estado exitoso (pendiente → confirmado)
        self.order.confirm(user=self.request.user)
    # HU-029 | ESCENARIO 3 | E | Transición inválida (validado en modelo)


class OrderCancelView(BaseOrderActionView):
    """
    HU-030: Cancelar pedido (admin)
    HU-035: Registrar incidencia (el motivo de cancelación actúa como incidencia)
    """
    form_class = OrderCancelForm
    template_name = TEMPLATE_ORDER_CANCEL
    
    def get_success_message(self):
        return f'Pedido {self.order.order_number} cancelado exitosamente.'
    
    def perform_action(self, form):
        reason = form.cleaned_data['reason']
        # HU-030 | ESCENARIO 1 | H | Cancelación exitosa (libera stock)
        # HU-030 | ESCENARIO 3 | H | Cancelación con motivo (incidencia)
        # HU-035 | ESCENARIO 1 | H | Registrar incidencia (motivo guardado en cancelled_reason)
        # HU-035 | ESCENARIO 2 | H | Tipos de incidencia disponibles (campo libre, pero se puede estandarizar)
        self.order.cancel(reason=reason, user=self.request.user)
        # HU-035 | ESCENARIO 3 | H | Notificación al administrador (no implementada explícitamente, pero el admin ve el motivo en el pedido)
    # HU-030 | ESCENARIO 2 | E | Pedido ya entregado (validado en formulario)
    # HU-035 | ESCENARIO 3 | E | Notificación al administrador (PENDIENTE - se podría enviar email)


class OrderAssignDeliveryView(BaseOrderActionView):
    """
    HU-032: Asignar repartidor
    """
    form_class = OrderAssignDeliveryForm
    template_name = TEMPLATE_ORDER_ASSIGN_DELIVERY
    
    def get_success_message(self):
        return f'Repartidor asignado al pedido {self.order.order_number}.'
    
    def perform_action(self, form):
        delivery_user = form.cleaned_data['delivery_user']
        # HU-032 | ESCENARIO 1 | H | Asignación exitosa (cambia estado a en_camino)
        self.order.assign_delivery(delivery_user, user=self.request.user)
    # HU-032 | ESCENARIO 2 | A | Sin entregadores disponibles (el formulario muestra queryset vacío)
    # HU-032 | ESCENARIO 3 | H | Reasignar entregador (se puede cambiar)


class OrderMarkAsDeliveredView(BaseOrderActionView):
    """
    HU-034: Marcar pedido como pagado/entregado (desde admin)
    """
    form_class = OrderMarkAsDeliveredForm
    template_name = TEMPLATE_ORDER_MARK_DELIVERED
    
    def get_success_message(self):
        return f'Pedido {self.order.order_number} marcado como entregado.'
    
    def perform_action(self, form):
        # HU-034 | ESCENARIO 1 | H | Marcar como pagado (admin)
        self.order.mark_as_delivered(user=self.request.user)
    # HU-034 | ESCENARIO 2 | H | Confirmación requerida (formulario)
    # HU-034 | ESCENARIO 3 | E | Pedido ya pagado (validado en modelo)


class OrderItemCreateView(PermissionRequiredMixin, CreateView):
    """
    HU-031 (parte): Agregar producto a pedido manual (admin)
    """
    model = OrderItem
    form_class = OrderItemCreateForm
    template_name = TEMPLATE_ORDER_ITEM_FORM
    permission_required = PERM_ORDER_CHANGE

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
        context[CONTEXT_CANCEL_URL] = ORDERS_DETAIL
        context[CONTEXT_CANCEL_ARGS] = [self.order.pk] if self.order and self.order.pk else []
        return context

    def form_valid(self, form):
        form.instance.order = self.order
        self.order.save()
        # HU-031 | ESCENARIO 2 | H | Buscar productos para agregar (formulario con variantes)
        messages.success(self.request, f'Producto agregado al pedido {self.order.order_number}.')
        return redirect(ORDERS_DETAIL, pk=self.order.pk)
    # HU-031 | ESCENARIO 3 | E | Stock insuficiente (validado en form)


class OrderItemUpdateView(PermissionRequiredMixin, UpdateView):
    """
    HU-031 (parte): Modificar cantidad de producto en pedido manual
    """
    model = OrderItem
    form_class = OrderItemUpdateForm
    template_name = TEMPLATE_ORDER_ITEM_FORM
    permission_required = PERM_ORDER_CHANGE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_ORDER] = self.object.order
        context[CONTEXT_CANCEL_URL] = ORDERS_DETAIL
        context[CONTEXT_CANCEL_ARGS] = [self.object.order.pk] if self.object.order and self.object.order.pk else []
        context[CONTEXT_TITLE] = 'Editar cantidad'
        return context

    def get_success_url(self):
        return reverse_lazy(ORDERS_DETAIL, kwargs={'pk': self.object.order.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.order.save()
        messages.success(self.request, f'Cantidad actualizada en pedido {self.object.order.order_number}.')
        return response


class OrderItemDeleteView(PermissionRequiredMixin, FormView):
    """
    HU-031 (parte): Eliminar producto de pedido manual
    """
    form_class = OrderItemDeleteForm
    template_name = TEMPLATE_ORDER_ITEM_CONFIRM_DELETE
    permission_required = PERM_ORDER_CHANGE

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
        context[CONTEXT_CANCEL_URL] = ORDERS_DETAIL
        context[CONTEXT_CANCEL_ARGS] = [self.order_item.order.pk] if self.order_item.order and self.order_item.order.pk else []
        return context

    def form_valid(self, form):
        order_pk = self.order_item.order.pk
        self.order_item.delete()
        order = Order.objects.get(pk=order_pk)
        order.save()
        messages.success(self.request, f'Producto eliminado del pedido {order.order_number}.')
        return redirect(ORDERS_DETAIL, pk=order_pk)


# =============================================================================
# HU-037: Exportar pedidos (NO IMPLEMENTADO)
# =============================================================================
# PENDIENTE: HU-037 - Exportar pedidos a Excel/PDF
# Motivo: Funcionalidad no implementada porque el cliente no la ha solicitado explícitamente.
# Decisión: Se marca como pendiente para futuras versiones.