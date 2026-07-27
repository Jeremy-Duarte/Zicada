from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.http import require_http_methods, require_POST, require_safe
from django.views.decorators.vary import vary_on_headers
from django.contrib.auth.decorators import login_required

import json

from apps.orders.models import Order
from apps.core.url_names import (
    DELIVERY_CLOSE_JOURNEY,
    DELIVERY_DAILY_SUMMARY,
    DELIVERY_DASHBOARD,
    DELIVERY_LOGIN,
    DELIVERY_MARK_PAID,
    DELIVERY_ORDER_DETAIL,
    DELIVERY_ORDERS,
    DELIVERY_REGISTER_INCIDENCE,
)


# =============================================================================
# HELPER PRIVADO
# =============================================================================

def _is_delivery_user(user):
    """Verifica que el usuario autenticado sea un repartidor activo."""
    return getattr(user, 'is_delivery', False) and user.is_active


# =============================================================================
# PWA — MANIFEST, SERVICE WORKER Y SALUD
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
        "start_url": reverse(DELIVERY_LOGIN),
        "display": settings.PWA_DISPLAY,
        "theme_color": settings.PWA_THEME_COLOR,
        "background_color": settings.PWA_BACKGROUND_COLOR,
        "orientation": settings.PWA_ORIENTATION,
        "scope": "/delivery/",
        "icons": icons,
        "categories": ["business", "productivity"],
        "lang": "es",
        "dir": "ltr",
        "prefer_related_applications": False,
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


@cache_page(60 * 15)
@vary_on_headers('User-Agent')
def sw_config(request):
    """
    Endpoint que devuelve la configuración del Service Worker.
    Permite que el SW sea estático pero configurable desde el servidor.
    """
    protocol = 'https' if request.is_secure() else 'http'
    base_url = f"{protocol}://{request.get_host()}"

    precache_urls = [
        base_url + reverse('delivery:offline'),
        base_url + reverse('delivery:login'),
        base_url + reverse('delivery:dashboard'),
        base_url + reverse('delivery:orders'),
        base_url + reverse('delivery:summary'),
        base_url + static('css/delivery/main.css'),
        base_url + static('js/delivery/base.js'),
        base_url + static('js/delivery/orders.js'),
        base_url + static('js/delivery/dashboard.js'),
        base_url + static('js/delivery/summary.js'),
        base_url + static('js/delivery/order-detail.js'),
    ]

    config = {
        'cacheName': getattr(settings, 'SW_CACHE_NAME', 'zicada-delivery-v1'),
        'offlineUrl': base_url + reverse('delivery:offline'),
        'precacheUrls': precache_urls,
        'version': getattr(settings, 'PWA_VERSION', '1.0.0'),
        'lastUpdated': timezone.now().isoformat(),
    }

    return JsonResponse(config, encoder=DjangoJSONEncoder)


@require_safe
def health_check(request):
    """Endpoint de health check para Railway/Render."""
    return JsonResponse({
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
        'app': 'Zicada Delivery PWA',
        'version': '1.0.0'
    })


# =============================================================================
# AUTENTICACIÓN
# =============================================================================

_DELIVERY_LOGIN_TEMPLATE = 'delivery/login.html'


def delivery_login(request):
    """
    Login específico para la PWA de delivery.
    Solo permite acceso a usuarios con is_delivery=True.
    """
    if request.user.is_authenticated:
        if _is_delivery_user(request.user):
            return redirect(DELIVERY_DASHBOARD)
        logout(request)
        return render(request, _DELIVERY_LOGIN_TEMPLATE, {
            'error': 'Esta app es solo para repartidores. Usa la web principal.'
        })

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user and _is_delivery_user(user):
            auth_login(request, user)
            return redirect(DELIVERY_DASHBOARD)

        return render(request, _DELIVERY_LOGIN_TEMPLATE, {
            'error': 'Credenciales inválidas o no tienes permisos de entregador.'
        })

    return render(request, _DELIVERY_LOGIN_TEMPLATE)


