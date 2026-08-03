# Status Strings
STATUS_PUBLISHED = 'publicada'
STATUS_DRAFT = 'borrador'
STATUS_ARCHIVED = 'archivada'

# Status Filter Choices
STATUS_FILTER_ACTIVE = 'activas'
STATUS_FILTER_UPCOMING = 'proximas'
STATUS_FILTER_ARCHIVED = 'archivadas'

STATUS_FILTER_CHOICES = [
    (STATUS_FILTER_ACTIVE, 'Activas'),
    (STATUS_FILTER_UPCOMING, 'Próximas'),
    (STATUS_FILTER_ARCHIVED, 'Archivadas'),
]

# Active/Inactive Filter Values
ACTIVE_FILTER_VALUE = 'true'
INACTIVE_FILTER_VALUE = 'false'

# Collection Filters
COLLECTION_FILTER_STATUS = STATUS_PUBLISHED
COLLECTION_ORDER = '-created_at'

# Product Filters
PRODUCT_FILTER_ACTIVE = True
PRODUCT_LIMIT_RELATED = 4

# Stock Thresholds
STOCK_LOW_THRESHOLD = 10
STOCK_ZERO = 0

# Order By
ORDER_BY_CREATED_AT = '-created_at'
ORDER_BY_SORT_ORDER = 'sort_order'
ORDER_BY_DELETED_AT = '-deleted_at'

# Order Choices
ORDER_CHOICE_RECENT = ('-created_at', 'Más recientes')
ORDER_CHOICE_OLDEST = ('created_at', 'Más antiguas')
ORDER_CHOICE_NAME_ASC = ('name', 'Nombre A-Z')
ORDER_CHOICE_NAME_DESC = ('-name', 'Nombre Z-A')
ORDER_CHOICE_PRICE_DESC = ('-price', 'Precio: mayor a menor')
ORDER_CHOICE_PRICE_ASC = ('price', 'Precio: menor a mayor')
ORDER_CHOICE_START_DATE_DESC = ('-start_date', 'Fecha inicio (reciente)')
ORDER_CHOICE_START_DATE_ASC = ('start_date', 'Fecha inicio (antigua)')

ORDER_CHOICES_CATALOG = [
    ORDER_CHOICE_RECENT,
    ORDER_CHOICE_OLDEST,
    ORDER_CHOICE_NAME_ASC,
    ORDER_CHOICE_NAME_DESC,
    ORDER_CHOICE_PRICE_DESC,
    ORDER_CHOICE_PRICE_ASC,
]

ORDER_CHOICES_COLLECTIONS = [
    ORDER_CHOICE_RECENT,
    ORDER_CHOICE_OLDEST,
    ORDER_CHOICE_NAME_ASC,
    ORDER_CHOICE_NAME_DESC,
    ORDER_CHOICE_START_DATE_DESC,
    ORDER_CHOICE_START_DATE_ASC,
]

# Pagination
PAGINATE_BY_DEFAULT = 20
PAGINATE_BY_COLLECTIONS = 9

# Date Formats
DATE_FORMAT_DISPLAY = '%d/%m/%Y %H:%M'
DATE_FORMAT_DAY_MONTH_YEAR = '%d/%m/%Y'

# Template Paths
TEMPLATE_STOCK_DASHBOARD = 'products/stock_dashboard.html'
TEMPLATE_CATALOG = 'products/catalog.html'
TEMPLATE_COLLECTIONS_LIST_PUBLIC = 'products/collections_list.html'
TEMPLATE_COLLECTION_INTERACTIVE = 'products/collection_interactive.html'
TEMPLATE_PRODUCT_DETAIL = 'products/product_detail.html'

# Backoffice Templates
TEMPLATE_SIZE_LIST = 'backoffice/size/size_list.html'
TEMPLATE_SIZE_FORM = 'backoffice/size/size_form.html'
TEMPLATE_SIZE_CONFIRM_DELETE = 'backoffice/size/size_confirm_delete.html'
TEMPLATE_SIZE_IMPORT = 'backoffice/size/size_import.html'
TEMPLATE_SIZE_IMPORT_RESULT = 'backoffice/size/size_import_result.html'

TEMPLATE_CATEGORY_LIST = 'backoffice/category/category_list.html'
TEMPLATE_CATEGORY_FORM = 'backoffice/category/category_form.html'
TEMPLATE_CATEGORY_CONFIRM_DELETE = 'backoffice/category/category_confirm_delete.html'
TEMPLATE_CATEGORY_IMPORT = 'backoffice/category/category_import.html'
TEMPLATE_CATEGORY_IMPORT_RESULT = 'backoffice/category/category_import_result.html'

