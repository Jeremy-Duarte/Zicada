from django.contrib.auth.models import AbstractUser, Group as BaseGroup
from django.db import models


# =============================================================================
# USER MODEL (HU-038, HU-039, HU-040, HU-041, HU-042, HU-043)
# =============================================================================

class User(AbstractUser):
    """
    HU-038: Listar usuarios (admin)
    HU-039: Crear usuario (admin)
    HU-040: Editar usuario (admin)
    HU-041: Archivar usuario (admin)
    HU-042: Reincorporar usuario (admin)
    HU-043: Ver/editar mi propio perfil
    """
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
        """
        HU-038 | ESCENARIO 1 | H | Obtiene nombre completo para mostrar en listado
        HU-039 | ESCENARIO 1 | H | Obtiene nombre completo para mensajes
        HU-043 | ESCENARIO 2 | H | Obtiene nombre completo para perfil
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    get_full_name.short_description = 'Nombre completo'


# =============================================================================
# GROUP MODEL (PROXY - SOPORTE PARA ROLES)
# =============================================================================

class Group(BaseGroup):
    """
    Soporte: Grupo/Rol (no tiene HU asignada directamente, necesario para HU-039)
    """
    class Meta:
        proxy = True
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.name