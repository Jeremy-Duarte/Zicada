from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from django.db.models import Max, Min, Sum, Count, Q, F, Avg
from django.utils import timezone
from apps.orders.models import Order, OrderItem
from apps.products.models import Product, ProductVariant, Category, Color, Size
from apps.users.models import User
from django.contrib.auth import get_user_model
from apps.backoffice.constants import (
    PAID_ORDER_STATUSES as PAID_STATUSES,
    ORDER_STATUS_READY as STATUS_READY,
    ORDER_STATUS_ON_THE_WAY as STATUS_ON_THE_WAY,
    ORDER_STATUS_DELIVERED as STATUS_DELIVERED,
    DATE_FORMAT_DAY_MONTH,
    DATE_FORMAT_DAY_MONTH_HOUR,
    DATE_FORMAT_DAY_MONTH_YEAR,
    DATE_FORMAT_DAY_MONTH_YEAR_HOUR_MINUTES,
)


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
        categories.append(current.strftime(DATE_FORMAT_DAY_MONTH))
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
        categories.append(current.strftime(DATE_FORMAT_DAY_MONTH))
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
            'date': order.created_at.strftime(DATE_FORMAT_DAY_MONTH_HOUR),
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


ALL_STATUSES = ['pendiente', 'confirmado', 'preparando', 'listo', 'en_camino', 'entregado', 'cancelado']

def get_daily_revenue_in_range(
    date_start: date, date_end: date
) -> Tuple[List[str], List[float]]:
    """Daily revenue for each day in the range (solo pedidos pagados)."""
    categories = []
    revenues = []
    current = date_start
    while current <= date_end:
        categories.append(current.strftime(DATE_FORMAT_DAY_MONTH))
        daily_total = Order.objects.filter(
            status__in=PAID_STATUSES,
            created_at__date=current
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        revenues.append(float(daily_total))
        current += timedelta(days=1)
    return categories, revenues


def get_top_customers_in_range(
    date_start: date, date_end: date, limit: int = 10
) -> List[Dict[str, Any]]:
    """Top customers by total spent and order count."""
    customers = Order.objects.filter(
        created_at__date__gte=date_start,
        created_at__date__lte=date_end,
        status__in=PAID_STATUSES  # Solo pedidos pagados
    ).values('customer_name', 'customer_phone', 'customer_email').annotate(
        total_spent=Sum('total_amount'),
        order_count=Count('id')
    ).order_by('-total_spent')[:limit]
    
    result = []
    for c in customers:
        result.append({
            'name': c['customer_name'] or 'Cliente anónimo',
            'phone': c['customer_phone'] or '—',
            'email': c['customer_email'] or '—',
            'total_spent': float(c['total_spent']),
            'order_count': c['order_count'],
        })
    return result


def get_order_status_distribution_in_range(
    date_start: date, date_end: date
) -> Dict[str, Any]:
    """Order counts by status within date range."""
    status_labels = {
        'pendiente': 'Pendientes',
        'confirmado': 'Confirmados',
        'preparando': 'Preparando',
        'listo': 'Listos',
        'en_camino': 'En camino',
        'entregado': 'Entregados',
        'cancelado': 'Cancelados',
    }
    
    # Obtener conteo por estado de una sola consulta
    status_counts = Order.objects.filter(
        created_at__date__gte=date_start,
        created_at__date__lte=date_end
    ).values('status').annotate(count=Count('id'))
    
    # Crear diccionario con todos los estados
    count_dict = {item['status']: item['count'] for item in status_counts}
    
    total = sum(count_dict.values())
    
    result = []
    for code, label in status_labels.items():
        cnt = count_dict.get(code, 0)
        result.append({
            'label': label,
            'code': code,
            'count': cnt,
            'percentage': round(cnt / total * 100, 1) if total > 0 else 0,
        })
    
    return {
        'items': result,
        'total': total,
    }


def get_avg_items_per_order_in_range(
    date_start: date, date_end: date
) -> float:
    """Average number of items per order within date range."""
    total_items = OrderItem.objects.filter(
        order__created_at__date__gte=date_start,
        order__created_at__date__lte=date_end,
        order__status__in=PAID_STATUSES
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    total_orders = Order.objects.filter(
        created_at__date__gte=date_start,
        created_at__date__lte=date_end,
        status__in=PAID_STATUSES
    ).count()
    
    return total_items / total_orders if total_orders > 0 else 0


def get_order_stats_summary(
    date_start: date, date_end: date
) -> Dict[str, Any]:
    """Resumen estadístico de pedidos."""
    orders = Order.objects.filter(
        created_at__date__gte=date_start,
        created_at__date__lte=date_end
    )
    
    total_orders = orders.count()
    paid_orders = orders.filter(status__in=PAID_STATUSES).count()
    cancelled_orders = orders.filter(status='cancelado').count()
    
    revenue = orders.filter(status__in=PAID_STATUSES).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    return {
        'total_orders': total_orders,
        'paid_orders': paid_orders,
        'cancelled_orders': cancelled_orders,
        'revenue': float(revenue),
        'avg_order_value': float(revenue / paid_orders) if paid_orders > 0 else 0,
    }

# =============================================================================
# PRODUCT METRICS (parametrizadas por rango de fechas)
# =============================================================================

def get_product_stats_in_range(date_start: date, date_end: date) -> Dict[str, Any]:
    """Get product statistics within date range."""
    # Productos activos
    total_products = Product.objects.filter(is_active=True).count()
    
    # Variantes
    total_variants = ProductVariant.objects.filter(is_active=True).count()
    variants_with_stock = ProductVariant.objects.filter(is_active=True, stock__gt=0).count()
    variants_low_stock = ProductVariant.objects.filter(
        is_active=True, stock__gt=0, stock__lte=10
    ).count()
    variants_out_stock = ProductVariant.objects.filter(is_active=True, stock=0).count()
    
    # Productos que vendieron en el período
    products_with_sales = OrderItem.objects.filter(
        order__created_at__date__gte=date_start,
        order__created_at__date__lte=date_end,
        order__status__in=['confirmado', 'preparando', 'listo', 'en_camino', 'entregado']
    ).values('product_name_snapshot').distinct().count()
    
    return {
        'total_products': total_products,
        'total_variants': total_variants,
        'variants_with_stock': variants_with_stock,
        'variants_low_stock': variants_low_stock,
        'variants_out_stock': variants_out_stock,
        'products_with_sales': products_with_sales,
        'products_without_sales': total_products - products_with_sales,
    }


def get_category_stats_in_range(date_start: date, date_end: date) -> List[Dict[str, Any]]:
    """Get sales by category within date range """

    categories_data = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).values('id', 'name', 'product_count')
    
    sales_data = OrderItem.objects.filter(
        order__created_at__date__gte=date_start,
        order__created_at__date__lte=date_end,
        order__status__in=PAID_STATUSES,
        variant__product__is_active=True,
        variant__product__category__isnull=False
    ).values('variant__product__category__id', 'variant__product__category__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal')
    )
    
    sales_dict = {
        sale['variant__product__category__id']: {
            'total_quantity': sale['total_quantity'] or 0,
            'total_revenue': float(sale['total_revenue'] or 0),
        }
        for sale in sales_data
    }
    
    result = []
    for cat in categories_data:
        cat_id = cat['id']
        sales = sales_dict.get(cat_id, {'total_quantity': 0, 'total_revenue': 0.0})
        
        # Solo incluir si tiene productos activos o ventas
        if cat['product_count'] > 0 or sales['total_quantity'] > 0:
            result.append({
                'name': cat['name'],
                'product_count': cat['product_count'],
                'total_quantity': sales['total_quantity'],
                'total_revenue': sales['total_revenue'],
            })
    
    return sorted(result, key=lambda x: x['total_revenue'], reverse=True)


