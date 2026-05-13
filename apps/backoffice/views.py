from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from typing import List, Dict, Tuple, Any
from django.db.models import Q, QuerySet, Sum
from apps.orders.models import Order, OrderItem
from apps.products.models import ProductVariant, Product
from apps.users.models import User

PAID_STATUSES = ['confirmado', 'preparando', 'listo', 'en_camino', 'entregado']

def get_paid_statuses() -> List[str]:
    return PAID_STATUSES

def sum_order_amount(*, date_start=None, date_end=None, year=None, month=None,
                     statuses: List[str] = None) -> float:
    qs = Order.objects.filter(status__in=statuses or get_paid_statuses())
    if date_start and date_end:
        qs = qs.filter(created_at__date__gte=date_start, created_at__date__lte=date_end)
    if year and month:
        qs = qs.filter(created_at__year=year, created_at__month=month)
    elif year:
        qs = qs.filter(created_at__year=year)
    total = qs.aggregate(total=Sum('total_amount'))['total'] or 0
    return float(total)

def get_daily_data(days: int = 7, statuses: List[str] = None) -> Tuple[List[str], List[float]]:
    today = timezone.now().date()
    categories, data = [], []
    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        categories.append(date.strftime('%d/%m'))
        total = sum_order_amount(date_start=date, date_end=date, statuses=statuses)
        data.append(total)
    return categories, data

def get_status_chart_data() -> Dict[str, Any]:
    labels = {
        'pendiente': 'Pendientes', 'confirmado': 'Confirmados',
        'preparando': 'Preparando', 'listo': 'Listos',
        'en_camino': 'En camino', 'entregado': 'Entregados',
        'cancelado': 'Cancelados',
    }
    counts, names = [], []
    for code in labels:
        cnt = Order.objects.filter(status=code).count()
        if cnt:
            counts.append(cnt)
            names.append(labels[code])
    return {'series': counts, 'labels': names}

def get_recent_orders(limit: int = 5) -> List[Dict[str, Any]]:
    orders = Order.objects.select_related('assigned_delivery_user').order_by('-created_at')[:limit]
    result = []
    for order in orders:
        status_display = dict(Order.STATUS_CHOICES).get(order.status, order.status)
        result.append({
            'title': f"Pedido {order.order_number}",
            'subtitle': order.customer_name,
            'value': f"${order.total_amount:,.0f}",
            'date': order.created_at.strftime('%d/%m %H:%M'),
            'icon': 'box', 'icon_bg': 'gray-100', 'icon_color': 'zicada-accent',
            'url': f"/backoffice/pedidos/{order.id}/",
            'status': order.status, 'status_display': status_display,
        })
    return result

def get_low_stock_products(limit: int = 5, max_stock: int = 10) -> List[Dict[str, Any]]:
    variants = ProductVariant.objects.filter(
        is_active=True, stock__gt=0, stock__lte=max_stock
    ).select_related('product', 'size', 'product_color__color')[:limit]
    result = []
    for v in variants:
        result.append({
            'title': v.product.name,
            'subtitle': f"{v.size.name} - {v.color_name}",
            'value': f"{v.stock} unidades",
            'icon': 'exclamation-triangle', 'icon_bg': 'yellow-100',
            'icon_color': 'yellow-600',
            'url': f"/backoffice/productos/{v.product.slug}/",
            'extra_info': f"SKU: {v.sku}",
        })
    return result

def get_top_products(limit: int = 5) -> List[Dict[str, Any]]:
    top = OrderItem.objects.filter(
        order__status__in=get_paid_statuses()
    ).values('product_name_snapshot').annotate(
        total_quantity=Sum('quantity'), total_revenue=Sum('subtotal')
    ).order_by('-total_quantity')[:limit]
    result = []
    for item in top:
        name = item['product_name_snapshot']
        try:
            product = Product.objects.get(name=name, is_active=True)
            url = f"/backoffice/productos/{product.slug}/"
        except Product.DoesNotExist:
            url = f"/backoffice/productos/?search={name}"
        result.append({
            'title': name,
            'subtitle': f"{item['total_quantity']} unidades vendidas",
            'value': f"${item['total_revenue']:,.0f}",
            'icon': 'chart-line', 'icon_bg': 'green-100',
            'icon_color': 'green-600', 'url': url,
            'extra_info': "Total recaudado",
        })
    return result

