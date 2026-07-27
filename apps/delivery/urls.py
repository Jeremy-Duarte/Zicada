# apps/delivery/urls.py

from django.urls import path
from . import views
from django.views.static import serve
from django.conf import settings
from .api import (
    DeliveryOrdersAPIView,
    DeliveryOrderDetailAPIView,
    DeliveryMarkAsPaidAPIView,
    DeliveryIncidenceAPIView,
    DeliverySummaryAPIView,
    get_csrf_token,
)

app_name = 'delivery'

urlpatterns = [    
    # PWA endpoints
    path('manifest.json', views.pwa_manifest, name='pwa_manifest'),
    path('offline/', views.offline_page, name='offline'),
    path('sw.js', serve, {
        'path': 'js/delivery/sw.js',
        'document_root': settings.STATIC_ROOT if not settings.DEBUG else settings.BASE_DIR / 'static',
    }, name='service_worker'),
    path('sw-config.json', views.sw_config, name='sw_config'),
    path('health/', views.health_check, name='health_check'),
    
    # Autenticación
    path('login/', views.delivery_login, name='login'),
    path('logout/', views.delivery_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # HU-033: Pedidos del día
    path('orders/', views.delivery_orders, name='orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # HU-034: Marcar pagado (HTML fallback)
    path('orders/<int:order_id>/mark-paid/', views.mark_as_paid, name='mark_paid'),
    
    # HU-035: Registrar incidencia (HTML fallback)
    path('orders/<int:order_id>/incidence/', views.register_incidence, name='register_incidence'),
    
    # HU-036: Resumen del día
    path('summary/', views.daily_summary, name='summary'),
    path('summary/close/', views.close_journey, name='close_journey'),
    
    # ==================== API ENDPOINTS
    
    # HU-033: Lista de pedidos
    path('api/orders/', DeliveryOrdersAPIView.as_view(), name='api_orders'),
    
    # HU-034: Detalle de pedido
    path('api/orders/<int:order_id>/', DeliveryOrderDetailAPIView.as_view(), name='api_order_detail'),
    
    # HU-034: Marcar como pagado
    path('api/orders/<int:order_id>/mark-paid/', DeliveryMarkAsPaidAPIView.as_view(), name='api_mark_paid'),
    
    # HU-035: Registrar incidencia
    path('api/incidences/', DeliveryIncidenceAPIView.as_view(), name='api_create_incidence'),
    
    # HU-036: Resumen del día
    path('api/summary/', DeliverySummaryAPIView.as_view(), name='api_summary'),
    path('api/csrf/', get_csrf_token, name='delivery_api_csrf'),
]