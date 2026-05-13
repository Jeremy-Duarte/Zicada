from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('lista/', views.users_list, name='users_list'),
    path('<int:pk>/', views.user_detail, name='user_detail'),
]