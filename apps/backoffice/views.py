from datetime import timedelta
from typing import Any, Dict, List

from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, FormView

from apps.orders.models import Order, OrderItem
from apps.products.models import Product, ProductVariant, Size, Category, Color, ProductImage
from apps.users.models import User, Group

from apps.core.crud.mixins import StaffPermissionRequiredMixin

from .metrics import (
    sum_order_amount,
    get_daily_data,
    get_status_chart_data,
    get_recent_orders,
    get_order_status_counts,
    get_daily_order_counts,
    get_low_stock_products,
    get_top_products,
    get_product_stats,
    get_recent_products,
    get_delivery_stats,
    get_delivery_order_stats,
    get_recent_deliveries,
    get_active_deliveries_list,
)

from .reports.report_forms import ReportForm
from .reports.financial import FinancialReport
from .reports.orders import OrdersReport
from .reports.products import ProductsReport
from .reports.delivery import DeliveryReport

from .constants import (
    # Order Statuses
    ORDER_STATUS_PENDING,
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_PREPARING,
    ORDER_STATUS_READY,
    ORDER_STATUS_ON_THE_WAY,
    ORDER_STATUS_DELIVERED,
    ORDER_STATUS_CANCELLED,
    PAID_ORDER_STATUSES,
    # URL Query Parameters
    QUERY_PARAM_STATUS,
    QUERY_PARAM_IS_ACTIVE,
    QUERY_PARAM_IS_DELIVERY,
    QUERY_PARAM_STOCK,
    # URL Query Templates
    QUERY_STATUS,
    QUERY_IS_ACTIVE,
    QUERY_IS_DELIVERY,
    QUERY_STOCK,
    # URL Query Parameter Values
    QUERY_VALUE_ALL,
    QUERY_VALUE_ACTIVE,
    QUERY_VALUE_INACTIVE,
    QUERY_VALUE_LOW_STOCK,
    QUERY_VALUE_OUT_OF_STOCK,
    # Template Paths
    TEMPLATE_ADMIN_DASHBOARD,
    TEMPLATE_ADMIN_ORDERS_DASHBOARD,
    TEMPLATE_ADMIN_PRODUCTS_DASHBOARD,
    TEMPLATE_ADMIN_USERS_DASHBOARD,
    TEMPLATE_ADMIN_CONFIG,
    TEMPLATE_REPORT_GENERATOR,
    TEMPLATE_IMPORTERS_DASHBOARD,
    # Chart and Display Labels
    CHART_SERIES_NAME_SALES,
    CHART_SERIES_NAME_REVENUE,
    CHART_SERIES_NAME_ORDERS,
    # Icon Names
    ICON_BOX,
    ICON_FILE_EXPORT,
    ICON_TABLE_LIST,
    ICON_PLUS_CIRCLE,
    ICON_RULER,
    ICON_TAGS,
    ICON_PALETTE,
    ICON_IMAGES,
    ICON_USERS,
    ICON_KEY,
    ICON_TRASH_ALT,
    # Icon Background Colors
    ICON_BG_BLUE,
    ICON_BG_GREEN,
    ICON_BG_PURPLE,
    ICON_BG_ORANGE,
    ICON_BG_INDIGO,
    ICON_BG_BLUE_50,
    ICON_BG_BLUE_100,
    ICON_BG_GREEN_50,
    ICON_BG_GREEN_100,
    ICON_BG_PURPLE_50,
    ICON_BG_PURPLE_100,
    ICON_BG_ORANGE_100,
    ICON_BG_GRAY_50,
    ICON_BG_GRAY_100,
    ICON_BG_AMBER_50,
    ICON_BG_AMBER_100,
    ICON_BG_RED_50,
    ICON_BG_RED_100,
    # Icon Colors
    ICON_COLOR_ACCENT,
    ICON_COLOR_BLUE_600,
    ICON_COLOR_GREEN_600,
    ICON_COLOR_PURPLE_600,
    ICON_COLOR_ORANGE_600,
    ICON_COLOR_GRAY_600,
    ICON_COLOR_AMBER_600,
    ICON_COLOR_RED,
    # Badge Labels
    BADGE_NEW,
    BADGE_COMING_SOON,
    BADGE_CSV_EXCEL,
    BADGE_PRIMARY,
    BADGE_PLUS,
    BADGE_TRASH,
    LABEL_EXPORT_REPORTS,
    LABEL_EXPORT_IMPORTS,
    # Button Titles
    BTN_TITLE_MANAGE_ORDERS,
    BTN_TITLE_CREATE_ORDER,
    BTN_TITLE_MANAGE_PRODUCTS,
    BTN_TITLE_CREATE_PRODUCT,
    BTN_TITLE_MANAGE_DELIVERIES,
    BTN_TITLE_ADD_DELIVERY,
    BTN_TITLE_SIZES,
    BTN_TITLE_CATEGORIES,
    BTN_TITLE_COLORS,
    BTN_TITLE_IMAGES,
    BTN_TITLE_PRODUCTS,
    BTN_TITLE_USERS,
    BTN_TITLE_ROLES,
    BTN_TITLE_TRASHCAN,
    BTN_TITLE_HERO_SLIDES,
    BTN_TITLE_MANAGE_COLLECTIONS,
    # Button Descriptions
    BTN_DESC_MANAGE_ORDERS,
    BTN_DESC_CREATE_ORDER,
    BTN_DESC_MANAGE_PRODUCTS,
    BTN_DESC_CREATE_PRODUCT,
    BTN_DESC_MANAGE_DELIVERIES,
    BTN_DESC_ADD_DELIVERY,
    BTN_DESC_EXPORT,
    BTN_DESC_EXPORT_DELIVERIES,
    BTN_DESC_FINANCIAL_REPORTS,
    BTN_DESC_MANAGE_COLLECTIONS,
    BTN_DESC_IMPORT_PRODUCTS,
    # Gradient Colors
    GRADIENT_ACCENT_FROM,
    GRADIENT_ACCENT_TO,
    GRADIENT_GREEN_FROM,
    GRADIENT_GREEN_TO,
    GRADIENT_BLUE_FROM,
    GRADIENT_BLUE_TO,
    # Financial Item Labels
    FINANCIAL_LABEL_AVG_TICKET,
    FINANCIAL_LABEL_ITEMS_PER_ORDER,
    FINANCIAL_LABEL_AVG_DAILY_INCOME,
    FINANCIAL_LABEL_TOTAL_PAID,
    FINANCIAL_LABEL_TODAY_INCOME,
    FINANCIAL_LABEL_YEAR_INCOME,
    # Financial Item Sub-values
    FINANCIAL_SUB_AVG_TICKET,
    FINANCIAL_SUB_AVG_ITEMS,
    FINANCIAL_SUB_AVG_DAILY,
    FINANCIAL_SUB_TOTAL_PAID,
    FINANCIAL_SUB_TODAY,
    # Financial Item Icons
    FINANCIAL_ICON_RECEIPT,
    FINANCIAL_ICON_BOX,
    FINANCIAL_ICON_CHART,
    FINANCIAL_ICON_CART,
    FINANCIAL_ICON_SUN,
    FINANCIAL_ICON_CALENDAR,
    # Financial Item Colors
    FINANCIAL_COLOR_BLUE,
    FINANCIAL_COLOR_GREEN,
    FINANCIAL_COLOR_PURPLE,
    FINANCIAL_COLOR_ORANGE,
    FINANCIAL_COLOR_INDIGO,
    # Stock Distribution Labels
    STOCK_LABEL_IN_STOCK,
    STOCK_LABEL_LOW_STOCK,
    STOCK_LABEL_OUT_OF_STOCK,
    STOCK_COLOR_GREEN,
    STOCK_COLOR_YELLOW,
    STOCK_COLOR_RED,
    # Delivery Stats Labels
    DELIVERY_LABEL_ACTIVE,
    DELIVERY_LABEL_INACTIVE,
    DELIVERY_COLOR_ACTIVE,
    DELIVERY_COLOR_INACTIVE,
    # Section Names
    SECTION_DASHBOARD,
    SECTION_ORDERS,
    SECTION_PRODUCTS,
    SECTION_USERS,
    SECTION_CONFIG,
    SECTION_IMPORT,
    # Context Keys
    CONTEXT_SECTION,
    CONTEXT_STATS,
    CONTEXT_URLS,
    CONTEXT_ACTION_BUTTONS,
    CONTEXT_RECENT_ORDERS,
    CONTEXT_RECENT_PRODUCTS,
    CONTEXT_RECENT_DELIVERIES,
    CONTEXT_ACTIVE_DELIVERIES,
    CONTEXT_LOW_STOCK_PRODUCTS,
    CONTEXT_TOP_PRODUCTS,
    CONTEXT_FINANCIAL_STATS,
    CONTEXT_FINANCIAL_ITEMS,
    CONTEXT_SALES_CHART_DATA,
    CONTEXT_DAILY_REVENUE_CHART_DATA,
    CONTEXT_ORDERS_STATUS_DATA,
    CONTEXT_ORDERS_TREND_DATA,
    CONTEXT_STOCK_DISTRIBUTION,
    CONTEXT_STOCK_STATS_LIST,
    CONTEXT_DELIVERY_STATS,
    CONTEXT_DELIVERY_STATS_LIST,
    CONTEXT_PENDING_ORDERS,
    CONTEXT_ORDERS_ON_THE_WAY,
    CONTEXT_QUICK_ACCESS_BUTTONS,
    CONTEXT_IMPORT_BUTTONS,
    # Numeric Constants
    DAYS_FOR_TREND,
    # Currency Display
    CURRENCY_PREFIX,
    # Common Strings
    STRING_ACTIVE,
    STRING_PRODUCTS,
    STRING_COLLECTIONS,
    # Report Types
    REPORT_TYPE_FINANCIAL,
    REPORT_TYPE_PRODUCTS,
    REPORT_TYPE_DELIVERY,
    REPORT_TYPE_ORDERS,
)

