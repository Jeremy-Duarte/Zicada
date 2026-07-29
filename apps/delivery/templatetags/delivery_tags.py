from django import template

register = template.Library()

STATUS_COLORS = {
    'listo': {'bg': 'bg-yellow-100', 'text': 'text-yellow-800', 'dot': 'text-yellow-500'},
    'en_camino': {'bg': 'bg-blue-100', 'text': 'text-blue-800', 'dot': 'text-blue-500'},
    'entregado': {'bg': 'bg-green-100', 'text': 'text-green-800', 'dot': 'text-green-500'},
    'cancelado': {'bg': 'bg-red-100', 'text': 'text-red-800', 'dot': 'text-red-500'},
}

PAYMENT_COLORS = {
    'pending': {'bg': 'bg-yellow-100', 'text': 'text-yellow-800'},
    'paid': {'bg': 'bg-green-100', 'text': 'text-green-800'},
    'online': {'bg': 'bg-blue-100', 'text': 'text-blue-800'},
}


@register.filter
def delivery_status_color(status):
    """Return color palette dict for a delivery status."""
    if not status:
        return {'bg': 'bg-gray-100', 'text': 'text-gray-800', 'dot': 'text-gray-500'}
    key = str(status).lower().replace(' ', '_')
    return STATUS_COLORS.get(key, {'bg': 'bg-gray-100', 'text': 'text-gray-800', 'dot': 'text-gray-500'})


@register.filter
def delivery_payment_color(payment_status):
    """Return color palette dict for a payment status."""
    if not payment_status:
        return {'bg': 'bg-gray-100', 'text': 'text-gray-800'}
    key = str(payment_status).lower().replace(' ', '_')
    return PAYMENT_COLORS.get(key, {'bg': 'bg-gray-100', 'text': 'text-gray-800'})
