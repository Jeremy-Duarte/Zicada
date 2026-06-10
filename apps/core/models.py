from django.conf import settings
from django.db import models
from django.utils import timezone


class ActiveManager(models.Manager):
    # HU-052, HU-057 | H | Manager que retorna solo registros activos
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class BaseAuditModel(models.Model):
    """
    Modelo base para entidades que requieren:
    - Soft delete (is_active + deleted_at)
    - Auditoría de creación/modificación (created_by, updated_by)
    
    Este modelo es abstracto y sus métodos son utilizados por:
    - HeroConfig (HU-055, HU-056)
    - Product (HU-012)
    - ProductVariant (HU-013)
    - Collection (HU-017)
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
        """
        HU-055 | ESCENARIO 1 | H | Soft delete (archivar) - HeroConfig
        HU-012 | ESCENARIO 1 | H | Soft delete (archivar) - Product
        HU-013 | ESCENARIO 4 | A | Soft delete (deshabilitar) - ProductVariant
        HU-017 | ESCENARIO 1 | H | Soft delete (archivar) - Collection
        """
        self.is_active = False
        self.deleted_at = timezone.now()
        
        fields = ['is_active', 'deleted_at']
        if user and hasattr(self, 'updated_by'):
            self.updated_by = user
            fields.append('updated_by')
        
        self.save(update_fields=fields)
    
    def restore(self, user=None):
        """
        HU-056 | ESCENARIO 1 | H | Restaurar slide archivado - HeroConfig
        HU-012 | ESCENARIO 4 | H | Restaurar producto archivado - Product
        HU-013 | ESCENARIO 4 | A | Restaurar variante deshabilitada - ProductVariant
        HU-017 | ESCENARIO 3 | H | Restaurar colección archivada - Collection
        """
        self.is_active = True
        self.deleted_at = None
        
        fields = ['is_active', 'deleted_at']
        if user and hasattr(self, 'updated_by'):
            self.updated_by = user
            fields.append('updated_by')
        
        self.save(update_fields=fields)


class HeroConfig(BaseAuditModel):
    """
    HU-050: Página de inicio personalizada (hero slides)
    HU-052: Listar slides del hero
    HU-053: Crear slide del hero
    HU-054: Editar slide del hero
    HU-055: Archivar slide del hero
    HU-056: Restaurar slide del hero
    HU-057: Ver papelera de slides
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

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición en el carrusel'
    )

    class Meta:
        ordering = ['sort_order']
        verbose_name = 'Configuración del Hero'
        verbose_name_plural = 'Configuraciones del Hero'
    
    def __str__(self):
        return f"Hero: {self.title_text}"
    
    def save(self, *args, **kwargs):
        """
        HU-053 | ESCENARIO 1 | H | Guardado normal del slide
        HU-054 | ESCENARIO 1 | H | Guardado al actualizar slide
        """
        super().save(*args, **kwargs)