from apps.core.url_names import (
    BACKOFFICE_REPORT_GENERATOR,
    BACKOFFICE_IMPORTERS_DASHBOARD,
    ORDERS_LIST,
    ORDERS_CREATE,
    PRODUCTS_LIST,
    PRODUCTS_CREATE,
    PRODUCTS_SIZE_LIST,
    PRODUCTS_CATEGORY_LIST,
    PRODUCTS_COLOR_LIST,
    PRODUCTS_IMAGE_LIST,
    PRODUCTS_SIZE_IMPORT,
    PRODUCTS_COLOR_IMPORT,
    PRODUCTS_CATEGORY_IMPORT,
    PRODUCTS_COLLECTION_LIST,
    USERS_LIST,
    USERS_CREATE,
    USERS_GROUP_LIST,
    USERS_TRASHCAN,
    CORE_HERO_LIST,
    CORE_HERO_TRASHCAN,
    CORE_GALLERY_PHOTO_LIST,
    CORE_GALLERY_PHOTO_TRASHCAN,
    CORE_GALLERY_LAYOUT_LIST,
)


# =============================================================================
# BASE DASHBOARD VIEW
# =============================================================================

class BaseDashboardView(StaffPermissionRequiredMixin, TemplateView):
    """Vista base para dashboards del backoffice."""
    permission_required = 'products.view_product'


