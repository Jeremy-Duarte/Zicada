from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def url_replace(context, key, value):
    """
    Reemplaza un parámetro en la URL actual.
    Uso: {% url_replace request 'category' category.slug %}
    """
    request = context.get('request')
    if not request:
        return ''
    
    params = request.GET.copy()
    if value:
        params[key] = value
    else:
        params.pop(key, None)
    
    return params.urlencode()

@register.filter
def get_item(dictionary, key):
    """Obtiene un valor de un diccionario por clave."""
    if not dictionary:
        return ''
    return dictionary.get(key, key)