def get_top_selling_products_in_range(
    date_start: date, date_end: date, limit: int = 10
) -> List[Dict[str, Any]]:
    """Best selling products by quantity and revenue."""
    top = OrderItem.objects.filter(
        order__created_at__date__gte=date_start,
        order__created_at__date__lte=date_end,
        order__status__in=['confirmado', 'preparando', 'listo', 'en_camino', 'entregado']
    ).values('product_name_snapshot').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_revenue')[:limit]
    
    result = []
    for item in top:
        result.append({
            'name': item['product_name_snapshot'],
            'total_quantity': item['total_quantity'],
            'total_revenue': float(item['total_revenue']),
        })
    return result


def get_low_stock_variants_in_range(limit: int = 20) -> List[Dict[str, Any]]:
    """Get variants with low stock (independiente del rango de fechas)."""
    variants = ProductVariant.objects.filter(
        is_active=True,
        stock__gt=0,
        stock__lte=10
    ).select_related('product', 'size', 'product_color__color').order_by('stock')[:limit]
    
    result = []
    for v in variants:
        result.append({
            'product_name': v.product.name,
            'color': v.color_name,
            'size': v.size.name,
            'stock': v.stock,
            'sku': v.sku,
            'price': float(v.product.price),
        })
    return result


def get_out_of_stock_variants_in_range(limit: int = 20) -> List[Dict[str, Any]]:
    """Get variants out of stock (independiente del rango de fechas)."""
    variants = ProductVariant.objects.filter(
        is_active=True,
        stock=0
    ).select_related('product', 'size', 'product_color__color').order_by('product__name')[:limit]
    
    result = []
    for v in variants:
        result.append({
            'product_name': v.product.name,
            'color': v.color_name,
            'size': v.size.name,
            'sku': v.sku,
            'price': float(v.product.price),
        })
    return result


