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
LOGIN_INACTIVE_MESSAGE = "Esta cuenta está inactiva. Por favor, contacta al administrador."

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

# Gallery Section Order By
GALLERY_ORDER_BY_SORT = 'sort_order'
GALLERY_ORDER_BY_DELETED_AT = '-deleted_at'

# Display Limits
FEATURED_COLLECTIONS_LIMIT = 3
LATEST_PRODUCTS_LIMIT = 8
FEATURED_CATEGORIES_LIMIT = 4
HOME_PROMOS_LIMIT = 3

# PWA Manifest Configuration
PWA_NAME = "Zicada"
PWA_SHORT_NAME = "Zicada"
PWA_START_URL = "/"
PWA_DISPLAY = "standalone"
PWA_BACKGROUND_COLOR = "#ffffff"
PWA_THEME_COLOR = "#1a1a1a"

# Hero Section Object Names
HERO_OBJECT_NAME = 'Slide del Hero'

# Gallery Section Messages
MSG_GALLERY_PHOTO_CREATED = 'Foto "{title}" creada exitosamente.'
MSG_GALLERY_PHOTO_UPDATED = 'Foto "{title}" actualizada exitosamente.'
MSG_GALLERY_PHOTO_DELETED = 'Foto "{title}" movida a la papelera.'
MSG_GALLERY_PHOTO_RESTORED = 'Foto "{title}" restaurada exitosamente.'
MSG_GALLERY_LAYOUT_CREATED = 'Layout "{name}" creado exitosamente.'
MSG_GALLERY_LAYOUT_UPDATED = 'Layout "{name}" actualizado exitosamente.'
MSG_GALLERY_LAYOUT_DELETED = 'Layout "{name}" eliminado.'

# Gallery Section Headers
HEADERS_GALLERY_PHOTO = ['Foto', 'Título', 'Layout', 'Orden', 'Estado']
HEADERS_GALLERY_PHOTO_TRASHCAN = ['Título', 'Layout', 'Orden', 'Eliminado el']
HEADERS_GALLERY_LAYOUT = ['Nombre', 'Columnas', 'Filas', 'Capacidad', 'Orden', 'Estado']

# Gallery Section Object Names
GALLERY_PHOTO_OBJECT_NAME = 'Foto de Galería'
GALLERY_LAYOUT_OBJECT_NAME = 'Layout de Galería'

# Gallery Section Context Keys
CONTEXT_GALLERY_PHOTOS = 'gallery_photos'
CONTEXT_GALLERY_LAYOUTS = 'gallery_layouts'

# Gallery Template Paths
TEMPLATE_GALLERY_PAGE = 'core/gallery_page.html'
TEMPLATE_GALLERY_PHOTO_FORM = 'backoffice/gallery/photo_form.html'
TEMPLATE_GALLERY_PHOTO_LIST = 'backoffice/gallery/photo_list.html'
TEMPLATE_GALLERY_PHOTO_CONFIRM_DELETE = 'backoffice/gallery/photo_confirm_delete.html'
TEMPLATE_GALLERY_PHOTO_RESTORE = 'backoffice/gallery/photo_restore.html'
TEMPLATE_GALLERY_PHOTO_TRASHCAN = 'backoffice/gallery/photo_trashcan.html'
TEMPLATE_GALLERY_LAYOUT_FORM = 'backoffice/gallery/layout_form.html'
TEMPLATE_GALLERY_LAYOUT_LIST = 'backoffice/gallery/layout_list.html'
TEMPLATE_GALLERY_LAYOUT_CONFIRM_DELETE = 'backoffice/gallery/layout_confirm_delete.html'

# Password Reset Templates
TEMPLATE_PASSWORD_RESET_FORM = 'core/registration/password_reset_form.html'
TEMPLATE_PASSWORD_RESET_DONE = 'core/registration/password_reset_done.html'
TEMPLATE_PASSWORD_RESET_CONFIRM = 'core/registration/password_reset_confirm.html'
TEMPLATE_PASSWORD_RESET_COMPLETE = 'core/registration/password_reset_complete.html'
TEMPLATE_PASSWORD_RESET_EMAIL = 'core/registration/password_reset_email.html'