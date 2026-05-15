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

def get_product_stats() -> Dict[str, int]:
    total_variants = ProductVariant.objects.filter(is_active=True).count()
    variants_with_stock = ProductVariant.objects.filter(is_active=True, stock__gt=0).count()
    variants_low_stock = ProductVariant.objects.filter(is_active=True, stock__gt=0, stock__lte=10).count()
    variants_out_stock = ProductVariant.objects.filter(is_active=True, stock=0).count()
    
    return {
        'total': Product.objects.filter(is_active=True).count(),
        'total_variantes': total_variants,
        'con_stock': variants_with_stock,
        'stock_bajo': variants_low_stock,
        'agotado': variants_out_stock,
        'sin_stock': variants_out_stock,
    }

def get_recent_products(limit: int = 5) -> List[Dict[str, Any]]:
    products = Product.objects.filter(is_active=True).order_by('-created_at')[:limit]
    result = []
    for product in products:
        result.append({
            'title': product.name,
            'subtitle': f"${product.price:,.0f} - {product.category.name if product.category else 'Sin categoría'}",
            'value': f"{product.total_stock()} unidades",
            'date': product.created_at.strftime('%d/%m/%Y'),
            'icon': 'tshirt',
            'icon_bg': 'blue-100',
            'icon_color': 'blue-600',
            'url': f"/backoffice/productos/{product.slug}/",
        })
    return result

def get_top_selling_products(limit: int = 5) -> List[Dict[str, Any]]:
    return get_top_products(limit=limit)

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

    financial_items = [
        {
            'label': 'Ticket promedio',
            'value': f"${avg_order:,.0f}",
            'icon': 'receipt',
            'icon_bg': 'zicada-accent/10',
            'icon_color': 'zicada-accent',
            'sub_value': 'por transacción',
        },
        {
            'label': 'Items por pedido',
            'value': f"{avg_items:.1f}",
            'icon': 'box',
            'icon_bg': 'blue-50',
            'icon_color': 'blue-500',
            'sub_value': 'promedio',
        },
        {
            'label': 'Ingreso diario promedio',
            'value': f"${week_revenue:,.0f}",
            'icon': 'chart-line',
            'icon_bg': 'green-50',
            'icon_color': 'green-500',
            'sub_value': 'últimos 7 días',
        },
        {
            'label': 'Total pedidos pagados',
            'value': total_paid,
            'icon': 'shopping-cart',
            'icon_bg': 'purple-50',
            'icon_color': 'purple-500',
            'sub_value': 'pedidos completados',
        },
        {
            'label': 'Ingreso hoy',
            'value': f"${today_revenue:,.0f}",
            'icon': 'sun',
            'icon_bg': 'orange-50',
            'icon_color': 'orange-500',
            'sub_value': 'acumulado',
        },
        {
            'label': 'Ingreso año',
            'value': f"${year_revenue:,.0f}",
            'icon': 'calendar-alt',
            'icon_bg': 'indigo-50',
            'icon_color': 'indigo-500',
            'sub_value': f'{year}',
        },
    ]

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
        'financial_items': financial_items,
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

def get_delivery_stats() -> Dict[str, int]:
    return {
        'total': User.objects.filter(is_delivery=True, is_active=True).count(),
        'activos': User.objects.filter(is_delivery=True, is_active=True).count(),
        'inactivos': User.objects.filter(is_delivery=True, is_active=False).count(),
    }

def get_delivery_order_stats() -> Dict[str, int]:
    return {
        'listos_para_entregar': Order.objects.filter(status='listo', assigned_delivery_user__isnull=True).count(),
        'en_camino': Order.objects.filter(status='en_camino').count(),
        'entregados_hoy': Order.objects.filter(status='entregado', updated_at__date=timezone.now().date()).count(),
        'pendientes_asignacion': Order.objects.filter(status='listo', assigned_delivery_user__isnull=True).count(),
    }

def get_recent_deliveries(limit: int = 5) -> List[Dict[str, Any]]:
    deliveries = Order.objects.filter(
        status='entregado',
        assigned_delivery_user__isnull=False
    ).select_related('assigned_delivery_user').order_by('-updated_at')[:limit]
    
    result = []
    for order in deliveries:
        result.append({
            'title': f"Pedido {order.order_number}",
            'subtitle': f"Entregado por {order.assigned_delivery_user.get_full_name() or order.assigned_delivery_user.username}",
            'value': f"${order.total_amount:,.0f}",
            'date': order.updated_at.strftime('%d/%m %H:%M'),
            'icon': 'check-circle',
            'icon_bg': 'green-100',
            'icon_color': 'green-600',
            'url': f"/backoffice/pedidos/{order.id}/",
        })
    return result

