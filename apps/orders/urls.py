from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('delivery/', views.delivery_dashboard, name='delivery_dashboard'),
    path('delivery/take/<int:order_id>/', views.take_order, name='take_order'),
    path('delivery/deliver/<int:order_id>/', views.deliver_order, name='deliver_order'),
    path('carrito/agregar/', views.cart_add, name='cart_add'),
    path('carrito/eliminar/', views.cart_remove, name='cart_remove'),
    path('carrito/actualizar/', views.cart_update, name='cart_update'),
    path('carrito/datos/', views.cart_data, name='cart_data'),
    path('carrito/', views.cart_detail, name='cart_detail'),
]