from django.urls import path, include
from . import views

app_name = 'orders'

admin_patterns = [
    path('lista/', views.OrderListView.as_view(), name='order_list'),
    path('crear/', views.OrderCreateView.as_view(), name='order_create'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('<int:pk>/editar/', views.OrderUpdateView.as_view(), name='order_edit'),
    path('<int:pk>/confirmar/', views.OrderConfirmView.as_view(), name='order_confirm'),
    path('<int:pk>/cancelar/', views.OrderCancelView.as_view(), name='order_cancel'),
    path('<int:pk>/asignar-repartidor/', views.OrderAssignDeliveryView.as_view(), name='order_assign_delivery'),
    path('<int:pk>/marcar-entregado/', views.OrderMarkAsDeliveredView.as_view(), name='order_mark_delivered'),
    path('<int:order_pk>/items/crear/', views.OrderItemCreateView.as_view(), name='orderitem_create'),
    path('items/<int:pk>/editar/', views.OrderItemUpdateView.as_view(), name='orderitem_edit'),
    path('items/<int:pk>/eliminar/', views.OrderItemDeleteView.as_view(), name='orderitem_delete'),
]

urlpatterns = [
    path('delivery/', views.delivery_dashboard, name='delivery_dashboard'),
    path('delivery/take/<int:order_id>/', views.take_order, name='take_order'),
    path('delivery/deliver/<int:order_id>/', views.deliver_order, name='deliver_order'),
    path('carrito/agregar/', views.cart_add, name='cart_add'),
    path('carrito/eliminar/', views.cart_remove, name='cart_remove'),
    path('carrito/actualizar/', views.cart_update, name='cart_update'),
    path('carrito/vaciar/', views.cart_clear, name='cart_clear'),
    path('carrito/datos/', views.cart_data, name='cart_data'),
    path('carrito/', views.cart_detail, name='cart_detail'),
    path('checkout/', views.checkout, name='checkout'),
    path('confirmacion/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('tracking/<uuid:tracking_token>/', views.order_tracking, name='order_tracking'),
    path('create-stripe-session/', views.create_stripe_checkout_session, name='create_stripe_checkout_session'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    #Crud Paths
    path('lista/', views.orders_list, name='orders_list'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('admin/', include(admin_patterns)),
]