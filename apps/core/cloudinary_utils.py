import re
from typing import Any
from urllib.parse import urlparse, urlunparse


CLOUDINARY_UPLOAD_SEGMENT = '/image/upload/'
TRANSFORMATION_SEPARATOR = ','


def is_cloudinary_url(url: str) -> bool:
    """Verifica si una URL proviene de Cloudinary."""
    return bool(url) and 'cloudinary.com' in url


def parse_cloudinary_public_id(url: str) -> str:
    """Extrae el public_id de una URL de Cloudinary sin version ni transformaciones."""
    if not is_cloudinary_url(url):
        return url
    parsed = urlparse(url)
    path = parsed.path
    if CLOUDINARY_UPLOAD_SEGMENT not in path:
        return url
    _, rest = path.split(CLOUDINARY_UPLOAD_SEGMENT, 1)
    # Eliminar version (v1234567890/) y extensiones
    rest = re.sub(r'^v\d+/', '', rest)
    return rest.rsplit('.', 1)[0]


def build_transformation_string(
    width: int | None = None,
    height: int | None = None,
    crop: str = 'limit',
    quality: str = 'auto',
    fetch_format: str = 'auto',
    **extra: Any,
) -> str:
    """Construye el segmento de transformaciones de Cloudinary."""
    transforms = []
    if width:
        transforms.append(f'w_{width}')
    if height:
        transforms.append(f'h_{height}')
    if crop:
        transforms.append(f'c_{crop}')
    if quality:
        transforms.append(f'q_{quality}')
    if fetch_format:
        transforms.append(f'f_{fetch_format}')
    for key, value in sorted(extra.items()):
        transforms.append(f'{key}_{value}')
    return TRANSFORMATION_SEPARATOR.join(transforms)


def build_cloudinary_url(
    image_url: str,
    width: int | None = None,
    height: int | None = None,
    crop: str = 'limit',
    quality: str = 'auto',
    fetch_format: str = 'auto',
    **extra: Any,
) -> str:
    """
    Inserta transformaciones en una URL de Cloudinary.
    Si la URL no es de Cloudinary, retorna la URL original.
    """
    if not is_cloudinary_url(image_url):
        return image_url

    transformation = build_transformation_string(
        width=width,
        height=height,
        crop=crop,
        quality=quality,
        fetch_format=fetch_format,
        **extra,
    )
    if not transformation:
        return image_url

    parsed = urlparse(image_url)
    path = parsed.path
    if CLOUDINARY_UPLOAD_SEGMENT not in path:
        return image_url

    prefix, rest = path.split(CLOUDINARY_UPLOAD_SEGMENT, 1)
    new_path = f'{prefix}{CLOUDINARY_UPLOAD_SEGMENT}{transformation}/{rest}'
    return urlunparse(parsed._replace(path=new_path))


def build_image_url(image_field, width: int | None = None, **transforms: Any) -> str:
    """Construye URL transformada para un campo ImageField."""
    if not image_field or not hasattr(image_field, 'url'):
        return ''
    url = image_field.url
    if not is_cloudinary_url(url):
        return url
    return build_cloudinary_url(url, width=width, **transforms)


def get_thumbnail_url(image_field, width: int = 400, **transforms: Any) -> str:
    """Retorna URL de thumbnail cuadrado con recorte."""
    return build_image_url(
        image_field,
        width=width,
        height=width,
        crop='fill',
        **transforms,
    )


def get_srcset(image_field, sizes: list[int], **transforms: Any) -> str:
    """Genera atributo srcset con múltiples tamaños."""
    if not image_field or not hasattr(image_field, 'url'):
        return ''
    urls = [
        f'{build_image_url(image_field, width=size, **transforms)} {size}w'
        for size in sizes
    ]
    return ', '.join(urls)


def get_default_image_url(image_field) -> str:
    """Retorna la URL por defecto del campo, o vacío si no existe."""
    if not image_field or not hasattr(image_field, 'url'):
        return ''
    return image_field.url
