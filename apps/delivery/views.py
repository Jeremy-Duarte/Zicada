from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe, require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
import json
from datetime import datetime, date, timedelta

# Importar url_names para mantener consistencia
from apps.core.url_names import (
    DELIVERY_LOGIN,
    DELIVERY_DASHBOARD,
    DELIVERY_ORDERS,
    DELIVERY_ORDER_DETAIL,
    DELIVERY_MARK_PAID,
    DELIVERY_REGISTER_INCIDENCE,
    DELIVERY_DAILY_SUMMARY,
    DELIVERY_CLOSE_JOURNEY,
    DELIVERY_API_ORDERS,
    DELIVERY_API_MARK_PAID,
    DELIVERY_API_CREATE_INCIDENCE,
    DELIVERY_LOGIN,
    DELIVERY_MANIFEST,
    DELIVERY_OFFLINE,
    DELIVERY_SERVICE_WORKER,
)

# =============================================================================
# PWA Y AUTENTICACIÓN
# =============================================================================

@never_cache
@require_safe
def pwa_manifest(request):
    """Genera manifest.json dinámico para la PWA de delivery."""
    protocol = 'https' if request.is_secure() else 'http'
    base_url = f"{protocol}://{request.get_host()}"
    
    icons = []
    for size, path in settings.PWA_ICONS.items():
        icons.append({
            "src": f"{base_url}/static/{path}",
            "sizes": f"{size}x{size}",
            "type": "image/png",
            "purpose": "any maskable"
        })
    
    manifest = {
        "name": settings.PWA_NAME,
        "short_name": settings.PWA_SHORT_NAME,
        "description": settings.PWA_DESCRIPTION,
        "start_url": reverse(DELIVERY_LOGIN),  # Usar reverse con url_name
        "display": settings.PWA_DISPLAY,
        "theme_color": settings.PWA_THEME_COLOR,
        "background_color": settings.PWA_BACKGROUND_COLOR,
        "orientation": settings.PWA_ORIENTATION,
        "scope": "/delivery/",
        "icons": icons,
        "categories": ["business", "productivity"],
        "lang": "es",
        "dir": "ltr",
        "shortcuts": [
            {
                "name": "Mis Pedidos",
                "short_name": "Pedidos",
                "description": "Ver pedidos asignados del día",
                "url": f"{base_url}{reverse(DELIVERY_ORDERS)}",
                "icons": [{
                    "src": f"{base_url}/static/delivery/icons/shortcut-orders.png",
                    "sizes": "96x96",
                    "type": "image/png"
                }]
            },
            {
                "name": "Resumen del Día",
                "short_name": "Resumen",
                "description": "Ver resumen de entregas",
                "url": f"{base_url}{reverse(DELIVERY_DAILY_SUMMARY)}",
                "icons": [{
                    "src": f"{base_url}/static/delivery/icons/shortcut-summary.png",
                    "sizes": "96x96",
                    "type": "image/png"
                }]
            }
        ]
    }
    
    return JsonResponse(manifest)

def delivery_login(request):
    """
    Login específico para la PWA de delivery.
    NO redirige a dashboard si ya está autenticado, 
    solo si es delivery y tiene sesión activa.
    """
    # Si ya está autenticado y es delivery, mostrar dashboard
    if request.user.is_authenticated:
        if getattr(request.user, 'is_delivery', False):
            return redirect(DELIVERY_DASHBOARD)
        else:
            # Si no es delivery, hacer logout y mostrar login
            from django.contrib.auth import logout
            logout(request)
            return render(request, 'delivery/login.html', {
                'error': 'Esta app es solo para repartidores. Usa la web principal.'
            })
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user and getattr(user, 'is_delivery', False) and user.is_active:
            auth_login(request, user)
            return redirect(DELIVERY_DASHBOARD)
        else:
            return render(request, 'delivery/login.html', {
                'error': 'Credenciales inválidas o no tienes permisos de entregador'
            })
    
    return render(request, 'delivery/login.html')

@login_required
def dashboard(request):
    """Dashboard principal del entregador."""
    # Verificar que es delivery, si no, logout y redirect a login
    if not getattr(request.user, 'is_delivery', False):
        from django.contrib.auth import logout
        logout(request)
        return redirect(DELIVERY_LOGIN)
    
    # Datos falsos para el dashboard
    context = {
        'user': request.user,
        'pwa_mode': True,
        'today_orders_count': 8,
        'completed_orders': 5,
        'pending_orders': 3,
        'today_earnings': 125000,
        'last_order': {
            'id': 1234,
            'customer': 'María González',
            'address': 'Calle 123 #45-67',
            'status': 'en_camino'
        },
        'orders_url': reverse(DELIVERY_ORDERS),
        'summary_url': reverse(DELIVERY_DAILY_SUMMARY),
        'logout_url': reverse(DELIVERY_LOGIN),
    }
    
    return render(request, 'delivery/dashboard.html', context)

