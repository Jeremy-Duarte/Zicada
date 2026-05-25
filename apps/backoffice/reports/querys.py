from datetime import date, timedelta
from typing import List, Tuple, Dict, Any
from django.db.models import Sum, Q
from django.utils import timezone
from apps.orders.models import Order, OrderItem
from apps.products.models import ProductVariant, Product
from apps.users.models import User


# =============================================================================
# CONSTANTES (copiadas localmente para evitar dependencias circulares)
# =============================================================================

PAID_STATUSES = ['confirmado', 'preparando', 'listo', 'en_camino', 'entregado']
STATUS_READY = 'listo'
STATUS_ON_THE_WAY = 'en_camino'
STATUS_DELIVERED = 'entregado'


# =============================================================================
# Financial Queries (parametrizadas por rango de fechas)
# =============================================================================

def sum_order_amount_in_range(
    date_start: date, date_end: date, statuses: List[str] = None
) -> float:
    """Sum of total_amount for orders in date range."""
    qs = Order.objects.filter(status__in=statuses or PAID_STATUSES)
    
    if date_start and date_end:
        qs = qs.filter(created_at__date__gte=date_start, created_at__date__lte=date_end)
    
    total = qs.aggregate(total=Sum('total_amount'))['total'] or 0
    return float(total)


def get_daily_data_in_range(
    date_start: date, date_end: date, statuses: List[str] = None
) -> Tuple[List[str], List[float]]:
    """Daily revenue for each day in the range."""
    categories = []
    data = []
    current = date_start
    while current <= date_end:
        categories.append(current.strftime('%d/%m'))
        daily_total = sum_order_amount_in_range(current, current, statuses)
        data.append(daily_total)
        current += timedelta(days=1)
    return categories, data


def get_daily_order_counts_in_range(
    date_start: date, date_end: date
) -> Tuple[List[str], List[int]]:
    """Daily order counts (all orders) for each day in the range."""
    categories = []
    counts = []
    current = date_start
    while current <= date_end:
        categories.append(current.strftime('%d/%m'))
        count = Order.objects.filter(created_at__date=current).count()
        counts.append(count)
        current += timedelta(days=1)
    return categories, counts


def get_status_chart_data_in_range(
    date_start: date, date_end: date
) -> Dict[str, Any]:
    """Order status distribution within date range."""
    status_labels = {
        'pendiente': 'Pendientes',
        'confirmado': 'Confirmados',
        'preparando': 'Preparando',
        'listo': 'Listos',
        'en_camino': 'En camino',
        'entregado': 'Entregados',
        'cancelado': 'Cancelados',
    }
    counts = []
    names = []
    for code, label in status_labels.items():
        cnt = Order.objects.filter(
            status=code,
            created_at__date__gte=date_start,
            created_at__date__lte=date_end
        ).count()
        if cnt:
            counts.append(cnt)
            names.append(label)
    return {'series': counts, 'labels': names}


def get_recent_orders_in_range(
    date_start: date, date_end: date, limit: int = 5
) -> List[Dict[str, Any]]:
    """Most recent orders within date range."""
    orders = Order.objects.filter(
        created_at__date__gte=date_start,
        created_at__date__lte=date_end
    ).select_related('assigned_delivery_user').order_by('-created_at')[:limit]
    result = []
    for order in orders:
        result.append({
            'title': f"Pedido {order.order_number}",
            'subtitle': order.customer_name,
            'value': f"${order.total_amount:,.0f}",
            'date': order.created_at.strftime('%d/%m %H:%M'),
            'status': order.status,
            'status_display': dict(Order.STATUS_CHOICES).get(order.status, order.status),
        })
    return result


# =============================================================================
# Product Queries (parametrizadas por rango de fechas)
# =============================================================================

def get_top_products_in_range(
    date_start: date, date_end: date, limit: int = 10
) -> List[Dict[str, Any]]:
    """Best selling products (by quantity) in date range."""
    top = OrderItem.objects.filter(
        order__created_at__date__gte=date_start,
        order__created_at__date__lte=date_end,
        order__status__in=PAID_STATUSES
    ).values('product_name_snapshot').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_quantity')[:limit]
    
    result = []
    for item in top:
        name = item['product_name_snapshot']
        result.append({
            'name': name,
            'total_quantity': item['total_quantity'],
            'total_revenue': item['total_revenue'],
        })
    return result


# =============================================================================
# Delivery Queries (parametrizadas por rango de fechas)
# =============================================================================

def get_delivery_order_stats_in_range(
    date_start: date, date_end: date
) -> Dict[str, int]:
    """Delivery‑related stats within date range."""
    return {
        'listos_para_entregar': Order.objects.filter(
            status=STATUS_READY,
            assigned_delivery_user__isnull=True,
            created_at__date__gte=date_start,
            created_at__date__lte=date_end
        ).count(),
        'en_camino': Order.objects.filter(
            status=STATUS_ON_THE_WAY,
            created_at__date__gte=date_start,
            created_at__date__lte=date_end
        ).count(),
        'entregados_hoy': Order.objects.filter(
            status=STATUS_DELIVERED,
            updated_at__date=timezone.now().date()
        ).count(),
        'pendientes_asignacion': Order.objects.filter(
            status=STATUS_READY,
            assigned_delivery_user__isnull=True,
            created_at__date__gte=date_start,
            created_at__date__lte=date_end
        ).count(),
    }