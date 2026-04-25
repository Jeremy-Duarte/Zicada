from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('nosotros/', views.about, name='about'),
    path('contacto/', views.contact, name='contact'),
    path('cambios/', views.returns_policy, name='returns_policy'),
    path('privacidad/', views.privacy_policy, name='privacy_policy'),
    path('terminos/', views.terms, name='terms'),
    path('newsletter/', views.newsletter_subscribe, name='newsletter_subscribe'),
]