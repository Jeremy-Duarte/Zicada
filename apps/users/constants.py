# Template Paths
TEMPLATE_USER_LIST = 'backoffice/users/user_list.html'
TEMPLATE_USER_FORM = 'backoffice/users/user_form.html'
TEMPLATE_USER_CHANGE_PASSWORD = 'backoffice/users/user_change_password.html'
TEMPLATE_USER_CONFIRM_DELETE = 'backoffice/users/user_confirm_delete.html'
TEMPLATE_USER_RESTORE = 'backoffice/users/user_restore.html'
TEMPLATE_USER_TRASHCAN = 'backoffice/users/user_trashcan.html'
TEMPLATE_USER_PROFILE = 'backoffice/profile.html'
TEMPLATE_USER_PROFILE_EDIT = 'backoffice/profile_edit.html'
TEMPLATE_USER_PROFILE_PASSWORD = 'backoffice/profile_password.html'
TEMPLATE_GROUP_LIST = 'backoffice/groups/group_list.html'
TEMPLATE_GROUP_FORM = 'backoffice/groups/group_form.html'
TEMPLATE_GROUP_DETAIL = 'backoffice/groups/group_detail.html'
TEMPLATE_GROUP_CONFIRM_DELETE = 'backoffice/groups/group_confirm_delete.html'

# Context Keys
CONTEXT_CANCEL_URL = 'cancel_url'
CONTEXT_CANCEL_ARGS = 'cancel_args'
CONTEXT_TITLE = 'title'
CONTEXT_SHOW_PASSWORD_CHANGE = 'show_password_change'
CONTEXT_USER_OBJ = 'user_obj'
CONTEXT_USERS = 'users'
CONTEXT_GROUP = 'group'
CONTEXT_GROUPS = 'groups'
CONTEXT_USER_COUNT = 'user_count'
CONTEXT_ROWS = 'rows'
CONTEXT_HEADERS = 'headers'

# Table Headers
HEADER_USERNAME = 'Usuario'
HEADER_FULL_NAME = 'Nombre'
HEADER_EMAIL = 'Email'
HEADER_PHONE = 'Teléfono'
HEADER_USER_TYPE = 'Tipo'
HEADER_STATUS = 'Estado'
HEADER_REGISTRATION = 'Registro'
HEADER_GROUP_NAME = 'Nombre del rol'
HEADER_ASSIGNED_USERS = 'Usuarios asignados'

# Table Header Lists
HEADERS_USER_LIST = [HEADER_USERNAME, HEADER_FULL_NAME, HEADER_EMAIL, HEADER_PHONE, HEADER_USER_TYPE, HEADER_STATUS, HEADER_REGISTRATION]
HEADERS_USER_TRASHCAN = [HEADER_USERNAME, HEADER_FULL_NAME, HEADER_EMAIL, HEADER_PHONE, HEADER_REGISTRATION]
HEADERS_GROUP_LIST = [HEADER_GROUP_NAME, HEADER_ASSIGNED_USERS]

# Filter Names
FILTER_USERNAME = 'username'
FILTER_FIRST_NAME = 'first_name'
FILTER_LAST_NAME = 'last_name'
FILTER_EMAIL = 'email'
FILTER_IS_DELIVERY = 'is_delivery'
FILTER_IS_ACTIVE = 'is_active'
FILTER_GROUP_NAME = 'name'

# Order By
ORDER_BY_USERNAME_DESC = '-username'

# Query Parameters
QUERY_PARAM_SEARCH = 'search'

# User Types
USER_TYPE_SUPERUSER = 'superuser'
USER_TYPE_STAFF = 'staff'
USER_TYPE_DELIVERY = 'delivery'
USER_TYPE_CUSTOMER = 'customer'

# User Type Badges
USER_TYPE_BADGES = {
    USER_TYPE_SUPERUSER: ('Superadmin', 'bg-purple-100 text-purple-700'),
    USER_TYPE_STAFF: ('Staff', 'bg-blue-100 text-blue-700'),
    USER_TYPE_DELIVERY: ('Entregador', 'bg-orange-100 text-orange-700'),
    USER_TYPE_CUSTOMER: ('Sin Rol', 'bg-gray-100 text-gray-700'),
}

# Status Badges
STATUS_ACTIVE_BADGE = ('Activo', 'bg-green-100 text-green-700')
STATUS_INACTIVE_BADGE = ('Inactivo', 'bg-red-100 text-red-700')

# Date Format
DATE_FORMAT_DISPLAY = '%d/%m/%Y'

# Pagination
PAGINATE_BY_DEFAULT = 20

# Form Context Values
CONTEXT_IS_CREATE = 'is_create'
CONTEXT_IS_UPDATE = 'is_update'

# Title Templates
TITLE_USER_CREATE = 'Crear usuario'
TITLE_USER_UPDATE = 'Editar usuario: {username}'
TITLE_GROUP_CREATE = 'Crear rol'
TITLE_GROUP_UPDATE = 'Editar rol: {name}'

# Success Messages
MSG_USER_CREATED = 'Usuario "{username}" creado exitosamente.'
MSG_USER_UPDATED = 'Usuario "{username}" actualizado exitosamente.'
MSG_USER_DELETED = 'Usuario "{username}" desactivado exitosamente.'
MSG_USER_RESTORED = 'Usuario "{username}" reactivado exitosamente.'
MSG_USER_ALREADY_ACTIVE = 'El usuario "{username}" ya está activo.'
MSG_PASSWORD_CHANGED = 'Contraseña de "{username}" actualizada exitosamente.'
MSG_GROUP_CREATED = 'Rol "{name}" creado exitosamente.'
MSG_GROUP_UPDATED = 'Rol "{name}" actualizado exitosamente.'
MSG_GROUP_DELETED = 'Rol "{name}" eliminado exitosamente.'
MSG_PROFILE_UPDATED = 'Tu perfil ha sido actualizado exitosamente.'
MSG_PASSWORD_UPDATED = 'Tu contraseña ha sido actualizada exitosamente.'

# Error Messages
ERROR_USER_CREATE = 'Error al crear el usuario. Corrige los errores.'
ERROR_USER_UPDATE = 'Error al actualizar el usuario.'
ERROR_USER_DELETE = 'Error al desactivar el usuario.'
ERROR_USER_RESTORE = 'Error al reactivar el usuario.'
ERROR_PASSWORD_CHANGE = 'Error al cambiar la contraseña.'
ERROR_GROUP_DELETE = 'Error al eliminar el rol.'
ERROR_SELF_DELETE = 'No puedes desactivar tu propio usuario.'
ERROR_PASSWORD_UPDATE = 'Error al actualizar la contraseña. Verifica los datos.'

# HTML Templates
STATUS_BADGE_TEMPLATE = '<span class="px-2 py-1 text-xs rounded-full {badge_class}">{badge_text}</span>'

# Default values
DEFAULT_EMPTY_VALUE = '—'

# Perms
PERM_USER_VIEW = 'users.view_user'
PERM_USER_ADD = 'users.add_user'
PERM_USER_CHANGE = 'users.change_user'
PERM_USER_DELETE = 'users.delete_user'

PERM_GROUP_VIEW = 'auth.view_group'
PERM_GROUP_ADD = 'auth.add_group'
PERM_GROUP_CHANGE = 'auth.change_group'
PERM_GROUP_DELETE = 'auth.delete_group'