from django.urls import path, include
from . import views

app_name = 'users'

admin_patterns = [
    path('lista/', views.UserListView.as_view(), name='user_list'),
    path('crear/', views.UserCreateView.as_view(), name='user_create'),
    path('<int:pk>/editar/', views.UserUpdateView.as_view(), name='user_edit'),
    path('<int:pk>/cambiar-password/', views.UserChangePasswordView.as_view(), name='user_change_password'),
    path('<int:pk>/desactivar/', views.UserDeleteView.as_view(), name='user_delete'),
    path('<int:pk>/reactivar/', views.UserRestoreView.as_view(), name='user_restore'),
    path('papelera/', views.UserTrashcanView.as_view(), name='user_trashcan'),
    path('roles/lista/', views.GroupListView.as_view(), name='group_list'),
    path('roles/crear/', views.GroupCreateView.as_view(), name='group_create'),
    path('roles/<int:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('roles/<int:pk>/editar/', views.GroupUpdateView.as_view(), name='group_edit'),
    path('roles/<int:pk>/eliminar/', views.GroupDeleteView.as_view(), name='group_delete'),
]

urlpatterns = [
    path('admin/', include(admin_patterns)),
]