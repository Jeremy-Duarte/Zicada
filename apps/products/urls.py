from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('stock-dashboard/', views.stock_dashboard, name='stock_dashboard'),
]