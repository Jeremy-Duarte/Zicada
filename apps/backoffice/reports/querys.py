from datetime import date, timedelta
from typing import List, Tuple, Dict, Any
from django.db.models import Count, Sum, Q
from django.utils import timezone
from apps.orders.models import Order, OrderItem
from apps.products.models import Product, ProductVariant, Category, Color, Size
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

PAID_STATUSES = ['confirmado', 'preparando', 'listo', 'en_camino', 'entregado']
ALL_STATUSES = ['pendiente', 'confirmado', 'preparando', 'listo', 'en_camino', 'entregado', 'cancelado']

def sum_order_amount_in_range(
    date_start: date, date_end: date, statuses: List[str] = None
) -> float:
    """Sum of total_amount for orders in date range (solo pagados por defecto)."""
    if statuses is None:
        statuses = PAID_STATUSES
    
    total = Order.objects.filter(
        status__in=statuses,
        created_at__date__gte=date_start,
        created_at__date__lte=date_end
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    return float(total)


def get_daily_order_counts_in_range(
    date_start: date, date_end: date
) -> Tuple[List[str], List[int]]:
    """Daily order counts for each day in the range."""
    categories = []
    counts = []
    current = date_start
    while current <= date_end:
        categories.append(current.strftime('%d/%m'))
        count = Order.objects.filter(created_at__date=current).count()
        counts.append(count)
        current += timedelta(days=1)
    return categories, counts


def get_daily_revenue_in_range(
    date_start: date, date_end: date
) -> Tuple[List[str], List[float]]:
    """Daily revenue for each day in the range (solo pedidos pagados)."""
    categories = []
    revenues = []
    current = date_start
    while current <= date_end:
        categories.append(current.strftime('%d/%m'))
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
    """Get sales by category within date range."""
    categories = Category.objects.all()
    result = []
    
    for category in categories:
        # Productos de esta categoría
        products = category.products.filter(is_active=True)
        product_count = products.count()
        
        # Ventas de productos de esta categoría
        sales = OrderItem.objects.filter(
            order__created_at__date__gte=date_start,
            order__created_at__date__lte=date_end,
            order__status__in=['confirmado', 'preparando', 'listo', 'en_camino', 'entregado'],
            variant__product__category=category
        ).aggregate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('subtotal')
        )
        
        if product_count > 0 or (sales['total_quantity'] or 0) > 0:
            result.append({
                'name': category.name,
                'product_count': product_count,
                'total_quantity': sales['total_quantity'] or 0,
                'total_revenue': float(sales['total_revenue'] or 0),
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