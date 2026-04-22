from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Order


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