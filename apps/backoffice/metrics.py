from datetime import timedelta
from typing import Any, Dict, List, Tuple
from django.db.models import Q, Sum, Count, Min, Max
from django.shortcuts import reverse
from django.utils import timezone
from apps.orders.models import Order, OrderItem
from apps.products.models import Product, ProductVariant, Size, Category, Color, ProductImage
from apps.users.models import User
from .constants import (
    PAID_ORDER_STATUSES, ORDER_STATUS_LABELS, DEFAULT_LIMIT, MAX_LOW_STOCK,
    DAYS_FOR_TREND, DATE_FORMAT_DAY_MONTH, DATE_FORMAT_DAY_MONTH_HOUR,
    DATE_FORMAT_DAY_MONTH_YEAR, CURRENCY_PREFIX, STRING_UNITS, STRING_UNITS_SOLD,
    STRING_TOTAL_COLLECTED, STRING_NO_CATEGORY, STRING_DELIVERED_BY,
    STRING_ON_THE_WAY, STRING_DELIVERED, STRING_NO_EMAIL, STRING_NO_PHONE,
    ORDER_STATUS_READY, ORDER_STATUS_ON_THE_WAY, ORDER_STATUS_DELIVERED,
    ICON_BOX, ICON_BG_GRAY, ICON_COLOR_ACCENT, ICON_EXCLAMATION_TRIANGLE,
    ICON_BG_YELLOW, ICON_COLOR_YELLOW, ICON_CHART_LINE, ICON_BG_GREEN,
    ICON_COLOR_GREEN, ICON_TSHIRT, ICON_BG_BLUE, ICON_COLOR_BLUE,
    ICON_CHECK_CIRCLE, ICON_BG_PURPLE, ICON_COLOR_PURPLE, ICON_USER,
    QUERY_NAME, QUERY_USERNAME, QUERY_IS_ACTIVE, QUERY_STOCK,
    QUERY_VALUE_ACTIVE, QUERY_VALUE_INACTIVE, QUERY_VALUE_LOW_STOCK,
    QUERY_VALUE_OUT_OF_STOCK, QUERY_VALUE_ALL, QUERY_STATUS,
)

from apps.core.url_names import(
    ORDERS_DETAIL, PRODUCTS_EDIT, PRODUCTS_LIST, USERS_LIST,
)

# =============================================================================
# ORDER METRICS
# =============================================================================

def sum_order_amount(
    *,
    date_start=None,
    date_end=None,
    year=None,
    month=None,
    statuses: List[str] = None
) -> float:
    """Calculate total order amount for given filters."""
    qs = Order.objects.filter(status__in=statuses or PAID_ORDER_STATUSES)
    if date_start and date_end:
        qs = qs.filter(created_at__date__gte=date_start, created_at__date__lte=date_end)
    if year and month:
        qs = qs.filter(created_at__year=year, created_at__month=month)
    elif year:
        qs = qs.filter(created_at__year=year)
    total = qs.aggregate(total=Sum('total_amount'))['total'] or 0
    return float(total)

def get_daily_data(days: int = DAYS_FOR_TREND, statuses: List[str] = None) -> Tuple[List[str], List[float]]:
    today = timezone.now().date()
    categories, data = [], []
    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        categories.append(date.strftime(DATE_FORMAT_DAY_MONTH))
        total = sum_order_amount(date_start=date, date_end=date, statuses=statuses)
        data.append(total)
    return categories, data

def get_status_chart_data() -> Dict[str, Any]:
    counts, names = [], []
    for code, label in ORDER_STATUS_LABELS.items():
        cnt = Order.objects.filter(status=code).count()
        if cnt:
            counts.append(cnt)
            names.append(label)
    return {'series': counts, 'labels': names}

