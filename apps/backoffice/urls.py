from django.urls import path
from . import views

app_name = 'backoffice'

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    path('pedidos/', views.AdminOrdersDashboardView.as_view(), name='orders'),
    path('productos/', views.AdminProductsDashboardView.as_view(), name='products'),
    path('usuarios/', views.AdminUsersDashboardView.as_view(), name='users'),
    path('configuracion/', views.AdminConfigView.as_view(), name='config'),
    path('reportes/', views.ReportGeneratorView.as_view(), name='report_generator'),
    path('importar/', views.ImportersDashboardView.as_view(), name='importers_dashboard'),
]