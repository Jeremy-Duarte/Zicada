from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('delivery/', views.delivery_dashboard, name='delivery_dashboard'),
    path('delivery/take/<int:order_id>/', views.take_order, name='take_order'),
    path('delivery/deliver/<int:order_id>/', views.deliver_order, name='deliver_order'),
]