@staff_member_required
def admin_dashboard(request):
    today = timezone.now().date()
    month, year = today.month, today.year
    week_ago = today - timedelta(days=7)
    paid = get_paid_statuses()

    pending_orders = Order.objects.filter(status='pendiente').count()
    today_orders = Order.objects.filter(created_at__date=today).count()
    month_revenue = sum_order_amount(year=year, month=month, statuses=paid)
    active_deliveries = User.objects.filter(is_delivery=True, is_active=True).count()

    today_revenue = sum_order_amount(date_start=today, date_end=today, statuses=paid)
    week_revenue = sum_order_amount(date_start=week_ago, date_end=today, statuses=paid)
    year_revenue = sum_order_amount(year=year, statuses=paid)
    total_paid = Order.objects.filter(status__in=paid).count()
    avg_order = month_revenue / total_paid if total_paid else 0
    total_items = OrderItem.objects.filter(
        order__status__in=paid
    ).aggregate(total=Sum('quantity'))['total'] or 0
    avg_items = total_items / total_paid if total_paid else 0

    categories, sales_data = get_daily_data(days=7, statuses=paid)
    if sum(sales_data) == 0:
        sales_data = [0] * 7
    _, daily_rev_data = get_daily_data(days=7, statuses=paid)

    context = {
        'section': 'dashboard',
        'stats': {
            'pending_orders': pending_orders,
            'today_orders': today_orders,
            'month_revenue': f"${month_revenue:,.0f}",
            'active_deliveries': active_deliveries,
        },
        'financial_stats': {
            'today_revenue': f"${today_revenue:,.0f}",
            'week_revenue': f"${week_revenue:,.0f}",
            'month_revenue': f"${month_revenue:,.0f}",
            'year_revenue': f"${year_revenue:,.0f}",
            'avg_order_value': f"${avg_order:,.0f}",
            'avg_items_per_order': f"{avg_items:.1f}",
        },
        'sales_chart_data': {
            'series': [{'name': 'Ventas (COP)', 'data': sales_data}],
            'categories': categories,
        },
        'daily_revenue_chart_data': {
            'series': [{'name': 'Ingreso diario (COP)', 'data': daily_rev_data}],
            'categories': categories,
        },
        'orders_status_data': get_status_chart_data(),
        'recent_orders': get_recent_orders(),
        'low_stock_products': get_low_stock_products(),
        'top_products': get_top_products(),
    }
    return render(request, 'backoffice/admin_dashboard.html', context)

def get_order_status_counts() -> Dict[str, int]:
    status_counts = {}
    for status_code, status_label in Order.STATUS_CHOICES:
        status_counts[status_code] = Order.objects.filter(status=status_code).count()
    return status_counts

def get_daily_order_counts(days: int = 7) -> Tuple[List[str], List[int]]:
    today = timezone.now().date()
    categories = []
    data = []
    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        categories.append(date.strftime('%d/%m'))
        count = Order.objects.filter(created_at__date=date).count()
        data.append(count)
    return categories, data

def get_orders_by_status_filtered(status: str = None, search: str = None) -> QuerySet:
    qs = Order.objects.select_related('assigned_delivery_user').order_by('-created_at')
    if status and status != 'todos':
        qs = qs.filter(status=status)
    if search:
        qs = qs.filter(
            Q(order_number__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(customer_phone__icontains=search)
        )
    return qs

def get_delivery_stats(user) -> Dict[str, Any]:
    if not getattr(user, 'is_delivery', False):
        return {}
    
    assigned_orders = Order.objects.filter(assigned_delivery_user=user)
    return {
        'assigned_count': assigned_orders.exclude(status='entregado').count(),
        'delivered_today': assigned_orders.filter(
            status='entregado', updated_at__date=timezone.now().date()
        ).count(),
        'pending_assignments': Order.objects.filter(
            status='listo', assigned_delivery_user__isnull=True
        ).count() if user.is_staff else 0,
        'my_orders': assigned_orders.order_by('-created_at')[:10],
    }

@staff_member_required
def admin_orders_dashboard(request):

    stats = get_order_status_counts()
    stats['total'] = sum(stats.values())
    recent_orders = get_recent_orders(limit=5)
    categories, order_counts = get_daily_order_counts(days=7)
    
    orders_index = 'orders:orders_list'
    urls = {
        'total': reverse(orders_index) + '?status=todos',
        'pendiente': reverse(orders_index) + '?status=pendiente',
        'confirmado': reverse(orders_index) + '?status=confirmado',
        'en_camino': reverse(orders_index) + '?status=en_camino',
        'entregado': reverse(orders_index) + '?status=entregado',
        'cancelado': reverse(orders_index) + '?status=cancelado',
        'orders_list': reverse(orders_index),
    }

    action_buttons = [
        {
            'url': reverse(orders_index),
            'icon': 'table-list',
            'title': 'Gestionar Pedidos',
            'description': 'Ver, filtrar y gestionar todos los pedidos',
            'gradient_from': 'zicada-accent',
            'gradient_to': 'zicada-accent/80',
            'badge': f"{stats['total']} activos"
        },
        {
            'url': '#',
            'icon': 'plus-circle',
            'title': 'Crear Pedido',
            'description': 'Agregar un nuevo pedido desde el catálogo',
            'gradient_from': 'green-500',
            'gradient_to': 'green-600',
            'badge': 'Nuevo'
        },
        {
            'url': '#',
            'icon': 'file-export',
            'title': 'Exportar Reportes',
            'description': 'Descargar reportes en Excel o PDF',
            'gradient_from': 'blue-500',
            'gradient_to': 'blue-600',
            'badge': 'Próximamente',
        },
    ]

    context = {
        'section': 'orders',
        'stats': stats,
        'urls': urls,
        'action_buttons': action_buttons,
        'recent_orders': recent_orders,
        'orders_trend_data': {
            'series': [{'name': 'Pedidos', 'data': order_counts}],
            'categories': categories,
        },
        'orders_status_data': get_status_chart_data(),
    }
    return render(request, 'backoffice/admin_orders_dashboard.html', context)

@staff_member_required
def admin_products(request):
    context = {'section': 'products'}
    return render(request, 'backoffice/admin_products.html', context)

@staff_member_required
def admin_users(request):
    context = {'section': 'users'}
    return render(request, 'backoffice/admin_users.html', context)

@staff_member_required
def admin_config(request):
    context = {'section': 'config'}
    return render(request, 'backoffice/admin_config.html', context)