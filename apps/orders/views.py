from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .cart import Cart
from .models import Order
from decimal import Decimal
import json

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