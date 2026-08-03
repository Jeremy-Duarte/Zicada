from datetime import datetime

from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.text import slugify
from apps.core.models import BaseAuditModel
from django.utils import timezone
from apps.products.constants import STOCK_LOW_THRESHOLD

# =============================================================================
# CONSTANTES PARA MODELOS
# =============================================================================

# Strings duplicados
VERBOSE_CATEGORY = 'Categoría'
DEFAULT_TITLE_FONT = "'Inter', sans-serif"

# Valores por defecto para configuración de tarjetas
DEFAULT_BADGE_TEXT_COLOR = '#ffffff'
DEFAULT_CARD_BORDER_RADIUS = '0.5rem'
DEFAULT_CARD_SHADOW = '0 1px 3px 0 rgba(0,0,0,0.1)'
DEFAULT_CARD_HOVER_SHADOW = '0 20px 25px -5px rgba(0,0,0,0.15)'
DEFAULT_HOVER_SCALE = 1.05
DEFAULT_SHOW_CATEGORY = True
DEFAULT_SHOW_STOCK_BADGE = True

# Colores por defecto
DEFAULT_PRIMARY_COLOR = '#c2a575'
DEFAULT_SECONDARY_COLOR = '#8b5e3c'
DEFAULT_BACKGROUND_COLOR = '#ffffff'
DEFAULT_TEXT_COLOR = '#1a1a1a'


# =============================================================================
# SIZE MODEL (HU-058 a HU-062)
# =============================================================================

class Size(models.Model):
    """
    HU-058: Listar tallas
    HU-059: Crear talla
    HU-060: Editar talla
    HU-061: Eliminar talla
    HU-062: Importar tallas
    """
    name = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Talla',
        help_text='Ej: XS, S, M, L, XL, XXL, 6M'
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición (0, 1, 2...)'
    )
    
    class Meta:
        ordering = ['sort_order']
        verbose_name = 'Talla'
        verbose_name_plural = 'Tallas'
    
    def __str__(self):
        return self.name


# =============================================================================
# CATEGORY MODEL (HU-063 a HU-067)
# =============================================================================

