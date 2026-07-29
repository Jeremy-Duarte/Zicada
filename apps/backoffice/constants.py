
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
LABEL_EXPORT_IMPORTS = 'Importaciones de modelos'

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
BTN_TITLE_MANAGE_COLLECTIONS = 'Gestionar Colecciones'

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
BTN_DESC_MANAGE_ORDERS = 'Ver, filtrar y gestionar todos los pedidos'
BTN_DESC_MANAGE_COLLECTIONS = 'Planear, Crear una Colección de productos'
BTN_DESC_IMPORT_PRODUCTS = 'Importa categorias, colores o tallas'

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
DATE_FORMAT_DAY_MONTH_YEAR_HOUR_MINUTES = '%d/%m/%Y %H:%M'

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
STRING_COLLECTIONS = 'colecciones'

# Report Types
REPORT_TYPE_FINANCIAL = 'financial'
REPORT_TYPE_PRODUCTS = 'products'
REPORT_TYPE_DELIVERY = 'delivery'
REPORT_TYPE_ORDERS = 'orders'