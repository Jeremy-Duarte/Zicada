from django.urls import path, include
from . import views

app_name = 'products'

admin_patterns = [
    path('lista/', views.products_list, name='products_list'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('tallas/', views.SizeListView.as_view(), name='size_list'),
    path('tallas/crear/', views.SizeCreateView.as_view(), name='size_create'),
    path('tallas/<int:pk>/editar/', views.SizeUpdateView.as_view(), name='size_edit'),
    path('tallas/<int:pk>/eliminar/', views.SizeDeleteView.as_view(), name='size_delete'),
    path('categorias/', views.CategoryListView.as_view(), name='category_list'),
    path('categorias/crear/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categorias/<int:pk>/editar/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categorias/<int:pk>/eliminar/', views.CategoryDeleteView.as_view(), name='category_delete'),
    path('colores/', views.ColorListView.as_view(), name='color_list'),
    path('colores/crear/', views.ColorCreateView.as_view(), name='color_create'),
    path('colores/<int:pk>/editar/', views.ColorUpdateView.as_view(), name='color_edit'),
    path('colores/<int:pk>/eliminar/', views.ColorDeleteView.as_view(), name='color_delete'),
]

urlpatterns = [
    path('stock-dashboard/', views.stock_dashboard, name='stock_dashboard'),
    path('', views.catalog, name='catalog'),
    path('colecciones/', views.collections_list, name='collections_list'),
    path('colecciones/<slug:slug>/', views.collection_detail, name='collection_detail'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),
    #Crud Paths
    path('admin/', include(admin_patterns)),
]