@login_required
def offline_page(request):
    """Página offline para la PWA."""
    return render(request, 'delivery/offline.html', {
        'login_url': reverse(DELIVERY_LOGIN),
    })

def delivery_logout(request):
    """Cierra sesión del entregador y redirige al login."""
    from django.contrib.auth import logout
    logout(request)
    return redirect(DELIVERY_LOGIN)

# =============================================================================
# HU-033: CONSULTAR PEDIDOS DEL DÍA
# =============================================================================

@login_required
def delivery_orders(request):
    """Lista de pedidos asignados para hoy."""
    if not getattr(request.user, 'is_delivery', False):
        return redirect(DELIVERY_LOGIN)
    
    # Datos falsos de pedidos para probar
    fake_orders = [
        {
            'id': 1001,
            'order_number': 'ZCD-0001',
            'customer_name': 'María González',
            'customer_phone': '3001234567',
            'shipping_address': 'Calle 123 #45-67, Chapinero, Bogotá',
            'total_amount': 78500,
            'is_paid': False,
            'status': 'listo',
            'status_display': 'Listo para enviar',
            'delivery_notes': 'Llamar antes de llegar, timbre 3B',
            'created_at': timezone.now().isoformat(),
        },
        {
            'id': 1002,
            'order_number': 'ZCD-0002',
            'customer_name': 'Carlos Rodríguez',
            'customer_phone': '3109876543',
            'shipping_address': 'Carrera 89 #12-34, Usaquén, Bogotá',
            'total_amount': 125500,
            'is_paid': True,
            'status': 'en_camino',
            'status_display': 'En camino',
            'delivery_notes': 'Entregar en portería',
            'created_at': (timezone.now() - timedelta(hours=2)).isoformat(),
        },
        {
            'id': 1003,
            'order_number': 'ZCD-0003',
            'customer_name': 'Ana Martínez',
            'customer_phone': '3155555555',
            'shipping_address': 'Avenida Chile #85-23, Chía, Cundinamarca',
            'total_amount': 45000,
            'is_paid': False,
            'status': 'listo',
            'status_display': 'Listo para enviar',
            'delivery_notes': 'Edificio Azul, apto 502',
            'created_at': (timezone.now() - timedelta(hours=1)).isoformat(),
        },
        {
            'id': 1004,
            'order_number': 'ZCD-0004',
            'customer_name': 'Laura Sánchez',
            'customer_phone': '3123456789',
            'shipping_address': 'Calle 200 #15-30, Suba, Bogotá',
            'total_amount': 234000,
            'is_paid': True,
            'status': 'en_camino',
            'status_display': 'En camino',
            'delivery_notes': 'Casa de dos pisos, portón rojo',
            'created_at': (timezone.now() - timedelta(hours=3)).isoformat(),
        },
    ]
    
    # Filtrar pedidos según estado
    if request.GET.get('filter') == 'pending':
        fake_orders = [o for o in fake_orders if not o['is_paid']]
    elif request.GET.get('filter') == 'completed':
        fake_orders = [o for o in fake_orders if o['is_paid']]
    
    context = {
        'orders': fake_orders,
        'today': date.today(),
        'total_orders': len(fake_orders),
        'pending_payment': len([o for o in fake_orders if not o['is_paid']]),
        'filter': request.GET.get('filter', 'all'),
        # URLs
        'order_detail_url_name': DELIVERY_ORDER_DETAIL,
        'mark_paid_url_name': DELIVERY_MARK_PAID,
        'register_incidence_url_name': DELIVERY_REGISTER_INCIDENCE,
    }
    
    return render(request, 'delivery/orders/list.html', context)

