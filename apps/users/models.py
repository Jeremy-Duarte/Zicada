from django.contrib.auth.models import AbstractUser, Group as BaseGroup
from django.db import models

class User(AbstractUser):
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
    )
    
    is_delivery = models.BooleanField(
        default=False,
        verbose_name='Es entregador',
        help_text='Designa si el usuario puede acceder a la PWA de entregas'
    )
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.get_full_name() or self.username
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    get_full_name.short_description = 'Nombre completo'

class Group(BaseGroup):
    class Meta:
        proxy = True
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.name