TEMPLATE_COLOR_LIST = 'backoffice/color/color_list.html'
TEMPLATE_COLOR_FORM = 'backoffice/color/color_form.html'
TEMPLATE_COLOR_CONFIRM_DELETE = 'backoffice/color/color_confirm_delete.html'
TEMPLATE_COLOR_IMPORT = 'backoffice/color/color_import.html'
TEMPLATE_COLOR_IMPORT_RESULT = 'backoffice/color/color_import_result.html'

TEMPLATE_PRODUCTIMAGE_LIST = 'backoffice/productimage/productimage_list.html'
TEMPLATE_PRODUCTIMAGE_FORM = 'backoffice/productimage/productimage_form.html'
TEMPLATE_PRODUCTIMAGE_CONFIRM_DELETE = 'backoffice/productimage/productimage_confirm_delete.html'

TEMPLATE_PRODUCT_LIST = 'backoffice/product/product_list.html'
TEMPLATE_PRODUCT_FORM = 'backoffice/product/product_form.html'
TEMPLATE_PRODUCT_CONFIRM_DELETE = 'backoffice/product/product_confirm_delete.html'
TEMPLATE_PRODUCT_RESTORE = 'backoffice/product/product_restore.html'
TEMPLATE_PRODUCT_TRASHCAN = 'backoffice/product/product_trashcan.html'

TEMPLATE_PRODUCTCOLOR_FORM = 'backoffice/productcolor/productcolor_form.html'
TEMPLATE_PRODUCTCOLOR_CONFIRM_DELETE = 'backoffice/productcolor/productcolor_confirm_delete.html'

TEMPLATE_PRODUCTVARIANT_FORM = 'backoffice/productvariant/productvariant_form.html'
TEMPLATE_PRODUCTVARIANT_CONFIRM_DELETE = 'backoffice/productvariant/productvariant_confirm_delete.html'
TEMPLATE_PRODUCTVARIANT_RESTORE = 'backoffice/productvariant/productvariant_restore.html'
TEMPLATE_PRODUCTVARIANT_TRASHCAN = 'backoffice/productvariant/productvariant_trashcan.html'

TEMPLATE_COLLECTIONS_LIST = 'backoffice/collection/collection_list.html'
TEMPLATE_COLLECTION_FORM = 'backoffice/collection/collection_form.html'
TEMPLATE_COLLECTION_CONFIRM_DELETE = 'backoffice/collection/collection_confirm_delete.html'
TEMPLATE_COLLECTION_RESTORE = 'backoffice/collection/collection_restore.html'
TEMPLATE_COLLECTION_TRASHCAN = 'backoffice/collection/collection_trashcan.html'
TEMPLATE_COLLECTION_ZONE_EDITOR = 'backoffice/collection/collection_zone_editor.html'

# Form Context Keys
CONTEXT_CANCEL_URL = 'cancel_url'
CONTEXT_CANCEL_ARGS = 'cancel_args'
CONTEXT_TITLE = 'title'
CONTEXT_IS_CREATE = 'is_create'
CONTEXT_IS_UPDATE = 'is_update'
CONTEXT_OBJECT_NAME = 'object_name'
CONTEXT_OBJECT_DISPLAY = 'object_display'
CONTEXT_IMAGE_PREVIEW = 'image_preview'
CONTEXT_PRODUCT = 'product'
CONTEXT_PRODUCTS = 'products'
CONTEXT_PRODUCT_COLORS = 'product_colors'
CONTEXT_VARIANTS = 'variants'

# Table Headers
HEADER_NAME = 'Nombre'
HEADER_SLUG = 'Slug'
HEADER_ORDER = 'Orden'
HEADER_CODE = 'Código'
HEADER_IMAGE = 'Imagen'
HEADER_ALT_TEXT = 'Texto alternativo'
HEADER_UPLOADED = 'Subida'
HEADER_CATEGORY = 'Categoría'
HEADER_PRICE = 'Precio'
HEADER_TYPE = 'Tipo'
HEADER_STATUS = 'Estado'
HEADER_DELETED_AT = 'Eliminado el'
HEADER_COVER_IMAGE = 'Portada'
HEADER_PRODUCT_COUNT = 'Productos'
HEADER_PRICE_RANGE = 'Rango de precios'
HEADER_DATES = 'Fechas'

