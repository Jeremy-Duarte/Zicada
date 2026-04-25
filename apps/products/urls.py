from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('stock-dashboard/', views.stock_dashboard, name='stock_dashboard'),
    path('', views.catalog, name='catalog'),
    path('colecciones/', views.collections_list, name='collections_list'),
    path('colecciones/<slug:slug>/', views.collection_detail, name='collection_detail'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),
]