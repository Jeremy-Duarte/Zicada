from decimal import Decimal
DEFAULT_SHIPPING_COST = Decimal(10000)
CART_EXPIRATION_DAYS = 7
MAX_QUANTITY_PER_ITEM = 99
FREE_SHIPPING_THRESHOLD = Decimal(150000)

# Order statuses
STATUS_PENDING = 'pendiente'
STATUS_CONFIRMED = 'confirmado'
STATUS_PREPARING = 'preparando'
STATUS_READY = 'listo'
STATUS_ON_THE_WAY = 'en_camino'
STATUS_DELIVERED = 'entregado'
STATUS_CANCELLED = 'cancelado'

# Status progression
STATUS_PROGRESSION = [
    STATUS_PENDING, STATUS_CONFIRMED, STATUS_PREPARING,
    STATUS_READY, STATUS_ON_THE_WAY, STATUS_DELIVERED
]

# Status badge mapping
STATUS_BADGE_MAP = {
    STATUS_PENDING: ('Pendiente', 'bg-yellow-100 text-yellow-700'),
    STATUS_CONFIRMED: ('Confirmado', 'bg-blue-100 text-blue-700'),
    STATUS_PREPARING: ('Preparando', 'bg-purple-100 text-purple-700'),
    STATUS_READY: ('Listo', 'bg-indigo-100 text-indigo-700'),
    STATUS_ON_THE_WAY: ('En camino', 'bg-orange-100 text-orange-700'),
    STATUS_DELIVERED: ('Entregado', 'bg-green-100 text-green-700'),
}
STATUS_BADGE_DEFAULT = ('Cancelado', 'bg-red-100 text-red-700')

# Stock thresholds
LOW_STOCK_THRESHOLD = 5

# Pagination
PAGINATE_BY_DEFAULT = 20

# Query parameters
QUERY_PARAM_SEARCH = 'search'

# Template paths
TEMPLATE_DELIVERY_DASHBOARD = 'orders/delivery_dashboard.html'
TEMPLATE_CART_DETAIL = 'orders/cart_detail.html'
TEMPLATE_CHECKOUT = 'orders/checkout.html'
TEMPLATE_ORDER_CONFIRMATION = 'orders/order_confirmation.html'
TEMPLATE_TRACKING = 'orders/tracking.html'
TEMPLATE_ORDER_LIST = 'backoffice/orders/order_list.html'
TEMPLATE_ORDER_FORM = 'backoffice/orders/order_form.html'
TEMPLATE_ORDER_DETAIL = 'backoffice/orders/order_detail.html'
TEMPLATE_ORDER_CONFIRM = 'backoffice/orders/order_confirm.html'
TEMPLATE_ORDER_CANCEL = 'backoffice/orders/order_cancel.html'
TEMPLATE_ORDER_ASSIGN_DELIVERY = 'backoffice/orders/order_assign_delivery.html'
TEMPLATE_ORDER_MARK_DELIVERED = 'backoffice/orders/order_mark_delivered.html'
TEMPLATE_ORDER_ITEM_FORM = 'backoffice/orders/orderitem_form.html'
TEMPLATE_ORDER_ITEM_CONFIRM_DELETE = 'backoffice/orders/orderitem_confirm_delete.html'

# Messages
MESSAGE_CART_EMPTY = 'Tu carrito está vacío. Agrega productos antes de continuar.'
MESSAGE_CART_CLEARED = 'Carrito vaciado correctamente'
MESSAGE_ORDER_NOT_FOUND = 'Pedido no encontrado.'
MESSAGE_PAYMENT_PROCESSING = 'Tu pago está siendo procesado. Se actualizará automáticamente en breve.'
MESSAGE_NO_SHIPPING_DATA = 'No se encontraron datos de envío. Por favor, vuelve a intentarlo.'
MESSAGE_STOCK_INSUFFICIENT = 'stock insuficiente'

# Error messages
MSG_INVALID_DATA = '❌ Datos inválidos'
MSG_QUANTITY_MIN = '❌ La cantidad debe ser al menos 1'
MSG_QUANTITY_MAX = '⚠️ No puedes agregar más de {max_quantity} unidades del mismo producto'
MSG_PRODUCT_UNAVAILABLE = 'no está disponible actualmente'
MSG_OUT_OF_STOCK = 'está agotado'
MSG_INSUFFICIENT_STOCK = '⚠️ Stock insuficiente para "{product}" ({size}, {color}). Disponible: {stock}.'
MSG_PRODUCT_NOT_FOUND = '❌ El producto no existe o no está disponible'
MSG_CART_ALREADY_EMPTY = '🛒 El carrito ya está vacío'
MSG_PRODUCT_REMOVED_WARNING = '⚠️ Este producto ya no está disponible. Se eliminó de tu carrito.'
MSG_UPDATE_ERROR = '❌ Error al actualizar la cantidad'
MSG_REMOVE_ERROR = '❌ Error al eliminar el producto'
MSG_ADD_ERROR = '❌ Error al agregar el producto. Intenta de nuevo'

# Stock status strings
STOCK_STATUS_OUT_OF_STOCK = 'out_of_stock'
STOCK_STATUS_LOW_STOCK = 'low_stock'
STOCK_STATUS_AVAILABLE = 'available'
STOCK_STATUS_UNAVAILABLE = 'unavailable'

# Stripe product data templates
STRIPE_PRODUCT_NAME_TEMPLATE = 'Pedido Zicada - {customer_name}'
STRIPE_PRODUCT_DESCRIPTION_TEMPLATE = '{total_items} productos'

# Context keys
CONTEXT_ORDER = 'order'
CONTEXT_ITEMS = 'items'
CONTEXT_CANCEL_URL = 'cancel_url'
CONTEXT_CANCEL_ARGS = 'cancel_args'
CONTEXT_TITLE = 'title'
CONTEXT_ROWS = 'rows'
CONTEXT_HEADERS = 'headers'
CONTEXT_SHOW_ACTIONS = 'show_actions'
CONTEXT_EDIT_URL_NAME = 'edit_url_name'
CONTEXT_STATUS_CHOICES = 'status_choices'
CONTEXT_DELIVERY_USERS = 'delivery_users'
CONTEXT_CAN_ASSIGN = 'can_assign'
CONTEXT_CAN_ADD_ITEMS = 'can_add_items'
CONTEXT_ITEMS_ROWS = 'items_rows'
CONTEXT_ITEMS_HEADERS = 'items_headers'

# Table headers
HEADERS_ORDER_LIST = ['Pedido', 'Cliente', 'Total', 'Estado', 'Fecha']
HEADERS_ORDER_ITEMS = ['Producto', 'Talla', 'Cantidad', 'Precio unit.', 'Subtotal']

# Allowed statuses for adding items
ALLOWED_ADD_ITEMS_STATUSES = [STATUS_PENDING, STATUS_CONFIRMED]

# Date format
DATE_FORMAT_DISPLAY = '%d/%m/%Y %H:%M'

# Perms
PERM_ORDER_VIEW = 'orders.view_order'
PERM_ORDER_ADD = 'orders.add_order'
PERM_ORDER_CHANGE = 'orders.change_order'