class Category(models.Model):
    """
    HU-063: Listar categorías
    HU-064: Crear categoría
    HU-065: Editar categoría
    HU-066: Eliminar categoría
    HU-067: Importar categorías
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=VERBOSE_CATEGORY,
        help_text='Ej: Camisetas, Hoodies, Pantalones, Accesorios'
    )
    slug = models.SlugField(
        max_length=60,
        unique=True,
        verbose_name='Slug',
        help_text='URL amigable (ej: camisetas, hoodies)'
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición en filtros'
    )
    
    class Meta:
        ordering = ['sort_order']
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # HU-064 | ESCENARIO 1 | H | Guarda la categoría generando slug automáticamente
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# =============================================================================
# COLOR MODEL (HU-068 a HU-072)
# =============================================================================

class Color(models.Model):
    """
    HU-068: Listar colores
    HU-069: Crear color
    HU-070: Editar color
    HU-071: Eliminar color
    HU-072: Importar colores
    """
    name = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='Color',
        help_text='Ej: Negro, Blanco, Rojo, Azul, Verde'
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Código hexadecimal',
        help_text='Ej: #000000, #FFFFFF, #FF0000'
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición en filtros (0, 1, 2...)'
    )
    
    class Meta:
        ordering = ['sort_order']
        verbose_name = 'Color'
        verbose_name_plural = 'Colores'
    
    def __str__(self):
        return self.name


# =============================================================================
# PRODUCT IMAGE MODEL (HU-073 a HU-076)
# =============================================================================

class ProductImage(models.Model):
    """
    HU-073: Listar imágenes de producto
    HU-074: Subir imagen de producto
    HU-075: Editar imagen de producto
    HU-076: Eliminar imagen de producto
    """
    image = models.ImageField(
        upload_to='products/images/',
        verbose_name='Imagen'
    )
    alt_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Texto alternativo'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Imagen'
        verbose_name_plural = 'Imágenes'

    def __str__(self):
        if self.alt_text:
            return self.alt_text
        return f"Imagen {self.id}"


# =============================================================================
# PRODUCT COLOR MODEL (HU-013 - Gestionar tallas y stock)
# =============================================================================

class ProductColor(BaseAuditModel):
    """
    HU-013 | ESCENARIO 1 | H | Asignar colores a un producto
    HU-013 | ESCENARIO 2 | H | Actualizar imágenes y orden de colores
    HU-013 | ESCENARIO 4 | A | Deshabilitar/eliminar un color del producto
    """
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='product_colors'
    )
    color = models.ForeignKey(
        Color,
        on_delete=models.PROTECT,
        related_name='product_colors'
    )
    images = models.ManyToManyField(
        ProductImage,
        blank=True,
        related_name='product_colors',
        verbose_name='Imágenes'
    )
    featured_image = models.ForeignKey(
        ProductImage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name='Imagen destacada'
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name='Orden')

    class Meta:
        unique_together = ['product', 'color']
        ordering = ['sort_order']
        verbose_name = 'Color del producto'
        verbose_name_plural = 'Colores del producto'

    def __str__(self):
        return f"{self.product.name} - {self.color.name}"

    def get_images(self):
        # HU-006 | ESCENARIO 1 | H | Obtiene imágenes del producto incluyendo la destacada primero
        qs = self.images.all()
        if self.featured_image and self.featured_image in qs:
            return [self.featured_image] + list(qs.exclude(id=self.featured_image.id))
        return list(qs)


# =============================================================================
# PRODUCT MODEL (HU-004 a HU-013)
# =============================================================================

class Product(BaseAuditModel):
    """
    HU-004: Consultar catálogo
    HU-006: Consultar detalle de producto
    HU-007: Filtrar productos
    HU-008: Consultar disponibilidad de talla
    HU-009: Listar productos (admin)
    HU-010: Crear producto
    HU-011: Editar producto
    HU-012: Eliminar producto
    HU-013: Gestionar tallas y stock
    """
    PRODUCT_TYPES = [
        ('fabrica', 'Producto de fábrica'),
        ('coleccion_limitada', 'Colección limitada'),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name='Nombre',
        help_text='Nombre del producto'
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        verbose_name='Slug',
        help_text='URL amigable (se genera automáticamente)'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada del producto'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio (COP)',
        help_text='Precio en pesos colombianos'
    )
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPES,
        default='fabrica',
        verbose_name='Tipo de producto',
        help_text='"Producto de fábrica" o "Colección limitada"'
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=VERBOSE_CATEGORY,
        help_text='Categoría a la que pertenece el producto'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        indexes = [
            models.Index(fields=['product_type', 'is_active']),
        ]
    
    def total_stock(self):
        # HU-009 | ESCENARIO 1 | H | Calcula stock total del producto
        return sum(v.stock for v in self.variants.filter(is_active=True))

    def stock_by_size_color(self):
        # HU-008 | ESCENARIO 1,2,3 | H/A | Retorna stock agrupado por talla y color
        result = {}
        for variant in self.variants.filter(is_active=True).select_related('size', 'product_color__color'):
            key = f"{variant.size.name}-{variant.color.name}"
            result[key] = variant.stock
        return result

    def available_variants(self):
        # HU-008 | ESCENARIO 1 | H | Retorna variantes con stock disponible
        return self.variants.filter(is_active=True, stock__gt=0).select_related('size', 'product_color__color')

    def is_available(self):
        # HU-006 | ESCENARIO 3 | A | Verifica si hay al menos una variante disponible
        return self.variants.filter(is_active=True, stock__gt=0).exists()
    
    def _get_featured_image_from_prefetched(self):
        """Obtiene imagen destacada usando caché prefetched."""
        for product_color in self.product_colors.all():
            if product_color.featured_image:
                return product_color.featured_image
            first_image = product_color.images.first()
            if first_image:
                return first_image
        return None

    def _get_featured_image_from_db(self):
        """Obtiene imagen destacada consultando directamente la BD."""
        for product_color in self.product_colors.filter(is_active=True).order_by('sort_order'):
            if product_color.featured_image:
                return product_color.featured_image
            first_image = product_color.images.first()
            if first_image:
                return first_image
        return None

    def get_featured_image(self):
        # HU-006 | ESCENARIO 1 | H | Obtiene la imagen destacada del producto
        if hasattr(self, '_prefetched_objects_cache') and 'product_colors' in self._prefetched_objects_cache:
            return self._get_featured_image_from_prefetched()
        return self._get_featured_image_from_db()

    def __str__(self):
        return self.name
    
    def clean(self):
        # HU-010 | ESCENARIO 2 | A | Validación: precio mayor a 0
        if self.price is not None and self.price <= 0:
            raise ValidationError({'price': 'El precio debe ser mayor a 0.'})
    
    def save(self, *args, **kwargs):
        # HU-010 | ESCENARIO 1 | H | Guarda producto generando slug automáticamente
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()
        super().save(*args, **kwargs)

    def soft_delete(self, *args, **kwargs):
        if self.variants.filter(order_items__isnull=False).exists():
            raise ValidationError('No se puede eliminar el producto porque está asociado a pedidos existentes.')
        super().soft_delete(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.variants.filter(order_items__isnull=False).exists():
            raise ValidationError('No se puede eliminar el producto porque está asociado a pedidos existentes.')
        super().delete(*args, **kwargs)


# =============================================================================
# PRODUCT VARIANT MANAGER (HU-008, HU-013)
# =============================================================================

class ProductVariantManager(models.Manager):
    def available(self):
        # HU-008 | ESCENARIO 1 | H | Retorna variantes disponibles
        return self.filter(is_active=True, stock__gt=0)
    
    def in_stock(self):
        # HU-008 | ESCENARIO 1 | H | Retorna variantes con stock > 0
        return self.filter(stock__gt=0)
    
    def out_of_stock(self):
        # HU-008 | ESCENARIO 2 | A | Retorna variantes agotadas
        return self.filter(is_active=True, stock=0)
    
    def low_stock(self, threshold=STOCK_LOW_THRESHOLD):
        # HU-008 | ESCENARIO 2 | A | Retorna variantes con stock bajo
        return self.filter(is_active=True, stock__gt=0, stock__lte=threshold)
    
    def for_product(self, product):
        return self.filter(product=product).select_related('size', 'product_color__color')
    
    def by_size_color(self, size_id=None, color_id=None):
        qs = self.all()
        if size_id:
            qs = qs.filter(size_id=size_id)
        if color_id:
             qs = qs.filter(product_color__color_id=color_id)
        return qs


# =============================================================================
# PRODUCT VARIANT MODEL (HU-008, HU-013)
# =============================================================================

class ProductVariant(BaseAuditModel):
    """
    HU-008: Consultar disponibilidad de talla
    HU-013 | ESCENARIO 1 | H | Asignar tallas y stock
    HU-013 | ESCENARIO 2 | H | Actualizar stock
    HU-013 | ESCENARIO 3 | E | Stock negativo no permitido
    HU-013 | ESCENARIO 4 | A | Deshabilitar talla (soft delete)
    HU-013 | ESCENARIO 5 | H | Stock automático al crear pedido
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name='Producto'
    )
    product_color = models.ForeignKey(
        ProductColor,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name='Producto y color',
        help_text='Asociación producto-color que define las imágenes'
    )
    size = models.ForeignKey(
        Size,
        on_delete=models.PROTECT,
        related_name='variants',
        verbose_name='Talla'
    )
    sku = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='SKU',
        help_text='Código interno único (se genera automáticamente)'
    )
    stock = models.PositiveIntegerField(
        default=0,
        verbose_name='Stock',
        help_text='Cantidad disponible (no puede ser negativo)'
    )

    objects = ProductVariantManager()

    class Meta:
        unique_together = ['product', 'product_color', 'size']
        indexes = [
            models.Index(fields=['stock']),
            models.Index(fields=['is_active', 'stock']),
            models.Index(fields=['product', 'product_color']),
            models.Index(fields=['size']),
        ]
        verbose_name = 'Variante de producto'
        verbose_name_plural = 'Variantes de productos'
        ordering = ['product', 'product_color__sort_order', 'size__sort_order']

    @property
    def color(self):
        return self.product_color.color

    @property
    def color_name(self):
        return self.product_color.color.name

    @property
    def color_code(self):
        return self.product_color.color.code

    @property
    def images(self):
        return self.product_color.get_images()

    @property
    def featured_image(self):
        return self.product_color.featured_image

    @property
    def stock_status(self):
        """
        HU-008 | ESCENARIO 1 | H | Stock disponible
        HU-008 | ESCENARIO 2 | A | Stock agotado o bajo
        """
        if not self.is_active:
            return 'discontinued'
        if self.stock == 0:
            return 'out_of_stock'
        if self.stock <= STOCK_LOW_THRESHOLD:
            return 'low_stock'
        return 'available'

    @property
    def is_available(self):
        # HU-008 | ESCENARIO 1 | H | Verifica disponibilidad
        return self.is_active and self.stock > 0

    def get_stock_display(self):
        # HU-008 | ESCENARIO 1,2 | H/A | Retorna mensaje amigable de stock
        status = self.stock_status
        if status == 'available':
            return f"{self.stock} disponibles"
        elif status == 'low_stock':
            return f"¡Últimas {self.stock} unidades!"
        elif status == 'out_of_stock':
            return "Agotado"
        else:
            return "No disponible"

    def __str__(self):
        return f"{self.product.name} - {self.product_color.color.name} - {self.size.name}"

    def clean(self):
        """
        HU-013 | ESCENARIO 3 | E | Stock negativo no permitido
        HU-013 | ESCENARIO 3 | E | ProductColor no pertenece al producto
        """
        if self.stock < 0:
            raise ValidationError({'stock': 'El stock no puede ser negativo.'})
    
    def save(self, *args, **kwargs):
        # HU-013 | ESCENARIO 1 | H | Genera SKU automáticamente
        if not self.sku:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.sku = f"ZCD-{self.product.id}-{self.product_color.color.name}-{self.size.name}-{timestamp}"

        self.full_clean()
        super().save(*args, **kwargs)


