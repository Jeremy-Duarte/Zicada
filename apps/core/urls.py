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

gallery_patterns = [
    path('fotos/', views.GalleryPhotoListView.as_view(), name='gallery_photo_list'),
    path('fotos/crear/', views.GalleryPhotoCreateView.as_view(), name='gallery_photo_create'),
    path('fotos/<int:pk>/editar/', views.GalleryPhotoUpdateView.as_view(), name='gallery_photo_edit'),
    path('fotos/<int:pk>/eliminar/', views.GalleryPhotoDeleteView.as_view(), name='gallery_photo_delete'),
    path('fotos/<int:pk>/restaurar/', views.GalleryPhotoRestoreView.as_view(), name='gallery_photo_restore'),
    path('fotos/papelera/', views.GalleryPhotoTrashcanView.as_view(), name='gallery_photo_trashcan'),
    path('layouts/', views.GalleryLayoutListView.as_view(), name='gallery_layout_list'),
    path('layouts/crear/', views.GalleryLayoutCreateView.as_view(), name='gallery_layout_create'),
    path('layouts/<int:pk>/editar/', views.GalleryLayoutUpdateView.as_view(), name='gallery_layout_edit'),
    path('layouts/<int:pk>/eliminar/', views.GalleryLayoutDeleteView.as_view(), name='gallery_layout_delete'),
]

urlpatterns = [
    path('galeria/', views.gallery_page, name='gallery'),
    path('nosotros/', views.about, name='about'),
    path('contacto/', views.contact, name='contact'),
    path('contacto/success/', views.contact_success, name='contact_success'),
    path('cambios/', views.returns_policy, name='returns_policy'),
    path('privacidad/', views.privacy_policy, name='privacy_policy'),
    path('terminos/', views.terms, name='terms'),
    path('staff/login/', views.StaffLoginView.as_view(), name='staff_login'),
    path('staff/logout/', views.staff_logout, name='staff_logout'),
    path('staff/password-reset/',
        views.PasswordResetView.as_view(),
        name='password_reset'),
    path('staff/password-reset/done/',
        views.PasswordResetDoneView.as_view(),
        name='password_reset_done'),
    path('staff/password-reset/<uidb64>/<token>/',
        views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'),
    path('staff/password-reset/complete/',
        views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete'),
        #Crud Paths
    path('admin/', include(admin_patterns)),
    path('admin/galeria/', include(gallery_patterns)),
]