def get_recent_orders(limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
    orders = Order.objects.select_related('assigned_delivery_user').order_by('-created_at')[:limit]
    result = []
    for order in orders:
        status_display = dict(Order.STATUS_CHOICES).get(order.status, order.status)
        result.append({
            'title': f"Pedido {order.order_number}",
            'subtitle': order.customer_name,
            'value': f"{CURRENCY_PREFIX}{order.total_amount:,.0f}",
            'date': order.created_at.strftime(DATE_FORMAT_DAY_MONTH_HOUR),
            'icon': ICON_BOX,
            'icon_bg': ICON_BG_GRAY,
            'icon_color': ICON_COLOR_ACCENT,
            'url': reverse(ORDERS_DETAIL, args=[order.pk]),
            'status': order.status,
            'status_display': status_display,
        })
    return result

def get_order_status_counts() -> Dict[str, int]:
    status_counts = {}
    for status_code, _ in Order.STATUS_CHOICES:
        status_counts[status_code] = Order.objects.filter(status=status_code).count()
    return status_counts

def get_daily_order_counts(days: int = DAYS_FOR_TREND) -> Tuple[List[str], List[int]]:
    today = timezone.now().date()
    categories, data = [], []
    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        categories.append(date.strftime(DATE_FORMAT_DAY_MONTH))
        data.append(Order.objects.filter(created_at__date=date).count())
    return categories, data

# =============================================================================
# PRODUCT METRICS
# =============================================================================

def get_low_stock_products(limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
    variants = ProductVariant.objects.filter(
        is_active=True, stock__gt=0, stock__lte=MAX_LOW_STOCK
    ).select_related('product', 'size', 'product_color__color')[:limit]
    result = []
    for v in variants:
        result.append({
            'title': v.product.name,
            'subtitle': f"{v.size.name} - {v.color_name}",
            'value': f"{v.stock} {STRING_UNITS}",
            'icon': ICON_EXCLAMATION_TRIANGLE,
            'icon_bg': ICON_BG_YELLOW,
            'icon_color': ICON_COLOR_YELLOW,
            'url': reverse(PRODUCTS_EDIT, args=[v.product.pk]),
            'extra_info': f"SKU: {v.sku}",
        })
    return result

def get_top_products(limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
    top = OrderItem.objects.filter(
        order__status__in=PAID_ORDER_STATUSES
    ).values('product_name_snapshot').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_quantity')[:limit]
    result = []
    for item in top:
        name = item['product_name_snapshot']
        try:
            product = Product.objects.get(name=name, is_active=True)
            url = reverse(PRODUCTS_EDIT, args=[product.pk])
        except Product.DoesNotExist:
            url = reverse(PRODUCTS_LIST) + QUERY_NAME.format(name)
        result.append({
            'title': name,
            'subtitle': f"{item['total_quantity']} {STRING_UNITS_SOLD}",
            'value': f"{CURRENCY_PREFIX}{item['total_revenue']:,.0f}",
            'icon': ICON_CHART_LINE,
            'icon_bg': ICON_BG_GREEN,
            'icon_color': ICON_COLOR_GREEN,
            'url': url,
            'extra_info': STRING_TOTAL_COLLECTED,
        })
    return result

def get_product_stats() -> Dict[str, int]:
    total_variants = ProductVariant.objects.filter(is_active=True).count()
    variants_with_stock = ProductVariant.objects.filter(is_active=True, stock__gt=0).count()
    variants_low_stock = ProductVariant.objects.filter(
        is_active=True, stock__gt=0, stock__lte=MAX_LOW_STOCK
    ).count()
    variants_out_stock = ProductVariant.objects.filter(is_active=True, stock=0).count()
    return {
        'total': Product.objects.filter(is_active=True).count(),
        'total_variants': total_variants,
        'in_stock': variants_with_stock,
        'low_stock': variants_low_stock,
        'out_of_stock': variants_out_stock,
    }

def get_recent_products(limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
    products = Product.objects.filter(is_active=True).order_by('-created_at')[:limit]
    result = []
    for product in products:
        category_name = product.category.name if product.category else STRING_NO_CATEGORY
        result.append({
            'title': product.name,
            'subtitle': f"{CURRENCY_PREFIX}{product.price:,.0f} - {category_name}",
            'value': f"{product.total_stock()} {STRING_UNITS}",
            'date': product.created_at.strftime(DATE_FORMAT_DAY_MONTH_YEAR),
            'icon': ICON_TSHIRT,
            'icon_bg': ICON_BG_BLUE,
            'icon_color': ICON_COLOR_BLUE,
            'url': reverse(PRODUCTS_EDIT, args=[product.pk]),
        })
    return result

# =============================================================================
# DELIVERY METRICS
# =============================================================================

def get_delivery_stats() -> Dict[str, int]:
    return {
        'total': User.objects.filter(is_delivery=True, is_active=True).count(),
        'active': User.objects.filter(is_delivery=True, is_active=True).count(),
        'inactive': User.objects.filter(is_delivery=True, is_active=False).count(),
    }

def get_delivery_order_stats() -> Dict[str, int]:
    return {
        'ready_for_delivery': Order.objects.filter(
            status=ORDER_STATUS_READY, assigned_delivery_user__isnull=True
        ).count(),
        'on_the_way': Order.objects.filter(status=ORDER_STATUS_ON_THE_WAY).count(),
        'delivered_today': Order.objects.filter(
            status=ORDER_STATUS_DELIVERED, updated_at__date=timezone.now().date()
        ).count(),
        'pending_assignment': Order.objects.filter(
            status=ORDER_STATUS_READY, assigned_delivery_user__isnull=True
        ).count(),
    }

def get_recent_deliveries(limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
    deliveries = Order.objects.filter(
        status=ORDER_STATUS_DELIVERED, assigned_delivery_user__isnull=False
    ).select_related('assigned_delivery_user').order_by('-updated_at')[:limit]
    result = []
    for order in deliveries:
        driver = order.assigned_delivery_user
        driver_name = driver.get_full_name() or driver.username
        result.append({
            'title': f"Pedido {order.order_number}",
            'subtitle': f"{STRING_DELIVERED_BY} {driver_name}",
            'value': f"{CURRENCY_PREFIX}{order.total_amount:,.0f}",
            'date': order.updated_at.strftime(DATE_FORMAT_DAY_MONTH_HOUR),
            'icon': ICON_CHECK_CIRCLE,
            'icon_bg': ICON_BG_GREEN,
            'icon_color': ICON_COLOR_GREEN,
            'url': reverse(ORDERS_DETAIL, args=[order.pk]),
        })
    return result

def get_active_deliveries_list(limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
    deliveries = User.objects.filter(is_delivery=True, is_active=True).order_by('-date_joined')[:limit]
    result = []
    for delivery in deliveries:
        assigned_count = Order.objects.filter(
            assigned_delivery_user=delivery, status=ORDER_STATUS_ON_THE_WAY
        ).count()
        delivered_count = Order.objects.filter(
            assigned_delivery_user=delivery, status=ORDER_STATUS_DELIVERED
        ).count()
        result.append({
            'title': delivery.get_full_name() or delivery.username,
            'subtitle': delivery.email or STRING_NO_EMAIL,
            'value': f"{assigned_count} {STRING_ON_THE_WAY}",
            'date': f"{delivered_count} {STRING_DELIVERED}",
            'icon': ICON_USER,
            'icon_bg': ICON_BG_PURPLE,
            'icon_color': ICON_COLOR_PURPLE,
            'url': reverse(USERS_LIST) + QUERY_USERNAME.format(delivery.username),
            'extra_info': delivery.phone or STRING_NO_PHONE,
        })
    return result

def get_delivery_stats_for_user(user: User) -> Dict[str, Any]:
    if not getattr(user, 'is_delivery', False):
        return {}
    assigned_orders = Order.objects.filter(assigned_delivery_user=user)
    return {
        'assigned_count': assigned_orders.exclude(status=ORDER_STATUS_DELIVERED).count(),
        'delivered_today': assigned_orders.filter(
            status=ORDER_STATUS_DELIVERED, updated_at__date=timezone.now().date()
        ).count(),
        'pending_assignments': Order.objects.filter(
            status=ORDER_STATUS_READY, assigned_delivery_user__isnull=True
        ).count() if user.is_staff else 0,
        'my_orders': assigned_orders.order_by('-created_at')[:10],
    }