def get_active_deliveries_list(limit: int = 5) -> List[Dict[str, Any]]:
    deliveries = User.objects.filter(is_delivery=True, is_active=True).order_by('-date_joined')[:limit]
    
    result = []
    for delivery in deliveries:
        assigned_count = Order.objects.filter(assigned_delivery_user=delivery, status='en_camino').count()
        delivered_count = Order.objects.filter(assigned_delivery_user=delivery, status='entregado').count()
        
        result.append({
            'title': delivery.get_full_name() or delivery.username,
            'subtitle': delivery.email or 'Sin email',
            'value': f"{assigned_count} en camino",
            'date': f"{delivered_count} entregados",
            'icon': 'user',
            'icon_bg': 'purple-100',
            'icon_color': 'purple-600',
            'url': f"/backoffice/usuarios/{delivery.id}/",
            'extra_info': delivery.phone if delivery.phone else 'Sin teléfono',
        })
    return result
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

    stats = get_product_stats() 
    recent_products = get_recent_products(limit=5)
    low_stock_products = get_low_stock_products(limit=5, max_stock=10)
    top_products = get_top_products(limit=5)
    
    products_index = 'products:products_list'
    urls = {
        'products_list': reverse(products_index),
        'total': reverse(products_index) + '?status=todos',
        'activos': reverse(products_index) + '?status=activos',
        'inactivos': reverse(products_index) + '?status=inactivos',
        'stock_bajo': reverse(products_index) + '?stock=bajo',
        'agotados': reverse(products_index) + '?stock=agotado',
    }
    
    action_buttons = [
        {
            'url': reverse(products_index),
            'icon': 'table-list',
            'title': 'Gestionar Productos',
            'description': 'Ver, filtrar y gestionar todos los productos',
            'gradient_from': 'zicada-accent',
            'gradient_to': 'zicada-accent/80',
            'badge': f"{stats['total']} productos"
        },
        {
            'url': '#',
            'icon': 'plus-circle',
            'title': 'Crear Producto',
            'description': 'Agregar un nuevo producto al catálogo',
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
    
    stock_distribution = {
        'series': [stats['con_stock'], stats['stock_bajo'], stats['agotado']],
        'labels': ['En stock', 'Stock bajo', 'Agotado'],
    }
    
    stock_stats_list = [
        {'label': 'Con stock', 'value': stats['con_stock'], 'color': 'green-500'},
        {'label': 'Stock bajo', 'value': stats['stock_bajo'], 'color': 'yellow-500'},
        {'label': 'Agotados', 'value': stats['agotado'], 'color': 'red-500'},
    ]

    context = {
        'section': 'products',
        'stats': stats,
        'urls': urls,
        'action_buttons': action_buttons,
        'recent_products': recent_products,
        'low_stock_products': low_stock_products,
        'top_products': top_products,
        'stock_distribution': stock_distribution,
        'stock_stats_list': stock_stats_list,
    }
    return render(request, 'backoffice/admin_products_dashboard.html', context)

@staff_member_required
def admin_users(request):
    
    delivery_stats = get_delivery_stats()    
    order_stats = get_delivery_order_stats()    
    recent_deliveries = get_recent_deliveries(limit=5)
    active_deliveries = get_active_deliveries_list(limit=5)
    
    users_index = 'users:users_list'
    urls = {
        'users_list': reverse(users_index),
        'total': reverse(users_index) + '?status=todos',
        'activos': reverse(users_index) + '?status=activos',
        'inactivos': reverse(users_index) + '?status=inactivos',
        'pedidos_listos': reverse('orders:orders_list') + '?status=listo',
        'pedidos_camino': reverse('orders:orders_list') + '?status=en_camino',
    }
    
    action_buttons = [
        {
            'url': reverse(users_index),
            'icon': 'users',
            'title': 'Gestionar Entregadores',
            'description': 'Ver, filtrar y gestionar todos los entregadores',
            'gradient_from': 'zicada-accent',
            'gradient_to': 'zicada-accent/80',
            'badge': f"{delivery_stats['total']} activos"
        },
        {
            'url': '#',
            'icon': 'plus-circle',
            'title': 'Agregar Entregador',
            'description': 'Registrar un nuevo entregador',
            'gradient_from': 'green-500',
            'gradient_to': 'green-600',
            'badge': 'Nuevo'
        },
        {
            'url': '#',
            'icon': 'file-export',
            'title': 'Exportar Reportes',
            'description': 'Descargar reportes de entregas',
            'gradient_from': 'blue-500',
            'gradient_to': 'blue-600',
            'badge': 'Próximamente',
        },
    ]
    
    delivery_stats_list = [
        {'label': 'Activos', 'value': delivery_stats['activos'], 'color': 'green-500'},
        {'label': 'Inactivos', 'value': delivery_stats['inactivos'], 'color': 'gray-400'},
    ]
    
    categories, order_counts = get_daily_order_counts(days=7)
    
    context = {
        'section': 'users',
        'stats': {
            'total_entregadores': delivery_stats['total'],
            'pedidos_por_entregar': order_stats['listos_para_entregar'],
            'pedidos_en_camino': order_stats['en_camino'],
            'entregados_hoy': order_stats['entregados_hoy'],
        },
        'urls': urls,
        'action_buttons': action_buttons,
        'recent_deliveries': recent_deliveries,
        'active_deliveries': active_deliveries,
        'delivery_stats': delivery_stats,
        'delivery_stats_list': delivery_stats_list,
        'pedidos_por_entregar': order_stats['listos_para_entregar'],
        'pedidos_en_camino': order_stats['en_camino'],
        'orders_trend_data': {
            'series': [{'name': 'Pedidos', 'data': order_counts}],
            'categories': categories,
        },
        'orders_status_data': get_status_chart_data(),
    }
    return render(request, 'backoffice/admin_users_dashboard.html', context)

@staff_member_required
def admin_config(request):
    context = {'section': 'config'}
    return render(request, 'backoffice/admin_config.html', context)