# Table Header Lists
HEADERS_SIZE = [HEADER_NAME, HEADER_ORDER]
HEADERS_CATEGORY = [HEADER_NAME, HEADER_SLUG, HEADER_ORDER]
HEADERS_COLOR = [HEADER_NAME, HEADER_CODE, HEADER_ORDER]
HEADERS_PRODUCT_IMAGE = [HEADER_IMAGE, HEADER_ALT_TEXT, HEADER_UPLOADED]
HEADERS_PRODUCT = [HEADER_IMAGE, HEADER_NAME, HEADER_CATEGORY, HEADER_PRICE, HEADER_TYPE, HEADER_STATUS]
HEADERS_PRODUCT_TRASHCAN = [HEADER_NAME, HEADER_CATEGORY, HEADER_PRICE, HEADER_DELETED_AT]
HEADERS_COLLECTION = [HEADER_NAME, HEADER_COVER_IMAGE, HEADER_PRODUCT_COUNT, HEADER_PRICE_RANGE, HEADER_DATES]

# Product Types
PRODUCT_TYPE_FABRICA = 'fabrica'
PRODUCT_TYPE_COLECCION_LIMITADA = 'coleccion_limitada'
PRODUCT_TYPES_DISPLAY = {
    PRODUCT_TYPE_FABRICA: 'Producto de fábrica',
    PRODUCT_TYPE_COLECCION_LIMITADA: 'Colección limitada',
}

# Stock Display Messages
STOCK_MESSAGE_OUT_OF_STOCK = 'Agotado'
STOCK_MESSAGE_LOW_STOCK = '¡Últimas {stock} unidades!'
STOCK_MESSAGE_AVAILABLE = 'Disponible'

# Stock Display Classes
STOCK_CLASS_OUT_OF_STOCK = 'out_of_stock'
STOCK_CLASS_LOW_STOCK = 'low_stock'
STOCK_CLASS_AVAILABLE = 'available'

# Status Badge Classes
BADGE_CLASS_ACTIVE = 'bg-green-100 text-green-700'
BADGE_CLASS_INACTIVE = 'bg-red-100 text-red-700'
BADGE_TEXT_ACTIVE = 'Activo'
BADGE_TEXT_INACTIVE = 'Inactivo'

# Filter Configuration
FILTER_CONFIG_DEFAULT = {
    'status': False,
    'price': True,
    'product_count': False,
    'date': False,
    'product_type': True,
}

FILTER_CONFIG_WITH_STATUS = {
    'status': True,
    'price': True,
    'product_count': True,
    'date': True,
    'product_type': True,
}

# Filter Labels
FILTER_LABEL_STATUS = 'Estado'
FILTER_LABEL_CATEGORY = 'Categoría'
FILTER_LABEL_TYPE = 'Tipo'
FILTER_LABEL_PRICE = 'Precio'

# Filter Names
FILTER_NAME = 'name'
FILTER_CATEGORY = 'category'
FILTER_PRODUCT_TYPE = 'product_type'
FILTER_IS_ACTIVE = 'is_active'

# Query Parameters
QUERY_PARAM_CATEGORY = 'category'
QUERY_PARAM_SEARCH = 'search'
QUERY_PARAM_STATUS = 'status'
QUERY_PARAM_MIN_PRICE = 'min_price'
QUERY_PARAM_MAX_PRICE = 'max_price'
QUERY_PARAM_PRODUCT_COUNT_MIN = 'product_count_min'
QUERY_PARAM_PRODUCT_COUNT_MAX = 'product_count_max'
QUERY_PARAM_DATE_FILTER = 'date_filter'
QUERY_PARAM_PRODUCT_TYPE = 'product_type'
QUERY_PARAM_ORDER_BY = 'order_by'

# Date Filter Options
DATE_FILTER_LAST_MONTH = 'ultimo_mes'
DATE_FILTER_LAST_QUARTER = 'ultimo_trimestre'
DATE_FILTER_LAST_SEMESTER = 'ultimo_semestre'
DATE_FILTER_LAST_YEAR = 'ultimo_anio'
DATE_FILTER_UPCOMING = 'proximas'

# Import Form Field Names
IMPORT_FILE_FIELD = 'file'
IMPORT_UPDATE_EXISTING_FIELD = 'update_existing'

