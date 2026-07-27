from urllib.parse import urlencode

from django.urls import reverse, resolve
from django.urls.exceptions import Resolver404
from django.core.cache import cache
from apps.orders.cart import Cart
from apps.products.models import Product, Collection, Category

def cart_context(request):
    cart = Cart(request)
    return {
        'cart_total_items': cart.get_total_items(),
    }

# =============================================================================
# BASE BREADCRUMBS
# =============================================================================

def _get_home_breadcrumb() -> dict:
    return {'name': 'Inicio', 'url': reverse('home')}

def _get_catalog_breadcrumb() -> dict:
    return {'name': 'Catálogo', 'url': reverse('products:catalog')}

def _get_collections_breadcrumb() -> dict:
    return {'name': 'Colecciones', 'url': reverse('products:collections_list')}

def _get_cart_breadcrumb() -> dict:
    return {'name': 'Carrito', 'url': reverse('orders:cart_detail')}

def _get_checkout_breadcrumb() -> dict:
    return {'name': 'Finalizar compra', 'url': None}

def _get_contact_breadcrumb() -> dict:
    return {'name': 'Contacto', 'url': reverse('core:contact')}

def _build_simple_breadcrumb(page_name: str, parent: dict = None) -> list:
    breadcrumbs = [_get_home_breadcrumb()]
    if parent:
        breadcrumbs.append(parent)
    breadcrumbs.append({'name': page_name, 'url': None})
    return breadcrumbs


# =============================================================================
# PRODUCT BREADCRUMBS
# =============================================================================

def _build_catalog_breadcrumb(category_slug: str = None) -> list:
    if category_slug:
        cache_key = f'breadcrumb_cat_{category_slug}'
        category_name = cache.get(cache_key)
        if category_name is None:
            category = Category.objects.filter(slug=category_slug).first()
            category_name = category.name if category else None
            cache.set(cache_key, category_name, 300)
        if category_name:
            return [
                _get_home_breadcrumb(),
                _get_catalog_breadcrumb(),
                {'name': category_name, 'url': None},
            ]
    return [
        _get_home_breadcrumb(),
        _get_catalog_breadcrumb(),
    ]

def _build_product_detail_breadcrumb(slug: str) -> list:
    try:
        product = Product.objects.select_related('category').get(slug=slug, is_active=True)
        category_url = f"{reverse('products:catalog')}?{urlencode({'category': product.category.slug})}"
        return [
            _get_home_breadcrumb(),
            _get_catalog_breadcrumb(),
            {'name': product.category.name, 'url': category_url},
            {'name': product.name, 'url': None},
        ]
    except Product.DoesNotExist:
        return _build_simple_breadcrumb('Producto')

def _build_collection_detail_breadcrumb(slug: str) -> list:
    try:
        from apps.products.models import Collection
        collection = Collection.objects.get(slug=slug, is_active=True)
        return [
            _get_home_breadcrumb(),
            _get_collections_breadcrumb(),
            {'name': collection.name, 'url': None},
        ]
    except Collection.DoesNotExist:
        return _build_simple_breadcrumb('Colección')

def _build_product_breadcrumbs(request, view_name: str, kwargs: dict) -> list | None:
    if view_name == 'products:catalog':
        return _build_catalog_breadcrumb(request.GET.get('category'))
    if view_name == 'products:product_detail':
        return _build_product_detail_breadcrumb(kwargs.get('slug'))
    if view_name == 'products:collections_list':
        return _build_simple_breadcrumb('Colecciones')
    if view_name == 'products:collection_detail':
        return _build_collection_detail_breadcrumb(kwargs.get('slug'))
    if view_name == 'products:stock_dashboard':
        return _build_simple_breadcrumb('Dashboard de stock')
    return None


# =============================================================================
# ORDER BREADCRUMBS
# =============================================================================

def _build_cart_breadcrumb() -> list:
    return _build_simple_breadcrumb('Carrito de compras')

def _build_checkout_breadcrumb() -> list:
    return [
        _get_home_breadcrumb(),
        _get_cart_breadcrumb(),
        _get_checkout_breadcrumb(),
    ]

def _build_order_confirmation_breadcrumb(order_number: str = None) -> list:
    order_text = f'Orden #{order_number}' if order_number else 'Confirmación'
    return [
        _get_home_breadcrumb(),
        _get_cart_breadcrumb(),
        _get_checkout_breadcrumb(),
        {'name': order_text, 'url': None},
    ]

def _build_tracking_breadcrumb() -> list:
    return _build_simple_breadcrumb('Tracking de pedido')

def _build_order_breadcrumbs(view_name: str, kwargs: dict) -> list | None:
    if view_name == 'orders:cart_detail':
        return _build_cart_breadcrumb()
    if view_name == 'orders:checkout':
        return _build_checkout_breadcrumb()
    if view_name == 'orders:order_confirmation':
        return _build_order_confirmation_breadcrumb(kwargs.get('order_number'))
    if view_name == 'orders:order_tracking':
        return _build_tracking_breadcrumb()
    return None


# =============================================================================
# CORE BREADCRUMBS
# =============================================================================

CORE_PAGES_MAPPING = {
    'core:about': 'Nosotros',
    'core:contact': 'Contacto',
    'core:returns_policy': 'Cambios y devoluciones',
    'core:privacy_policy': 'Política de privacidad',
    'core:terms': 'Términos y condiciones',
    'core:staff_login': 'Acceso staff',
}

def _build_core_breadcrumbs(view_name: str) -> list | None:
    if view_name in CORE_PAGES_MAPPING:
        return _build_simple_breadcrumb(CORE_PAGES_MAPPING[view_name])
    if view_name == 'core:contact_success':
        return [
            _get_home_breadcrumb(),
            _get_contact_breadcrumb(),
            {'name': 'Mensaje enviado', 'url': None},
        ]
    return None


# =============================================================================
# MAIN CONTEXT PROCESSOR
# =============================================================================

def breadcrumbs(request):
    path = request.path
    
    if path == '/':
        return {'breadcrumbs': []}
    
    try:
        resolver = resolve(path)
        view_name = resolver.view_name
        kwargs = resolver.kwargs
    except Resolver404:
        return {'breadcrumbs': _build_simple_breadcrumb('Inicio')}
    
    breadcrumbs_data = _build_product_breadcrumbs(request, view_name, kwargs)
    if breadcrumbs_data is not None:
        return {'breadcrumbs': breadcrumbs_data}
    
    breadcrumbs_data = _build_order_breadcrumbs(view_name, kwargs)
    if breadcrumbs_data is not None:
        return {'breadcrumbs': breadcrumbs_data}
    
    breadcrumbs_data = _build_core_breadcrumbs(view_name)
    if breadcrumbs_data is not None:
        return {'breadcrumbs': breadcrumbs_data}
    
    return {'breadcrumbs': _build_simple_breadcrumb('Inicio')}


def is_home(request):
    return {'is_home': request.path == '/'}