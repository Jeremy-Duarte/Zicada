from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

admin_patterns = [
    path('hero/', views.HeroConfigListView.as_view(), name='hero_list'),
    path('hero/crear/', views.HeroConfigCreateView.as_view(), name='hero_create'),
    path('hero/<int:pk>/editar/', views.HeroConfigUpdateView.as_view(), name='hero_edit'),
    path('hero/<int:pk>/eliminar/', views.HeroConfigDeleteView.as_view(), name='hero_delete'),
    path('hero/<int:pk>/restaurar/', views.HeroConfigRestoreView.as_view(), name='hero_restore'),
    path('hero/papelera/', views.HeroConfigTrashcanView.as_view(), name='hero_trashcan'),
]

urlpatterns = [
    path('nosotros/', views.about, name='about'),
    path('contacto/', views.contact, name='contact'),
    path('contacto/success/', views.contact_success, name='contact_success'),
    path('cambios/', views.returns_policy, name='returns_policy'),
    path('privacidad/', views.privacy_policy, name='privacy_policy'),
    path('terminos/', views.terms, name='terms'),
    path('staff/login/', views.StaffLoginView.as_view(), name='staff_login'),
    path('staff/logout/', views.staff_logout, name='staff_logout'),
    path('staff/password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.html',
            success_url=reverse_lazy('core:password_reset_done'),
        ),
        name='password_reset'),
    path('staff/password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html',
        ),
        name='password_reset_done'),
    path('staff/password-reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
            success_url=reverse_lazy('core:password_reset_complete'),
        ),
        name='password_reset_confirm'),
    path('staff/password-reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html',
        ),
        name='password_reset_complete'),
        #Crud Paths
    path('admin/', include(admin_patterns)),
]