# =============================================================================
# DASHBOARD PRINCIPAL
# =============================================================================

class AdminDashboardView(BaseDashboardView):
    """Dashboard principal del administrador con métricas financieras y de órdenes."""
    template_name = TEMPLATE_ADMIN_DASHBOARD

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        month, year = today.month, today.year
        week_ago = today - timedelta(days=DAYS_FOR_TREND)

        # Métricas principales
        pending_orders = Order.objects.filter(status=ORDER_STATUS_PENDING).count()
        today_orders = Order.objects.filter(created_at__date=today).count()
        month_revenue = sum_order_amount(year=year, month=month)
        active_deliveries = User.objects.filter(is_delivery=True, is_active=True).count()

        # Métricas financieras
        today_revenue = sum_order_amount(date_start=today, date_end=today)
        week_revenue = sum_order_amount(date_start=week_ago, date_end=today)
        year_revenue = sum_order_amount(year=year)

        total_paid = Order.objects.filter(status__in=PAID_ORDER_STATUSES).count()
        avg_order = (month_revenue / total_paid) if total_paid > 0 else 0.0
        
        total_items = OrderItem.objects.filter(
            order__status__in=PAID_ORDER_STATUSES
        ).aggregate(total=Sum('quantity'))['total'] or 0
        avg_items = (total_items / total_paid) if total_paid > 0 else 0.0

        # Datos para gráficos
        categories, sales_data = get_daily_data(days=DAYS_FOR_TREND)
        if sum(sales_data) == 0:
            sales_data = [0] * DAYS_FOR_TREND
        _, daily_rev_data = get_daily_data(days=DAYS_FOR_TREND)

        # Items financieros para el dashboard
        financial_items = self._build_financial_items(
            avg_order=avg_order,
            avg_items=avg_items,
            week_revenue=week_revenue,
            total_paid=total_paid,
            today_revenue=today_revenue,
            year=year,
            year_revenue=year_revenue
        )

        reports_url = reverse(BACKOFFICE_REPORT_GENERATOR)
        action_buttons = [{
            'url': reports_url,
            'icon': ICON_FILE_EXPORT,
            'title': LABEL_EXPORT_REPORTS,
            'description': BTN_DESC_FINANCIAL_REPORTS,
            'gradient_from': GRADIENT_BLUE_FROM,
            'gradient_to': GRADIENT_BLUE_TO,
            'badge': BADGE_NEW
        }]

        context.update({
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
        })
        return context

    def _build_financial_items(
        self,
        avg_order: float,
        avg_items: float,
        week_revenue: float,
        total_paid: int,
        today_revenue: float,
        year: int,
        year_revenue: float
    ) -> List[Dict[str, Any]]:
        """Construye la lista de items financieros para evitar duplicación."""
        return [
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


class AdminOrdersDashboardView(BaseDashboardView):
    """Dashboard de gestión de órdenes."""
    template_name = TEMPLATE_ADMIN_ORDERS_DASHBOARD

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        stats = get_order_status_counts()
        stats['total'] = sum(stats.values())
        recent_orders = get_recent_orders()
        categories, order_counts = get_daily_order_counts()

        orders_url = reverse(ORDERS_LIST)
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
                'url': reverse(ORDERS_CREATE),
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

        context.update({
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
        })
        return context


class AdminProductsDashboardView(BaseDashboardView):
    """Dashboard de gestión de productos."""
    template_name = TEMPLATE_ADMIN_PRODUCTS_DASHBOARD

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        stats = get_product_stats()
        recent_products = get_recent_products()
        low_stock_products = get_low_stock_products()
        top_products = get_top_products()

        products_url = reverse(PRODUCTS_LIST)
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
                'url': reverse(PRODUCTS_CREATE),
                'icon': ICON_PLUS_CIRCLE,
                'title': BTN_TITLE_CREATE_PRODUCT,
                'description': BTN_DESC_CREATE_PRODUCT,
                'gradient_from': GRADIENT_GREEN_FROM,
                'gradient_to': GRADIENT_GREEN_TO,
                'badge': BADGE_NEW
            },
            {
                'url': reverse(PRODUCTS_COLLECTION_LIST),
                'icon': ICON_TABLE_LIST,
                'title': BTN_TITLE_MANAGE_COLLECTIONS,
                'description': BTN_DESC_MANAGE_COLLECTIONS,
                'gradient_from': GRADIENT_GREEN_FROM,
                'gradient_to': GRADIENT_GREEN_TO,
                'badge': f"{stats['total']} {STRING_COLLECTIONS}"
            },
            {
                'url': reverse(BACKOFFICE_IMPORTERS_DASHBOARD),
                'icon': ICON_FILE_EXPORT,
                'title': LABEL_EXPORT_IMPORTS,
                'description': BTN_DESC_IMPORT_PRODUCTS,
                'gradient_from': GRADIENT_BLUE_FROM,
                'gradient_to': GRADIENT_BLUE_TO,
                'badge': BADGE_COMING_SOON
            },
        ]

        quick_access_buttons = self._build_quick_access_buttons()

        stock_distribution = {
            'series': [stats['in_stock'], stats['low_stock'], stats['out_of_stock']],
            'labels': [STOCK_LABEL_IN_STOCK, STOCK_LABEL_LOW_STOCK, STOCK_LABEL_OUT_OF_STOCK],
        }
        stock_stats_list = [
            {'label': STOCK_LABEL_IN_STOCK, 'value': stats['in_stock'], 'color': STOCK_COLOR_GREEN},
            {'label': STOCK_LABEL_LOW_STOCK, 'value': stats['low_stock'], 'color': STOCK_COLOR_YELLOW},
            {'label': STOCK_LABEL_OUT_OF_STOCK, 'value': stats['out_of_stock'], 'color': STOCK_COLOR_RED},
        ]

        context.update({
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
        })
        return context

    def _build_quick_access_buttons(self) -> List[Dict[str, Any]]:
        """Construye botones de acceso rápido para productos."""
        return [
            {
                'url': reverse(PRODUCTS_SIZE_LIST),
                'icon': ICON_RULER,
                'title': BTN_TITLE_SIZES,
                'bg_from': ICON_BG_BLUE_50,
                'bg_to': ICON_BG_BLUE_100,
                'icon_color': ICON_COLOR_BLUE_600,
                'badge': str(Size.objects.count()),
            },
            {
                'url': reverse(PRODUCTS_CATEGORY_LIST),
                'icon': ICON_TAGS,
                'title': BTN_TITLE_CATEGORIES,
                'bg_from': ICON_BG_GREEN_50,
                'bg_to': ICON_BG_GREEN_100,
                'icon_color': ICON_COLOR_GREEN_600,
                'badge': str(Category.objects.count()),
            },
            {
                'url': reverse(PRODUCTS_COLOR_LIST),
                'icon': ICON_PALETTE,
                'title': BTN_TITLE_COLORS,
                'bg_from': ICON_BG_PURPLE_50,
                'bg_to': ICON_BG_PURPLE_100,
                'icon_color': ICON_COLOR_PURPLE_600,
                'badge': str(Color.objects.count()),
            },
            {
                'url': reverse(PRODUCTS_IMAGE_LIST),
                'icon': ICON_IMAGES,
                'title': BTN_TITLE_IMAGES,
                'bg_from': ICON_BG_ORANGE,
                'bg_to': ICON_BG_ORANGE_100,
                'icon_color': ICON_COLOR_ORANGE_600,
                'badge': str(ProductImage.objects.count()),
            },
            {
                'url': reverse(PRODUCTS_LIST),
                'icon': ICON_BOX,
                'title': BTN_TITLE_PRODUCTS,
                'bg_from': f'{ICON_COLOR_ACCENT}/10',
                'bg_to': f'{ICON_COLOR_ACCENT}/20',
                'icon_color': ICON_COLOR_ACCENT,
                'badge': BADGE_PRIMARY,
            },
        ]


