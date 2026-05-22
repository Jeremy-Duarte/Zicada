from django.urls import path, include
from . import views

app_name = 'users'

admin_patterns = [
    path('lista/', views.UserListView.as_view(), name='user_list'),
    path('crear/', views.UserCreateView.as_view(), name='user_create'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('<int:pk>/editar/', views.UserUpdateView.as_view(), name='user_edit'),
    path('<int:pk>/cambiar-password/', views.UserChangePasswordView.as_view(), name='user_change_password'),
    path('<int:pk>/desactivar/', views.UserDeleteView.as_view(), name='user_delete'),
    path('<int:pk>/reactivar/', views.UserRestoreView.as_view(), name='user_restore'),
    path('papelera/', views.UserTrashcanView.as_view(), name='user_trashcan'),
]

urlpatterns = [
    path('lista/', views.users_list, name='users_list'),
    path('<int:pk>/', views.user_detail, name='user_detail'),
    path('admin/', include(admin_patterns)),
]