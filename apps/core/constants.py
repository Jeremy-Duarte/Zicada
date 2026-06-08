# Collection Statuses
COLLECTION_STATUS_PUBLISHED = 'publicada'
COLLECTION_STATUS_DRAFT = 'borrador'
COLLECTION_STATUS_ARCHIVED = 'archivado'

# Template Paths
TEMPLATE_HOME = 'home.html'
TEMPLATE_ABOUT = 'about.html'
TEMPLATE_CONTACT = 'contact.html'
TEMPLATE_RETURNS = 'returns_policy.html'
TEMPLATE_PRIVACY = 'privacy_policy.html'
TEMPLATE_TERMS = 'terms.html'
TEMPLATE_STAFF_LOGIN = 'core/staff_login.html'
TEMPLATE_CONTACT_SUCCESS = 'core/contact_success.html'
TEMPLATE_HERO_FORM = 'backoffice/hero/hero_form.html'
TEMPLATE_HERO_LIST = 'backoffice/hero/hero_list.html'
TEMPLATE_HERO_CONFIRM_DELETE = 'backoffice/hero/hero_confirm_delete.html'
TEMPLATE_HERO_RESTORE = 'backoffice/hero/hero_restore.html'
TEMPLATE_HERO_TRASHCAN = 'backoffice/hero/hero_trashcan.html'

# Email Configuration
EMAIL_SUBJECT_PREFIX = '[Contacto Zicada] '
EMAIL_USER_SUBJECT = 'Hemos recibido tu mensaje - Zicada'

# Contact Form Field Names
CONTACT_FIELD_NAME = 'name'
CONTACT_FIELD_EMAIL = 'email'
CONTACT_FIELD_PHONE = 'phone'
CONTACT_FIELD_SUBJECT = 'subject'
CONTACT_FIELD_MESSAGE = 'message'

# Contact Messages
CONTACT_SUCCESS_MESSAGE = '¡Mensaje enviado con éxito! Te responderemos pronto.'
CONTACT_ERROR_MESSAGE = 'Error al enviar el mensaje. Por favor intenta de nuevo.'

# URL Names
URL_HOME = 'home'

# Login/Logout Messages
LOGIN_ERROR_MESSAGE = 'Usuario o contraseña incorrectos'
LOGOUT_SUCCESS_MESSAGE = 'Sesión cerrada correctamente'
LOGIN_WELCOME_MESSAGE = 'Bienvenido {username}'

# Status Labels
STATUS_ACTIVE_LABEL = 'Activo'
STATUS_INACTIVE_LABEL = 'Inactivo'

# Badge CSS Classes
BADGE_ACTIVE_CSS = 'bg-green-100 text-green-700'
BADGE_INACTIVE_CSS = 'bg-red-100 text-red-700'

# Hero Section Messages
MSG_HERO_CREATED = 'Slide "{title}" creado exitosamente.'
MSG_HERO_UPDATED = 'Slide "{title}" actualizado exitosamente.'
MSG_HERO_DELETED = 'Slide "{title}" movido a la papelera.'
MSG_HERO_RESTORED = 'Slide "{title}" restaurado exitosamente.'

# Hero Section Headers
HEADERS_HERO = ['Título', 'Orden', 'Estado']
HEADERS_HERO_TRASHCAN = ['Título', 'Subtítulo', 'Orden', 'Eliminado el']

# Hero Section Context Keys
CONTEXT_BACKGROUND_IMAGE_URL = 'background_image_url'
CONTEXT_ROWS = 'rows'
CONTEXT_HEADERS = 'headers'
CONTEXT_HERO_SLIDES = 'hero_slides'

# Hero Section Order By
HERO_ORDER_BY_SORT = 'sort_order'
HERO_ORDER_BY_DELETED_AT = '-deleted_at'

# Display Limits
FEATURED_COLLECTIONS_LIMIT = 3
LATEST_PRODUCTS_LIMIT = 8
FEATURED_CATEGORIES_LIMIT = 4

# PWA Manifest Configuration
PWA_NAME = "Zicada"
PWA_SHORT_NAME = "Zicada"
PWA_START_URL = "/"
PWA_DISPLAY = "standalone"
PWA_BACKGROUND_COLOR = "#ffffff"
PWA_THEME_COLOR = "#1a1a1a"

# Hero Section Object Names
HERO_OBJECT_NAME = 'Slide del Hero'