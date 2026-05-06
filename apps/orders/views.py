from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .cart import Cart
from decimal import Decimal
import json
from decimal import Decimal
from .models import Order, OrderItem
from apps.products.models import ProductVariant
from django.conf import settings
from apps.orders.stripe_client import get_stripe
from .forms import CheckoutOrderForm
from .email import send_order_confirmation_email

DELIVERY_DASHBOARD_ROUTE ='orders:delivery_dashboard'

@staff_member_required
def delivery_dashboard(request):
    pedidos_listos = Order.objects.filter(status='listo')
    pedidos_asignados = Order.objects.filter(
        assigned_delivery_user=request.user,
        status='en_camino'
    )
    
    context = {
        'pedidos_listos': pedidos_listos,
        'pedidos_asignados': pedidos_asignados,
    }
    return render(request, 'orders/delivery_dashboard.html', context)


@staff_member_required
def take_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.status != 'listo':
        messages.error(request, f'El pedido {order.order_number} no está listo para entregar (estado actual: {order.get_status_display()}).')
        return redirect(DELIVERY_DASHBOARD_ROUTE)
    order.assigned_delivery_user = request.user
    order.status = 'en_camino'
    order.save()
    messages.success(request, f'Pedido {order.order_number} asignado correctamente.')
    return redirect(DELIVERY_DASHBOARD_ROUTE)


@staff_member_required
def deliver_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, assigned_delivery_user=request.user)
    order.mark_as_delivered(user=request.user)
    messages.success(request, f'Pedido {order.order_number} entregado y pagado.')
    return redirect(DELIVERY_DASHBOARD_ROUTE)

@require_http_methods(['POST'])
def cart_add(request):
    try:
        data = json.loads(request.body) if request.body else request.POST
        variant_id = data.get('variant_id')
        quantity = int(data.get('quantity', 1))
    except (json.JSONDecodeError, ValueError, TypeError):
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


@require_http_methods(['POST'])
def cart_remove(request):
    try:
        data = json.loads(request.body) if request.body else request.POST
        variant_id = data.get('variant_id')
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    cart = Cart(request)
    cart.remove(variant_id)
    return JsonResponse({
        'success': True,
        'total_items': cart.get_total_items(),
    })

@require_http_methods(['POST'])
def cart_update(request):
    try:
        data = json.loads(request.body) if request.body else request.POST
        variant_id = data.get('variant_id')
        quantity = data.get('quantity')
        
        if isinstance(quantity, str):
            quantity = int(quantity)
        elif isinstance(quantity, int):
            pass
        else:
            return JsonResponse({'error': 'Cantidad inválida'}, status=400)
            
    except (json.JSONDecodeError, ValueError, TypeError) as e:
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

@require_http_methods(['POST'])
def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    return JsonResponse({
        'success': True,
        'total_items': 0,
        'message': 'Carrito vaciado correctamente'
    })

def cart_data(request):
    cart = Cart(request)
    summary = cart.get_summary()
    summary['subtotal'] = float(summary['subtotal'])
    summary['shipping_cost'] = float(summary['shipping_cost'])
    summary['total'] = float(summary['total'])
    for item in summary['items']:
        item['price'] = float(item['price'])
        item['subtotal'] = float(Decimal(item['price']) * item['quantity'])
    return JsonResponse(summary)

def cart_detail(request):
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
    
    return render(request, 'orders/cart_detail.html', context)

def checkout(request):
    cart = Cart(request)
    
    if cart.is_empty():
        messages.warning(request, 'Tu carrito está vacío. Agrega productos antes de continuar.')
        return redirect('products:catalog')
    
    stock_errors = cart.validate_stock()
    if stock_errors:
        for error in stock_errors:
            messages.error(request, f'"{error["name"]}" ({error["size"]}, {error["color"]}): solicitado {error["requested"]}, disponible {error["available"]}')
        return redirect('orders:cart_detail')
    
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
            return redirect('orders:create_stripe_checkout_session')
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
    return render(request, 'orders/checkout.html', context)

