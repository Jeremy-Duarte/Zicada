from datetime import timedelta
from typing import Any, Dict, List, Tuple

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, QuerySet, Sum
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from apps.orders.models import Order, OrderItem
from apps.products.models import Product, ProductVariant, Size, Category, Color, ProductImage
from apps.users.models import User, Group

from .reports.report_forms import ReportForm
from .reports.financial import FinancialReport
from .reports.orders import OrdersReport
from .reports.products import ProductsReport
from .reports.delivery import DeliveryReport

# =============================================================================
# CONSTANTS
# =============================================================================

# Order Statuses
STATUS_PENDING = 'pendiente'
STATUS_CONFIRMED = 'confirmado'
STATUS_PREPARING = 'preparando'
STATUS_READY = 'listo'
STATUS_ON_THE_WAY = 'en_camino'
STATUS_DELIVERED = 'entregado'
STATUS_CANCELLED = 'cancelado'

PAID_STATUSES = [
    STATUS_CONFIRMED,
    STATUS_PREPARING,
    STATUS_READY,
    STATUS_ON_THE_WAY,
    STATUS_DELIVERED
]

STATUS_LABELS = {
    STATUS_PENDING: 'Pendientes',
    STATUS_CONFIRMED: 'Confirmados',
    STATUS_PREPARING: 'Preparando',
    STATUS_READY: 'Listos',
    STATUS_ON_THE_WAY: 'En camino',
    STATUS_DELIVERED: 'Entregados',
    STATUS_CANCELLED: 'Cancelados',
}

# Route Names
ROUTE_ORDER_DETAIL = 'orders:order_detail'
ROUTE_ORDER_LIST = 'orders:order_list'
ROUTE_ORDER_CREATE = 'orders:order_create'
ROUTE_PRODUCT_LIST = 'products:product_list'
ROUTE_PRODUCT_EDIT = 'products:product_edit'
ROUTE_PRODUCT_CREATE = 'products:product_create'
ROUTE_USER_LIST = 'users:user_list'
ROUTE_USER_CREATE = 'users:user_create'
DASHBOARD_IMPORT_ROUTE = 'backoffice:importers_dashboard'

# URL Query Parameters
QUERY_STATUS = '?status={}'
QUERY_NAME = '?name={}'
QUERY_IS_ACTIVE = '?is_active={}'
QUERY_IS_DELIVERY = '?is_delivery={}'
QUERY_STOCK = '?stock={}'
QUERY_USERNAME = '?username={}'

# Template Paths
TEMPLATE_ADMIN_DASHBOARD = 'backoffice/admin_dashboard.html'
TEMPLATE_ADMIN_ORDERS_DASHBOARD = 'backoffice/admin_orders_dashboard.html'
TEMPLATE_ADMIN_PRODUCTS_DASHBOARD = 'backoffice/admin_products_dashboard.html'
TEMPLATE_ADMIN_USERS_DASHBOARD = 'backoffice/admin_users_dashboard.html'
TEMPLATE_ADMIN_CONFIG = 'backoffice/admin_config.html'

# Chart and Display Labels
CHART_SERIES_NAME_SALES = 'Ventas (COP)'
CHART_SERIES_NAME_REVENUE = 'Ingreso diario (COP)'
CHART_SERIES_NAME_ORDERS = 'Pedidos'

# Icon Names
ICON_BOX = 'box'
ICON_CHART_LINE = 'chart-line'
ICON_USER = 'user'
ICON_CHECK_CIRCLE = 'check-circle'
ICON_EXCLAMATION_TRIANGLE = 'exclamation-triangle'
ICON_TSHIRT = 'tshirt'

# Icon Background Colors
ICON_BG_GRAY = 'gray-100'
ICON_BG_YELLOW = 'yellow-100'
ICON_BG_GREEN = 'green-100'
ICON_BG_BLUE = 'blue-100'
ICON_BG_PURPLE = 'purple-100'

# Icon Colors
ICON_COLOR_ACCENT = 'zicada-accent'
ICON_COLOR_YELLOW = 'yellow-600'
ICON_COLOR_GREEN = 'green-600'
ICON_COLOR_BLUE = 'blue-600'
ICON_COLOR_PURPLE = 'purple-600'

# Badge Labels
BADGE_NEW = 'Nuevo'
BADGE_COMING_SOON = 'Próximamente'
LABEL_EXPORT_REPORTS = 'Exportar Reportes'

# Button Titles
BTN_TITLE_MANAGE_ORDERS = 'Gestionar Pedidos'
BTN_TITLE_CREATE_ORDER = 'Crear Pedido'
BTN_TITLE_MANAGE_PRODUCTS = 'Gestionar Productos'
BTN_TITLE_CREATE_PRODUCT = 'Crear Producto'
BTN_TITLE_MANAGE_DELIVERIES = 'Gestionar Entregadores'
BTN_TITLE_ADD_DELIVERY = 'Agregar Entregador'