@login_required
def order_detail(request, order_id):
    """Detalle de un pedido específico."""
    if not getattr(request.user, 'is_delivery', False):
        return redirect(DELIVERY_LOGIN)
    
    # Datos falsos para el detalle del pedido
    fake_order = {
        'id': order_id,
        'order_number': f'ZCD-{order_id:04d}',
        'customer_name': 'María González' if order_id == 1001 else 'Carlos Rodríguez',
        'customer_phone': '3001234567' if order_id == 1001 else '3109876543',
        'customer_email': f'cliente{order_id}@example.com',
        'shipping_address': 'Calle 123 #45-67, Chapinero, Bogotá',
        'delivery_notes': 'Llamar antes de llegar. Timbre 3B',
        'total_amount': 78500,
        'subtotal': 75000,
        'shipping_cost': 3500,
        'is_paid': order_id % 2 == 0,
        'status': 'listo' if order_id % 2 != 0 else 'en_camino',
        'status_display': 'Listo para enviar' if order_id % 2 != 0 else 'En camino',
        'payment_method': 'Efectivo contraentrega',
        'created_at': (timezone.now() - timedelta(hours=2)).isoformat(),
        'items': [
            {
                'product_name': 'Camiseta Deportiva',
                'size': 'M',
                'quantity': 2,
                'unit_price': 25000,
                'subtotal': 50000,
            },
            {
                'product_name': 'Short Deportivo',
                'size': 'L',
                'quantity': 1,
                'unit_price': 25000,
                'subtotal': 25000,
            }
        ]
    }
    
    context = {
        'order': fake_order,
        'order_id': order_id,
        # URLs
        'mark_paid_url': reverse(DELIVERY_MARK_PAID, args=[order_id]),
        'register_incidence_url': reverse(DELIVERY_REGISTER_INCIDENCE, args=[order_id]),
        'back_url': reverse(DELIVERY_ORDERS),
    }
    
    return render(request, 'delivery/orders/detail.html', context)


# =============================================================================
# HU-034: MARCAR PEDIDO COMO PAGADO
# =============================================================================

@login_required
@require_http_methods(["POST"])
def mark_as_paid(request, order_id):
    """Marca un pedido como pagado."""
    if not getattr(request.user, 'is_delivery', False):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    # Simulación de marcado como pagado
    context = {
        'success': True,
        'message': f'Pedido #{order_id} marcado como pagado exitosamente',
        'order_id': order_id,
        'paid_at': timezone.now().isoformat(),
    }
    
    messages.success(request, f'Pedido #{order_id} marcado como pagado')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(context)
    
    return redirect(DELIVERY_ORDER_DETAIL, order_id=order_id)


# =============================================================================
# HU-035: REGISTRAR INCIDENCIA
# =============================================================================

@login_required
def register_incidence(request, order_id):
    """Registra una incidencia en un pedido."""
    if not getattr(request.user, 'is_delivery', False):
        return redirect(DELIVERY_LOGIN)
    
    INCIDENCE_TYPES = [
        {'value': 'customer_not_home', 'label': 'Cliente no estaba', 'icon': '🏠'},
        {'value': 'wrong_address', 'label': 'Dirección incorrecta', 'icon': '📍'},
        {'value': 'customer_cancelled', 'label': 'Cliente canceló', 'icon': '❌'},
        {'value': 'product_rejected', 'label': 'Producto rechazado', 'icon': '📦'},
        {'value': 'other', 'label': 'Otro', 'icon': '📝'},
    ]
    
    if request.method == 'POST':
        incidence_type = request.POST.get('incidence_type')
        comments = request.POST.get('comments', '')
        action = request.POST.get('action', 'report')
        
        if action == 'cancel':
            messages.warning(request, f'Pedido #{order_id} cancelado. Motivo: {comments}')
        else:
            messages.info(request, f'Incidencia reportada para pedido #{order_id}')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Incidencia registrada correctamente',
                'incidence_type': incidence_type,
            })
        
        return redirect(DELIVERY_ORDERS)
    
    context = {
        'order_id': order_id,
        'incidence_types': INCIDENCE_TYPES,
        'order_info': {
            'order_number': f'ZCD-{order_id:04d}',
            'customer_name': 'Cliente de prueba',
            'total_amount': 78500,
        },
        'back_url': reverse(DELIVERY_ORDER_DETAIL, args=[order_id]),
    }
    
    return render(request, 'delivery/incidences/form.html', context)


# =============================================================================
# HU-036: VER RESUMEN DEL DÍA Y CIERRE DE JORNADA
# =============================================================================

