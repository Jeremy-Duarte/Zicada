from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'delivery'

urlpatterns = [
    # PWA endpoints
    path('manifest.json', views.pwa_manifest, name='pwa_manifest'),
    path('offline/', views.offline_page, name='offline'),
    path('sw.js', TemplateView.as_view(
        template_name='delivery/sw.js',
        content_type='application/javascript'
    ), name='service_worker'),
    path('health/', views.health_check, name='health_check'),
    
    # Autenticación
    path('login/', views.delivery_login, name='login'),
    path('logout/', views.delivery_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # HU-033: Pedidos del día
    path('orders/', views.delivery_orders, name='orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # HU-034: Marcar pagado
    path('orders/<int:order_id>/mark-paid/', views.mark_as_paid, name='mark_paid'),
    
    # HU-035: Registrar incidencia
    path('orders/<int:order_id>/incidence/', views.register_incidence, name='register_incidence'),
    
    # HU-036: Resumen del día
    path('summary/', views.daily_summary, name='summary'),
    path('summary/close/', views.close_journey, name='close_journey'),
    
    # API endpoints
    path('api/orders/', views.api_orders, name='api_orders'),
    path('api/orders/<int:order_id>/mark-paid/', views.api_mark_paid, name='api_mark_paid'),
    path('api/incidences/create/', views.api_create_incidence, name='api_create_incidence'),
]