class AdminUsersDashboardView(BaseDashboardView):
    """Dashboard de gestión de usuarios (foco en delivery)."""
    template_name = TEMPLATE_ADMIN_USERS_DASHBOARD

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        delivery_stats = get_delivery_stats()
        order_stats = get_delivery_order_stats()
        recent_deliveries = get_recent_deliveries()
        active_deliveries = get_active_deliveries_list()

        users_url = reverse(USERS_LIST)
        urls = {
            'users_list': users_url,
            'total': users_url,
            'active': users_url + QUERY_IS_ACTIVE.format(QUERY_VALUE_ACTIVE),
            'inactive': users_url + QUERY_IS_ACTIVE.format(QUERY_VALUE_INACTIVE),
            'only_deliveries': users_url + QUERY_IS_DELIVERY.format(QUERY_VALUE_ACTIVE),
            'ready_orders': reverse(ORDERS_LIST) + QUERY_STATUS.format(ORDER_STATUS_READY),
            'on_the_way_orders': reverse(ORDERS_LIST) + QUERY_STATUS.format(ORDER_STATUS_ON_THE_WAY),
            'delivered_today' : reverse(ORDERS_LIST) + QUERY_STATUS.format(ORDER_STATUS_DELIVERED),
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
                'url': reverse(USERS_CREATE),
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

        quick_access_buttons = self._build_quick_access_buttons(delivery_stats)

        delivery_stats_list = [
            {'label': DELIVERY_LABEL_ACTIVE, 'value': delivery_stats['active'], 'color': DELIVERY_COLOR_ACTIVE},
            {'label': DELIVERY_LABEL_INACTIVE, 'value': delivery_stats['inactive'], 'color': DELIVERY_COLOR_INACTIVE},
        ]

        categories, order_counts = get_daily_order_counts()

        context.update({
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
        })
        return context

    def _build_quick_access_buttons(self, delivery_stats: Dict[str, int]) -> List[Dict[str, Any]]:
        """Construye botones de acceso rápido para usuarios."""
        return [
            {
                'url': reverse(USERS_LIST),
                'icon': ICON_USERS,
                'title': BTN_TITLE_USERS,
                'bg_from': ICON_BG_GRAY_50,
                'bg_to': ICON_BG_GRAY_100,
                'icon_color': ICON_COLOR_GRAY_600,
                'badge': str(delivery_stats['total']),
            },
            {
                'url': reverse(USERS_GROUP_LIST),
                'icon': ICON_KEY,
                'title': BTN_TITLE_ROLES,
                'bg_from': ICON_BG_AMBER_50,
                'bg_to': ICON_BG_AMBER_100,
                'icon_color': ICON_COLOR_AMBER_600,
                'badge': str(Group.objects.count()),
            },
            {
                'url': reverse(USERS_TRASHCAN),
                'icon': ICON_TRASH_ALT,
                'title': BTN_TITLE_TRASHCAN,
                'bg_from': ICON_BG_RED_50,
                'bg_to': ICON_BG_RED_100,
                'icon_color': ICON_COLOR_RED,
                'badge': str(User.objects.filter(is_active=False).count()),
            },
        ]


class AdminConfigView(BaseDashboardView):
    """Vista de configuración del administrador."""
    template_name = TEMPLATE_ADMIN_CONFIG

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        quick_access_buttons = [
            {
                'url': reverse(CORE_HERO_LIST),
                'icon': ICON_IMAGES,
                'title': BTN_TITLE_HERO_SLIDES,
                'bg_from': ICON_BG_PURPLE_50,
                'bg_to': ICON_BG_PURPLE_100,
                'icon_color': ICON_COLOR_PURPLE_600,
                'badge': BADGE_PLUS,
            },
            {
                'url': reverse(CORE_GALLERY_PHOTO_LIST),
                'icon': ICON_IMAGES,
                'title': 'Galería de Fotos',
                'bg_from': ICON_BG_ORANGE,
                'bg_to': ICON_BG_ORANGE_100,
                'icon_color': ICON_COLOR_ORANGE_600,
                'badge': BADGE_PLUS,
            },
            {
                'url': reverse(CORE_GALLERY_LAYOUT_LIST),
                'icon': ICON_IMAGES,
                'title': 'Layouts de Galería',
                'bg_from': ICON_BG_BLUE_50,
                'bg_to': ICON_BG_BLUE_100,
                'icon_color': ICON_COLOR_BLUE_600,
                'badge': BADGE_PLUS,
            },
            {
                'url': reverse(CORE_HERO_TRASHCAN),
                'icon': ICON_TRASH_ALT,
                'title': BTN_TITLE_TRASHCAN,
                'bg_from': ICON_BG_RED_50,
                'bg_to': ICON_BG_RED_100,
                'icon_color': ICON_COLOR_RED,
                'badge': BADGE_TRASH,
            },
            {
                'url': reverse(CORE_GALLERY_PHOTO_TRASHCAN),
                'icon': ICON_TRASH_ALT,
                'title': 'Papelera de Galería',
                'bg_from': ICON_BG_RED_50,
                'bg_to': ICON_BG_RED_100,
                'icon_color': ICON_COLOR_RED,
                'badge': BADGE_TRASH,
            },
        ]
        context[CONTEXT_SECTION] = SECTION_CONFIG
        context[CONTEXT_QUICK_ACCESS_BUTTONS] = quick_access_buttons
        return context


class ReportGeneratorView(StaffPermissionRequiredMixin, FormView):
    """Vista para generación de reportes PDF."""
    template_name = TEMPLATE_REPORT_GENERATOR
    form_class = ReportForm
    permission_required = 'backoffice.generate_report'

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
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
            report_class = reports.get(report_type)
            if report_class is None:
                messages.error(request, 'Tipo de reporte inválido.')
                return redirect('backoffice:dashboard')
            report = report_class(request, **params)
            return report.render_pdf()
        return self.form_invalid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class ImportersDashboardView(StaffPermissionRequiredMixin, TemplateView):
    """Dashboard de importación de datos."""
    template_name = TEMPLATE_IMPORTERS_DASHBOARD
    permission_required = 'backoffice.import_data'

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        import_buttons = [
            {
                'url': reverse(PRODUCTS_SIZE_IMPORT),
                'icon': ICON_RULER,
                'title': BTN_TITLE_SIZES,
                'bg_from': ICON_BG_BLUE_50,
                'bg_to': ICON_BG_BLUE_100,
                'icon_color': ICON_COLOR_BLUE_600,
                'badge': BADGE_CSV_EXCEL
            },
            {
                'url': reverse(PRODUCTS_COLOR_IMPORT),
                'icon': ICON_PALETTE,
                'title': BTN_TITLE_COLORS,
                'bg_from': ICON_BG_PURPLE_50,
                'bg_to': ICON_BG_PURPLE_100,
                'icon_color': ICON_COLOR_PURPLE_600,
                'badge': BADGE_CSV_EXCEL
            },
            {
                'url': reverse(PRODUCTS_CATEGORY_IMPORT),
                'icon': ICON_TAGS,
                'title': BTN_TITLE_CATEGORIES,
                'bg_from': ICON_BG_GREEN_50,
                'bg_to': ICON_BG_GREEN_100,
                'icon_color': ICON_COLOR_GREEN_600,
                'badge': BADGE_CSV_EXCEL
            },
        ]
        context[CONTEXT_SECTION] = SECTION_IMPORT
        context[CONTEXT_IMPORT_BUTTONS] = import_buttons
        return context