def get_products_without_sales_in_range(
    date_start: date, date_end: date, limit: int = 20
) -> List[Dict[str, Any]]:
    """Get products that haven't sold in the period."""
    # Obtener nombres de productos que sí vendieron
    sold_products = set(OrderItem.objects.filter(
        order__created_at__date__gte=date_start,
        order__created_at__date__lte=date_end,
        order__status__in=['confirmado', 'preparando', 'listo', 'en_camino', 'entregado']
    ).values_list('product_name_snapshot', flat=True).distinct())
    
    # Productos activos que no vendieron
    products = Product.objects.filter(
        is_active=True
    ).exclude(name__in=sold_products).select_related('category')[:limit]
    
    result = []
    for p in products:
        result.append({
            'name': p.name,
            'category': p.category.name if p.category else 'Sin categoría',
            'price': float(p.price),
            'total_stock': p.total_stock(),
        })
    return result


def get_stock_movement_summary(date_start: date, date_end: date) -> Dict[str, Any]:
    """Summary of stock movement (approximated by sales)."""
    # Unidades vendidas en el período
    units_sold = OrderItem.objects.filter(
        order__created_at__date__gte=date_start,
        order__created_at__date__lte=date_end,
        order__status__in=['confirmado', 'preparando', 'listo', 'en_camino', 'entregado']
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    # Valor de ventas
    revenue = OrderItem.objects.filter(
        order__created_at__date__gte=date_start,
        order__created_at__date__lte=date_end,
        order__status__in=['confirmado', 'preparando', 'listo', 'en_camino', 'entregado']
    ).aggregate(total=Sum('subtotal'))['total'] or 0
    
    return {
        'units_sold': units_sold,
        'revenue': float(revenue),
        'avg_price_per_unit': float(revenue / units_sold) if units_sold > 0 else 0,
    }

# =============================================================================
# DELIVERY METRICS (parametrizadas por rango de fechas)
# =============================================================================

def get_delivery_stats_in_range(date_start: date, date_end: date) -> Dict[str, Any]:
    """Get delivery user statistics within date range."""
    total_deliveries = User.objects.filter(is_delivery=True).count()
    active_deliveries = User.objects.filter(is_delivery=True, is_active=True).count()
    inactive_deliveries = User.objects.filter(is_delivery=True, is_active=False).count()
    
    # Entregadores que hicieron entregas en el período
    deliveries_with_activity = Order.objects.filter(
        status='entregado',
        assigned_delivery_user__isnull=False,
        updated_at__date__gte=date_start,
        updated_at__date__lte=date_end
    ).values('assigned_delivery_user').distinct().count()
    
    return {
        'total_deliveries': total_deliveries,
        'active_deliveries': active_deliveries,
        'inactive_deliveries': inactive_deliveries,
        'deliveries_with_activity': deliveries_with_activity,
        'inactive_deliveries_no_activity': active_deliveries - deliveries_with_activity,
    }


# =============================================================================
# Delivery Performance - Funciones Auxiliares
# =============================================================================

def _fetch_delivery_performance_data(
    date_start: date, date_end: date, limit: int = 10
) -> List[Dict[str, Any]]:
    """Consulta principal: obtiene entregas agregadas por entregador."""
    return list(Order.objects.filter(
        status='entregado',
        assigned_delivery_user__isnull=False,
        updated_at__date__gte=date_start,
        updated_at__date__lte=date_end
    ).values(
        'assigned_delivery_user__id',
        'assigned_delivery_user__username',
        'assigned_delivery_user__first_name',
        'assigned_delivery_user__last_name',
        'assigned_delivery_user__phone',
        'assigned_delivery_user__email',
    ).annotate(
        total_deliveries=Count('id'),
        total_revenue=Sum('total_amount'),
        avg_order_value=Avg('total_amount'),
        first_delivery=Min('updated_at'),
        last_delivery=Max('updated_at'),
    ).order_by('-total_deliveries')[:limit])


def _calculate_deliveries_per_day(
    first_delivery: Optional[datetime],
    last_delivery: Optional[datetime],
    total_deliveries: int
) -> float:
    """Calcula el promedio de entregas por día."""
    if not first_delivery or not last_delivery:
        return float(total_deliveries)
    
    days_active = (last_delivery.date() - first_delivery.date()).days + 1
    if days_active <= 0:
        return float(total_deliveries)
    
    return total_deliveries / days_active


def _build_delivery_user_name(d: Dict[str, Any]) -> str:
    """Construye el nombre completo del entregador."""
    first_name = d.get('assigned_delivery_user__first_name', '')
    last_name = d.get('assigned_delivery_user__last_name', '')
    username = d.get('assigned_delivery_user__username', '')
    
    full_name = f"{first_name} {last_name}".strip()
    return full_name or username


def _build_delivery_performance_item(d: Dict[str, Any]) -> Dict[str, Any]:
    """Construye el diccionario de resultado para un entregador."""
    total_deliveries = d['total_deliveries']
    total_revenue = float(d['total_revenue'] or 0)
    first_delivery = d.get('first_delivery')
    last_delivery = d.get('last_delivery')
    
    deliveries_per_day = _calculate_deliveries_per_day(
        first_delivery, last_delivery, total_deliveries
    )
    
    return {
        'id': d['assigned_delivery_user__id'],
        'name': _build_delivery_user_name(d),
        'username': d['assigned_delivery_user__username'],
        'phone': d['assigned_delivery_user__phone'] or '—',
        'email': d['assigned_delivery_user__email'] or '—',
        'total_deliveries': total_deliveries,
        'total_revenue': total_revenue,
        'avg_order_value': f"${d['avg_order_value']:,.0f}" if d['avg_order_value'] else "$0",
        'deliveries_per_day': round(deliveries_per_day, 1),
        'first_delivery': first_delivery.strftime(DATE_FORMAT_DAY_MONTH_YEAR) if first_delivery else '—',
        'last_delivery': last_delivery.strftime(DATE_FORMAT_DAY_MONTH_YEAR) if last_delivery else '—',
    }


def get_delivery_performance_in_range(
    date_start: date, date_end: date, limit: int = 10
) -> List[Dict[str, Any]]:
    """Get delivery performance metrics for each delivery user."""
    deliveries_data = _fetch_delivery_performance_data(date_start, date_end, limit)
    return [_build_delivery_performance_item(d) for d in deliveries_data]



def get_daily_deliveries_in_range(
    date_start: date, date_end: date
) -> Tuple[List[str], List[int], List[float]]:
    """Daily deliveries count and revenue within date range."""
    categories = []
    delivery_counts = []
    revenues = []
    current = date_start
    
    while current <= date_end:
        categories.append(current.strftime(DATE_FORMAT_DAY_MONTH))
        
        # Entregas del día
        daily_deliveries = Order.objects.filter(
            status='entregado',
            assigned_delivery_user__isnull=False,
            updated_at__date=current
        )
        delivery_counts.append(daily_deliveries.count())
        
        # Ingreso del día
        daily_revenue = daily_deliveries.aggregate(total=Sum('total_amount'))['total'] or 0
        revenues.append(float(daily_revenue))
        
        current += timedelta(days=1)
    
    return categories, delivery_counts, revenues


def get_delivery_summary_stats(date_start: date, date_end: date) -> Dict[str, Any]:
    """Overall delivery summary within date range."""
    deliveries = Order.objects.filter(
        status='entregado',
        assigned_delivery_user__isnull=False,
        updated_at__date__gte=date_start,
        updated_at__date__lte=date_end
    )
    
    total_deliveries = deliveries.count()
    total_revenue = deliveries.aggregate(total=Sum('total_amount'))['total'] or 0
    unique_deliveries = deliveries.values('assigned_delivery_user').distinct().count()
    
    # Promedio por entregador
    avg_per_delivery = total_revenue / unique_deliveries if unique_deliveries > 0 else 0
    
    # Mejor día de entregas
    best_day = deliveries.values('updated_at__date').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    return {
        'total_deliveries': total_deliveries,
        'total_revenue': float(total_revenue),
        'unique_deliveries': unique_deliveries,
        'avg_revenue_per_delivery': float(avg_per_delivery),
        'avg_deliveries_per_day': round(total_deliveries / ((date_end - date_start).days + 1), 1),
        'best_day': best_day['updated_at__date'].strftime(DATE_FORMAT_DAY_MONTH_YEAR) if best_day else '—',
        'best_day_count': best_day['count'] if best_day else 0,
    }


def get_delivery_details_list(
    date_start: date, date_end: date, limit: int = 20
) -> List[Dict[str, Any]]:
    """Detailed list of deliveries within date range."""
    deliveries = Order.objects.filter(
        status='entregado',
        assigned_delivery_user__isnull=False,
        updated_at__date__gte=date_start,
        updated_at__date__lte=date_end
    ).select_related('assigned_delivery_user').order_by('-updated_at')[:limit]
    
    result = []
    for order in deliveries:
        driver = order.assigned_delivery_user
        result.append({
            'order_number': order.order_number,
            'customer_name': order.customer_name,
            'delivery_date': order.updated_at.strftime(DATE_FORMAT_DAY_MONTH_YEAR_HOUR_MINUTES),
            'delivery_user': driver.get_full_name() or driver.username,
            'total_amount': float(order.total_amount),
        })
    
    return result