from django import template

from apps.core.cloudinary_utils import (
    build_image_url,
    get_default_image_url,
    get_srcset,
    get_thumbnail_url,
)

register = template.Library()


@register.filter
def cloudinary_url(image_field, width: int = 600):
    """Genera URL de Cloudinary con ancho especificado."""
    return build_image_url(image_field, width=width)


@register.filter
def cloudinary_thumb(image_field, width: int = 400):
    """Genera URL de thumbnail cuadrado."""
    return get_thumbnail_url(image_field, width=width)


@register.filter
def cloudinary_srcset(image_field, sizes: str):
    """
    Genera atributo srcset desde una lista de tamaños separados por comas.
    Ejemplo: {{ photo.image|cloudinary_srcset:"400,800,1200" }}
    """
    try:
        size_list = [int(size.strip()) for size in sizes.split(',') if size.strip()]
    except ValueError:
        return ''
    return get_srcset(image_field, sizes=size_list)


@register.filter
def default_image_url(image_field):
    """Retorna la URL original de la imagen."""
    return get_default_image_url(image_field)


@register.filter
def gallery_photo_classes(photo):
    """Retorna las clases CSS de span de grid de una foto."""
    return photo.display_zone or 'col-span-1 row-span-1'


@register.filter
def is_external_url(url: str) -> bool:
    """Retorna True si la URL es externa (empieza con http)."""
    return bool(url) and url.strip().lower().startswith('http')