@require_POST
def delivery_logout(request):
    """Cierra sesión del entregador y limpia el caché del Service Worker."""
    logout(request)
    response = redirect(DELIVERY_LOGIN)
    # Fuerza al navegador a limpiar el SW y su caché para evitar servir datos obsoletos
    response['Clear-Site-Data'] = '"cache", "storage"'
    return response


@login_required
def offline_page(request):
    """Página offline para la PWA."""
    return render(request, 'delivery/offline.html', {
        'login_url': reverse(DELIVERY_LOGIN),
    })


# =============================================================================
# HU-033: DASHBOARD DEL ENTREGADOR
# =============================================================================

@login_required
def dashboard(request):
    """Dashboard principal del entregador con métricas reales del día."""
    if not _is_delivery_user(request.user):
        logout(request)
        return redirect(DELIVERY_LOGIN)

    today = timezone.localdate()
    user = request.user

    from django.db.models import Q
    
    # Pedidos asignados al usuario que:
    # 1. Están pendientes activos (listo o en camino)
    # O 2. Fueron completados o cancelados hoy (acción realizada hoy)
    all_relevant_orders = Order.objects.filter(
        Q(assigned_delivery_user=user) &
        (Q(status__in=['listo', 'en_camino']) | Q(status__in=['entregado', 'cancelado'], updated_at__date=today))
    )

    completed = all_relevant_orders.filter(status='entregado').count()
    pending = all_relevant_orders.filter(status__in=['listo', 'en_camino']).count()
    total_today = all_relevant_orders.count()

    # Último pedido activo
    last_order = Order.objects.filter(
        assigned_delivery_user=user,
        status__in=['listo', 'en_camino']
    ).select_related('assigned_delivery_user').prefetch_related('items').order_by('-created_at').first()

    context = {
        'user': user,
        'pwa_mode': True,
        'today_orders_count': total_today,
        'completed_orders': completed,
        'pending_orders': pending,
        'last_order': last_order,
        'orders_url': reverse(DELIVERY_ORDERS),
        'summary_url': reverse(DELIVERY_DAILY_SUMMARY),
        'logout_url': reverse('delivery:logout'),
        'is_admin': user.is_staff or user.groups.filter(name='Administrador').exists(),
    }

    return render(request, 'delivery/dashboard.html', context)


# =============================================================================
# HU-033: LISTA DE PEDIDOS DEL DÍA
# =============================================================================

@login_required
def delivery_orders(request):
    """Lista de pedidos asignados — la carga real se hace vía API desde orders.js."""
    if not _is_delivery_user(request.user):
        return redirect(DELIVERY_LOGIN)

    context = {
        'today': timezone.localdate(),
        'filter': request.GET.get('filter', 'all'),
        'order_detail_url_name': DELIVERY_ORDER_DETAIL,
        'mark_paid_url_name': DELIVERY_MARK_PAID,
        'register_incidence_url_name': DELIVERY_REGISTER_INCIDENCE,
    }

    return render(request, 'delivery/orders/list.html', context)


# =============================================================================
# HU-034: DETALLE DE PEDIDO
# =============================================================================

@login_required
def order_detail(request, order_id):
    """Detalle de un pedido asignado al repartidor autenticado."""
    if not _is_delivery_user(request.user):
        return redirect(DELIVERY_LOGIN)

    order = get_object_or_404(
        Order,
        id=order_id,
        assigned_delivery_user=request.user
    )

    context = {
        'order': order,
        'order_id': order_id,
        'mark_paid_url': reverse(DELIVERY_MARK_PAID, args=[order_id]),
        'register_incidence_url': reverse(DELIVERY_REGISTER_INCIDENCE, args=[order_id]),
        'back_url': reverse(DELIVERY_ORDERS),
    }

    return render(request, 'delivery/orders/detail.html', context)


# =============================================================================
# HU-034: CONFIRMAR ENTREGA DEL PEDIDO
# (Todos los pedidos son pre-pagados vía pasarela — el repartidor solo confirma entrega)
# =============================================================================

