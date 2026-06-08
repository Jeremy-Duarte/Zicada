from datetime import timedelta
from typing import Any, Dict, List, Tuple

from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_GET, require_http_methods
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
ORDER_STATUS_PENDING = 'pendiente'
ORDER_STATUS_CONFIRMED = 'confirmado'
ORDER_STATUS_PREPARING = 'preparando'
ORDER_STATUS_READY = 'listo'
ORDER_STATUS_ON_THE_WAY = 'en_camino'
ORDER_STATUS_DELIVERED = 'entregado'
ORDER_STATUS_CANCELLED = 'cancelado'

PAID_ORDER_STATUSES = [
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_PREPARING,
    ORDER_STATUS_READY,
    ORDER_STATUS_ON_THE_WAY,
    ORDER_STATUS_DELIVERED
]

ORDER_STATUS_LABELS = {
    ORDER_STATUS_PENDING: 'Pendientes',
    ORDER_STATUS_CONFIRMED: 'Confirmados',
    ORDER_STATUS_PREPARING: 'Preparando',
    ORDER_STATUS_READY: 'Listos',
    ORDER_STATUS_ON_THE_WAY: 'En camino',
    ORDER_STATUS_DELIVERED: 'Entregados',
    ORDER_STATUS_CANCELLED: 'Cancelados',
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
ROUTE_IMPORTERS_DASHBOARD = 'backoffice:importers_dashboard'
ROUTE_REPORT_GENERATOR = 'backoffice:report_generator'
ROUTE_SIZE_LIST = 'products:size_list'
ROUTE_CATEGORY_LIST = 'products:category_list'
ROUTE_COLOR_LIST = 'products:color_list'
ROUTE_PRODUCT_IMAGE_LIST = 'products:productimage_list'
ROUTE_SIZE_IMPORT = 'products:size_import'
ROUTE_COLOR_IMPORT = 'products:color_import'
ROUTE_CATEGORY_IMPORT = 'products:category_import'
ROUTE_USER_LIST_BASE = 'users:user_list'
ROUTE_GROUP_LIST = 'users:group_list'
ROUTE_USER_TRASHCAN = 'users:user_trashcan'
ROUTE_HERO_LIST = 'core:hero_list'
ROUTE_HERO_TRASHCAN = 'core:hero_trashcan'

# URL Query Parameters
QUERY_PARAM_STATUS = 'status'
QUERY_PARAM_NAME = 'name'
QUERY_PARAM_IS_ACTIVE = 'is_active'
QUERY_PARAM_IS_DELIVERY = 'is_delivery'
QUERY_PARAM_STOCK = 'stock'
QUERY_PARAM_USERNAME = 'username'

# URL Query Templates
QUERY_STATUS = f'?{QUERY_PARAM_STATUS}={{}}'
QUERY_NAME = f'?{QUERY_PARAM_NAME}={{}}'
QUERY_IS_ACTIVE = f'?{QUERY_PARAM_IS_ACTIVE}={{}}'
QUERY_IS_DELIVERY = f'?{QUERY_PARAM_IS_DELIVERY}={{}}'
QUERY_STOCK = f'?{QUERY_PARAM_STOCK}={{}}'
QUERY_USERNAME = f'?{QUERY_PARAM_USERNAME}={{}}'

# URL Query Parameter Values
QUERY_VALUE_ALL = 'all'
QUERY_VALUE_ACTIVE = 'true'
QUERY_VALUE_INACTIVE = 'false'
QUERY_VALUE_LOW_STOCK = 'low'
QUERY_VALUE_OUT_OF_STOCK = 'out'
QUERY_VALUE_TODOS = 'todos'  # Spanish legacy support

# Template Paths
TEMPLATE_ADMIN_DASHBOARD = 'backoffice/admin_dashboard.html'
TEMPLATE_ADMIN_ORDERS_DASHBOARD = 'backoffice/admin_orders_dashboard.html'
TEMPLATE_ADMIN_PRODUCTS_DASHBOARD = 'backoffice/admin_products_dashboard.html'
TEMPLATE_ADMIN_USERS_DASHBOARD = 'backoffice/admin_users_dashboard.html'
TEMPLATE_ADMIN_CONFIG = 'backoffice/admin_config.html'
TEMPLATE_REPORT_GENERATOR = 'backoffice/reports/report_generator.html'
TEMPLATE_IMPORTERS_DASHBOARD = 'backoffice/importers/importers_dashboard.html'

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
ICON_FILE_EXPORT = 'file-export'
ICON_TABLE_LIST = 'table-list'
ICON_PLUS_CIRCLE = 'plus-circle'
ICON_RULER = 'ruler'
ICON_TAGS = 'tags'
ICON_PALETTE = 'palette'
ICON_IMAGES = 'images'
ICON_USERS = 'users'
ICON_KEY = 'key'
ICON_TRASH_ALT = 'trash-alt'
ICON_RECEIPT = 'receipt'
ICON_SHOPPING_CART = 'shopping-cart'
ICON_SUN = 'sun'
ICON_CALENDAR_ALT = 'calendar-alt'

# Icon Background Colors
ICON_BG_GRAY = 'gray-100'
ICON_BG_YELLOW = 'yellow-100'
ICON_BG_GREEN = 'green-100'
ICON_BG_BLUE = 'blue-100'
ICON_BG_PURPLE = 'purple-100'
ICON_BG_ORANGE = 'orange-50'
ICON_BG_INDIGO = 'indigo-50'
ICON_BG_BLUE_50 = 'blue-50'
ICON_BG_BLUE_100 = 'blue-100'
ICON_BG_GREEN_50 = 'green-50'
ICON_BG_GREEN_100 = 'green-100'
ICON_BG_PURPLE_50 = 'purple-50'
ICON_BG_PURPLE_100 = 'purple-100'
ICON_BG_ORANGE_100 = 'orange-100'
ICON_BG_GRAY_50 = 'gray-50'
ICON_BG_GRAY_100 = 'gray-100'
ICON_BG_AMBER_50 = 'amber-50'
ICON_BG_AMBER_100 = 'amber-100'
ICON_BG_RED_50 = 'red-50'
ICON_BG_RED_100 = 'red-100'

# Icon Colors
ICON_COLOR_ACCENT = 'zicada-accent'
ICON_COLOR_YELLOW = 'yellow-600'
ICON_COLOR_GREEN = 'green-600'
ICON_COLOR_BLUE = 'blue-600'
ICON_COLOR_PURPLE = 'purple-600'
ICON_COLOR_BLUE_600 = 'blue-600'
ICON_COLOR_GREEN_600 = 'green-600'
ICON_COLOR_PURPLE_600 = 'purple-600'
ICON_COLOR_ORANGE_600 = 'orange-600'
ICON_COLOR_GRAY_600 = 'gray-600'
ICON_COLOR_AMBER_600 = 'amber-600'
ICON_COLOR_RED = 'red-500'

# Badge Labels
BADGE_NEW = 'Nuevo'
BADGE_COMING_SOON = 'Próximamente'
BADGE_CSV_EXCEL = 'CSV/Excel'
BADGE_PRIMARY = 'Principal'
BADGE_PLUS = '+'
BADGE_TRASH = '🗑'
LABEL_EXPORT_REPORTS = 'Exportar Reportes'

# Button Titles
BTN_TITLE_MANAGE_ORDERS = 'Gestionar Pedidos'
BTN_TITLE_CREATE_ORDER = 'Crear Pedido'
BTN_TITLE_MANAGE_PRODUCTS = 'Gestionar Productos'
BTN_TITLE_CREATE_PRODUCT = 'Crear Producto'
BTN_TITLE_MANAGE_DELIVERIES = 'Gestionar Entregadores'
BTN_TITLE_ADD_DELIVERY = 'Agregar Entregador'
BTN_TITLE_SIZES = 'Tallas'
BTN_TITLE_CATEGORIES = 'Categorías'
BTN_TITLE_COLORS = 'Colores'
BTN_TITLE_IMAGES = 'Imágenes'
BTN_TITLE_PRODUCTS = 'Productos'
BTN_TITLE_USERS = 'Usuarios'
BTN_TITLE_ROLES = 'Roles'
BTN_TITLE_TRASHCAN = 'Papelera'
BTN_TITLE_HERO_SLIDES = 'Slides del Hero'

# Button Descriptions
BTN_DESC_MANAGE_ORDERS = 'Ver, filtrar y gestionar todos los pedidos'
BTN_DESC_CREATE_ORDER = 'Agregar un nuevo pedido desde el catálogo'
BTN_DESC_MANAGE_PRODUCTS = 'Ver, filtrar y gestionar todos los productos'
BTN_DESC_CREATE_PRODUCT = 'Agregar un nuevo producto al catálogo'
BTN_DESC_MANAGE_DELIVERIES = 'Ver, filtrar y gestionar todos los entregadores'
BTN_DESC_ADD_DELIVERY = 'Registrar un nuevo entregador'
BTN_DESC_EXPORT = 'Descargar reportes en Excel o PDF'
BTN_DESC_EXPORT_DELIVERIES = 'Descargar reportes de entregas'
BTN_DESC_FINANCIAL_REPORTS = 'Generar reportes financieros personalizados'

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
FINANCIAL_ICON_RECEIPT = ICON_RECEIPT
FINANCIAL_ICON_BOX = ICON_BOX
FINANCIAL_ICON_CHART = ICON_CHART_LINE
FINANCIAL_ICON_CART = ICON_SHOPPING_CART
FINANCIAL_ICON_SUN = ICON_SUN
FINANCIAL_ICON_CALENDAR = ICON_CALENDAR_ALT

# Financial Item Colors
FINANCIAL_COLOR_ACCENT = ICON_COLOR_ACCENT
FINANCIAL_COLOR_BLUE = ICON_COLOR_BLUE
FINANCIAL_COLOR_GREEN = ICON_COLOR_GREEN
FINANCIAL_COLOR_PURPLE = ICON_COLOR_PURPLE
FINANCIAL_COLOR_ORANGE = ICON_COLOR_ORANGE_600
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
SECTION_IMPORT = 'import'

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
CONTEXT_PENDING_ORDERS = 'pending_orders'
CONTEXT_ORDERS_ON_THE_WAY = 'orders_on_the_way'
CONTEXT_QUICK_ACCESS_BUTTONS = 'quick_access_buttons'
CONTEXT_IMPORT_BUTTONS = 'import_buttons'

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

# Common Strings (English names, Spanish values for UI)
STRING_EMPTY = ''
STRING_NO_CATEGORY = 'Sin categoría'
STRING_NO_EMAIL = 'Sin email'
STRING_NO_PHONE = 'Sin teléfono'
STRING_UNITS = 'unidades'
STRING_UNITS_SOLD = 'unidades vendidas'
STRING_TOTAL_COLLECTED = 'Total recaudado'
STRING_DELIVERED_BY = 'Entregado por'
STRING_ON_THE_WAY = 'en camino'
STRING_DELIVERED = 'entregados'
STRING_ACTIVE = 'activos'
STRING_PER_TRANSACTION = 'por transacción'
STRING_AVERAGE = 'promedio'
STRING_LAST_7_DAYS = 'últimos 7 días'
STRING_COMPLETED_ORDERS = 'pedidos completados'
STRING_ACCUMULATED = 'acumulado'
STRING_PRODUCTS = 'productos'

# Report Types
REPORT_TYPE_FINANCIAL = 'financial'
REPORT_TYPE_PRODUCTS = 'products'
REPORT_TYPE_DELIVERY = 'delivery'
REPORT_TYPE_ORDERS = 'orders'


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

    for code, label in ORDER_STATUS_LABELS.items():
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
            'value': f"{v.stock} {STRING_UNITS}",
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
            url = reverse(ROUTE_PRODUCT_EDIT, args=[product.pk])
        except Product.DoesNotExist:
            url = reverse(ROUTE_PRODUCT_LIST) + QUERY_NAME.format(name)

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
    """Get aggregated product statistics."""
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
    """Get most recently added products."""
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
        'active': User.objects.filter(is_delivery=True, is_active=True).count(),
        'inactive': User.objects.filter(is_delivery=True, is_active=False).count(),
    }


