from django.urls import reverse, resolve
from apps.orders.cart import Cart
from apps.products.models import Product, Collection, Category

def cart_context(request):
    cart = Cart(request)
    return {
        'cart_total_items': cart.get_total_items(),
    }

def breadcrumbs(request):
    """Context processor para breadcrumbs usando rutas nombradas."""
    path = request.path
    breadcrumbs = [{'name': 'Inicio', 'url': reverse('home')}]
    
    try:
        resolver = resolve(path)
        view_name = resolver.view_name
        kwargs = resolver.kwargs
    except:
        view_name = None
        kwargs = {}
    
    # ========== PRODUCTOS ==========
    
    # Catálogo
    if view_name == 'products:catalog':
        breadcrumbs.append({'name': 'Catálogo', 'url': None})
        
        category_slug = request.GET.get('category')
        if category_slug:
            try:
                category = Category.objects.filter(slug=category_slug).first()
                if category:
                    breadcrumbs = [
                        {'name': 'Inicio', 'url': reverse('home')},
                        {'name': 'Catálogo', 'url': reverse('products:catalog')},
                        {'name': category.name, 'url': None}
                    ]
            except:
                pass
    
    # Detalle de producto
    elif view_name == 'products:product_detail':
        slug = kwargs.get('slug')
        if slug:
            try:
                product = Product.objects.select_related('category').get(slug=slug, is_active=True)
                category_url = f"{reverse('products:catalog')}?category={product.category.slug}"
                breadcrumbs = [
                    {'name': 'Inicio', 'url': reverse('home')},
                    {'name': 'Catálogo', 'url': reverse('products:catalog')},
                    {'name': product.category.name, 'url': category_url},
                    {'name': product.name, 'url': None}
                ]
            except Product.DoesNotExist:
                breadcrumbs.append({'name': 'Producto', 'url': None})
    
    # Lista de colecciones
    elif view_name == 'products:collections_list':
        breadcrumbs.append({'name': 'Colecciones', 'url': None})
    
    # Detalle de colección
    elif view_name == 'products:collection_detail':
        slug = kwargs.get('slug')
        if slug:
            try:
                collection = Collection.objects.get(slug=slug, is_active=True)
                breadcrumbs = [
                    {'name': 'Inicio', 'url': reverse('home')},
                    {'name': 'Colecciones', 'url': reverse('products:collections_list')},
                    {'name': collection.name, 'url': None}
                ]
            except Collection.DoesNotExist:
                breadcrumbs.append({'name': 'Colección', 'url': None})
    
    # Stock dashboard
    elif view_name == 'products:stock_dashboard':
        breadcrumbs.append({'name': 'Dashboard de stock', 'url': None})
    
    # ========== ÓRDENES ==========
    
    # Carrito
    elif view_name == 'orders:cart_detail':
        breadcrumbs.append({'name': 'Carrito de compras', 'url': None})
    
    # Checkout
    elif view_name == 'orders:checkout':
        breadcrumbs = [
            {'name': 'Inicio', 'url': reverse('home')},
            {'name': 'Carrito', 'url': reverse('orders:cart_detail')},
            {'name': 'Finalizar compra', 'url': None}
        ]
    
    # Confirmación de orden
    elif view_name == 'orders:order_confirmation':
        order_number = kwargs.get('order_number')
        breadcrumbs = [
            {'name': 'Inicio', 'url': reverse('home')},
            {'name': 'Carrito', 'url': reverse('orders:cart_detail')},
            {'name': 'Checkout', 'url': reverse('orders:checkout')},
            {'name': f'Orden #{order_number}' if order_number else 'Confirmación', 'url': None}
        ]
    
    # Tracking de orden
    elif view_name == 'orders:order_tracking':
        breadcrumbs = [
            {'name': 'Inicio', 'url': reverse('home')},
            {'name': 'Tracking de pedido', 'url': None}
        ]
    
    # ========== PÁGINAS ESTÁTICAS (CORE) ==========
    
    elif view_name == 'core:about':
        breadcrumbs.append({'name': 'Nosotros', 'url': None})
    
    elif view_name == 'core:contact':
        breadcrumbs.append({'name': 'Contacto', 'url': None})
    
    elif view_name == 'core:contact_success':
        breadcrumbs = [
            {'name': 'Inicio', 'url': reverse('home')},
            {'name': 'Contacto', 'url': reverse('core:contact')},
            {'name': 'Mensaje enviado', 'url': None}
        ]
    
    elif view_name == 'core:returns_policy':
        breadcrumbs.append({'name': 'Cambios y devoluciones', 'url': None})
    
    elif view_name == 'core:privacy_policy':
        breadcrumbs.append({'name': 'Política de privacidad', 'url': None})
    
    elif view_name == 'core:terms':
        breadcrumbs.append({'name': 'Términos y condiciones', 'url': None})
    
    elif view_name == 'core:staff_login':
        breadcrumbs.append({'name': 'Acceso staff', 'url': None})
    
    # ========== HOME ==========
    
    elif view_name == 'home' or path == '/':
        breadcrumbs = []
    
    return {'breadcrumbs': breadcrumbs}