@login_required
@require_http_methods(["POST"])
def mark_as_paid(request, order_id):
    """
    Confirma la entrega física del pedido.
    El pago ya fue procesado por Stripe antes de la entrega.
    """
    if not _is_delivery_user(request.user):
        return JsonResponse({'success': False, 'message': 'No autorizado'}, status=403)

    order = get_object_or_404(
        Order,
        id=order_id,
        assigned_delivery_user=request.user
    )

    if order.status == 'entregado':
        msg = 'Este pedido ya fue marcado como entregado.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.warning(request, msg)
        return redirect(DELIVERY_ORDER_DETAIL, order_id=order_id)

    if order.status != 'en_camino':
        msg = f'Solo puedes confirmar entregas en estado "En camino". Estado actual: {order.get_status_display()}'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect(DELIVERY_ORDER_DETAIL, order_id=order_id)

    order.mark_as_delivered(user=request.user)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Pedido {order.order_number} confirmado como entregado.',
            'order_id': order.id,
            'order_number': order.order_number,
            'delivered_at': timezone.now().isoformat(),
        })

    messages.success(request, f'✅ Pedido {order.order_number} entregado correctamente.')
    return redirect(DELIVERY_ORDERS)


# =============================================================================
# HU-035: REGISTRAR INCIDENCIA
# =============================================================================

INCIDENCE_TYPES = [
    {'value': 'customer_not_home', 'label': 'Cliente no estaba', 'icon': '🏠'},
    {'value': 'wrong_address', 'label': 'Dirección incorrecta', 'icon': '📍'},
    {'value': 'customer_cancelled', 'label': 'Cliente canceló', 'icon': '❌'},
    {'value': 'product_rejected', 'label': 'Producto rechazado', 'icon': '📦'},
    {'value': 'other', 'label': 'Otro', 'icon': '📝'},
]

_INCIDENCE_VALUES = {t['value'] for t in INCIDENCE_TYPES}


@login_required
def register_incidence(request, order_id):
    """Registra una incidencia en un pedido asignado al repartidor."""
    if not _is_delivery_user(request.user):
        return redirect(DELIVERY_LOGIN)

    if request.method == 'POST':
        incidence_type = request.POST.get('incidence_type', '').strip()
        comments = request.POST.get('comments', '').strip()
        action = request.POST.get('action', 'report')

        # Validar tipo de incidencia
        if incidence_type not in _INCIDENCE_VALUES:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Tipo de incidencia inválido.'
                }, status=400)
            messages.error(request, 'Tipo de incidencia inválido.')
            return redirect(DELIVERY_REGISTER_INCIDENCE, order_id=order_id)

        type_label = next(
            (t['label'] for t in INCIDENCE_TYPES if t['value'] == incidence_type),
            incidence_type
        )

        incidence_data = {
            'type': incidence_type,
            'type_label': type_label,
            'comments': comments,
            'reported_by': request.user.id,
            'reported_by_name': request.user.get_full_name() or request.user.username,
            'reported_at': timezone.now().isoformat(),
            'action_taken': action,
        }

        try:
            with transaction.atomic():
                order = get_object_or_404(
                    Order.objects.prefetch_related('items'),
                    id=order_id,
                    assigned_delivery_user=request.user
                )
                if action == 'cancel':
                    reason = json.dumps(incidence_data, ensure_ascii=False)
                    order.cancel(reason, user=request.user)

                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': f'Pedido {order.order_number} cancelado por: {type_label}',
                            'order_number': order.order_number,
                            'status': 'cancelado',
                        })

                    messages.warning(request, f'Pedido {order.order_number} cancelado. Motivo: {type_label}')
                else:
                    # Acumular incidencias en cancelled_reason como lista JSON
                    existing = []
                    if order.cancelled_reason:
                        try:
                            parsed = json.loads(order.cancelled_reason)
                            existing = parsed if isinstance(parsed, list) else [parsed]
                        except json.JSONDecodeError:
                            pass

                    existing.append(incidence_data)
                    order.cancelled_reason = json.dumps(existing, ensure_ascii=False)
                    order.save(update_fields=['cancelled_reason', 'updated_at'])

                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': f'Incidencia reportada: {type_label}',
                            'order_number': order.order_number,
                            'status': order.status,
                        })

                    messages.info(request, f'Incidencia reportada para pedido {order.order_number}.')

        except Exception as exc:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Error al procesar la incidencia: {exc}'
                }, status=500)
            messages.error(request, f'Error: {exc}')
            return redirect(DELIVERY_REGISTER_INCIDENCE, order_id=order_id)

        return redirect(DELIVERY_ORDERS)

    order = get_object_or_404(
        Order,
        id=order_id,
        assigned_delivery_user=request.user
    )

    context = {
        'order': order,
        'order_id': order_id,
        'incidence_types': INCIDENCE_TYPES,
        'back_url': reverse(DELIVERY_ORDER_DETAIL, args=[order_id]),
    }

    return render(request, 'delivery/incidences/form.html', context)


