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

class HeroConfig(models.Model):
    """
    Configuración de la sección principal (hero) del landing page.
    Solo debe existir un registro activo.
    """
    background_image = models.ImageField(
        upload_to='landingpage/hero/',
        blank=True,
        null=True,
        verbose_name='Imagen de fondo',
        help_text='Imagen de fondo para el hero (recomendado: 1920x1080px).'
    )
    overlay_opacity = models.FloatField(
        default=0.5,
        help_text='Opacidad del overlay oscuro (0 = transparente, 1 = negro total).'
    )    
    title_text = models.CharField(
        max_length=200,
        default='ZICADA',
        verbose_name='Texto del título'
    )
    title_font_family = models.CharField(
        max_length=100,
        default="'Inter', sans-serif",
        verbose_name='Fuente del título (CSS)'
    )
    title_font_size = models.CharField(
        max_length=20,
        default='4rem',
        verbose_name='Tamaño de fuente'
    )
    title_font_weight = models.CharField(
        max_length=20,
        default='800',
        verbose_name='Peso de la fuente'
    )
    title_line_height = models.CharField(
        max_length=20,
        default='1.2',
        verbose_name='Altura de línea'
    )
    title_color = models.CharField(
        max_length=20,
        default='#ffffff',
        verbose_name='Color'
    )
    title_margin_bottom = models.CharField(
        max_length=20,
        default='1rem',
        verbose_name='Margen inferior'
    )    
    subtitle_text = models.CharField(
        max_length=300,
        default='LA MODA SE VA, TU ESTILO PERMANECE',
        verbose_name='Texto del lema'
    )
    subtitle_font_family = models.CharField(
        max_length=100,
        default="'Inter', sans-serif",
        verbose_name='Fuente del lema'
    )
    subtitle_font_size = models.CharField(
        max_length=20,
        default='1.25rem',
    )
    subtitle_font_weight = models.CharField(
        max_length=20,
        default='400',
    )
    subtitle_line_height = models.CharField(
        max_length=20,
        default='1.5',
    )
    subtitle_color = models.CharField(
        max_length=20,
        default='#e5e5e5',
    )
    subtitle_margin_bottom = models.CharField(
        max_length=20,
        default='2rem',
    )
    button_text = models.CharField(
        max_length=50,
        default='Explorar Catálogo',
        verbose_name='Texto del botón'
    )
    button_url = models.CharField(
        max_length=200,
        default='/catalogo/',
        verbose_name='URL del botón'
    )
    button_style = models.CharField(
        max_length=100,
        default='bg-zicada-accent hover:bg-opacity-90',
        verbose_name='Clases CSS del botón'
    )
    
    content_alignment = models.CharField(
        max_length=20,
        choices=[
            ('center', 'Centrado'),
            ('left', 'Izquierda'),
            ('right', 'Derecha'),
        ],
        default='center',
        verbose_name='Alineación del contenido'
    )
    section_height = models.CharField(
        max_length=20,
        default='100vh',
        verbose_name='Altura de la sección (ej: 100vh, 90vh, 700px)'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración del Hero'
        verbose_name_plural = 'Configuraciones del Hero'
    
    def __str__(self):
        return f"Hero: {self.title_text}"
    
    def save(self, *args, **kwargs):
        # Solo un registro activo
        if self.is_active:
            HeroConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)