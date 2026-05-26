from django.urls import path
from . import views

app_name = 'backoffice'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('pedidos/', views.admin_orders_dashboard, name='orders'),
    path('productos/', views.admin_products, name='products'),
    path('usuarios/', views.admin_users, name='users'),
    path('configuracion/', views.admin_config, name='config'),
    path('reportes/', views.report_generator, name='report_generator'),
    path('importar/', views.importers_dashboard, name='importers_dashboard'),
]