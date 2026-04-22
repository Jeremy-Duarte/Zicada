from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from apps.core.models import BaseAuditModel
from django.utils import timezone

class Size(models.Model):
    # Catálogo de tallas (sin auditoría, es estático).
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


class Category(models.Model):
    # Catálogo de categorías (sin auditoría, es estático).
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Categoría',
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
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Color(models.Model):
    # Catálogo de colores (sin auditoría, es estático).
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
    

class Product(BaseAuditModel):
    # Producto del catálogo.
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
        verbose_name='Categoría',
        help_text='Categoría a la que pertenece el producto'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
    
    def __str__(self):
        return self.name
    
    def clean(self):
        if self.price <= 0:
            raise ValidationError({'price': 'El precio debe ser mayor a 0.'})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()
        super().save(*args, **kwargs)


class ProductVariant(BaseAuditModel):
    # Variante por talla y color.
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name='Producto'
    )
    size = models.ForeignKey(
        Size,
        on_delete=models.PROTECT,
        related_name='variants',
        verbose_name='Talla'
    )
    color = models.ForeignKey(
        Color,
        on_delete=models.PROTECT,
        related_name='variants',
        verbose_name='Color',
        help_text='Color de esta variante'
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
    image = models.ImageField(
        upload_to='products/variants/',
        blank=True,
        null=True,
        verbose_name='Imagen',
        help_text='Imagen de la variante'
    )
    is_portrait = models.BooleanField(
        default=False,
        verbose_name='Imagen destacada',
        help_text='Si es True, muestra esta imagen como destacada en el catálogo'
    )
    
    class Meta:
        unique_together = ['product', 'size', 'color']
        verbose_name = 'Variante de producto'
        verbose_name_plural = 'Variantes de productos'
        ordering = ['product', 'size__sort_order', 'color__sort_order']
    
    def __str__(self):
        return f"{self.product.name} - {self.size.name} - {self.color.name}"
    
    def clean(self):
        if self.stock < 0:
            raise ValidationError({'stock': 'El stock no puede ser negativo.'})
    
    def save(self, *args, **kwargs):
        # Generar SKU automáticamente si no existe
        if not self.sku:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.sku = f"ZCD-{self.product.id}-{self.size.name}-{self.color.name}-{timestamp}"
       
        self.full_clean()
        super().save(*args, **kwargs)


class Collection(BaseAuditModel):
    # Colecciones temáticas
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
        verbose_name='Estado',
        help_text='Borrador (no visible), Publicada (visible), Archivada (oculta)'
    )
    style_config = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Configuración visual',
        help_text='JSON con colores, fondos, tipografías para la colección'
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
    
    def __str__(self):
        return self.name
    
    def update_products_type(self):
        """
        Actualiza el tipo de producto de todos los productos de esta colección.
        Si la colección está publicada, los productos pasan a 'coleccion_limitada'.
        Si está archivada o borrador, pasan a 'fabrica' (pero cuidado: un producto puede estar en varias colecciones).
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
        # Validar fechas
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError({
                    'end_date': 'La fecha de fin debe ser posterior a la fecha de inicio.'
                })
        
        # Validar que una colección publicada tenga al menos un producto
        if self.status == 'publicada' and not self.products.exists():
            raise ValidationError({
                'status': 'Una colección publicada debe tener al menos un producto asignado.'
            })
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()
        super().save(*args, **kwargs)