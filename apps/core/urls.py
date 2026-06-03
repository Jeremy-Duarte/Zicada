from django.urls import path, include
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
    path('contacto/submit/', views.contact_submit, name='contact_submit'),
    path('contacto/success/', views.contact_success, name='contact_success'),
    path('cambios/', views.returns_policy, name='returns_policy'),
    path('privacidad/', views.privacy_policy, name='privacy_policy'),
    path('terminos/', views.terms, name='terms'),
    path('newsletter/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('staff/login/', views.StaffLoginView.as_view(), name='staff_login'),
    path('staff/logout/', views.staff_logout, name='staff_logout'),
        #Crud Paths
    path('admin/', include(admin_patterns)),
]