# Import Template Columns
IMPORT_TEMPLATE_COLUMNS_SIZE = ['name']
IMPORT_TEMPLATE_COLUMNS_COLOR = ['name', 'code']
IMPORT_TEMPLATE_COLUMNS_CATEGORY = ['name']

# Import Messages
MSG_IMPORT_NO_FILE = 'Por favor selecciona un archivo.'

# UI Text Strings
UI_NO_IMAGE = 'Sin imagen'
UI_STATUS_LABEL = 'Estado'
UI_PLACEHOLDER_SEARCH_PRODUCT = 'Buscar producto...'

# Icon HTML
ICON_IMAGE_PLACEHOLDER = (
    '<div class="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center text-gray-400">'
    '<i class="fas fa-image"></i>'
    '</div>'
)

# Success Messages
MSG_SIZE_CREATED = 'Talla "{name}" creada exitosamente.'
MSG_SIZE_UPDATED = 'Talla "{name}" actualizada exitosamente.'
MSG_SIZE_DELETED = 'Talla "{name}" eliminada exitosamente.'

MSG_CATEGORY_CREATED = 'Categoría "{name}" creada exitosamente.'
MSG_CATEGORY_UPDATED = 'Categoría "{name}" actualizada exitosamente.'
MSG_CATEGORY_DELETED = 'Categoría "{name}" eliminada exitosamente.'

MSG_COLOR_CREATED = 'Color "{name}" creado exitosamente.'
MSG_COLOR_UPDATED = 'Color "{name}" actualizado exitosamente.'
MSG_COLOR_DELETED = 'Color "{name}" eliminado exitosamente.'

MSG_PRODUCT_IMAGE_UPLOADED = 'Imagen "{name}" subida exitosamente.'
MSG_PRODUCT_IMAGE_UPDATED = 'Texto alternativo de la imagen actualizado exitosamente.'
MSG_PRODUCT_IMAGE_DELETED = 'Imagen "{name}" eliminada exitosamente.'

MSG_PRODUCT_CREATED = 'Producto "{name}" creado exitosamente.'
MSG_PRODUCT_UPDATED = 'Producto "{name}" actualizado exitosamente.'
MSG_PRODUCT_DELETED = 'Producto "{name}" movido a la papelera.'
MSG_PRODUCT_RESTORED = 'Producto "{name}" restaurado exitosamente.'

MSG_PRODUCT_COLOR_UPDATED = 'Color "{name}" actualizado correctamente.'
MSG_PRODUCT_COLOR_DELETED = 'Color "{name}" eliminado correctamente.'

MSG_VARIANT_CREATED = 'Variante "{variant}" agregada.'
MSG_VARIANT_UPDATED = 'Variante actualizada correctamente.'
MSG_VARIANT_DELETED = 'Variante desactivada correctamente.'
MSG_VARIANT_RESTORED = 'Variante restaurada correctamente.'
MSG_VARIANT_RESTORE_ERROR = 'Error al restaurar la variante.'

MSG_COLLECTION_CREATED = 'Colección "{name}" creada exitosamente.'
MSG_COLLECTION_UPDATED = 'Colección "{name}" actualizada exitosamente.'
MSG_COLLECTION_DELETED = 'Colección "{name}" movida a la papelera.'
MSG_COLLECTION_RESTORED = 'Colección "{name}" restaurada exitosamente.'

# Import Template Filenames
IMPORT_TEMPLATE_FILENAME_SIZE = 'plantilla_tallas.csv'
IMPORT_TEMPLATE_FILENAME_COLOR = 'plantilla_colores.csv'
IMPORT_TEMPLATE_FILENAME_CATEGORY = 'plantilla_categorias.csv'

# Import Example Data
IMPORT_EXAMPLE_DATA_SIZE = [['XS'], ['S'], ['M'], ['L'], ['XL']]
IMPORT_EXAMPLE_DATA_COLOR = [
    ['Negro', '#000000'],
    ['Blanco', '#FFFFFF'],
    ['Rojo', '#FF0000'],
    ['Azul', '#0000FF'],
    ['Verde', '#00FF00'],
]
IMPORT_EXAMPLE_DATA_CATEGORY = [
    ['Camisetas'],
    ['Hoodies'],
    ['Pantalones'],
    ['Accesorios'],
    ['Chaquetas'],
]

# Perms
PERM_COLLECTION_VIEW = 'products.view_collection'
PERM_COLLECTION_ADD = 'products.add_collection'
PERM_COLLECTION_CHANGE = 'products.change_collection'
PERM_COLLECTION_DELETE = 'products.delete_collection'