def get_delivery_order_stats() -> Dict[str, int]:
    """Get delivery-related order statistics."""
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
    """Get most recent completed deliveries."""
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
            'url': reverse(ROUTE_USER_LIST) + QUERY_USERNAME.format(delivery.username),
            'extra_info': delivery.phone or STRING_NO_PHONE,
        })

    return result


def get_delivery_stats_for_user(user: User) -> Dict[str, Any]:
    """Get delivery statistics for a specific user."""
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


# =============================================================================
# VIEWS
# =============================================================================

@staff_member_required
@require_GET
def admin_dashboard(request):
    """Main admin dashboard view."""
    today = timezone.now().date()
    month, year = today.month, today.year
    week_ago = today - timedelta(days=DAYS_FOR_TREND)

    pending_orders = Order.objects.filter(status=ORDER_STATUS_PENDING).count()
    today_orders = Order.objects.filter(created_at__date=today).count()
    month_revenue = sum_order_amount(year=year, month=month)
    active_deliveries = User.objects.filter(is_delivery=True, is_active=True).count()

    today_revenue = sum_order_amount(date_start=today, date_end=today)
    week_revenue = sum_order_amount(date_start=week_ago, date_end=today)
    year_revenue = sum_order_amount(year=year)

    total_paid = Order.objects.filter(status__in=PAID_ORDER_STATUSES).count()
    avg_order = month_revenue / total_paid if total_paid else 0

    total_items = OrderItem.objects.filter(
        order__status__in=PAID_ORDER_STATUSES
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
            'icon_bg': ICON_BG_BLUE,
            'icon_color': FINANCIAL_COLOR_BLUE,
            'sub_value': FINANCIAL_SUB_AVG_ITEMS,
        },
        {
            'label': FINANCIAL_LABEL_AVG_DAILY_INCOME,
            'value': f"{CURRENCY_PREFIX}{week_revenue:,.0f}",
            'icon': FINANCIAL_ICON_CHART,
            'icon_bg': ICON_BG_GREEN,
            'icon_color': FINANCIAL_COLOR_GREEN,
            'sub_value': FINANCIAL_SUB_AVG_DAILY,
        },
        {
            'label': FINANCIAL_LABEL_TOTAL_PAID,
            'value': total_paid,
            'icon': FINANCIAL_ICON_CART,
            'icon_bg': ICON_BG_PURPLE,
            'icon_color': FINANCIAL_COLOR_PURPLE,
            'sub_value': FINANCIAL_SUB_TOTAL_PAID,
        },
        {
            'label': FINANCIAL_LABEL_TODAY_INCOME,
            'value': f"{CURRENCY_PREFIX}{today_revenue:,.0f}",
            'icon': FINANCIAL_ICON_SUN,
            'icon_bg': ICON_BG_ORANGE,
            'icon_color': FINANCIAL_COLOR_ORANGE,
            'sub_value': FINANCIAL_SUB_TODAY,
        },
        {
            'label': FINANCIAL_LABEL_YEAR_INCOME,
            'value': f"{CURRENCY_PREFIX}{year_revenue:,.0f}",
            'icon': FINANCIAL_ICON_CALENDAR,
            'icon_bg': ICON_BG_INDIGO,
            'icon_color': FINANCIAL_COLOR_INDIGO,
            'sub_value': str(year),
        },
    ]

    reports_url = reverse(ROUTE_REPORT_GENERATOR)
    
    action_buttons = [
        {
            'url': reports_url,
            'icon': ICON_FILE_EXPORT,
            'title': LABEL_EXPORT_REPORTS,
            'description': BTN_DESC_FINANCIAL_REPORTS,
            'gradient_from': GRADIENT_BLUE_FROM,
            'gradient_to': GRADIENT_BLUE_TO,
            'badge': BADGE_NEW
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
@require_GET
def admin_orders_dashboard(request):
    """Orders management dashboard view."""
    stats = get_order_status_counts()
    stats['total'] = sum(stats.values())
    recent_orders = get_recent_orders()
    categories, order_counts = get_daily_order_counts()

    orders_url = reverse(ROUTE_ORDER_LIST)
    urls = {
        'total': orders_url,
        ORDER_STATUS_PENDING: orders_url + QUERY_STATUS.format(ORDER_STATUS_PENDING),
        ORDER_STATUS_CONFIRMED: orders_url + QUERY_STATUS.format(ORDER_STATUS_CONFIRMED),
        ORDER_STATUS_PREPARING: orders_url + QUERY_STATUS.format(ORDER_STATUS_PREPARING),
        ORDER_STATUS_READY: orders_url + QUERY_STATUS.format(ORDER_STATUS_READY),
        ORDER_STATUS_ON_THE_WAY: orders_url + QUERY_STATUS.format(ORDER_STATUS_ON_THE_WAY),
        ORDER_STATUS_DELIVERED: orders_url + QUERY_STATUS.format(ORDER_STATUS_DELIVERED),
        ORDER_STATUS_CANCELLED: orders_url + QUERY_STATUS.format(ORDER_STATUS_CANCELLED),
        'orders_list': orders_url,
    }

    action_buttons = [
        {
            'url': orders_url,
            'icon': ICON_TABLE_LIST,
            'title': BTN_TITLE_MANAGE_ORDERS,
            'description': BTN_DESC_MANAGE_ORDERS,
            'gradient_from': GRADIENT_ACCENT_FROM,
            'gradient_to': GRADIENT_ACCENT_TO,
            'badge': f"{stats['total']} {STRING_ACTIVE}"
        },
        {
            'url': reverse(ROUTE_ORDER_CREATE),
            'icon': ICON_PLUS_CIRCLE,
            'title': BTN_TITLE_CREATE_ORDER,
            'description': BTN_DESC_CREATE_ORDER,
            'gradient_from': GRADIENT_GREEN_FROM,
            'gradient_to': GRADIENT_GREEN_TO,
            'badge': BADGE_NEW
        },
        {
            'url': '#',
            'icon': ICON_FILE_EXPORT,
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
@require_GET
def admin_products(request):
    """Products management dashboard view."""
    stats = get_product_stats()
    recent_products = get_recent_products()
    low_stock_products = get_low_stock_products()
    top_products = get_top_products()

    products_url = reverse(ROUTE_PRODUCT_LIST)
    urls = {
        'products_list': products_url,
        'total': f"{products_url}?{QUERY_PARAM_STATUS}={QUERY_VALUE_ALL}",
        'active': products_url + QUERY_IS_ACTIVE.format(QUERY_VALUE_ACTIVE),
        'inactive': products_url + QUERY_IS_ACTIVE.format(QUERY_VALUE_INACTIVE),
        'low_stock': products_url + QUERY_STOCK.format(QUERY_VALUE_LOW_STOCK),
        'out_of_stock': products_url + QUERY_STOCK.format(QUERY_VALUE_OUT_OF_STOCK),
    }

    action_buttons = [
        {
            'url': products_url,
            'icon': ICON_TABLE_LIST,
            'title': BTN_TITLE_MANAGE_PRODUCTS,
            'description': BTN_DESC_MANAGE_PRODUCTS,
            'gradient_from': GRADIENT_ACCENT_FROM,
            'gradient_to': GRADIENT_ACCENT_TO,
            'badge': f"{stats['total']} {STRING_PRODUCTS}"
        },
        {
            'url': reverse(ROUTE_PRODUCT_CREATE),
            'icon': ICON_PLUS_CIRCLE,
            'title': BTN_TITLE_CREATE_PRODUCT,
            'description': BTN_DESC_CREATE_PRODUCT,
            'gradient_from': GRADIENT_GREEN_FROM,
            'gradient_to': GRADIENT_GREEN_TO,
            'badge': BADGE_NEW
        },
        {
            'url': reverse(ROUTE_IMPORTERS_DASHBOARD),
            'icon': ICON_FILE_EXPORT,
            'title': LABEL_EXPORT_REPORTS,
            'description': BTN_DESC_EXPORT,
            'gradient_from': GRADIENT_BLUE_FROM,
            'gradient_to': GRADIENT_BLUE_TO,
            'badge': BADGE_COMING_SOON
        },
    ]

    quick_access_buttons = [
        {
            'url': reverse(ROUTE_SIZE_LIST),
            'icon': ICON_RULER,
            'title': BTN_TITLE_SIZES,
            'bg_from': ICON_BG_BLUE_50,
            'bg_to': ICON_BG_BLUE_100,
            'icon_color': ICON_COLOR_BLUE_600,
            'badge': f'{Size.objects.count()}',
        },
        {
            'url': reverse(ROUTE_CATEGORY_LIST),
            'icon': ICON_TAGS,
            'title': BTN_TITLE_CATEGORIES,
            'bg_from': ICON_BG_GREEN_50,
            'bg_to': ICON_BG_GREEN_100,
            'icon_color': ICON_COLOR_GREEN_600,
            'badge': f'{Category.objects.count()}',
        },
        {
            'url': reverse(ROUTE_COLOR_LIST),
            'icon': ICON_PALETTE,
            'title': BTN_TITLE_COLORS,
            'bg_from': ICON_BG_PURPLE_50,
            'bg_to': ICON_BG_PURPLE_100,
            'icon_color': ICON_COLOR_PURPLE_600,
            'badge': f'{Color.objects.count()}',
        },
        {
            'url': reverse(ROUTE_PRODUCT_IMAGE_LIST),
            'icon': ICON_IMAGES,
            'title': BTN_TITLE_IMAGES,
            'bg_from': ICON_BG_ORANGE,
            'bg_to': ICON_BG_ORANGE_100,
            'icon_color': ICON_COLOR_ORANGE_600,
            'badge': f'{ProductImage.objects.count()}',
        },
        {
            'url': reverse(ROUTE_PRODUCT_LIST),
            'icon': ICON_BOX,
            'title': BTN_TITLE_PRODUCTS,
            'bg_from': f'{ICON_COLOR_ACCENT}/10',
            'bg_to': f'{ICON_COLOR_ACCENT}/20',
            'icon_color': ICON_COLOR_ACCENT,
            'badge': BADGE_PRIMARY,
        },
    ]


    stock_distribution = {
        'series': [stats['in_stock'], stats['low_stock'], stats['out_of_stock']],
        'labels': [STOCK_LABEL_IN_STOCK, STOCK_LABEL_LOW_STOCK, STOCK_LABEL_OUT_OF_STOCK],
    }

    stock_stats_list = [
        {'label': STOCK_LABEL_IN_STOCK, 'value': stats['in_stock'], 'color': STOCK_COLOR_GREEN},
        {'label': STOCK_LABEL_LOW_STOCK, 'value': stats['low_stock'], 'color': STOCK_COLOR_YELLOW},
        {'label': STOCK_LABEL_OUT_OF_STOCK, 'value': stats['out_of_stock'], 'color': STOCK_COLOR_RED},
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
        CONTEXT_QUICK_ACCESS_BUTTONS: quick_access_buttons,
    }

    return render(request, TEMPLATE_ADMIN_PRODUCTS_DASHBOARD, context)


@staff_member_required
@require_GET
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
        'active': users_url + QUERY_IS_ACTIVE.format(QUERY_VALUE_ACTIVE),
        'inactive': users_url + QUERY_IS_ACTIVE.format(QUERY_VALUE_INACTIVE),
        'only_deliveries': users_url + QUERY_IS_DELIVERY.format(QUERY_VALUE_ACTIVE),
        'ready_orders': reverse(ROUTE_ORDER_LIST) + QUERY_STATUS.format(ORDER_STATUS_READY),
        'on_the_way_orders': reverse(ROUTE_ORDER_LIST) + QUERY_STATUS.format(ORDER_STATUS_ON_THE_WAY),
    }

    action_buttons = [
        {
            'url': users_url,
            'icon': ICON_USERS,
            'title': BTN_TITLE_MANAGE_DELIVERIES,
            'description': BTN_DESC_MANAGE_DELIVERIES,
            'gradient_from': GRADIENT_ACCENT_FROM,
            'gradient_to': GRADIENT_ACCENT_TO,
            'badge': f"{delivery_stats['total']} {STRING_ACTIVE}"
        },
        {
            'url': reverse(ROUTE_USER_CREATE),
            'icon': ICON_PLUS_CIRCLE,
            'title': BTN_TITLE_ADD_DELIVERY,
            'description': BTN_DESC_ADD_DELIVERY,
            'gradient_from': GRADIENT_GREEN_FROM,
            'gradient_to': GRADIENT_GREEN_TO,
            'badge': BADGE_NEW
        },
        {
            'url': '#',
            'icon': ICON_FILE_EXPORT,
            'title': LABEL_EXPORT_REPORTS,
            'description': BTN_DESC_EXPORT_DELIVERIES,
            'gradient_from': GRADIENT_BLUE_FROM,
            'gradient_to': GRADIENT_BLUE_TO,
            'badge': BADGE_COMING_SOON
        },
    ]

    quick_access_buttons = [
        {
            'url': reverse(ROUTE_USER_LIST_BASE),
            'icon': ICON_USERS,
            'title': BTN_TITLE_USERS,
            'bg_from': ICON_BG_GRAY_50,
            'bg_to': ICON_BG_GRAY_100,
            'icon_color': ICON_COLOR_GRAY_600,
            'badge': f"{delivery_stats['total']}",
        },
        {
            'url': reverse(ROUTE_GROUP_LIST),
            'icon': ICON_KEY,
            'title': BTN_TITLE_ROLES,
            'bg_from': ICON_BG_AMBER_50,
            'bg_to': ICON_BG_AMBER_100,
            'icon_color': ICON_COLOR_AMBER_600,
            'badge': f"{Group.objects.count()}",
        },
        {
            'url': reverse(ROUTE_USER_TRASHCAN),
            'icon': ICON_TRASH_ALT,
            'title': BTN_TITLE_TRASHCAN,
            'bg_from': ICON_BG_RED_50,
            'bg_to': ICON_BG_RED_100,
            'icon_color': ICON_COLOR_RED,
            'badge': f"{User.objects.filter(is_active=False).count()}",
        },
    ]
    delivery_stats_list = [
        {'label': DELIVERY_LABEL_ACTIVE, 'value': delivery_stats['active'], 'color': DELIVERY_COLOR_ACTIVE},
        {'label': DELIVERY_LABEL_INACTIVE, 'value': delivery_stats['inactive'], 'color': DELIVERY_COLOR_INACTIVE},
    ]

    categories, order_counts = get_daily_order_counts()

    context = {
        CONTEXT_SECTION: SECTION_USERS,
        CONTEXT_STATS: {
            'total_deliveries': delivery_stats['total'],
            CONTEXT_PENDING_ORDERS: order_stats['ready_for_delivery'],
            CONTEXT_ORDERS_ON_THE_WAY: order_stats['on_the_way'],
            'delivered_today': order_stats['delivered_today'],
        },
        CONTEXT_URLS: urls,
        CONTEXT_ACTION_BUTTONS: action_buttons,
        CONTEXT_RECENT_DELIVERIES: recent_deliveries,
        CONTEXT_ACTIVE_DELIVERIES: active_deliveries,
        CONTEXT_DELIVERY_STATS: delivery_stats,
        CONTEXT_DELIVERY_STATS_LIST: delivery_stats_list,
        CONTEXT_PENDING_ORDERS: order_stats['ready_for_delivery'],
        CONTEXT_ORDERS_ON_THE_WAY: order_stats['on_the_way'],
        CONTEXT_ORDERS_TREND_DATA: {
            'series': [{'name': CHART_SERIES_NAME_ORDERS, 'data': order_counts}],
            'categories': categories,
        },
        CONTEXT_ORDERS_STATUS_DATA: get_status_chart_data(),
        CONTEXT_QUICK_ACCESS_BUTTONS: quick_access_buttons,
    }

    return render(request, TEMPLATE_ADMIN_USERS_DASHBOARD, context)


@staff_member_required
@require_GET
def admin_config(request):
    """Admin configuration view."""
    quick_access_buttons = [
        {
            'url': reverse(ROUTE_HERO_LIST),
            'icon': ICON_IMAGES,
            'title': BTN_TITLE_HERO_SLIDES,
            'bg_from': ICON_BG_PURPLE_50,
            'bg_to': ICON_BG_PURPLE_100,
            'icon_color': ICON_COLOR_PURPLE_600,
            'badge': BADGE_PLUS,
        },
        {
            'url': reverse(ROUTE_HERO_TRASHCAN),
            'icon': ICON_TRASH_ALT,
            'title': BTN_TITLE_TRASHCAN,
            'bg_from': ICON_BG_RED_50,
            'bg_to': ICON_BG_RED_100,
            'icon_color': ICON_COLOR_RED,
            'badge': BADGE_TRASH,
        },
    ]
    context = {CONTEXT_SECTION: SECTION_CONFIG, CONTEXT_QUICK_ACCESS_BUTTONS: quick_access_buttons}
    return render(request, TEMPLATE_ADMIN_CONFIG, context)


@staff_member_required
@require_http_methods(['GET', 'POST'])
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
                REPORT_TYPE_FINANCIAL: FinancialReport,
                REPORT_TYPE_PRODUCTS: ProductsReport,
                REPORT_TYPE_DELIVERY: DeliveryReport,
                REPORT_TYPE_ORDERS: OrdersReport,
            }
            
            report = reports[report_type](request, **params)
            return report.render_pdf()
    else:
        form = ReportForm()
    
    return render(request, TEMPLATE_REPORT_GENERATOR, {'form': form})


@staff_member_required
@require_GET
def importers_dashboard(request):
    """Dashboard de importación de datos."""
    
    import_buttons = [
        {
            'url': reverse(ROUTE_SIZE_IMPORT),
            'icon': ICON_RULER,
            'title': BTN_TITLE_SIZES,
            'bg_from': ICON_BG_BLUE_50,
            'bg_to': ICON_BG_BLUE_100,
            'icon_color': ICON_COLOR_BLUE_600,
            'badge': BADGE_CSV_EXCEL
        },
        {
            'url': reverse(ROUTE_COLOR_IMPORT),
            'icon': ICON_PALETTE,
            'title': BTN_TITLE_COLORS,
            'bg_from': ICON_BG_PURPLE_50,
            'bg_to': ICON_BG_PURPLE_100,
            'icon_color': ICON_COLOR_PURPLE_600,
            'badge': BADGE_CSV_EXCEL
        },
        {
            'url': reverse(ROUTE_CATEGORY_IMPORT),
            'icon': ICON_TAGS,
            'title': BTN_TITLE_CATEGORIES,
            'bg_from': ICON_BG_GREEN_50,
            'bg_to': ICON_BG_GREEN_100,
            'icon_color': ICON_COLOR_GREEN_600,
            'badge': BADGE_CSV_EXCEL
        },
    ]
    
    context = {
        CONTEXT_SECTION: SECTION_IMPORT,
        CONTEXT_IMPORT_BUTTONS: import_buttons,
    }
    return render(request, TEMPLATE_IMPORTERS_DASHBOARD, context)