@login_required
def daily_summary(request):
    """Muestra el resumen del día para el entregador."""
    if not getattr(request.user, 'is_delivery', False):
        return redirect(DELIVERY_LOGIN)
    
    today = date.today()
    closed_summary = request.session.get(f'closed_summary_{today.isoformat()}')
    
    if closed_summary:
        summary = closed_summary
        is_closed = True
    else:
        summary = {
            'date': today.isoformat(),
            'total_delivered': 8,
            'total_paid': 5,
            'total_amount': 785000,
            'pending_payment': 3,
            'pending_amount': 125000,
            'delivered_orders': [
                {'id': 1001, 'customer': 'María González', 'amount': 78500, 'paid': True},
                {'id': 1002, 'customer': 'Carlos Rodríguez', 'amount': 125500, 'paid': True},
                {'id': 1003, 'customer': 'Ana Martínez', 'amount': 45000, 'paid': False},
                {'id': 1004, 'customer': 'Laura Sánchez', 'amount': 234000, 'paid': True},
                {'id': 1005, 'customer': 'Pedro López', 'amount': 67000, 'paid': True},
                {'id': 1006, 'customer': 'Sofia Ramírez', 'amount': 89000, 'paid': False},
                {'id': 1007, 'customer': 'Juan Pérez', 'amount': 95000, 'paid': True},
                {'id': 1008, 'customer': 'Diana Castro', 'amount': 56000, 'paid': False},
            ],
            'incidences': [
                {'order_id': 1009, 'type': 'Cliente no estaba', 'comments': 'Intenté contactar 3 veces'},
                {'order_id': 1010, 'type': 'Dirección incorrecta', 'comments': 'La dirección no existe'},
            ]
        }
        is_closed = False
    
    context = {
        'summary': summary,
        'today': today,
        'is_closed': is_closed,
        'can_close': not is_closed and summary['total_delivered'] > 0,
        'close_url': reverse(DELIVERY_CLOSE_JOURNEY),
        'orders_url': reverse(DELIVERY_ORDERS),
    }
    
    return render(request, 'delivery/summary/daily.html', context)

@login_required
@require_http_methods(["POST"])
def close_journey(request):
    """Cierra la jornada del entregador."""
    if not getattr(request.user, 'is_delivery', False):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    today = date.today()
    
    summary = {
        'date': today.isoformat(),
        'total_delivered': 8,
        'total_paid': 5,
        'total_amount': 785000,
        'pending_payment': 3,
        'pending_amount': 125000,
        'closed_at': timezone.now().isoformat(),
        'closed_by': request.user.get_full_name() or request.user.username,
    }
    
    request.session[f'closed_summary_{today.isoformat()}'] = summary
    
    messages.success(request, 'Jornada cerrada exitosamente. ¡Buen trabajo!')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Jornada cerrada exitosamente',
            'summary': summary,
        })
    
    return redirect(DELIVERY_DAILY_SUMMARY)


# =============================================================================
# API ENDPOINTS
# =============================================================================

@login_required
def api_orders(request):
    """API endpoint para obtener pedidos (para pull-to-refresh)."""
    if not getattr(request.user, 'is_delivery', False):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    fake_orders = [
        {
            'id': 1001,
            'order_number': 'ZCD-0001',
            'customer_name': 'María González',
            'shipping_address': 'Calle 123 #45-67, Bogotá',
            'total_amount': 78500,
            'is_paid': False,
            'status': 'listo',
            'detail_url': reverse(DELIVERY_ORDER_DETAIL, args=[1001]),
            'mark_paid_url': reverse(DELIVERY_API_MARK_PAID, args=[1001]),
        },
        {
            'id': 1002,
            'order_number': 'ZCD-0002',
            'customer_name': 'Carlos Rodríguez',
            'shipping_address': 'Carrera 89 #12-34, Bogotá',
            'total_amount': 125500,
            'is_paid': True,
            'status': 'en_camino',
            'detail_url': reverse(DELIVERY_ORDER_DETAIL, args=[1002]),
            'mark_paid_url': reverse(DELIVERY_API_MARK_PAID, args=[1002]),
        },
    ]
    
    return JsonResponse({
        'success': True,
        'orders': fake_orders,
        'last_update': timezone.now().isoformat(),
    })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_mark_paid(request, order_id):
    """API endpoint para marcar pedido como pagado desde JS."""
    if not getattr(request.user, 'is_delivery', False):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        data = json.loads(request.body) if request.body else {}
        
        return JsonResponse({
            'success': True,
            'message': f'Pedido #{order_id} marcado como pagado',
            'order_id': order_id,
            'paid_at': timezone.now().isoformat(),
            'redirect_url': reverse(DELIVERY_ORDER_DETAIL, args=[order_id]),
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_create_incidence(request):
    """API endpoint para crear incidencias desde JS."""
    if not getattr(request.user, 'is_delivery', False):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        incidence_type = data.get('incidence_type')
        comments = data.get('comments', '')
        
        return JsonResponse({
            'success': True,
            'message': 'Incidencia registrada correctamente',
            'incidence': {
                'id': 999,
                'order_id': order_id,
                'type': incidence_type,
                'comments': comments,
                'created_at': timezone.now().isoformat(),
            },
            'redirect_url': reverse(DELIVERY_ORDERS),
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =============================================================================
# HEALTH CHECK PARA RAILWAY/RENDER
# =============================================================================

@require_safe
def health_check(request):
    """Endpoint de health check para despliegue."""
    return JsonResponse({
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
        'app': 'Zicada Delivery PWA',
        'version': '1.0.0'
    })