from django.conf import settings
from django.db import models
from django.utils import timezone


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class BaseAuditModel(models.Model):
    """
    Modelo base para entidades que requieren:
    - Soft delete (is_active + deleted_at)
    - Auditoría de creación/modificación (created_by, updated_by)
    """
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si el registro está activo (no eliminado suavemente)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creado el'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Actualizado el'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Eliminado el'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name='Creado por'
    )
    
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name='Actualizado por'
    )
    
    objects = ActiveManager()
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def soft_delete(self, user=None):
        self.is_active = False
        self.deleted_at = timezone.now()
        
        fields = ['is_active', 'deleted_at']
        if user and hasattr(self, 'updated_by'):
            self.updated_by = user
            fields.append('updated_by')
        
        self.save(update_fields=fields)
    
    def restore(self, user=None):
        self.is_active = True
        self.deleted_at = None
        
        fields = ['is_active', 'deleted_at']
        if user and hasattr(self, 'updated_by'):
            self.updated_by = user
            fields.append('updated_by')
        
        self.save(update_fields=fields)