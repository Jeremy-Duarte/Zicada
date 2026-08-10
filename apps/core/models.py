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
        verbose_name='Opacidad del overlay',
        help_text='Opacidad del overlay oscuro (0 = transparente, 1 = negro total).'
    )    
    title_text = models.CharField(
        max_length=255,
        default='ZICADA',
        verbose_name='Texto del título'
    )
    title_font_family = models.CharField(
        max_length=255,
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
        max_length=500,
        default='LA MODA SE VA, TU ESTILO PERMANECE',
        verbose_name='Texto del lema'
    )
    subtitle_font_family = models.CharField(
        max_length=255,
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
        max_length=500,
        default='/catalogo/',
        verbose_name='URL del botón'
    )
    button_style = models.CharField(
        max_length=500,
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
    
    def clean(self):
        if self.background_image:
            try:
                if self.background_image.size > 5 * 1024 * 1024:
                    from django.core.exceptions import ValidationError
                    raise ValidationError({'background_image': 'La imagen no puede superar los 5MB.'})
            except OSError:
                pass

    def save(self, *args, **kwargs):
        """
        HU-053 | ESCENARIO 1 | H | Guardado normal del slide
        HU-054 | ESCENARIO 1 | H | Guardado al actualizar slide
        """
        self.full_clean()
        super().save(*args, **kwargs)


class Gallery(BaseAuditModel):
    """
    Galería del home: carrusel vertical estilo TikTok con fotos de Instagram.
    Solo necesita: descripción, fotografía y texto alternativo (SEO).
    """
    description = models.CharField(
        max_length=255,
        verbose_name='Descripción',
        help_text='Descripción corta de la fotografía.'
    )
    image = models.ImageField(
        upload_to='landingpage/gallery/',
        verbose_name='Fotografía',
        help_text='Imagen vertical recomendada (formato celular 9:16).'
    )
    alt_text = models.CharField(
        max_length=255,
        verbose_name='Texto alternativo (SEO)',
        help_text='Texto alternativo de la imagen para SEO y accesibilidad.'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición en el carrusel de galería.'
    )

    class Meta:
        ordering = ['sort_order']
        verbose_name = 'Foto de Galería'
        verbose_name_plural = 'Fotos de Galería'

    def __str__(self) -> str:
        return f"Galería: {self.description[:40]}"


class HomePromo(BaseAuditModel):
    """
    Espacios publicitarios configurables del home (de 1 a 3 activos).
    Banner de ancho completo con imagen publicitaria debajo de las colecciones.
    """
    title = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Título',
        help_text='Título opcional sobre la imagen.'
    )
    subtitle = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='Subtítulo',
        help_text='Texto secundario opcional.'
    )
    image = models.ImageField(
        upload_to='landingpage/promos/',
        verbose_name='Imagen publicitaria',
        help_text='Imagen del espacio publicitario (recomendado: 1920x800px).'
    )
    link_url = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='URL del enlace',
        help_text='Destino al hacer clic (opcional).'
    )
    link_text = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='Texto del botón',
        help_text='Texto del CTA (opcional).'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición (se muestran máximo 3 activos).'
    )

    class Meta:
        ordering = ['sort_order']
        verbose_name = 'Espacio Publicitario'
        verbose_name_plural = 'Espacios Publicitarios'

    def __str__(self) -> str:
        return self.title or f"Promo #{self.pk}"


class GalleryLayout(BaseAuditModel):
    """
    Configuración de layouts para la galería de fotos (1x1, 2x2, 3x3, 4x4).
    """
    name = models.CharField(
        max_length=100,
        verbose_name='Nombre del layout',
        help_text='Ej: Grid 3x3, Mosaico 2x2.'
    )
    columns = models.PositiveSmallIntegerField(
        default=3,
        verbose_name='Columnas',
        help_text='Número de columnas del grid (1-4).'
    )
    rows = models.PositiveSmallIntegerField(
        default=3,
        verbose_name='Filas',
        help_text='Número de filas del grid (1-4).'
    )
    css_class = models.CharField(
        max_length=100,
        default='grid-cols-3',
        verbose_name='Clase CSS',
        help_text='Clases Tailwind para el contenedor del grid.'
    )
    max_photos = models.PositiveSmallIntegerField(
        default=9,
        verbose_name='Máximo de fotos',
        help_text='Capacidad máxima del layout (columnas x filas).'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición en la lista de layouts.'
    )

    class Meta:
        ordering = ['sort_order']
        verbose_name = 'Layout de Galería'
        verbose_name_plural = 'Layouts de Galería'

    def __str__(self) -> str:
        return self.name

    def capacity(self) -> int:
        """Retorna la capacidad total del layout."""
        return self.columns * self.rows

    def clean(self):
        expected_capacity = self.columns * self.rows
        if self.max_photos != expected_capacity:
            from django.core.exceptions import ValidationError
            raise ValidationError({
                'max_photos': f'La capacidad debe ser {expected_capacity} ({self.columns}x{self.rows}).'
            })


class GalleryPhoto(BaseAuditModel):
    """
    Fotografía de la galería interactiva del landing page.
    El admin elige explícitamente si la foto ocupa 1x1 o 2x2 celdas del grid.
    """
    DISPLAY_1X1 = '1x1'
    DISPLAY_2X2 = '2x2'

    DISPLAY_SIZE_CHOICES = [
        (DISPLAY_1X1, '1×1 — Rectangular / cuadrada'),
        (DISPLAY_2X2, '2×2 — Vertical (formato celular)'),
    ]

    image = models.ImageField(
        upload_to='landingpage/gallery/photos/',
        verbose_name='Fotografía',
        help_text='Imagen de la galería (máximo 5MB).'
    )
    redirect_url = models.URLField(
        blank=True,
        default='',
        verbose_name='URL de redirección',
        help_text='Destino al hacer clic (opcional).'
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='Título',
        help_text='Título o leyenda de la foto.'
    )
    alt_text = models.CharField(
        max_length=255,
        verbose_name='Texto alternativo (SEO)',
        help_text='Descripción para SEO y accesibilidad.'
    )
    display_size = models.CharField(
        max_length=3,
        choices=DISPLAY_SIZE_CHOICES,
        default=DISPLAY_1X1,
        verbose_name='Tamaño de celda',
        help_text='1×1 para fotos rectangulares, 2×2 para verticales destacadas (formato celular).'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición en la galería.'
    )

    class Meta:
        ordering = ['sort_order']
        verbose_name = 'Foto de Galería'
        verbose_name_plural = 'Fotos de Galería'

    def __str__(self) -> str:
        return self.title or f"Gallery Photo #{self.pk}"

    def display_classes(self) -> str:
        """Clases CSS de span del grid (4 cols, filas ~35vh).
        - 1x1 = 1 celda (col-span-1 row-span-1) — rectangular/cuadrada.
        - 2x2 = 4 celdas (col-span-2 row-span-2) — caben 2 fotos verticales."""
        if self.display_size == self.DISPLAY_1X1:
            return 'col-span-1 row-span-1'
        return 'col-span-2 row-span-2'
