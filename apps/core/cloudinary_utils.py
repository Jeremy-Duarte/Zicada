import re
from typing import Any
from urllib.parse import urlparse, urlunparse


CLOUDINARY_UPLOAD_SEGMENT = '/image/upload/'
TRANSFORMATION_SEPARATOR = ','

CLOUDINARY_KEY_MAP = {
    'quality': 'q',
    'fetch_format': 'f',
    'dpr': 'dpr',
    'fl': 'fl',
    'e': 'e',
    'width': 'w',
    'height': 'h',
    'crop': 'c',
}

# Default chain: auto format (WebP/AVIF), auto quality, auto DPR, progressive load, sharpen
DEFAULT_TRANSFORMS: dict[str, Any] = {
    'fetch_format': 'auto',
    'quality': 'auto',
    'dpr': 'auto',
    'fl': 'progressive',
    'e': 'sharpen:400',
}


def _cloudinary_key(key: str) -> str:
    """Convierte nombre amigable a parámetro de Cloudinary (ej: quality → q)."""
    return CLOUDINARY_KEY_MAP.get(key, key)


def build_transformation_string(
    width: int | None = None,
    height: int | None = None,
    crop: str | None = None,
    **extra: Any,
) -> str:
    """Construye el segmento de transformaciones de Cloudinary."""
    transforms: list[str] = []
    if width:
        transforms.append(f'w_{width}')
    if height:
        transforms.append(f'h_{height}')
    if crop:
        transforms.append(f'c_{crop}')
    for key, value in sorted(extra.items()):
        ckey = _cloudinary_key(key)
        transforms.append(f'{ckey}_{value}')
    return TRANSFORMATION_SEPARATOR.join(transforms)


def build_cloudinary_url(
    image_url: str,
    width: int | None = None,
    height: int | None = None,
    crop: str | None = None,
    **extra: Any,
) -> str:
    """Inserta transformaciones en una URL de Cloudinary."""
    if not image_url or CLOUDINARY_UPLOAD_SEGMENT not in image_url:
        return image_url

    transformation = build_transformation_string(
        width=width, height=height, crop=crop, **extra,
    )
    if not transformation:
        return image_url

    parsed = urlparse(image_url)
    prefix, rest = parsed.path.split(CLOUDINARY_UPLOAD_SEGMENT, 1)
    new_path = f'{prefix}{CLOUDINARY_UPLOAD_SEGMENT}{transformation}/{rest}'
    return urlunparse(parsed._replace(path=new_path))


def build_image_url(image_field, width: int | None = None, **transforms: Any) -> str:
    """Construye URL transformada con defaults cache-friendly para un ImageField."""
    if not image_field or not hasattr(image_field, 'url'):
        return ''
    merged = {**DEFAULT_TRANSFORMS, **transforms}
    if width:
        merged['width'] = width
    return build_cloudinary_url(image_field.url, **merged)


def get_thumbnail_url(image_field, width: int = 400, **transforms: Any) -> str:
    """Retorna URL de thumbnail cuadrado con recorte central."""
    merged = {**DEFAULT_TRANSFORMS, **transforms}
    return build_cloudinary_url(
        image_field.url,
        width=width,
        height=width,
        crop='fill',
        **merged,
    )


def get_srcset(image_field, sizes: list[int], **transforms: Any) -> str:
    """Genera atributo srcset con múltiples tamaños."""
    if not image_field or not hasattr(image_field, 'url'):
        return ''
    merged = {**DEFAULT_TRANSFORMS, **transforms}
    urls = [
        f'{build_cloudinary_url(image_field.url, width=size, **merged)} {size}w'
        for size in sizes
    ]
    return ', '.join(urls)


def get_default_image_url(image_field) -> str:
    """Retorna la URL por defecto del campo, o vacío si no existe."""
    if not image_field or not hasattr(image_field, 'url'):
        return ''
    return image_field.url