# =============================================================================
# COLLECTION MODEL (HU-005, HU-014 a HU-018)
# =============================================================================

class Collection(BaseAuditModel):
    """
    HU-005: Consultar colecciones (público)
    HU-014: Listar colecciones (admin)
    HU-015: Crear colección
    HU-016: Editar colección
    HU-017: Eliminar colección
    HU-018: Asignar productos a colección
    """
    STATUS_CHOICES = [
        ('borrador', 'Borrador'),
        ('publicada', 'Publicada'),
        ('archivada', 'Archivada'),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name='Nombre',
        help_text='Nombre de la colección'
    )
    slug = models.SlugField(
        max_length=110,
        unique=True,
        verbose_name='Slug',
        help_text='URL amigable (se genera automáticamente)'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción o inspiración de la colección'
    )
    start_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de inicio',
        help_text='Fecha en que la colección comienza a ser visible (opcional)'
    )
    end_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de fin',
        help_text='Fecha en que la colección deja de ser visible (opcional)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='borrador',
        db_index=True,
        verbose_name='Estado',
        help_text='Borrador (no visible), Publicada (visible), Archivada (oculta)'
    )
    
    cover_image = models.ImageField(
        upload_to='collections/covers/',
        blank=True,
        null=True,
        verbose_name='Imagen de portada',
        help_text='Imagen que se mostrará en la tarjeta de la colección (recomendado: 800x600px)'
    )
    primary_color = models.CharField(
        max_length=20,
        blank=True,
        default=DEFAULT_PRIMARY_COLOR,
        verbose_name='Color principal',
        help_text='Color de botones, enlaces y acentos'
    )
    secondary_color = models.CharField(
        max_length=20,
        blank=True,
        default=DEFAULT_SECONDARY_COLOR,
        verbose_name='Color secundario',
        help_text='Color para hover y detalles'
    )
    background_color = models.CharField(
        max_length=20,
        blank=True,
        default=DEFAULT_BACKGROUND_COLOR,
        verbose_name='Color de fondo',
        help_text='Color de fondo de la página de la colección'
    )
    text_color = models.CharField(
        max_length=20,
        blank=True,
        default=DEFAULT_TEXT_COLOR,
        verbose_name='Color de texto',
        help_text='Color principal del texto'
    )
    background_image = models.ImageField(
        upload_to='collections/bg/',
        blank=True,
        null=True,
        verbose_name='Imagen de fondo',
        help_text='Imagen de fondo para la página de la colección'
    )
    interactive_background = models.ImageField(
        upload_to='collections/interactive/',
        blank=True,
        null=True,
        verbose_name='Fondo interactivo',
        help_text='Imagen usada para delimitar las zonas clicleables que redirigen a productos'
    )
    title_font = models.CharField(
        max_length=100,
        blank=True,
        default=DEFAULT_TITLE_FONT,
        verbose_name='Fuente de títulos',
        help_text='Ej: "Playfair Display", serif'
    )
    effects_config = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Configuración de efectos',
        help_text='JSON para efectos avanzados (hover, animaciones)'
    )
    custom_css = models.TextField(
        blank=True,
        verbose_name='CSS personalizado',
        help_text='CSS adicional para esta colección (solo si sabes lo que haces)'
    )
    style_config = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Configuración visual (legado)',
        help_text='JSON con configuración visual (se genera automáticamente desde los campos)'
    )
    
    products = models.ManyToManyField(
        Product,
        related_name='collections',
        blank=True,
        verbose_name='Productos',
        help_text='Productos que pertenecen a esta colección'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Colección'
        verbose_name_plural = 'Colecciones'
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_style_config(self):
        # HU-015 | ESCENARIO 4 | H | Obtiene configuración de estilos
        if self.style_config and not self._has_individual_styles():
            return self.style_config
        
        return {
            'cover_image': self.cover_image.url if self.cover_image else None,
            'colors': {
                'primary': self.primary_color or DEFAULT_PRIMARY_COLOR,
                'secondary': self.secondary_color or DEFAULT_SECONDARY_COLOR,
                'background': self.background_color or DEFAULT_BACKGROUND_COLOR,
                'text': self.text_color or DEFAULT_TEXT_COLOR,
            },
            'background_image': self.background_image.url if self.background_image else None,
            'typography': {
                'title_font': self.title_font or DEFAULT_TITLE_FONT,
            },
            'effects': self.effects_config or {},
            'custom_css': self.custom_css or '',
        }
    
    def get_card_config(self):
        """Retorna la configuración de tarjetas para esta colección."""
        self.get_style_config()
        
        if self.style_config and 'card_config' in self.style_config:
            return self.style_config['card_config']
        
        return {
            'background_color': self.background_color or DEFAULT_BACKGROUND_COLOR,
            'text_color': self.text_color or DEFAULT_TEXT_COLOR,
            'title_color': self.primary_color or DEFAULT_PRIMARY_COLOR,
            'price_color': self.primary_color or DEFAULT_PRIMARY_COLOR,
            'badge_background': self.primary_color or DEFAULT_PRIMARY_COLOR,
            'badge_text_color': DEFAULT_BADGE_TEXT_COLOR,
            'border_radius': DEFAULT_CARD_BORDER_RADIUS,
            'shadow': DEFAULT_CARD_SHADOW,
            'hover_shadow': DEFAULT_CARD_HOVER_SHADOW,
            'hover_scale': DEFAULT_HOVER_SCALE,
            'show_category': DEFAULT_SHOW_CATEGORY,
            'show_stock_badge': DEFAULT_SHOW_STOCK_BADGE,
        }
    
    def _has_individual_styles(self):
        return any([
            self.cover_image,
            self.primary_color != DEFAULT_PRIMARY_COLOR,
            self.secondary_color != DEFAULT_SECONDARY_COLOR,
            self.background_color != DEFAULT_BACKGROUND_COLOR,
            self.text_color != DEFAULT_TEXT_COLOR,
            self.background_image,
            self.title_font != DEFAULT_TITLE_FONT,
            self.custom_css,
        ])

    def update_products_type(self):
        """
        HU-015 | ESCENARIO 1 | H | Actualiza tipo de productos al cambiar estado
        HU-016 | ESCENARIO 2 | A | Actualiza tipo al modificar fechas
        HU-017 | ESCENARIO 2 | A | Actualiza tipo al archivar
        HU-017 | ESCENARIO 3 | H | Actualiza tipo al restaurar
        HU-018 | ESCENARIO 4 | A | Previene asignación a múltiples colecciones limitadas
        """
        for product in self.products.all():
            otras_publicadas = product.collections.filter(
                status='publicada',
                is_active=True
            ).exclude(id=self.id)
            
            if self.status == 'publicada' and not otras_publicadas.exists():
                product.product_type = 'coleccion_limitada'
            elif self.status != 'publicada' and not otras_publicadas.exists():
                product.product_type = 'fabrica'
            product.save(update_fields=['product_type'])

    def check_and_update_status(self):
        """
        HU-005 | ESCENARIO 2,3 | A | Actualiza automáticamente estado según fechas
        HU-016 | ESCENARIO 3 | A | Colección expirada cambia a archivada
        """
        changed = False
        hoy = timezone.now()
        
        if self.status == 'publicada' and self.end_date and self.end_date < hoy:
            self.status = 'archivada'
            self.save(update_fields=['status'])
            self.update_products_type()
            changed = True
        
        if self.status == 'borrador' and self.start_date and self.start_date <= hoy:
            self.status = 'publicada'
            self.save(update_fields=['status'])
            self.update_products_type()
            changed = True
        
        return changed
    
    def clean(self):
        """
        HU-015 | ESCENARIO 2 | E | Fechas inválidas (inicio > fin)
        HU-015 | ESCENARIO 3 | E | Nombre duplicado
        HU-015 | ESCENARIO 5 | E | Colección publicada sin productos
        """
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError({
                    'end_date': 'La fecha de fin debe ser posterior a la fecha de inicio.'
                })
        
        if self.pk and self.status == 'publicada' and not self.products.exists():
            raise ValidationError({
                'status': 'Una colección publicada debe tener al menos un producto asignado.'
            })
    
    def save(self, *args, **kwargs):
        # HU-015 | ESCENARIO 1 | H | Guarda colección generando slug automáticamente
        if not self.slug:
            self.slug = slugify(self.name)
        
        existing_card_config = None
        if self.style_config and 'card_config' in self.style_config:
            existing_card_config = self.style_config['card_config']
        
        if self._has_individual_styles():
            self.style_config = self.get_style_config()
        
        if existing_card_config:
            self.style_config['card_config'] = existing_card_config
        
        self.full_clean()
        super().save(*args, **kwargs)


# =============================================================================
# INTERACTIVE ZONE MODEL (colecciones navegables por imagen)
# =============================================================================

class InteractiveZone(BaseAuditModel):
    """
    Zona rectangular clicleable sobre el fondo interactivo de una colección.
    Las coordenadas se guardan en porcentaje (0-100) para soporte responsive.
    """
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name='interactive_zones',
        verbose_name='Colección'
    )
    product_color = models.ForeignKey(
        ProductColor,
        on_delete=models.CASCADE,
        related_name='interactive_zones',
        verbose_name='Color del producto',
        help_text='Producto (y color) al que redirige esta zona'
    )
    x = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Posición X (%)',
        help_text='Porcentaje horizontal desde el borde izquierdo (0-100)'
    )
    y = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Posición Y (%)',
        help_text='Porcentaje vertical desde el borde superior (0-100)'
    )
    width = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Ancho (%)',
        help_text='Ancho de la zona en porcentaje (0-100)'
    )
    height = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Alto (%)',
        help_text='Alto de la zona en porcentaje (0-100)'
    )
    label = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Etiqueta',
        help_text='Etiqueta opcional mostrada al hacer hover'
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name='Orden')

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Zona interactiva'
        verbose_name_plural = 'Zonas interactivas'

    def __str__(self):
        return self.label or f"Zona {self.id} de {self.collection.name}"

    def clean(self):
        """HU: Valida que las coordenadas estén dentro del rango 0-100."""
        errors = {}
        for field in ('x', 'y', 'width', 'height'):
            value = getattr(self, field, None)
            if value is None:
                errors[field] = 'Este campo es obligatorio.'
            elif value < 0 or value > 100:
                errors[field] = 'Debe estar entre 0 y 100.'
        if errors:
            raise ValidationError(errors)
        if self.width is not None and self.width <= 0:
            raise ValidationError({'width': 'El ancho debe ser mayor a 0.'})
        if self.height is not None and self.height <= 0:
            raise ValidationError({'height': 'El alto debe ser mayor a 0.'})
        if (
            self.x is not None and self.width is not None
            and (self.x + self.width) > 100
        ):
            raise ValidationError({'width': 'La zona se sale del ancho de la imagen.'})
        if (
            self.y is not None and self.height is not None
            and (self.y + self.height) > 100
        ):
            raise ValidationError({'height': 'La zona se sale del alto de la imagen.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return (
            f"{reverse('products:product_detail', kwargs={'slug': self.product_color.product.slug})}"
            f"?color={self.product_color.pk}"
        )

    @property
    def product(self):
        return self.product_color.product