# Button Descriptions
BTN_DESC_MANAGE_ORDERS = 'Ver, filtrar y gestionar todos los pedidos'
BTN_DESC_CREATE_ORDER = 'Agregar un nuevo pedido desde el catálogo'
BTN_DESC_MANAGE_PRODUCTS = 'Ver, filtrar y gestionar todos los productos'
BTN_DESC_CREATE_PRODUCT = 'Agregar un nuevo producto al catálogo'
BTN_DESC_MANAGE_DELIVERIES = 'Ver, filtrar y gestionar todos los entregadores'
BTN_DESC_ADD_DELIVERY = 'Registrar un nuevo entregador'
BTN_DESC_EXPORT = 'Descargar reportes en Excel o PDF'
BTN_DESC_EXPORT_DELIVERIES = 'Descargar reportes de entregas'

# Gradient Colors
GRADIENT_ACCENT_FROM = 'zicada-accent'
GRADIENT_ACCENT_TO = 'zicada-accent/80'
GRADIENT_GREEN_FROM = 'green-500'
GRADIENT_GREEN_TO = 'green-600'
GRADIENT_BLUE_FROM = 'blue-500'
GRADIENT_BLUE_TO = 'blue-600'

# Financial Item Labels
FINANCIAL_LABEL_AVG_TICKET = 'Ticket promedio'
FINANCIAL_LABEL_ITEMS_PER_ORDER = 'Items por pedido'
FINANCIAL_LABEL_AVG_DAILY_INCOME = 'Ingreso diario promedio'
FINANCIAL_LABEL_TOTAL_PAID = 'Total pedidos pagados'
FINANCIAL_LABEL_TODAY_INCOME = 'Ingreso hoy'
FINANCIAL_LABEL_YEAR_INCOME = 'Ingreso año'

# Financial Item Sub-values
FINANCIAL_SUB_AVG_TICKET = 'por transacción'
FINANCIAL_SUB_AVG_ITEMS = 'promedio'
FINANCIAL_SUB_AVG_DAILY = 'últimos 7 días'
FINANCIAL_SUB_TOTAL_PAID = 'pedidos completados'
FINANCIAL_SUB_TODAY = 'acumulado'

# Financial Item Icons
FINANCIAL_ICON_RECEIPT = 'receipt'
FINANCIAL_ICON_BOX = 'box'
FINANCIAL_ICON_CHART = 'chart-line'
FINANCIAL_ICON_CART = 'shopping-cart'
FINANCIAL_ICON_SUN = 'sun'
FINANCIAL_ICON_CALENDAR = 'calendar-alt'

# Financial Item Colors
FINANCIAL_COLOR_ACCENT = 'zicada-accent'
FINANCIAL_COLOR_BLUE = 'blue-500'
FINANCIAL_COLOR_GREEN = 'green-500'
FINANCIAL_COLOR_PURPLE = 'purple-500'
FINANCIAL_COLOR_ORANGE = 'orange-500'
FINANCIAL_COLOR_INDIGO = 'indigo-500'

# Stock Distribution Labels
STOCK_LABEL_IN_STOCK = 'En stock'
STOCK_LABEL_LOW_STOCK = 'Stock bajo'
STOCK_LABEL_OUT_OF_STOCK = 'Agotado'
STOCK_COLOR_GREEN = 'green-500'
STOCK_COLOR_YELLOW = 'yellow-500'
STOCK_COLOR_RED = 'red-500'

# Delivery Stats Labels
DELIVERY_LABEL_ACTIVE = 'Activos'
DELIVERY_LABEL_INACTIVE = 'Inactivos'
DELIVERY_COLOR_ACTIVE = 'green-500'
DELIVERY_COLOR_INACTIVE = 'gray-400'

# Section Names
SECTION_DASHBOARD = 'dashboard'
SECTION_ORDERS = 'orders'
SECTION_PRODUCTS = 'products'
SECTION_USERS = 'users'
SECTION_CONFIG = 'config'

# Context Keys
CONTEXT_SECTION = 'section'
CONTEXT_STATS = 'stats'
CONTEXT_URLS = 'urls'
CONTEXT_ACTION_BUTTONS = 'action_buttons'
CONTEXT_RECENT_ORDERS = 'recent_orders'
CONTEXT_RECENT_PRODUCTS = 'recent_products'
CONTEXT_RECENT_DELIVERIES = 'recent_deliveries'
CONTEXT_ACTIVE_DELIVERIES = 'active_deliveries'
CONTEXT_LOW_STOCK_PRODUCTS = 'low_stock_products'
CONTEXT_TOP_PRODUCTS = 'top_products'
CONTEXT_FINANCIAL_STATS = 'financial_stats'
CONTEXT_FINANCIAL_ITEMS = 'financial_items'
CONTEXT_SALES_CHART_DATA = 'sales_chart_data'
CONTEXT_DAILY_REVENUE_CHART_DATA = 'daily_revenue_chart_data'
CONTEXT_ORDERS_STATUS_DATA = 'orders_status_data'
CONTEXT_ORDERS_TREND_DATA = 'orders_trend_data'
CONTEXT_STOCK_DISTRIBUTION = 'stock_distribution'
CONTEXT_STOCK_STATS_LIST = 'stock_stats_list'
CONTEXT_DELIVERY_STATS = 'delivery_stats'
CONTEXT_DELIVERY_STATS_LIST = 'delivery_stats_list'
CONTEXT_PEDIDOS_POR_ENTREGAR = 'pedidos_por_entregar'
CONTEXT_PEDIDOS_EN_CAMINO = 'pedidos_en_camino'

