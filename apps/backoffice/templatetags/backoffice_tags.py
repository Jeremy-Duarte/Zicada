from django import template

register = template.Library()

STATUS_COLORS = {
    'activo': ('bg-green-100', 'text-green-800'),
    'inactivo': ('bg-gray-100', 'text-gray-800'),
    'pendiente': ('bg-yellow-100', 'text-yellow-800'),
    'completado': ('bg-green-100', 'text-green-800'),
    'entregado': ('bg-green-100', 'text-green-800'),
    'cancelado': ('bg-red-100', 'text-red-800'),
    'en_camino': ('bg-blue-100', 'text-blue-800'),
    'listo': ('bg-yellow-100', 'text-yellow-800'),
    'procesando': ('bg-blue-100', 'text-blue-800'),
}


@register.filter
def backoffice_status_color(status):
    """Return tuple of (bg_class, text_class) for a given status."""
    if not status:
        return ('bg-gray-100', 'text-gray-800')
    key = str(status).lower().replace(' ', '_')
    return STATUS_COLORS.get(key, ('bg-gray-100', 'text-gray-800'))