# =============================================================================
# HU-036: RESUMEN DEL DÍA Y CIERRE DE JORNADA
# =============================================================================

def _build_summary(user, today):
    """
    Construye el resumen del día para el repartidor.
    Todos los pedidos son pre-pagados vía Stripe, por lo que
    las métricas son de entrega, no de cobro.
    """
    # Pedidos entregados hoy (independientemente de cuándo fueron creados)
    delivered_orders = Order.objects.filter(
        assigned_delivery_user=user,
        status='entregado',
        updated_at__date=today
    )

    # Pedidos actualmente pendientes (en estado listo o en camino)
    pending_orders = Order.objects.filter(
        assigned_delivery_user=user,
        status__in=['listo', 'en_camino']
    )

    # Pedidos con incidencias reportadas hoy (estatus cancelado, actualizados hoy, con cancelled_reason no vacía)
    incidences_orders = Order.objects.filter(
        assigned_delivery_user=user,
        status='cancelado',
        updated_at__date=today
    ).exclude(
        cancelled_reason=''
    ).exclude(
        cancelled_reason__isnull=True
    )

    total_delivered = delivered_orders.count()
    pending_delivery = pending_orders.count()
    total_today = total_delivered + pending_delivery + incidences_orders.count()

    # Incidencias del día (guardadas en cancelled_reason como JSON)
    incidences = []
    for order in incidences_orders:
        try:
            data = json.loads(order.cancelled_reason)
            entries = data if isinstance(data, list) else [data]
            for inc in entries:
                incidences.append({
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'type': inc.get('type_label', 'Desconocida'),
                    'comments': inc.get('comments', ''),
                    'reported_at': inc.get('reported_at', order.updated_at.isoformat()),
                })
        except json.JSONDecodeError:
            continue

    return {
        'date': today.isoformat(),
        'total_today': total_today,
        'total_delivered': total_delivered,
        'pending_delivery': pending_delivery,
        'delivered_orders': [
            {
                'id': o.id,
                'order_number': o.order_number,
                'customer': o.customer_name,
                'amount': str(o.total_amount),
            }
            for o in delivered_orders
        ],
        'incidences': incidences,
    }


@login_required
def daily_summary(request):
    """Muestra el resumen del día para el entregador."""
    if not _is_delivery_user(request.user):
        return redirect(DELIVERY_LOGIN)

    today = timezone.localdate()
    session_key = f'closed_summary_{today.isoformat()}'
    closed_summary = request.session.get(session_key)

    if closed_summary:
        summary = closed_summary
        is_closed = True
    else:
        summary = _build_summary(request.user, today)
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
    """Cierra la jornada del entregador guardando el resumen en sesión."""
    if not _is_delivery_user(request.user):
        return JsonResponse({'success': False, 'message': 'No autorizado'}, status=403)

    today = timezone.localdate()
    summary = _build_summary(request.user, today)
    summary_light = {
        'date': summary['date'],
        'total_delivered': summary['total_delivered'],
        'pending_delivery': summary['pending_delivery'],
        'total_today': summary['total_today'],
        'incidence_count': len(summary['incidences']),
        'closed_at': timezone.now().isoformat(),
        'closed_by': request.user.get_full_name() or request.user.username,
    }

    session_key = f'closed_summary_{today.isoformat()}'
    request.session[session_key] = summary_light

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': '¡Jornada cerrada exitosamente! Buen trabajo.',
            'summary': summary,
        })

    messages.success(request, '¡Jornada cerrada exitosamente! Buen trabajo.')
    return redirect(DELIVERY_DAILY_SUMMARY)