# Numeric Constants
DEFAULT_LIMIT = 5
MAX_LOW_STOCK = 10
DAYS_FOR_TREND = 7

# Date Formats
DATE_FORMAT_DAY_MONTH = '%d/%m'
DATE_FORMAT_DAY_MONTH_YEAR = '%d/%m/%Y'
DATE_FORMAT_DAY_MONTH_HOUR = '%d/%m %H:%M'

# Currency Display
CURRENCY_PREFIX = '$'

# Common Strings
STRING_EMPTY = ''
STRING_SIN_CATEGORIA = 'Sin categoría'
STRING_SIN_EMAIL = 'Sin email'
STRING_SIN_TELEFONO = 'Sin teléfono'
STRING_UNIDADES = 'unidades'
STRING_UNIDADES_VENDIDAS = 'unidades vendidas'
STRING_TOTAL_RECAUDADO = 'Total recaudado'
STRING_ENTREGADO_POR = 'Entregado por'
STRING_EN_CAMINO = 'en camino'
STRING_ENTREGADOS = 'entregados'
STRING_ACTIVOS = 'activos'
STRING_POR_TRANSACCION = 'por transacción'
STRING_PROMEDIO = 'promedio'
STRING_ULTIMOS_7_DIAS = 'últimos 7 días'
STRING_PEDIDOS_COMPLETADOS = 'pedidos completados'
STRING_ACUMULADO = 'acumulado'


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
    qs = Order.objects.filter(status__in=statuses or PAID_STATUSES)

    if date_start and date_end:
        qs = qs.filter(created_at__date__gte=date_start, created_at__date__lte=date_end)
    if year and month:
        qs = qs.filter(created_at__year=year, created_at__month=month)
    elif year:
        qs = qs.filter(created_at__year=year)

    total = qs.aggregate(total=Sum('total_amount'))['total'] or 0
    return float(total)


def get_daily_data(days: int = DAYS_FOR_TREND, statuses: List[str] = None) -> Tuple[List[str], List[float]]:
    """Get daily revenue data for the last N days."""
    today = timezone.now().date()
    categories, data = [], []

    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        categories.append(date.strftime(DATE_FORMAT_DAY_MONTH))
        total = sum_order_amount(date_start=date, date_end=date, statuses=statuses)
        data.append(total)

    return categories, data


def get_status_chart_data() -> Dict[str, Any]:
    """Get order counts by status for chart display."""
    counts, names = [], []

    for code, label in STATUS_LABELS.items():
        cnt = Order.objects.filter(status=code).count()
        if cnt:
            counts.append(cnt)
            names.append(label)

    return {'series': counts, 'labels': names}


def get_recent_orders(limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
    """Get most recent orders with formatted data."""
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
            'url': reverse(ROUTE_ORDER_DETAIL, args=[order.pk]),
            'status': order.status,
            'status_display': status_display,
        })

    return result


def get_order_status_counts() -> Dict[str, int]:
    """Get count of orders per status."""
    status_counts = {}
    for status_code, _ in Order.STATUS_CHOICES:
        status_counts[status_code] = Order.objects.filter(status=status_code).count()
    return status_counts


def get_daily_order_counts(days: int = DAYS_FOR_TREND) -> Tuple[List[str], List[int]]:
    """Get daily order counts for the last N days."""
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
    """Get products with low stock levels."""
    variants = ProductVariant.objects.filter(
        is_active=True, stock__gt=0, stock__lte=MAX_LOW_STOCK
    ).select_related('product', 'size', 'product_color__color')[:limit]

    result = []
    for v in variants:
        result.append({
            'title': v.product.name,
            'subtitle': f"{v.size.name} - {v.color_name}",
            'value': f"{v.stock} {STRING_UNIDADES}",
            'icon': ICON_EXCLAMATION_TRIANGLE,
            'icon_bg': ICON_BG_YELLOW,
            'icon_color': ICON_COLOR_YELLOW,
            'url': reverse(ROUTE_PRODUCT_EDIT, args=[v.product.pk]),
            'extra_info': f"SKU: {v.sku}",
        })

    return result


