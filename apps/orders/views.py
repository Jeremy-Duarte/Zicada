from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .cart import Cart
from .models import Order
from decimal import Decimal
import json
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from .cart import Cart
from .models import Order
from django.conf import settings
import stripe

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
        return redirect('orders:delivery_dashboard')
    order.assigned_delivery_user = request.user
    order.status = 'en_camino'
    order.save()
    messages.success(request, f'Pedido {order.order_number} asignado correctamente.')
    return redirect('orders:delivery_dashboard')


@staff_member_required
def deliver_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, assigned_delivery_user=request.user)
    order.mark_as_delivered(user=request.user)
    messages.success(request, f'Pedido {order.order_number} entregado y pagado.')
    return redirect('orders:delivery_dashboard')

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
        return JsonResponse({
            'success': True,
            'total_items': cart.get_total_items(),
            'message': 'Producto agregado al carrito'
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
    context = cart.get_summary()
    return render(request, 'orders/cart_detail.html', context)

def checkout(request):
    """Página de checkout - formulario de datos del cliente y resumen del pedido."""
    cart = Cart(request)
    
    if cart.is_empty():
        messages.warning(request, 'Tu carrito está vacío. Agrega productos antes de continuar.')
        return redirect('products:catalog')
    
    stock_errors = cart.validate_stock()
    if stock_errors:
        for error in stock_errors:
            messages.error(
                request, 
                f'"{error["name"]}" ({error["size"]}, {error["color"]}): '
                f'solicitado {error["requested"]}, disponible {error["available"]}'
            )
        return redirect('orders:cart_detail')
    
    if request.method == 'POST':
        # Si es una petición de pago simulada
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return process_payment(request, cart)
        return process_order(request, cart)
    
    summary = cart.get_summary()
    summary['shipping_cost'] = float(summary['shipping_cost'])
    summary['subtotal'] = float(summary['subtotal'])
    summary['total'] = float(summary['total'])
    
    context = {
        'cart_summary': summary,
        'shipping_cost': summary['shipping_cost'],
    }
    return render(request, 'orders/checkout.html', context)


def process_payment(request, cart):
    """Procesa el pago del pedido (simulado o con pasarela real)."""
    import json
    from decimal import Decimal
    
    try:
        data = json.loads(request.body)
        payment_method = data.get('payment_method', 'contraentrega')
        
        # Aquí iría la integración con pasarela de pagos (Wompi, PayU, etc.)
        # Por ahora, simulamos un pago exitoso
        
        # Simular procesamiento
        import time
        time.sleep(1)  # Simular latencia de red
        
        # Crear el pedido después del pago exitoso
        customer_name = data.get('customer_name', '').strip()
        customer_phone = data.get('customer_phone', '').strip()
        customer_email = data.get('customer_email', '').strip() or None
        shipping_address = data.get('shipping_address', '').strip()
        delivery_notes = data.get('delivery_notes', '').strip()
        
        if not customer_name or not customer_phone or not shipping_address:
            return JsonResponse({'success': False, 'error': 'Faltan datos obligatorios'}, status=400)
        
        with transaction.atomic():
            order = Order(
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email,
                shipping_address=shipping_address,
                delivery_notes=delivery_notes or '',
                subtotal=cart.get_subtotal(),
                shipping_cost=cart.get_shipping_cost(),
                total_amount=cart.get_total(),
                status='confirmado',  # El pedido se confirma inmediatamente después del pago
                is_paid=True,  # Se marca como pagado
                created_by=request.user if request.user.is_authenticated else None,
                updated_by=request.user if request.user.is_authenticated else None,
            )
            order.save()
            
            cart.to_order_items(order)
            cart.clear()
            
            return JsonResponse({
                'success': True,
                'order_number': order.order_number,
                'message': 'Pago procesado exitosamente'
            })
            
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'}, status=400)


def order_confirmation(request, order_number):
    """Página de confirmación de pedido (factura/comprobante)."""
    from .models import Order
    
    try:
        order = Order.objects.select_related('created_by').get(order_number=order_number)
    except Order.DoesNotExist:
        messages.error(request, 'Pedido no encontrado.')
        return redirect('products:catalog')
    
    context = {
        'order': order,
        'items': order.items.all(),
    }
    return render(request, 'orders/order_confirmation.html', context)

@csrf_exempt
def stripe_webhook(request):
    print("Webhook recibido!")
    print("Headers:", request.headers)
    print("Body:", request.body.decode('utf-8'))
    return HttpResponse(status=200)

@require_http_methods(['POST'])
def create_stripe_checkout_session(request):
    """
    Crea una sesión de pago en Stripe y redirige al checkout de Stripe.
    Esta vista maneja SOLO la creación de la sesión.
    """
    cart = Cart(request)
    
    if cart.is_empty():
        return JsonResponse({'error': 'Carrito vacío'}, status=400)
    
    stock_errors = cart.validate_stock()
    if stock_errors:
        return JsonResponse({'error': 'Stock insuficiente para algunos productos'}, status=400)
    
    customer_name = request.POST.get('customer_name', '').strip()
    customer_phone = request.POST.get('customer_phone', '').strip()
    customer_email = request.POST.get('customer_email', '').strip()
    shipping_address = request.POST.get('shipping_address', '').strip()
    delivery_notes = request.POST.get('delivery_notes', '').strip()
    
    if not all([customer_name, customer_phone, shipping_address]):
        return JsonResponse({'error': 'Faltan datos obligatorios'}, status=400)
    
    # Guardar datos del cliente en la sesión (para usarlos en el webhook)
    request.session['checkout_data'] = {
        'customer_name': customer_name,
        'customer_phone': customer_phone,
        'customer_email': customer_email,
        'shipping_address': shipping_address,
        'delivery_notes': delivery_notes,
        'cart_summary': cart.get_summary(),
    }
    
    try:
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
            success_url=settings.SITE_URL + f'/orders/confirmacion/{checkout_session.id}/',
            cancel_url=settings.SITE_URL + '/orders/carrito/',
            client_reference_id=request.session.session_key,
            customer_email=customer_email or None,
            metadata={
                'session_key': request.session.session_key,
            }
        )
        
        request.session['stripe_session_id'] = checkout_session.id
        
        return JsonResponse({'redirect_url': checkout_session.url})
        
    except stripe.error.StripeError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error inesperado: {str(e)}'}, status=400)