@csrf_exempt
def stripe_webhook(request):
    import stripe
    import logging
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
            logger.error(f"❌ Pedido no encontrado para session_id: {session_id}")
            return HttpResponse(status=200)
        
        if order.is_paid:
            logger.info(f"Pedido {order.order_number} ya estaba pagado")
            return HttpResponse(status=200)
        
        try:
            if order.status == 'pendiente':
                order.confirm(user=None)
                logger.info(f"Pedido {order.order_number} confirmado y stock reducido")
            
            order.is_paid = True
            order.save(update_fields=['is_paid'])
            logger.info(f"Pedido {order.order_number} marcado como pagado")

            if order.customer_email:
                send_order_confirmation_email(order)
                logger.info(f"Correo de confirmación enviado a {order.customer_email}")
            else:
                logger.warning(f"Pedido {order.order_number} no tiene email asociado")
            
        except Exception as e:
            logger.error(f"Error al procesar pedido {order.order_number}: {e}")
            return HttpResponse(status=500)
    
    return HttpResponse(status=200)

@require_http_methods(['GET', 'POST'])
def create_stripe_checkout_session(request):
    # Crea una sesión de pago en Stripe y redirige al checkout de Stripe.
    stripe = get_stripe()
    cart = Cart(request)
    
    if cart.is_empty():
        messages.error(request, 'Tu carrito está vacío.')
        return redirect('products:catalog')
    
    stock_errors = cart.validate_stock()
    if stock_errors:
        for error in stock_errors:
            messages.error(request, f'"{error["name"]}" ({error["size"]}, {error["color"]}): stock insuficiente')
        return redirect('orders:cart_detail')
    
    checkout_data = request.session.get('checkout_data')
    if not checkout_data:
        messages.error(request, 'No se encontraron datos de envío. Por favor, vuelve a intentarlo.')
        return redirect('orders:checkout')
    
    customer_name = checkout_data.get('customer_name')
    customer_phone = checkout_data.get('customer_phone')
    customer_email = checkout_data.get('customer_email')
    shipping_address = checkout_data.get('shipping_address')
    delivery_notes = checkout_data.get('delivery_notes', '')
    
    from .models import Order
    
    order = Order(
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email or None,
        shipping_address=shipping_address,
        delivery_notes=delivery_notes,
        subtotal=cart.get_subtotal(),
        shipping_cost=cart.get_shipping_cost(),
        total_amount=cart.get_total(),
        status='pendiente',
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
        from django.urls import reverse
        success_url = settings.SITE_URL + reverse('orders:order_confirmation', kwargs={'order_number': order.order_number})
        cancel_url = settings.SITE_URL + reverse('orders:cart_detail')
        
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
        order.status = 'cancelado'
        order.cancelled_reason = f'Error al crear sesión de pago: {str(e)}'
        order.save()
        messages.error(request, f'Error al procesar el pago: {str(e)}')
        return redirect('orders:checkout')


def order_confirmation(request, order_number):
    """Página de confirmación de pedido después del pago exitoso."""
    
    try:
        # Buscar por order_number en lugar de session_id
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        messages.error(request, 'Pedido no encontrado.')
        return redirect('products:catalog')
    
    # Verificar si el pedido está pagado, si no, esperar un momento
    if not order.is_paid:
        import time
        # Esperar hasta 5 segundos por el webhook
        for _ in range(10):
            if order.is_paid:
                break
            time.sleep(0.5)
            order.refresh_from_db()

        if order.is_paid:
            cart = Cart(request)
            if not cart.is_empty():
                cart.clear()
    
    if not order.is_paid:
        messages.warning(request, 'Tu pago está siendo procesado. Se actualizará automáticamente en breve.')
    
    context = {
        'order': order,
        'items': order.items.all(),
    }
    return render(request, 'orders/order_confirmation.html', context)

def order_tracking(request, tracking_token):
    """Vista pública para seguimiento de pedidos"""
    order = get_object_or_404(Order, tracking_token=tracking_token)
    
    status_order = [
        'pendiente',
        'confirmado', 
        'preparando',
        'listo',
        'en_camino',
        'entregado'
    ]
    
    current_step = status_order.index(order.status) if order.status in status_order else 0
    total_steps = len(status_order) - 1

    context = {
        'order': order,
        'items': order.items.all(),
        'current_step': current_step,
        'total_steps': total_steps,
        'status_percentage': (current_step / total_steps) * 100 if total_steps > 0 else 0,
    }
    return render(request, 'orders/tracking.html', context)