def get_top_products(limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
    """Get best-selling products."""
    top = OrderItem.objects.filter(
        order__status__in=PAID_STATUSES
    ).values('product_name_snapshot').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_quantity')[:limit]

    result = []
    for item in top:
        name = item['product_name_snapshot']
        try:
            product = Product.objects.get(name=name, is_active=True)
            url = reverse(ROUTE_PRODUCT_EDIT, args=[product.pk])
        except Product.DoesNotExist:
            url = reverse(ROUTE_PRODUCT_LIST) + QUERY_NAME.format(name)

        result.append({
            'title': name,
            'subtitle': f"{item['total_quantity']} {STRING_UNIDADES_VENDIDAS}",
            'value': f"{CURRENCY_PREFIX}{item['total_revenue']:,.0f}",
            'icon': ICON_CHART_LINE,
            'icon_bg': ICON_BG_GREEN,
            'icon_color': ICON_COLOR_GREEN,
            'url': url,
            'extra_info': STRING_TOTAL_RECAUDADO,
        })

    return result


def get_product_stats() -> Dict[str, int]:
    """Get aggregated product statistics."""
    total_variants = ProductVariant.objects.filter(is_active=True).count()
    variants_with_stock = ProductVariant.objects.filter(is_active=True, stock__gt=0).count()
    variants_low_stock = ProductVariant.objects.filter(
        is_active=True, stock__gt=0, stock__lte=MAX_LOW_STOCK
    ).count()
    variants_out_stock = ProductVariant.objects.filter(is_active=True, stock=0).count()

    return {
        'total': Product.objects.filter(is_active=True).count(),
        'total_variantes': total_variants,
        'con_stock': variants_with_stock,
        'stock_bajo': variants_low_stock,
        'agotado': variants_out_stock,
        'sin_stock': variants_out_stock,
    }


def get_recent_products(limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
    """Get most recently added products."""
    products = Product.objects.filter(is_active=True).order_by('-created_at')[:limit]

    result = []
    for product in products:
        category_name = product.category.name if product.category else STRING_SIN_CATEGORIA
        result.append({
            'title': product.name,
            'subtitle': f"{CURRENCY_PREFIX}{product.price:,.0f} - {category_name}",
            'value': f"{product.total_stock()} {STRING_UNIDADES}",
            'date': product.created_at.strftime(DATE_FORMAT_DAY_MONTH_YEAR),
            'icon': ICON_TSHIRT,
            'icon_bg': ICON_BG_BLUE,
            'icon_color': ICON_COLOR_BLUE,
            'url': reverse(ROUTE_PRODUCT_EDIT, args=[product.pk]),
        })

    return result


# =============================================================================
# DELIVERY METRICS
# =============================================================================

def get_delivery_stats() -> Dict[str, int]:
    """Get delivery user statistics."""
    return {
        'total': User.objects.filter(is_delivery=True, is_active=True).count(),
        'activos': User.objects.filter(is_delivery=True, is_active=True).count(),
        'inactivos': User.objects.filter(is_delivery=True, is_active=False).count(),
    }


def get_delivery_order_stats() -> Dict[str, int]:
    """Get delivery-related order statistics."""
    return {
        'listos_para_entregar': Order.objects.filter(
            status=STATUS_READY, assigned_delivery_user__isnull=True
        ).count(),
        'en_camino': Order.objects.filter(status=STATUS_ON_THE_WAY).count(),
        'entregados_hoy': Order.objects.filter(
            status=STATUS_DELIVERED, updated_at__date=timezone.now().date()
        ).count(),
        'pendientes_asignacion': Order.objects.filter(
            status=STATUS_READY, assigned_delivery_user__isnull=True
        ).count(),
    }


def get_recent_deliveries(limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
    """Get most recent completed deliveries."""
    deliveries = Order.objects.filter(
        status=STATUS_DELIVERED, assigned_delivery_user__isnull=False
    ).select_related('assigned_delivery_user').order_by('-updated_at')[:limit]

    result = []
    for order in deliveries:
        driver = order.assigned_delivery_user
        driver_name = driver.get_full_name() or driver.username

        result.append({
            'title': f"Pedido {order.order_number}",
            'subtitle': f"{STRING_ENTREGADO_POR} {driver_name}",
            'value': f"{CURRENCY_PREFIX}{order.total_amount:,.0f}",
            'date': order.updated_at.strftime(DATE_FORMAT_DAY_MONTH_HOUR),
            'icon': ICON_CHECK_CIRCLE,
            'icon_bg': ICON_BG_GREEN,
            'icon_color': ICON_COLOR_GREEN,
            'url': reverse(ROUTE_ORDER_DETAIL, args=[order.pk]),
        })

    return result


def get_active_deliveries_list(limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
    """Get list of active delivery users with their stats."""
    deliveries = User.objects.filter(
        is_delivery=True, is_active=True
    ).order_by('-date_joined')[:limit]

    result = []
    for delivery in deliveries:
        assigned_count = Order.objects.filter(
            assigned_delivery_user=delivery, status=STATUS_ON_THE_WAY
        ).count()
        delivered_count = Order.objects.filter(
            assigned_delivery_user=delivery, status=STATUS_DELIVERED
        ).count()

        result.append({
            'title': delivery.get_full_name() or delivery.username,
            'subtitle': delivery.email or STRING_SIN_EMAIL,
            'value': f"{assigned_count} {STRING_EN_CAMINO}",
            'date': f"{delivered_count} {STRING_ENTREGADOS}",
            'icon': ICON_USER,
            'icon_bg': ICON_BG_PURPLE,
            'icon_color': ICON_COLOR_PURPLE,
            'url': reverse(ROUTE_USER_LIST) + QUERY_USERNAME.format(delivery.username),
            'extra_info': delivery.phone or STRING_SIN_TELEFONO,
        })

    return result


def get_delivery_stats_for_user(user: User) -> Dict[str, Any]:
    """Get delivery statistics for a specific user."""
    if not getattr(user, 'is_delivery', False):
        return {}

    assigned_orders = Order.objects.filter(assigned_delivery_user=user)

    return {
        'assigned_count': assigned_orders.exclude(status=STATUS_DELIVERED).count(),
        'delivered_today': assigned_orders.filter(
            status=STATUS_DELIVERED, updated_at__date=timezone.now().date()
        ).count(),
        'pending_assignments': Order.objects.filter(
            status=STATUS_READY, assigned_delivery_user__isnull=True
        ).count() if user.is_staff else 0,
        'my_orders': assigned_orders.order_by('-created_at')[:10],
    }


# =============================================================================
# VIEWS
# =============================================================================

@staff_member_required
def admin_dashboard(request):
    """Main admin dashboard view."""
    today = timezone.now().date()
    month, year = today.month, today.year
    week_ago = today - timedelta(days=DAYS_FOR_TREND)

    pending_orders = Order.objects.filter(status=STATUS_PENDING).count()
    today_orders = Order.objects.filter(created_at__date=today).count()
    month_revenue = sum_order_amount(year=year, month=month)
    active_deliveries = User.objects.filter(is_delivery=True, is_active=True).count()

    today_revenue = sum_order_amount(date_start=today, date_end=today)
    week_revenue = sum_order_amount(date_start=week_ago, date_end=today)
    year_revenue = sum_order_amount(year=year)

    total_paid = Order.objects.filter(status__in=PAID_STATUSES).count()
    avg_order = month_revenue / total_paid if total_paid else 0

    total_items = OrderItem.objects.filter(
        order__status__in=PAID_STATUSES
    ).aggregate(total=Sum('quantity'))['total'] or 0
    avg_items = total_items / total_paid if total_paid else 0

    categories, sales_data = get_daily_data(days=DAYS_FOR_TREND)
    if sum(sales_data) == 0:
        sales_data = [0] * DAYS_FOR_TREND
    _, daily_rev_data = get_daily_data(days=DAYS_FOR_TREND)

    financial_items = [
        {
            'label': FINANCIAL_LABEL_AVG_TICKET,
            'value': f"{CURRENCY_PREFIX}{avg_order:,.0f}",
            'icon': FINANCIAL_ICON_RECEIPT,
            'icon_bg': f'{ICON_COLOR_ACCENT}/10',
            'icon_color': ICON_COLOR_ACCENT,
            'sub_value': FINANCIAL_SUB_AVG_TICKET,
        },
        {
            'label': FINANCIAL_LABEL_ITEMS_PER_ORDER,
            'value': f"{avg_items:.1f}",
            'icon': FINANCIAL_ICON_BOX,
            'icon_bg': 'blue-50',
            'icon_color': FINANCIAL_COLOR_BLUE,
            'sub_value': FINANCIAL_SUB_AVG_ITEMS,
        },
        {
            'label': FINANCIAL_LABEL_AVG_DAILY_INCOME,
            'value': f"{CURRENCY_PREFIX}{week_revenue:,.0f}",
            'icon': FINANCIAL_ICON_CHART,
            'icon_bg': 'green-50',
            'icon_color': FINANCIAL_COLOR_GREEN,
            'sub_value': FINANCIAL_SUB_AVG_DAILY,
        },
        {
            'label': FINANCIAL_LABEL_TOTAL_PAID,
            'value': total_paid,
            'icon': FINANCIAL_ICON_CART,
            'icon_bg': 'purple-50',
            'icon_color': FINANCIAL_COLOR_PURPLE,
            'sub_value': FINANCIAL_SUB_TOTAL_PAID,
        },
        {
            'label': FINANCIAL_LABEL_TODAY_INCOME,
            'value': f"{CURRENCY_PREFIX}{today_revenue:,.0f}",
            'icon': FINANCIAL_ICON_SUN,
            'icon_bg': 'orange-50',
            'icon_color': FINANCIAL_COLOR_ORANGE,
            'sub_value': FINANCIAL_SUB_TODAY,
        },
        {
            'label': FINANCIAL_LABEL_YEAR_INCOME,
            'value': f"{CURRENCY_PREFIX}{year_revenue:,.0f}",
            'icon': FINANCIAL_ICON_CALENDAR,
            'icon_bg': 'indigo-50',
            'icon_color': FINANCIAL_COLOR_INDIGO,
            'sub_value': str(year),
        },
    ]

    reports_url = reverse('backoffice:report_generator')
    
    action_buttons = [
        {
            'url': reports_url,
            'icon': 'file-export',
            'title': LABEL_EXPORT_REPORTS,
            'description': 'Generar reportes financieros personalizados',
            'gradient_from': GRADIENT_BLUE_FROM,
            'gradient_to': GRADIENT_BLUE_TO,
            'badge': 'Nuevo'
        }
    ]

    context = {
        CONTEXT_SECTION: SECTION_DASHBOARD,
        CONTEXT_STATS: {
            'pending_orders': pending_orders,
            'today_orders': today_orders,
            'month_revenue': f"{CURRENCY_PREFIX}{month_revenue:,.0f}",
            'active_deliveries': active_deliveries,
        },
        CONTEXT_FINANCIAL_STATS: {
            'today_revenue': f"{CURRENCY_PREFIX}{today_revenue:,.0f}",
            'week_revenue': f"{CURRENCY_PREFIX}{week_revenue:,.0f}",
            'month_revenue': f"{CURRENCY_PREFIX}{month_revenue:,.0f}",
            'year_revenue': f"{CURRENCY_PREFIX}{year_revenue:,.0f}",
            'avg_order_value': f"{CURRENCY_PREFIX}{avg_order:,.0f}",
            'avg_items_per_order': f"{avg_items:.1f}",
        },
        CONTEXT_FINANCIAL_ITEMS: financial_items,
        CONTEXT_SALES_CHART_DATA: {
            'series': [{'name': CHART_SERIES_NAME_SALES, 'data': sales_data}],
            'categories': categories,
        },
        CONTEXT_DAILY_REVENUE_CHART_DATA: {
            'series': [{'name': CHART_SERIES_NAME_REVENUE, 'data': daily_rev_data}],
            'categories': categories,
        },
        CONTEXT_ORDERS_STATUS_DATA: get_status_chart_data(),
        CONTEXT_RECENT_ORDERS: get_recent_orders(),
        CONTEXT_LOW_STOCK_PRODUCTS: get_low_stock_products(),
        CONTEXT_TOP_PRODUCTS: get_top_products(),
        CONTEXT_ACTION_BUTTONS: action_buttons,
    }

    return render(request, TEMPLATE_ADMIN_DASHBOARD, context)


@staff_member_required
def admin_orders_dashboard(request):
    """Orders management dashboard view."""
    stats = get_order_status_counts()
    stats['total'] = sum(stats.values())
    recent_orders = get_recent_orders()
    categories, order_counts = get_daily_order_counts()

    orders_url = reverse(ROUTE_ORDER_LIST)
    urls = {
        'total': orders_url,
        STATUS_PENDING: orders_url + QUERY_STATUS.format(STATUS_PENDING),
        STATUS_CONFIRMED: orders_url + QUERY_STATUS.format(STATUS_CONFIRMED),
        STATUS_PREPARING: orders_url + QUERY_STATUS.format(STATUS_PREPARING),
        STATUS_READY: orders_url + QUERY_STATUS.format(STATUS_READY),
        STATUS_ON_THE_WAY: orders_url + QUERY_STATUS.format(STATUS_ON_THE_WAY),
        STATUS_DELIVERED: orders_url + QUERY_STATUS.format(STATUS_DELIVERED),
        STATUS_CANCELLED: orders_url + QUERY_STATUS.format(STATUS_CANCELLED),
        'orders_list': orders_url,
    }

    action_buttons = [
        {
            'url': orders_url,
            'icon': 'table-list',
            'title': BTN_TITLE_MANAGE_ORDERS,
            'description': BTN_DESC_MANAGE_ORDERS,
            'gradient_from': GRADIENT_ACCENT_FROM,
            'gradient_to': GRADIENT_ACCENT_TO,
            'badge': f"{stats['total']} {STRING_ACTIVOS}"
        },
        {
            'url': reverse(ROUTE_ORDER_CREATE),
            'icon': 'plus-circle',
            'title': BTN_TITLE_CREATE_ORDER,
            'description': BTN_DESC_CREATE_ORDER,
            'gradient_from': GRADIENT_GREEN_FROM,
            'gradient_to': GRADIENT_GREEN_TO,
            'badge': BADGE_NEW
        },
        {
            'url': '#',
            'icon': 'file-export',
            'title': LABEL_EXPORT_REPORTS,
            'description': BTN_DESC_EXPORT,
            'gradient_from': GRADIENT_BLUE_FROM,
            'gradient_to': GRADIENT_BLUE_TO,
            'badge': BADGE_COMING_SOON
        },
    ]

    context = {
        CONTEXT_SECTION: SECTION_ORDERS,
        CONTEXT_STATS: stats,
        CONTEXT_URLS: urls,
        CONTEXT_ACTION_BUTTONS: action_buttons,
        CONTEXT_RECENT_ORDERS: recent_orders,
        CONTEXT_ORDERS_TREND_DATA: {
            'series': [{'name': CHART_SERIES_NAME_ORDERS, 'data': order_counts}],
            'categories': categories,
        },
        CONTEXT_ORDERS_STATUS_DATA: get_status_chart_data(),
    }

    return render(request, TEMPLATE_ADMIN_ORDERS_DASHBOARD, context)


@staff_member_required
def admin_products(request):
    """Products management dashboard view."""
    stats = get_product_stats()
    recent_products = get_recent_products()
    low_stock_products = get_low_stock_products()
    top_products = get_top_products()

    products_url = reverse(ROUTE_PRODUCT_LIST)
    urls = {
        'products_list': products_url,
        'total': f"{products_url}?status=todos",
        'activos': products_url + QUERY_IS_ACTIVE.format('true'),
        'inactivos': products_url + QUERY_IS_ACTIVE.format('false'),
        'stock_bajo': products_url + QUERY_STOCK.format('bajo'),
        'agotados': products_url + QUERY_STOCK.format('agotado'),
    }

    action_buttons = [
        {
            'url': products_url,
            'icon': 'table-list',
            'title': BTN_TITLE_MANAGE_PRODUCTS,
            'description': BTN_DESC_MANAGE_PRODUCTS,
            'gradient_from': GRADIENT_ACCENT_FROM,
            'gradient_to': GRADIENT_ACCENT_TO,
            'badge': f"{stats['total']} productos"
        },
        {
            'url': reverse(ROUTE_PRODUCT_CREATE),
            'icon': 'plus-circle',
            'title': BTN_TITLE_CREATE_PRODUCT,
            'description': BTN_DESC_CREATE_PRODUCT,
            'gradient_from': GRADIENT_GREEN_FROM,
            'gradient_to': GRADIENT_GREEN_TO,
            'badge': BADGE_NEW
        },
        {
            'url': reverse(DASHBOARD_IMPORT_ROUTE),
            'icon': 'file-export',
            'title': LABEL_EXPORT_REPORTS,
            'description': BTN_DESC_EXPORT,
            'gradient_from': GRADIENT_BLUE_FROM,
            'gradient_to': GRADIENT_BLUE_TO,
            'badge': BADGE_COMING_SOON
        },
    ]

    quick_access_buttons = [
        {
            'url': reverse('products:size_list'),
            'icon': 'ruler',
            'title': 'Tallas',
            'bg_from': 'blue-50',
            'bg_to': 'blue-100',
            'icon_color': 'blue-600',
            'badge': f'{Size.objects.count()}',
        },
        {
            'url': reverse('products:category_list'),
            'icon': 'tags',
            'title': 'Categorías',
            'bg_from': 'green-50',
            'bg_to': 'green-100',
            'icon_color': 'green-600',
            'badge': f'{Category.objects.count()}',
        },
        {
            'url': reverse('products:color_list'),
            'icon': 'palette',
            'title': 'Colores',
            'bg_from': 'purple-50',
            'bg_to': 'purple-100',
            'icon_color': 'purple-600',
            'badge': f'{Color.objects.count()}',
        },
        {
            'url': reverse('products:productimage_list'),
            'icon': 'images',
            'title': 'Imágenes',
            'bg_from': 'orange-50',
            'bg_to': 'orange-100',
            'icon_color': 'orange-600',
            'badge': f'{ProductImage.objects.count()}',
        },
        {
            'url': reverse('products:product_list'),
            'icon': 'box',
            'title': 'Productos',
            'bg_from': 'zicada-accent/10',
            'bg_to': 'zicada-accent/20',
            'icon_color': 'zicada-accent',
            'badge': 'Principal',
        },
    ]


    stock_distribution = {
        'series': [stats['con_stock'], stats['stock_bajo'], stats['agotado']],
        'labels': [STOCK_LABEL_IN_STOCK, STOCK_LABEL_LOW_STOCK, STOCK_LABEL_OUT_OF_STOCK],
    }

    stock_stats_list = [
        {'label': STOCK_LABEL_IN_STOCK, 'value': stats['con_stock'], 'color': STOCK_COLOR_GREEN},
        {'label': STOCK_LABEL_LOW_STOCK, 'value': stats['stock_bajo'], 'color': STOCK_COLOR_YELLOW},
        {'label': STOCK_LABEL_OUT_OF_STOCK, 'value': stats['agotado'], 'color': STOCK_COLOR_RED},
    ]

    context = {
        CONTEXT_SECTION: SECTION_PRODUCTS,
        CONTEXT_STATS: stats,
        CONTEXT_URLS: urls,
        CONTEXT_ACTION_BUTTONS: action_buttons,
        CONTEXT_RECENT_PRODUCTS: recent_products,
        CONTEXT_LOW_STOCK_PRODUCTS: low_stock_products,
        CONTEXT_TOP_PRODUCTS: top_products,
        CONTEXT_STOCK_DISTRIBUTION: stock_distribution,
        CONTEXT_STOCK_STATS_LIST: stock_stats_list,
        'quick_access_buttons' : quick_access_buttons,
    }

    return render(request, TEMPLATE_ADMIN_PRODUCTS_DASHBOARD, context)


@staff_member_required
def admin_users(request):
    """Users management dashboard view (focused on delivery users)."""
    delivery_stats = get_delivery_stats()
    order_stats = get_delivery_order_stats()
    recent_deliveries = get_recent_deliveries()
    active_deliveries = get_active_deliveries_list()

    users_url = reverse(ROUTE_USER_LIST)
    urls = {
        'users_list': users_url,
        'total': users_url,
        'activos': users_url + QUERY_IS_ACTIVE.format('true'),
        'inactivos': users_url + QUERY_IS_ACTIVE.format('false'),
        'solo_entregadores': users_url + QUERY_IS_DELIVERY.format('true'),
        'pedidos_listos': reverse(ROUTE_ORDER_LIST) + QUERY_STATUS.format(STATUS_READY),
        'pedidos_camino': reverse(ROUTE_ORDER_LIST) + QUERY_STATUS.format(STATUS_ON_THE_WAY),
    }

    action_buttons = [
        {
            'url': users_url,
            'icon': 'users',
            'title': BTN_TITLE_MANAGE_DELIVERIES,
            'description': BTN_DESC_MANAGE_DELIVERIES,
            'gradient_from': GRADIENT_ACCENT_FROM,
            'gradient_to': GRADIENT_ACCENT_TO,
            'badge': f"{delivery_stats['total']} {STRING_ACTIVOS}"
        },
        {
            'url': reverse(ROUTE_USER_CREATE),
            'icon': 'plus-circle',
            'title': BTN_TITLE_ADD_DELIVERY,
            'description': BTN_DESC_ADD_DELIVERY,
            'gradient_from': GRADIENT_GREEN_FROM,
            'gradient_to': GRADIENT_GREEN_TO,
            'badge': BADGE_NEW
        },
        {
            'url': '#',
            'icon': 'file-export',
            'title': LABEL_EXPORT_REPORTS,
            'description': BTN_DESC_EXPORT_DELIVERIES,
            'gradient_from': GRADIENT_BLUE_FROM,
            'gradient_to': GRADIENT_BLUE_TO,
            'badge': BADGE_COMING_SOON
        },
    ]

    quick_access_buttons = [
        {
            'url': reverse('users:user_list'),
            'icon': 'users',
            'title': 'Usuarios',
            'bg_from': 'gray-50',
            'bg_to': 'gray-100',
            'icon_color': 'gray-600',
            'badge': f"{delivery_stats['total']}",
        },
        {
            'url': reverse('users:group_list'),
            'icon': 'key',
            'title': 'Roles',
            'bg_from': 'amber-50',
            'bg_to': 'amber-100',
            'icon_color': 'amber-600',
            'badge': f"{Group.objects.count()}",
        },
        {
            'url': reverse('users:user_trashcan'),
            'icon': 'trash-alt',
            'title': 'Papelera',
            'bg_from': 'red-50',
            'bg_to': 'red-100',
            'icon_color': 'red-500',
            'badge': f"{User.objects.filter(is_active=False).count()}",
        },
    ]
    delivery_stats_list = [
        {'label': DELIVERY_LABEL_ACTIVE, 'value': delivery_stats['activos'], 'color': DELIVERY_COLOR_ACTIVE},
        {'label': DELIVERY_LABEL_INACTIVE, 'value': delivery_stats['inactivos'], 'color': DELIVERY_COLOR_INACTIVE},
    ]

    categories, order_counts = get_daily_order_counts()

    context = {
        CONTEXT_SECTION: SECTION_USERS,
        CONTEXT_STATS: {
            'total_entregadores': delivery_stats['total'],
            CONTEXT_PEDIDOS_POR_ENTREGAR: order_stats['listos_para_entregar'],
            CONTEXT_PEDIDOS_EN_CAMINO: order_stats['en_camino'],
            'entregados_hoy': order_stats['entregados_hoy'],
        },
        CONTEXT_URLS: urls,
        CONTEXT_ACTION_BUTTONS: action_buttons,
        CONTEXT_RECENT_DELIVERIES: recent_deliveries,
        CONTEXT_ACTIVE_DELIVERIES: active_deliveries,
        CONTEXT_DELIVERY_STATS: delivery_stats,
        CONTEXT_DELIVERY_STATS_LIST: delivery_stats_list,
        CONTEXT_PEDIDOS_POR_ENTREGAR: order_stats['listos_para_entregar'],
        CONTEXT_PEDIDOS_EN_CAMINO: order_stats['en_camino'],
        CONTEXT_ORDERS_TREND_DATA: {
            'series': [{'name': CHART_SERIES_NAME_ORDERS, 'data': order_counts}],
            'categories': categories,
        },
        CONTEXT_ORDERS_STATUS_DATA: get_status_chart_data(),
        'quick_access_buttons' : quick_access_buttons,
    }

    return render(request, TEMPLATE_ADMIN_USERS_DASHBOARD, context)


@staff_member_required
def admin_config(request):
    """Admin configuration view."""
    context = {CONTEXT_SECTION: SECTION_CONFIG}
    return render(request, TEMPLATE_ADMIN_CONFIG, context)

@staff_member_required
def report_generator(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data
            report_type = cleaned['report_type']
            
            params = {
                'date_from': cleaned['date_from'].strftime('%Y-%m-%d'),
                'date_to': cleaned['date_to'].strftime('%Y-%m-%d'),
                'include_charts': cleaned.get('include_charts', False),
                'include_tables': cleaned.get('include_tables', True),
            }
            
            reports = {
                'financial': FinancialReport,
                'products': ProductsReport,
                'delivery': DeliveryReport,
                'orders': OrdersReport,
            }
            
            report = reports[report_type](request, **params)
            return report.render_pdf()
    else:
        form = ReportForm()
    
    return render(request, 'backoffice/reports/report_generator.html', {'form': form})

@staff_member_required
def importers_dashboard(request):
    """Dashboard de importación de datos."""
    
    import_buttons = [
        {
            'url': reverse('products:size_import'),
            'icon': 'ruler',
            'title': 'Tallas',
            'bg_from': 'blue-50',
            'bg_to': 'blue-100',
            'icon_color': 'blue-600',
            'badge': 'CSV/Excel'
        },
        {
            'url': reverse('products:color_import'),
            'icon': 'palette',
            'title': 'Colores',
            'bg_from': 'purple-50',
            'bg_to': 'purple-100',
            'icon_color': 'purple-600',
            'badge': 'CSV/Excel'
        },
        {
            'url': "#" """reverse('products:category_import')""",
            'icon': 'tags',
            'title': 'Categorías',
            'bg_from': 'green-50',
            'bg_to': 'green-100',
            'icon_color': 'green-600',
            'badge': 'CSV/Excel'
        },
    ]
    
    context = {
        'section': 'import',
        'import_buttons': import_buttons,
    }
    return render(request, 'backoffice/importers/importers_dashboard.html', context)