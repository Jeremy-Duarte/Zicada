from datetime import timezone
from decimal import Decimal
import decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .models import (
    Size, Category, Color, Product, ProductVariant, 
    Collection, ProductColor, ProductImage
)
from apps.core.crud.mixins import FormStyleMixin, SortableCreateMixin, SortableUpdateMixin
from apps.core.crud.widgets import CloudinaryImageSelectWidget, CloudinaryFeaturedImageWidget, SortableOrderWidget, ProductCheckboxSelectWidget
import re

from apps.core.design_options import (
    FONT_FAMILY_CHOICES, FONT_WEIGHT_CHOICES, FONT_SIZE_CHOICES,
    LINE_HEIGHT_CHOICES, MARGIN_CHOICES, CARD_BORDER_RADIUS_CHOICES,
    CARD_SHADOW_CHOICES, CARD_HOVER_SCALE_CHOICES,
    DEFAULT_BORDER_RADIUS, DEFAULT_BOX_SHADOW, DEFAULT_HOVER_SCALE,
    DEFAULT_SHOW_CATEGORY, DEFAULT_SHOW_STOCK_BADGE,
    DEFAULT_BADGE_TEXT_COLOR, DEFAULT_PRIMARY_COLOR, DEFAULT_SECONDARY_COLOR,
    DEFAULT_BACKGROUND_COLOR, DEFAULT_TEXT_COLOR, DEFAULT_TITLE_FONT, COLOR_PALETTES,
    get_color_palette_choices, apply_color_palette
)

# =============================================================================
# CONSTANTES PARA FORMULARIOS
# =============================================================================

# Estilos
STYLE_COLOR_INPUT = 'height: 40px;'
HEX_COLOR_PATTERN = r'^#(?:[0-9a-fA-F]{3}){1,2}$'

# Mensajes de error
ERROR_PRODUCT_NOT_SPECIFIED = 'Producto no especificado.'
ERROR_CONFIRM_REQUIRED = 'Debes confirmar la eliminación.'
ERROR_COLOR_NOT_SPECIFIED = 'Color no especificado.'
ERROR_CATEGORY_NOT_SPECIFIED = 'Categoría no especificada.'
ERROR_SIZE_NOT_SPECIFIED = 'Talla no especificada.'
ERROR_VARIANT_NOT_SPECIFIED = 'Variante no especificada.'
ERROR_COLLECTION_NOT_SPECIFIED = 'Colección no especificada.'
ERROR_CONFIRM_RESTORE = 'Debes confirmar la restauración.'
ERROR_IMAGE_NOT_SPECIFIED = 'Imagen no especificada.'

# Mensajes de confirmación
CONFIRM_DELETE_PROMPT = 'Escribe el nombre del {} para confirmar'
CONFIRM_DELETE_COLOR = 'Escribe el nombre del color para confirmar'
CONFIRM_DELETE_CATEGORY = 'Escribe el nombre de la categoría para confirmar'
CONFIRM_DELETE_SIZE = 'Escribe el nombre de la talla para confirmar'
CONFIRM_DELETE_PRODUCT = 'Escribe el nombre del producto para confirmar'
CONFIRM_DELETE_COLLECTION = 'Escribe el nombre de la colección para confirmar'
CONFIRM_DELETE_VARIANT = 'Escribe "ELIMINAR" para confirmar'

# Validaciones de precio
MAX_PRICE = 10000000
PRICE_ERROR_POSITIVE = 'El precio debe ser mayor a 0.'
PRICE_ERROR_MAX = f'El precio no puede superar los ${MAX_PRICE:,} COP.'

# Validaciones de imagen
MAX_IMAGE_SIZE = 5 * 1024 * 1024
IMAGE_SIZE_ERROR = 'La imagen no puede superar los 5MB.'
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
IMAGE_EXTENSION_ERROR = 'Formato no soportado. Usa JPG, PNG, WEBP o GIF.'

# Product types
PRODUCT_TYPE_FABRICA = 'fabrica'
PRODUCT_TYPE_COLECCION_LIMITADA = 'coleccion_limitada'

# Order statuses for validation
ORDER_STATUSES_ACTIVE = ['pendiente', 'confirmado', 'preparando', 'listo', 'en_camino']

# Colores por defecto para colecciones
DEFAULT_PRIMARY_COLOR = '#c2a575'
DEFAULT_SECONDARY_COLOR = '#8b5e3c'
DEFAULT_BACKGROUND_COLOR = '#ffffff'
DEFAULT_TEXT_COLOR = '#1a1a1a'
DEFAULT_TITLE_FONT = "'Inter', sans-serif"

# Configuración de tarjetas
DEFAULT_BORDER_RADIUS = '0.5rem'
DEFAULT_BOX_SHADOW = '0 1px 3px 0 rgba(0,0,0,0.1)'
DEFAULT_HOVER_SCALE = 1.05
DEFAULT_SHOW_CATEGORY = True
DEFAULT_SHOW_STOCK_BADGE = True
DEFAULT_BADGE_TEXT_COLOR = '#ffffff'

# Estilos
STYLE_COLOR_PICKER = 'width: 60px; height: 35px; cursor: pointer;'

# Mensajes para colecciones (si no existen)
MSG_COLLECTION_NAME_EXISTS_ACTIVE = 'Ya existe una colección activa con ese nombre.'
MSG_COLLECTION_NAME_EXISTS_DELETED = 'Ya existe una colección con ese nombre (activa o eliminada).'
MSG_COLLECTION_END_DATE_AFTER_START = 'La fecha de fin debe ser posterior a la fecha de inicio.'
MSG_COLLECTION_PUBLISHED_NO_PRODUCTS = 'Una colección publicada debe tener al menos un producto asignado.'
MSG_COLLECTION_PRODUCTS_IN_OTHER_PUBLISHED = 'Los siguientes productos ya pertenecen a otra colección publicada: {}'
MSG_COLLECTION_SLUG_EXISTS = 'Ya existe una colección con ese slug.'
MSG_COLLECTION_SLUG_GENERATED = 'El slug se genera automáticamente si lo dejas vacío.'
MSG_COLLECTION_DATE_PAST_ERROR = 'La fecha de inicio no puede ser anterior a la fecha actual.'
MSG_COLLECTION_RESTORE_ACTIVE_SLUG = 'Ya existe una colección activa con el slug "{}".'
MSG_COLLECTION_CONFIRM_DELETE = 'Escribe el nombre de la colección para confirmar'
MSG_COLLECTION_CONFIRM_RESTORE = 'Confirmo que deseo restaurar esta colección'
MSG_COLLECTION_RESTORE_PRODUCTS_TYPE = 'Actualizar tipo de productos'
MSG_COLLECTION_RESTORE_PRODUCTS_TYPE_HELP = 'Si está activado, los productos de esta colección pasarán a "Colección limitada" si no están en otra colección publicada.'

# Configuración de tarjetas (labels)
LABEL_CARD_BG_COLOR = 'Color de fondo de tarjetas'
LABEL_CARD_TITLE_COLOR = 'Color del título'
LABEL_CARD_PRICE_COLOR = 'Color del precio'
LABEL_CARD_BORDER_RADIUS = 'Radio de borde'
LABEL_CARD_SHADOW = 'Sombra de tarjeta'
LABEL_CARD_HOVER_SCALE = 'Escala al hover'
LABEL_CARD_SHOW_CATEGORY = 'Mostrar categoría'
LABEL_CARD_SHOW_STOCK_BADGE = 'Mostrar badge de stock'


# =============================================================================
# HU-059: SIZE CREATE FORM
# =============================================================================

class SizeCreateForm(FormStyleMixin, SortableCreateMixin, forms.ModelForm):
    """
    HU-059: Crear talla
    Escenarios: H (nombre válido y único), A (nombre duplicado), E (sin permisos)
    """
    class Meta:
        model = Size
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ej: XS, S, M, L, XL'}),
        }
    
    def clean_name(self):
        """
        HU-059 | ESCENARIO 1 | H | Nombre de talla válido y único
        HU-059 | ESCENARIO 2 | A | Nombre duplicado → error
        """
        name = self.cleaned_data.get('name', '').upper().strip()
        if Size.objects.filter(name=name).exists():
            raise ValidationError(f'La talla "{name}" ya existe.')
        return name


# =============================================================================
# HU-060: SIZE UPDATE FORM
# =============================================================================

class SizeUpdateForm(FormStyleMixin, SortableUpdateMixin, forms.ModelForm):
    """
    HU-060: Editar talla
    Escenarios: H (nombre válido y único), A (nombre duplicado), E (sin permisos, talla no existe)
    """
    class Meta:
        model = Size
        fields = ['name']
        widgets = {
            'name': forms.TextInput(),
        }

    sortable_queryset = None
    sortable_label_attr = 'name'
    sortable_widget_name = 'size_order'
    sortable_widget_label = 'Orden de tallas'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sortable_queryset = Size.objects.filter().order_by('sort_order')
        self._setup_sortable_widget()

    def clean_name(self):
        """
        HU-060 | ESCENARIO 1 | H | Nombre de talla válido y único (excluyendo la actual)
        HU-060 | ESCENARIO 2 | A | Nombre duplicado con otra talla → error
        """
        name = self.cleaned_data.get('name', '').upper().strip()
        qs = Size.objects.filter(name=name)
        
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError(f'La talla "{name}" ya existe.')
        
        return name


# =============================================================================
# HU-061: SIZE DELETE FORM
# =============================================================================

class SizeDeleteForm(FormStyleMixin, forms.Form):
    """
    HU-061: Eliminar talla
    Escenarios: H (confirmación correcta y sin variantes), A (nombre no coincide, cancelar), E (sin permisos)
    """
    confirm = forms.CharField(
        required=True,
        label=CONFIRM_DELETE_SIZE,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: M'})
    )
    
    def __init__(self, *args, **kwargs):
        self.size = kwargs.pop('size', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        """
        HU-061 | ESCENARIO 1 | H | Confirmación correcta y talla sin variantes
        HU-061 | ESCENARIO 2 | A | Nombre no coincide → error
        HU-061 | ESCENARIO 4 | A | Talla con variantes activas → error
        """
        value = self.cleaned_data.get('confirm', '').upper().strip()
        
        if not self.size:
            raise ValidationError(ERROR_SIZE_NOT_SPECIFIED)
        
        if self.size.name != value:
            raise ValidationError('El nombre de la talla no coincide.')
        
        if self.size.variants.filter(is_active=True).exists():
            raise ValidationError(
                f'No se puede eliminar la talla "{self.size.name}" porque está siendo usada '
                f'en {self.size.variants.count()} variante(s) activas.'
            )
        
        return value


# =============================================================================
# HU-064: CATEGORY CREATE FORM
# =============================================================================

class CategoryCreateForm(FormStyleMixin, SortableCreateMixin, forms.ModelForm):
    """
    HU-064: Crear categoría
    Escenarios: H (nombre válido y único), A (nombre duplicado), E (sin permisos)
    """
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ej: Camisetas, Hoodies'}),
        }
    
    def clean_name(self):
        """
        HU-064 | ESCENARIO 1 | H | Nombre de categoría válido y único
        HU-064 | ESCENARIO 2 | A | Nombre duplicado → error
        """
        name = self.cleaned_data.get('name', '').strip()
        
        if Category.objects.filter(name__iexact=name).exists():
            raise ValidationError(f'La categoría "{name}" ya existe.')
        
        return name


# =============================================================================
# HU-065: CATEGORY UPDATE FORM
# =============================================================================

class CategoryUpdateForm(FormStyleMixin, SortableUpdateMixin, forms.ModelForm):
    """
    HU-065: Editar categoría
    Escenarios: H (nombre válido), A (nombre duplicado), E (sin permisos, categoría no existe)
    """
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(),
        }

    sortable_queryset = None
    sortable_label_attr = 'name'
    sortable_widget_name = 'category_order'
    sortable_widget_label = 'Orden de categorías'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sortable_queryset = Category.objects.filter().order_by('sort_order')
        self._setup_sortable_widget()

    def clean_name(self):
        """
        HU-065 | ESCENARIO 1 | H | Nombre de categoría válido y único (excluyendo la actual)
        HU-065 | ESCENARIO 2 | A | Nombre duplicado con otra categoría → error
        """
        name = self.cleaned_data.get('name', '').strip()
        qs = Category.objects.filter(name__iexact=name)
        
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError(f'La categoría "{name}" ya existe.')
        
        return name
    
    def save(self, commit=True):
        # HU-065 | ESCENARIO 1 | H | Genera slug automáticamente al guardar
        instance = super().save(commit=False)
        instance.slug = slugify(instance.name)
        
        if commit:
            instance.save()
        
        return instance


# =============================================================================
# HU-066: CATEGORY DELETE FORM
# =============================================================================

class CategoryDeleteForm(FormStyleMixin, forms.Form):
    """
    HU-066: Eliminar categoría
    Escenarios: H (confirmación correcta y sin productos), A (nombre no coincide), E (sin permisos)
    """
    confirm = forms.CharField(
        required=True,
        label=CONFIRM_DELETE_CATEGORY,
        widget=forms.TextInput()
    )
    
    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        """
        HU-066 | ESCENARIO 1 | H | Confirmación correcta y categoría sin productos activos
        HU-066 | ESCENARIO 2 | A | Nombre no coincide → error
        HU-066 | ESCENARIO 4 | A | Categoría con productos activos → error
        """
        value = self.cleaned_data.get('confirm', '').strip().lower()
        
        if not self.category:
            raise ValidationError(ERROR_CATEGORY_NOT_SPECIFIED)
        
        if self.category.name.lower() != value:
            raise ValidationError('El nombre de la categoría no coincide.')
        
        active_products = self.category.products.filter(is_active=True)
        if active_products.exists():
            raise ValidationError(
                f'No se puede eliminar la categoría "{self.category.name}" porque tiene '
                f'{active_products.count()} producto(s) activo(s).'
            )
        
        return value


# =============================================================================
# HU-067: CATEGORY IMPORT FORM (soporte para importación)
# =============================================================================

class CategoryImportForm(forms.ModelForm):
    """
    HU-067: Importar categorías (formulario base para cada fila)
    Escenarios: H (nombre válido), A (nombre duplicado), E (sin permisos)
    """
    class Meta:
        model = Category
        fields = ['name']
    
    def clean_name(self):
        """
        HU-067 | ESCENARIO 2 | H | Nombre válido para importación
        HU-067 | ESCENARIO 3 | A | Nombre duplicado → error (fila no se importa)
        """
        name = self.cleaned_data.get('name', '').strip()
        if Category.objects.filter(name__iexact=name).exists():
            raise ValidationError(f'La categoría "{name}" ya existe.')
        return name


# =============================================================================
# HU-069: COLOR CREATE FORM
# =============================================================================

class ColorCreateForm(FormStyleMixin, SortableCreateMixin, forms.ModelForm):
    """
    HU-069: Crear color
    Escenarios: H (nombre y código válidos y únicos), A (nombre/código duplicado o código inválido), E (sin permisos)
    """
    class Meta:
        model = Color
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(),
            'code': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_INPUT}),
        }
    
    def clean_name(self):
        """
        HU-069 | ESCENARIO 1 | H | Nombre de color válido y único
        HU-069 | ESCENARIO 2 | A | Nombre duplicado → error
        """
        name = self.cleaned_data.get('name', '').strip().capitalize()
        if Color.objects.filter(name__iexact=name).exists():
            raise ValidationError(f'El color "{name}" ya existe.')
        return name
    
    def clean_code(self):
        """
        HU-069 | ESCENARIO 1 | H | Código hexadecimal válido y único
        HU-069 | ESCENARIO 2 | A | Código inválido o duplicado → error
        """
        code = self.cleaned_data.get('code', '').strip()
        if not code.startswith('#'):
            code = f'#{code}'
        
        if not re.match(HEX_COLOR_PATTERN, code):
            raise ValidationError('El código debe ser un color hexadecimal válido (ej: #FF0000, #F00)')
        
        if Color.objects.filter(code__iexact=code).exists():
            raise ValidationError(f'El código de color "{code}" ya está en uso.')
        
        return code


# =============================================================================
# HU-070: COLOR UPDATE FORM
# =============================================================================

class ColorUpdateForm(FormStyleMixin, SortableUpdateMixin, forms.ModelForm):
    """
    HU-070: Editar color
    Escenarios: H (nombre/código válidos), A (duplicado), E (sin permisos, color no existe)
    """
    class Meta:
        model = Color
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(),
            'code': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_INPUT}),
        }

    sortable_queryset = None
    sortable_label_attr = 'name'
    sortable_widget_name = 'color_order'
    sortable_widget_label = 'Orden de colores'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sortable_queryset = Color.objects.filter().order_by('sort_order')
        self._setup_sortable_widget()

    def clean_name(self):
        """
        HU-070 | ESCENARIO 1 | H | Nombre de color válido y único (excluyendo el actual)
        HU-070 | ESCENARIO 2 | A | Nombre duplicado con otro color → error
        """
        name = self.cleaned_data.get('name', '').strip().capitalize()
        qs = Color.objects.filter(name__iexact=name)
        
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError(f'El color "{name}" ya existe.')
        
        return name
    
    def clean_code(self):
        """
        HU-070 | ESCENARIO 1 | H | Código hexadecimal válido y único (excluyendo el actual)
        HU-070 | ESCENARIO 2 | A | Código inválido o duplicado con otro color → error
        """
        code = self.cleaned_data.get('code', '').strip()
        if not code.startswith('#'):
            code = f'#{code}'
        
        if not re.match(HEX_COLOR_PATTERN, code):
            raise ValidationError('El código debe ser un color hexadecimal válido (ej: #FF0000, #F00)')
        
        qs = Color.objects.filter(code__iexact=code)
        
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError(f'El código de color "{code}" ya está en uso.')
        
        return code


# =============================================================================
# HU-071: COLOR DELETE FORM
# =============================================================================

class ColorDeleteForm(FormStyleMixin, forms.Form):
    """
    HU-071: Eliminar color
    Escenarios: H (confirmación correcta y sin variantes), A (nombre no coincide), E (sin permisos)
    """
    confirm = forms.CharField(
        required=True,
        label=CONFIRM_DELETE_COLOR,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Rojo'})
    )
    
    def __init__(self, *args, **kwargs):
        self.color = kwargs.pop('color', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        """
        HU-071 | ESCENARIO 1 | H | Confirmación correcta y color sin variantes
        HU-071 | ESCENARIO 2 | A | Nombre no coincide → error
        HU-071 | ESCENARIO 4 | A | Color con variantes activas → error
        """
        value = self.cleaned_data.get('confirm', '').strip().capitalize()
        
        if not self.color:
            raise ValidationError(ERROR_COLOR_NOT_SPECIFIED)
        
        if self.color.name != value:
            raise ValidationError('El nombre del color no coincide.')
        
        if self.color.product_colors.filter(is_active=True).exists():
            count = self.color.product_colors.filter(is_active=True).count()
            raise ValidationError(
                f'No se puede eliminar el color "{self.color.name}" porque está siendo usado '
                f'en {count} variante(s) de producto(s).'
            )
        
        return value


# =============================================================================
# HU-072: COLOR IMPORT FORM (soporte para importación)
# =============================================================================

class ColorImportForm(forms.ModelForm):
    """
    HU-072: Importar colores (formulario base para cada fila)
    Escenarios: H (nombre/código válidos), A (duplicado o código inválido), E (sin permisos)
    """
    class Meta:
        model = Color
        fields = ['name', 'code']
    
    def clean_name(self):
        """
        HU-072 | ESCENARIO 2 | H | Nombre válido para importación
        HU-072 | ESCENARIO 3 | A | Nombre duplicado → error (fila no se importa)
        """
        name = self.cleaned_data.get('name', '').capitalize().strip()
        if Color.objects.filter(name__iexact=name).exists():
            raise ValidationError(f'El color "{name}" ya existe.')
        return name
    
    def clean_code(self):
        """
        HU-072 | ESCENARIO 2 | H | Código válido para importación
        HU-072 | ESCENARIO 3 | A | Código inválido o duplicado → error
        """
        code = self.cleaned_data.get('code', '').strip()
        if not code.startswith('#'):
            code = f'#{code}'
        if not re.match(HEX_COLOR_PATTERN, code):
            raise ValidationError(f'"{code}" no es un código hexadecimal válido.')
        if Color.objects.filter(code__iexact=code).exists():
            raise ValidationError(f'El código de color "{code}" ya está en uso.')
        return code


# =============================================================================
# HU-074: PRODUCT IMAGE CREATE FORM
# =============================================================================

class ProductImageCreateForm(FormStyleMixin, forms.ModelForm):
    """
    HU-074: Subir imagen de producto
    Escenarios: H (imagen válida), A (tamaño excedido o formato no soportado), E (sin permisos)
    """
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'alt_text': forms.TextInput(attrs={'placeholder': 'Descripción de la imagen para SEO'}),
        }
    
    def clean_image(self):
        """
        HU-074 | ESCENARIO 1 | H | Imagen válida (tamaño y formato correctos)
        HU-074 | ESCENARIO 2 | A | Tamaño excedido (max 5MB) → error
        HU-074 | ESCENARIO 2 | A | Formato no soportado → error
        """
        image = self.cleaned_data.get('image')
        
        if image:
            if image.size > MAX_IMAGE_SIZE:
                raise ValidationError(IMAGE_SIZE_ERROR)
            
            import os
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                raise ValidationError(IMAGE_EXTENSION_ERROR)
        
        return image


# =============================================================================
# HU-075: PRODUCT IMAGE UPDATE FORM
# =============================================================================

class ProductImageUpdateForm(FormStyleMixin, forms.ModelForm):
    """
    HU-075: Editar imagen de producto (texto alternativo)
    Escenarios: H (alt_text válido), A (errores), E (sin permisos, imagen no existe)
    """
    class Meta:
        model = ProductImage
        fields = ['alt_text']
        widgets = {
            'alt_text': forms.TextInput(),
        }


# =============================================================================
# HU-076: PRODUCT IMAGE DELETE FORM
# =============================================================================

class ProductImageDeleteForm(FormStyleMixin, forms.Form):
    """
    HU-076: Eliminar imagen de producto
    Escenarios: H (confirmación correcta), A (cancelar), E (sin permisos, imagen no especificada)
    """
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que deseo eliminar esta imagen permanentemente'
    )
    
    def __init__(self, *args, **kwargs):
        self.image = kwargs.pop('image', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        """
        HU-076 | ESCENARIO 1 | H | Confirmación correcta
        HU-076 | ESCENARIO 2 | A | Confirmación no marcada → error
        """
        cleaned_data = super().clean()
        
        if not self.image:
            raise ValidationError(ERROR_IMAGE_NOT_SPECIFIED)
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError(ERROR_CONFIRM_REQUIRED)
        
        return cleaned_data


# =============================================================================
# HU-010: PRODUCT CREATE FORM
# =============================================================================

class ProductCreateForm(FormStyleMixin, forms.ModelForm):
    """
    HU-010: Crear producto
    Escenarios: H (datos válidos), A (errores en formulario), E (sin permisos)
    """
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'product_type', 'category']
        widgets = {
            'name': forms.TextInput(),
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'min': 0, 'step': 100}),
            'product_type': forms.Select(),
            'category': forms.Select(),
        }
    
    def clean_name(self):
        """
        HU-010 | ESCENARIO 1 | H | Nombre de producto válido y único
        HU-010 | ESCENARIO 2 | A | Nombre vacío (error de required)
        HU-010 | ESCENARIO 3 | A | Nombre duplicado (activo o eliminado) → error
        """
        name = self.cleaned_data.get('name', '').strip()
        
        if Product.all_objects.filter(name__iexact=name).exists():
            raise ValidationError('Ya existe un producto con ese nombre (activo o eliminado).')
        
        return name
    
    def clean_price(self):
        """
        HU-010 | ESCENARIO 1 | H | Precio válido (>0 y ≤ MAX_PRICE)
        HU-010 | ESCENARIO 2 | A | Precio <= 0 o excede máximo → error
        """
        price = self.cleaned_data.get('price')
        
        if price is None or price == '':
            raise ValidationError('El precio es obligatorio.')
        
        try:
            if isinstance(price, str):
                price = Decimal(price)
            elif isinstance(price, (int, float)):
                price = Decimal(str(price))
        except (ValueError, TypeError):
            raise ValidationError('Ingrese un precio válido.')
        
        if price <= 0:
            raise ValidationError('El precio debe ser mayor a 0.')
        
        if price > MAX_PRICE:
            raise ValidationError(f'El precio no puede superar los ${MAX_PRICE:,.0f} COP.')
        
        return price

# =============================================================================
# HU-011: PRODUCT UPDATE FORM
# =============================================================================

class ProductUpdateForm(FormStyleMixin, forms.ModelForm):
    """
    HU-011: Editar producto
    Escenarios: H (datos válidos), A (errores), E (sin permisos, producto no existe)
    """
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'product_type', 'category', 'is_active']
        widgets = {
            'name': forms.TextInput(),
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'min': 0, 'step': 100}),
            'product_type': forms.Select(),
            'category': forms.Select(),
            'is_active': forms.CheckboxInput(),
        }
    
    def clean_name(self):
        """
        HU-011 | ESCENARIO 1 | H | Nombre válido y único (excluyendo el actual)
        HU-011 | ESCENARIO 2 | A | Nombre duplicado con otro producto activo → error
        """
        name = self.cleaned_data.get('name', '').strip()
        qs = Product.objects.filter(name__iexact=name)
        
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError('Ya existe un producto activo con ese nombre.')
        
        return name
    
    def clean_price(self):
        """
        HU-011 | ESCENARIO 1 | H | Precio válido
        HU-011 | ESCENARIO 2 | A | Precio <= 0 o excede máximo → error
        """
        price = self.cleaned_data.get('price', 0)
        
        if price <= 0:
            raise ValidationError(PRICE_ERROR_POSITIVE)
        
        if price > MAX_PRICE:
            raise ValidationError(PRICE_ERROR_MAX)
        
        return price


# =============================================================================
# HU-012: PRODUCT DELETE FORM
# =============================================================================

class ProductDeleteForm(FormStyleMixin, forms.Form):
    """
    HU-012: Eliminar producto (soft delete)
    Escenarios: H (confirmación correcta), A (nombre no coincide), E (sin permisos, producto con pedidos)
    """
    confirm = forms.CharField(
        required=True,
        label=CONFIRM_DELETE_PRODUCT,
        widget=forms.TextInput()
    )
    
    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        """
        HU-012 | ESCENARIO 1 | H | Confirmación correcta
        HU-012 | ESCENARIO 2 | A | Producto con pedidos en curso → error
        HU-012 | ESCENARIO 3 | A | Nombre no coincide → error
        """
        value = self.cleaned_data.get('confirm', '').strip().lower()
        
        if not self.product:
            raise ValidationError(ERROR_PRODUCT_NOT_SPECIFIED)
        
        if self.product.name.lower() != value:
            raise ValidationError('El nombre del producto no coincide.')
        
        has_orders = self.product.variants.filter(
            order_items__order__status__in=ORDER_STATUSES_ACTIVE
        ).exists()
        
        if has_orders:
            raise ValidationError(
                'No se puede eliminar este producto porque tiene pedidos en curso asociados. '
                'Considere desactivarlo en lugar de eliminarlo.'
            )
        
        return value


# =============================================================================
# HU-012 (PARTE): PRODUCT RESTORE FORM
# =============================================================================

class ProductRestoreForm(FormStyleMixin, forms.Form):
    """
    HU-012 | ESCENARIO 4 | H | Restaurar producto desde papelera
    Escenarios: H (confirmación correcta), A (confirmación no marcada o nombre duplicado)
    """
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que deseo restaurar este producto'
    )
    
    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        """
        HU-012 | ESCENARIO 4 | H | Restauración válida
        HU-012 | ESCENARIO 4 | A | Ya existe producto activo con ese nombre → error
        HU-012 | ESCENARIO 4 | A | Confirmación no marcada → error
        """
        cleaned_data = super().clean()
        
        if not self.product:
            raise ValidationError(ERROR_PRODUCT_NOT_SPECIFIED)
        
        if Product.objects.filter(name__iexact=self.product.name).exists():
            raise ValidationError('Ya existe un producto activo con este nombre.')
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError(ERROR_CONFIRM_RESTORE)
        
        return cleaned_data


# =============================================================================
# HU-013 (PARTE): PRODUCT COLOR CREATE FORM
# =============================================================================

class ProductColorCreateForm(FormStyleMixin, SortableCreateMixin, forms.ModelForm):
    """
    HU-013 | ESCENARIO 1 | H | Asignar colores a un producto
    Escenarios: H (color no asignado previamente), A (color ya asignado), E (sin permisos)
    """
    class Meta:
        model = ProductColor
        fields = ['color', 'images', 'featured_image']
        widgets = {
            'color': forms.Select(),
            'images': CloudinaryImageSelectWidget(),
            'featured_image': CloudinaryFeaturedImageWidget(images_widget_name='images'),
        }
    
    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
        if self.product:
            self.fields['featured_image'].queryset = ProductImage.objects.all()
            self.fields['images'].queryset = ProductImage.objects.all()
    
    def clean(self):
        """
        HU-013 | ESCENARIO 1 | H | Color válido y no previamente asignado
        HU-013 | ESCENARIO 3 | E | Color ya asignado a este producto → error
        HU-013 | ESCENARIO 2 | A | Imagen destacada no está en imágenes seleccionadas → error
        """
        cleaned_data = super().clean()
        
        if not self.product:
            raise ValidationError(ERROR_PRODUCT_NOT_SPECIFIED)
        
        color = cleaned_data.get('color')
        
        if color and ProductColor.all_objects.filter(product=self.product, color=color).exists():
            raise ValidationError(f'El color {color.name} ya está asignado a este producto.')
        
        featured_image = cleaned_data.get('featured_image')
        images = cleaned_data.get('images', [])
        
        if featured_image and featured_image not in images:
            raise ValidationError('La imagen destacada debe estar seleccionada en la lista de imágenes.')
        
        return cleaned_data


# =============================================================================
# HU-013 (PARTE): PRODUCT COLOR UPDATE FORM
# =============================================================================

class ProductColorUpdateForm(FormStyleMixin, SortableUpdateMixin, forms.ModelForm):
    """
    HU-013 | ESCENARIO 2 | H | Actualizar imágenes y orden de colores del producto
    Escenarios: H (datos válidos), A (imagen destacada no seleccionada), E (sin permisos)
    """
    class Meta:
        model = ProductColor
        fields = ['images', 'featured_image', 'is_active']
        widgets = {
            'is_active': forms.CheckboxInput(),
        }

    sortable_queryset = None
    sortable_label_attr = lambda self, pc: pc.color.name
    sortable_filter_field = 'product'
    sortable_widget_name = 'color_order'
    sortable_widget_label = 'Orden de colores'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            product_color_id = self.instance.pk
            
            self.fields['images'].widget = CloudinaryImageSelectWidget(
                product_color_id=product_color_id
            )
            self.fields['featured_image'].widget = CloudinaryFeaturedImageWidget(
                product_color_id=product_color_id,
                images_widget_name='images'
            )
            
            self.fields['featured_image'].queryset = ProductImage.objects.all()
            self.fields['images'].queryset = ProductImage.objects.all()
            
            self.sortable_queryset = ProductColor.objects.filter(
                product=self.instance.product,
                is_active=True
            ).order_by('sort_order').select_related('color')
            self._setup_sortable_widget()

    def clean(self):
        """
        HU-013 | ESCENARIO 2 | H | Actualización válida
        HU-013 | ESCENARIO 2 | A | Imagen destacada no está en imágenes seleccionadas → error
        """
        cleaned_data = super().clean()
        featured_image = cleaned_data.get('featured_image')
        images = cleaned_data.get('images', [])
        if featured_image and featured_image not in images:
            raise ValidationError('La imagen destacada debe estar seleccionada en la lista de imágenes.')
        return cleaned_data


# =============================================================================
# HU-013 (PARTE): PRODUCT COLOR DELETE FORM
# =============================================================================

class ProductColorDeleteForm(FormStyleMixin, forms.Form):
    """
    HU-013 | ESCENARIO 4 | A | Deshabilitar/eliminar un color del producto
    Escenarios: H (confirmación correcta y sin variantes), A (nombre no coincide o con variantes activas)
    """
    confirm = forms.CharField(
        required=True,
        label=CONFIRM_DELETE_COLOR,
        widget=forms.TextInput()
    )
    
    def __init__(self, *args, **kwargs):
        self.product_color = kwargs.pop('product_color', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        """
        HU-013 | ESCENARIO 4 | A | Confirmación correcta y sin variantes activas
        HU-013 | ESCENARIO 4 | A | Nombre no coincide → error
        HU-013 | ESCENARIO 4 | A | Color con variantes activas → error
        """
        value = self.cleaned_data.get('confirm', '').strip().lower()
        
        if not self.product_color:
            raise ValidationError('Color de producto no especificado.')
        
        if self.product_color.color.name.lower() != value:
            raise ValidationError('El nombre del color no coincide.')
        
        active_variants = self.product_color.variants.filter(is_active=True)
        if active_variants.exists():
            raise ValidationError(
                f'No se puede eliminar el color {self.product_color.color.name} porque tiene '
                f'{active_variants.count()} variante(s) activa(s). Desactive las variantes primero.'
            )
        
        return value


# =============================================================================
# HU-013 (PARTE): PRODUCT VARIANT CREATE FORM
# =============================================================================

class ProductVariantCreateForm(FormStyleMixin, forms.ModelForm):
    """
    HU-013 | ESCENARIO 1 | H | Asignar tallas y stock a un producto (crear variante)
    Escenarios: H (combinación válida), A (variante ya existe), E (sin permisos)
    """
    class Meta:
        model = ProductVariant
        fields = ['product_color', 'size', 'stock']
        widgets = {
            'product_color': forms.Select(),
            'size': forms.Select(),
            'stock': forms.NumberInput(attrs={'min': 0}),
        }
    
    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
        if self.product:
            self.fields['product_color'].queryset = ProductColor.objects.filter(
                product=self.product, is_active=True
            )
    
    def clean(self):
        """
        HU-013 | ESCENARIO 1 | H | Variante con combinación única
        HU-013 | ESCENARIO 3 | E | Variante ya existe → error
        HU-013 | ESCENARIO 3 | E | ProductColor no pertenece al producto → error
        """
        cleaned_data = super().clean()
        
        if not self.product:
            raise ValidationError(ERROR_PRODUCT_NOT_SPECIFIED)
        
        product_color = cleaned_data.get('product_color')
        size = cleaned_data.get('size')
        
        if product_color and product_color.product_id != self.product.id:
            raise ValidationError(
                'El color seleccionado no pertenece a este producto.'
            )
        
        if product_color and size and ProductVariant.all_objects.filter(
            product=self.product, product_color=product_color, size=size
        ).exists():
            raise ValidationError(
                f'Ya existe una variante para {product_color.color.name} - Talla {size.name}.'
            )
        
        return cleaned_data


# =============================================================================
# HU-013 (PARTE): PRODUCT VARIANT UPDATE FORM
# =============================================================================

class ProductVariantUpdateForm(FormStyleMixin, forms.ModelForm):
    """
    HU-013 | ESCENARIO 2 | H | Actualizar stock de una talla
    HU-013 | ESCENARIO 3 | E | Stock negativo no permitido
    Escenarios: H (stock ≥ 0), E (stock negativo), E (sin permisos, variante no existe)
    """
    class Meta:
        model = ProductVariant
        fields = ['stock', 'is_active']
        widgets = {
            'stock': forms.NumberInput(attrs={'min': 0}),
            'is_active': forms.CheckboxInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_stock = self.instance.stock if self.instance else 0
    
    def clean_stock(self):
        """
        HU-013 | ESCENARIO 2 | H | Stock ≥ 0
        HU-013 | ESCENARIO 3 | E | Stock negativo → error
        """
        new_stock = self.cleaned_data.get('stock', 0)
        
        if new_stock < 0:
            raise ValidationError('El stock no puede ser negativo.')
        
        return new_stock


# =============================================================================
# HU-013 (PARTE): PRODUCT VARIANT DELETE FORM
# =============================================================================

class ProductVariantDeleteForm(FormStyleMixin, forms.Form):
    """
    HU-013 | ESCENARIO 4 | A | Deshabilitar una talla (soft delete)
    Escenarios: H (confirmación correcta), A (confirmación no coincide), E (con pedidos pendientes)
    """
    confirm = forms.CharField(
        required=True,
        label=CONFIRM_DELETE_VARIANT,
        widget=forms.TextInput(attrs={'placeholder': 'ELIMINAR'})
    )
    
    def __init__(self, *args, **kwargs):
        self.variant = kwargs.pop('variant', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        """
        HU-013 | ESCENARIO 4 | A | Confirmación "ELIMINAR" correcta
        HU-013 | ESCENARIO 4 | A | Confirmación no coincide → error
        HU-013 | ESCENARIO 4 | A | Variante con pedidos pendientes → error
        """
        value = self.cleaned_data.get('confirm', '').upper().strip()
        
        if not self.variant:
            raise ValidationError(ERROR_VARIANT_NOT_SPECIFIED)
        
        if value != 'ELIMINAR':
            raise ValidationError('Debes escribir "ELIMINAR" para confirmar.')
        
        pending_orders = self.variant.order_items.filter(
            order__status__in=ORDER_STATUSES_ACTIVE
        ).exists()
        
        if pending_orders:
            raise ValidationError(
                'No se puede eliminar esta variante porque tiene pedidos pendientes asociados.'
            )
        
        return value


# =============================================================================
# HU-013 (PARTE): PRODUCT VARIANT RESTORE FORM
# =============================================================================

class ProductVariantRestoreForm(FormStyleMixin, forms.Form):
    """
    HU-013 | ESCENARIO 4 | A | Restaurar variante deshabilitada
    Escenarios: H (restauración válida), A (combinación ya existe o confirmación no marcada)
    """
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que deseo restaurar esta variante'
    )
    
    def __init__(self, *args, **kwargs):
        self.variant = kwargs.pop('variant', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        """
        HU-013 | ESCENARIO 4 | A | Restauración válida
        HU-013 | ESCENARIO 4 | A | Ya existe variante activa con esa combinación → error
        HU-013 | ESCENARIO 4 | A | Confirmación no marcada → error
        """
        cleaned_data = super().clean()
        
        if not self.variant:
            raise ValidationError(ERROR_VARIANT_NOT_SPECIFIED)
        
        if ProductVariant.objects.filter(
            product=self.variant.product,
            product_color=self.variant.product_color,
            size=self.variant.size,
            is_active=True
        ).exists():
            raise ValidationError(
                'Ya existe una variante activa con esta combinación de producto, color y talla.'
            )
        
        if not cleaned_data.get('confirm'):
            raise ValidationError(ERROR_CONFIRM_RESTORE)
        
        return cleaned_data


# =============================================================================
# OPCIONES DE ESTILO (soporte para colecciones)
# =============================================================================

# Opciones de fuentes (limitadas a Tailwind + Google Fonts populares)
FONT_FAMILY_CHOICES = [
    ("'Inter', sans-serif", "Inter"),
    ("'Roboto', sans-serif", "Roboto"),
    ("'Poppins', sans-serif", "Poppins"),
    ("'Montserrat', sans-serif", "Montserrat"),
    ("'Open Sans', sans-serif", "Open Sans"),
    ("'Playfair Display', serif", "Playfair Display"),
    ("'Merriweather', serif", "Merriweather"),
]

# Opciones de altura de sección (para efectos)
SECTION_HEIGHT_CHOICES = [(f'{i}vh', f'{i}% de la pantalla') for i in range(10, 101, 10)]

# Opciones de tamaño (fuente, margen, etc.)
SIZE_CHOICES = [
    ('0.5rem', 'Muy pequeño (0.5rem)'),
    ('0.75rem', 'Pequeño (0.75rem)'),
    ('1rem', 'Normal (1rem)'),
    ('1.25rem', 'Mediano (1.25rem)'),
    ('1.5rem', 'Grande (1.5rem)'),
    ('2rem', 'Muy grande (2rem)'),
    ('2.5rem', 'Extra grande (2.5rem)'),
    ('3rem', 'Gigante (3rem)'),
    ('4rem', 'Muy gigante (4rem)'),
]

# Opciones de altura de línea
LINE_HEIGHT_CHOICES = [
    ('1.2', 'Compacto (1.2)'),
    ('1.4', 'Normal (1.4)'),
    ('1.6', 'Espaciado (1.6)'),
    ('1.8', 'Muy espaciado (1.8)'),
    ('2.0', 'Doble espacio (2.0)'),
]

# Opciones de margen
MARGIN_CHOICES = SIZE_CHOICES


# =============================================================================
# HU-015: COLLECTION CREATE FORM
# =============================================================================

class CollectionCreateForm(FormStyleMixin, forms.ModelForm):
    """
    HU-015: Crear colección
    Escenarios: H (datos básicos válidos), A (errores), E (sin permisos)
    """
    class Meta:
        model = Collection
        fields = [
            'name', 'description', 'products',
            'cover_image',
            'primary_color', 'secondary_color', 'background_color', 'text_color',
            'background_image',
            'title_font',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full', 
                'placeholder': 'Ej: Colección Verano 2024'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'w-full',
                'placeholder': 'Describe la inspiración y detalles de esta colección...'
            }),
            'products': ProductCheckboxSelectWidget(editing=False),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'w-full'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}),
            'background_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}),
            'text_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}),
            'background_image': forms.ClearableFileInput(attrs={'class': 'w-full'}),
            'title_font': forms.Select(choices=FONT_FAMILY_CHOICES, attrs={'class': 'w-full'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['products'].queryset = Product.objects.filter(is_active=True, product_type='fabrica')
        self.fields['primary_color'].required = False
        self.fields['secondary_color'].required = False
        self.fields['background_color'].required = False
        self.fields['text_color'].required = False
        self.fields['title_font'].required = False

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if Collection.objects.filter(name__iexact=name).exists():
            raise ValidationError('Ya existe una colección con este nombre.')
        return name

    def save(self, commit=True):
        # HU-015 | ESCENARIO 1 | H | Guarda colección en estado borrador
        instance = super().save(commit=False)
        instance.status = 'borrador'
        instance.slug = slugify(instance.name)
        
        if commit:
            instance.save()
            self.save_m2m()
        return instance


# =============================================================================
# HU-016 & HU-018: COLLECTION UPDATE FORM
# =============================================================================

class CollectionUpdateForm(FormStyleMixin, forms.ModelForm):
    """
    HU-016: Editar colección
    HU-018: Asignar productos a colección
    Escenarios: H (datos válidos), A (fechas inválidas, sin productos si publicada), E (sin permisos)
    """
    
    start_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full'}),
        label='Fecha de inicio'
    )
    end_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full'}),
        label='Fecha de fin'
    )

    class Meta:
        model = Collection
        fields = [
            'name', 'description', 'products',
            'cover_image',
            'primary_color', 'secondary_color', 'background_color', 'text_color',
            'background_image',
            'title_font',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'w-full'}),
            'products': ProductCheckboxSelectWidget(editing=True),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'w-full'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}),
            'background_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}),
            'text_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}),
            'background_image': forms.ClearableFileInput(attrs={'class': 'w-full'}),
            'title_font': forms.Select(choices=FONT_FAMILY_CHOICES, attrs={'class': 'w-full'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle-switch'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # HU-018 | ESCENARIO 1 | H | Productos de fábrica y colección limitada disponibles
        self.fields['products'].queryset = Product.objects.filter(is_active=True)
        self.fields['primary_color'].required = False
        self.fields['secondary_color'].required = False
        self.fields['background_color'].required = False
        self.fields['text_color'].required = False
        self.fields['title_font'].required = False
        self.fields['is_active'].required = False
        
        if self.instance and self.instance.pk:
            if self.instance.start_date:
                self.initial['start_date'] = self.instance.start_date.strftime('%Y-%m-%dT%H:%M')
            if self.instance.end_date:
                self.initial['end_date'] = self.instance.end_date.strftime('%Y-%m-%dT%H:%M')

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        qs = Collection.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Ya existe otra colección con este nombre.')
        return name

    def clean(self):
        cleaned_data = super().clean()
        
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError({
                'end_date': 'La fecha de fin debe ser posterior a la fecha de inicio.'
            })
        
        if cleaned_data.get('is_active') and cleaned_data.get('status') == 'publicada':
            if not cleaned_data.get('products'):
                raise ValidationError({
                    'products': 'Una colección publicada debe tener al menos un producto asignado.'
                })
        
        return cleaned_data

    def save(self, commit=True):
        # HU-016 | ESCENARIO 1 | H | Guarda cambios de colección
        instance = super().save(commit=False)
        instance.start_date = self.cleaned_data.get('start_date')
        instance.end_date = self.cleaned_data.get('end_date')
        
        if commit:
            instance.save()
            self.save_m2m()
        return instance


# =============================================================================
# HU-017: COLLECTION DELETE FORM
# =============================================================================

class CollectionDeleteForm(FormStyleMixin, forms.Form):
    """
    HU-017: Eliminar colección (soft delete)
    Escenarios: H (confirmación correcta), A (nombre no coincide), E (sin permisos, con pedidos asociados)
    """

    confirm = forms.CharField(
        required=True,
        label=CONFIRM_DELETE_COLLECTION,
        widget=forms.TextInput(attrs={'class': 'w-full', 'placeholder': 'Escribe el nombre de la colección'})
    )

    def __init__(self, *args, **kwargs):
        self.collection = kwargs.pop('collection', None)
        super().__init__(*args, **kwargs)

    def clean_confirm(self):
        """
        HU-017 | ESCENARIO 1 | H | Confirmación correcta
        HU-017 | ESCENARIO 2 | A | Colección con productos asignados (advertencia en template, pero permite archivar)
        HU-017 | ESCENARIO 3 | A | Nombre no coincide → error
        """
        value = self.cleaned_data.get('confirm', '').strip().lower()

        if not self.collection:
            raise ValidationError(ERROR_COLLECTION_NOT_SPECIFIED)

        if self.collection.name.lower() != value:
            raise ValidationError('El nombre de la colección no coincide.')

        if self.collection.status == 'publicada':
            has_orders = self.collection.products.filter(
                variants__order_items__order__status__in=ORDER_STATUSES_ACTIVE
            ).exists()
            if has_orders:
                raise ValidationError(
                    'No se puede eliminar esta colección porque tiene productos en pedidos en curso. '
                    'Considere archivarla en lugar de eliminarla.'
                )

        return value


# =============================================================================
# HU-017 (PARTE): COLLECTION RESTORE FORM
# =============================================================================

class CollectionRestoreForm(FormStyleMixin, forms.Form):
    """
    HU-017 | ESCENARIO 3 | H | Restaurar colección
    Escenarios: H (restauración válida), A (slug duplicado o confirmación no marcada)
    """

    confirm = forms.BooleanField(
        required=True,
        label=MSG_COLLECTION_CONFIRM_RESTORE,
        widget=forms.CheckboxInput(attrs={'class': 'toggle-switch'})
    )

    restore_products_type = forms.BooleanField(
        required=False,
        initial=True,
        label=MSG_COLLECTION_RESTORE_PRODUCTS_TYPE,
        help_text=MSG_COLLECTION_RESTORE_PRODUCTS_TYPE_HELP,
        widget=forms.CheckboxInput(attrs={'class': 'toggle-switch'})
    )

    def __init__(self, *args, **kwargs):
        self.collection = kwargs.pop('collection', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        """
        HU-017 | ESCENARIO 3 | H | Restauración válida
        HU-017 | ESCENARIO 3 | A | Slug duplicado (ya existe colección activa) → error
        HU-017 | ESCENARIO 3 | A | Confirmación no marcada → error
        """
        cleaned_data = super().clean()

        if not self.collection:
            raise ValidationError(ERROR_COLLECTION_NOT_SPECIFIED)

        if Collection.objects.filter(slug=self.collection.slug, is_active=True).exists():
            raise ValidationError(MSG_COLLECTION_RESTORE_ACTIVE_SLUG.format(self.collection.slug))

        if not cleaned_data.get('confirm'):
            raise ValidationError(ERROR_CONFIRM_RESTORE)

        return cleaned_data


# =============================================================================
# EFECTOS PREDEFINIDOS (soporte para CollectionStyleForm)
# =============================================================================

LABEL_CARD_BG_COLOR = 'Color de fondo de tarjetas'
LABEL_CARD_TITLE_COLOR = 'Color del título'
LABEL_CARD_PRICE_COLOR = 'Color del precio'
LABEL_CARD_BORDER_RADIUS = 'Radio de borde'
LABEL_CARD_SHADOW = 'Sombra de tarjeta'
LABEL_CARD_HOVER_SCALE = 'Escala al hover'
LABEL_CARD_SHOW_CATEGORY = 'Mostrar categoría'
LABEL_CARD_SHOW_STOCK_BADGE = 'Mostrar badge de stock'

# =============================================================================
# EFECTOS PREDEFINIDOS
# =============================================================================

EFFECT_PRESETS = {
    'none': {
        'name': '✨ Sin efectos',
        'description': 'Tarjetas estáticas, sin animaciones',
        'config': {
            'hover_effect': 'none',
            'card_animation': 'none',
            'parallax': False,
            'particles': False
        }
    },
    'zoom_fade': {
        'name': '🔍 Zoom + Fade',
        'description': 'Zoom al hacer hover + animación de entrada fade',
        'config': {
            'hover_effect': 'zoom',
            'card_animation': 'fadeIn',
            'parallax': False,
            'particles': False,
            'animation_duration': 0.5
        }
    },
    'lift_slide': {
        'name': '⬆️ Levitar + Slide',
        'description': 'Tarjeta se levanta al hover + entrada deslizante',
        'config': {
            'hover_effect': 'lift',
            'card_animation': 'slideInUp',
            'parallax': False,
            'particles': False,
            'animation_duration': 0.6
        }
    },
    'glow_premium': {
        'name': '✨ Glow Premium',
        'description': 'Efecto de brillo dorado al hover + fade suave',
        'config': {
            'hover_effect': 'glow',
            'card_animation': 'fadeInUp',
            'parallax': False,
            'particles': False,
            'glow_color': '#c2a575',
            'animation_duration': 0.5
        }
    },
    'parallax_scroll': {
        'name': '🌊 Parallax + Partículas',
        'description': 'Efecto parallax suave y partículas flotantes',
        'config': {
            'hover_effect': 'none',
            'card_animation': 'fadeIn',
            'parallax': True,
            'particles': True,
            'animation_duration': 0.8
        }
    },
    'explosion': {
        'name': '💥 Explosión Dinámica',
        'description': 'Efecto de escala explosiva al hover + entrada dramática',
        'config': {
            'hover_effect': 'explode',
            'card_animation': 'zoomIn',
            'parallax': False,
            'particles': True,
            'animation_duration': 0.4,
            'hover_scale': 1.1
        }
    },
    'soft_shadow': {
        'name': '🎨 Sombra Suave',
        'description': 'Sombra flotante y transición suave',
        'config': {
            'hover_effect': 'shadow',
            'card_animation': 'none',
            'parallax': False,
            'particles': False,
            'shadow_intensity': 'lg'
        }
    },
    'cinematic': {
        'name': '🎬 Cinemático',
        'description': 'Efecto de luz y movimiento cinematográfico',
        'config': {
            'hover_effect': 'cinematic',
            'card_animation': 'slideInLeft',
            'parallax': True,
            'particles': False,
            'animation_duration': 0.7,
            'light_intensity': 0.3
        }
    }
}

def get_effect_preset_choices():
    """Retorna las opciones de efectos predefinidos para selects rápidos"""
    return [(key, preset['name']) for key, preset in EFFECT_PRESETS.items()]

def get_effect_preset_description(preset_key):
    """Retorna la descripción de un preset de efectos"""
    return EFFECT_PRESETS.get(preset_key, {}).get('description', '')


# =============================================================================
# HU-015 & HU-016 (PARTE): COLLECTION STYLE FORM
# =============================================================================

class CollectionStyleForm(FormStyleMixin, forms.ModelForm):
    """
    HU-015 | ESCENARIO 4 | H | Estilos visuales personalizados
    HU-016 (parte): Configuración de estilos de colección
    Escenarios: H (estilos guardados correctamente), A (errores en configuración)
    """
    
    # Selector rápido de paleta de colores
    color_palette = forms.ChoiceField(
        choices=get_color_palette_choices(),
        required=False,
        label='🎨 Paleta de colores rápida',
        help_text='Selecciona una combinación de colores predefinida',
        widget=forms.Select(attrs={'class': 'w-full'})
    )
    
    # Selector rápido de efectos
    effect_preset = forms.ChoiceField(
        choices=get_effect_preset_choices(),
        required=False,
        label='✨ Efectos rápidos',
        help_text='Selecciona un efecto predefinido para las tarjetas de producto',
        widget=forms.Select(attrs={'class': 'w-full'})
    )
    
    # Configuración de tarjetas
    card_background_color = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}),
        label=LABEL_CARD_BG_COLOR
    )
    card_title_color = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}),
        label=LABEL_CARD_TITLE_COLOR
    )
    card_price_color = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}),
        label=LABEL_CARD_PRICE_COLOR
    )
    card_border_radius = forms.ChoiceField(
        choices=CARD_BORDER_RADIUS_CHOICES,
        required=False,
        initial=DEFAULT_BORDER_RADIUS,
        label=LABEL_CARD_BORDER_RADIUS,
        help_text='Redondeo de las esquinas de la tarjeta'
    )
    card_shadow = forms.ChoiceField(
        choices=CARD_SHADOW_CHOICES,
        required=False,
        initial=DEFAULT_BOX_SHADOW,
        label=LABEL_CARD_SHADOW,
        help_text='Sombra de la tarjeta'
    )
    card_hover_scale = forms.ChoiceField(
        choices=CARD_HOVER_SCALE_CHOICES,
        required=False,
        initial=str(DEFAULT_HOVER_SCALE),
        label=LABEL_CARD_HOVER_SCALE,
        help_text='Escala al pasar el mouse sobre la tarjeta'
    )
    card_show_category = forms.BooleanField(
        required=False,
        initial=DEFAULT_SHOW_CATEGORY,
        label=LABEL_CARD_SHOW_CATEGORY,
        help_text='Muestra la categoría del producto en la tarjeta'
    )
    card_show_stock_badge = forms.BooleanField(
        required=False,
        initial=DEFAULT_SHOW_STOCK_BADGE,
        label=LABEL_CARD_SHOW_STOCK_BADGE,
        help_text='Muestra el estado del stock'
    )

    class Meta:
        model = Collection
        fields = [
            'color_palette',
            'effect_preset',
            'primary_color', 'secondary_color', 'background_color', 'text_color',
            'background_image',
            'title_font',
            'effects_config',
            'custom_css',
            'style_config',
            'is_active',
        ]
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER, 'class': 'w-16 h-10 p-1'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER, 'class': 'w-16 h-10 p-1'}),
            'background_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER, 'class': 'w-16 h-10 p-1'}),
            'text_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER, 'class': 'w-16 h-10 p-1'}),
            'background_image': forms.ClearableFileInput(attrs={'class': 'w-full'}),
            'title_font': forms.Select(choices=FONT_FAMILY_CHOICES, attrs={'class': 'w-full'}),
            'custom_css': forms.Textarea(attrs={'rows': 8, 'class': 'w-full font-mono'}),
            'effects_config': forms.Textarea(attrs={'rows': 6, 'class': 'w-full font-mono', 'placeholder': '{\n  "hover_effect": "zoom",\n  "card_animation": "fadeInUp"\n}'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle-switch'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._make_all_fields_optional()
        self._load_card_config_from_instance()
        self._load_effect_config_from_instance()


    def _make_all_fields_optional(self):
        for field_name in self.fields:
            self.fields[field_name].required = False


    def _get_card_field_value(self, card_config, field_name, config_key, instance_attr, default):
        """Helper para obtener el valor inicial de un campo de tarjeta."""
        config_value = card_config.get(config_key)
        if config_value is not None:
            return config_value
        if instance_attr is not None:
            return instance_attr
        return default


    def _load_card_config_from_instance(self):
        if not (self.instance and self.instance.style_config):
            return
        
        card_config = self.instance.style_config.get('card_config', {})
        
        self.fields['card_background_color'].initial = self._get_card_field_value(
            card_config, 'card_background_color', 'background_color', self.instance.background_color, DEFAULT_BACKGROUND_COLOR
        )
        self.fields['card_title_color'].initial = self._get_card_field_value(
            card_config, 'card_title_color', 'title_color', self.instance.primary_color, DEFAULT_PRIMARY_COLOR
        )
        self.fields['card_price_color'].initial = self._get_card_field_value(
            card_config, 'card_price_color', 'price_color', self.instance.primary_color, DEFAULT_PRIMARY_COLOR
        )
        self.fields['card_border_radius'].initial = self._get_card_field_value(
            card_config, 'card_border_radius', 'border_radius', None, DEFAULT_BORDER_RADIUS
        )
        self.fields['card_shadow'].initial = self._get_card_field_value(
            card_config, 'card_shadow', 'shadow', None, DEFAULT_BOX_SHADOW
        )
        self.fields['card_hover_scale'].initial = str(self._get_card_field_value(
            card_config, 'card_hover_scale', 'hover_scale', None, DEFAULT_HOVER_SCALE
        ))
        self.fields['card_show_category'].initial = self._get_card_field_value(
            card_config, 'card_show_category', 'show_category', None, DEFAULT_SHOW_CATEGORY
        )
        self.fields['card_show_stock_badge'].initial = self._get_card_field_value(
            card_config, 'card_show_stock_badge', 'show_stock_badge', None, DEFAULT_SHOW_STOCK_BADGE
        )


    def _find_matching_effect_preset(self, current_config):
        for preset_key, preset in EFFECT_PRESETS.items():
            preset_config = preset.get('config', {})
            if (preset_config.get('hover_effect') == current_config.get('hover_effect') and
                preset_config.get('card_animation') == current_config.get('card_animation')):
                return preset_key
        return None


    def _load_effect_config_from_instance(self):
        if not (self.instance and self.instance.effects_config):
            return
        
        matching_preset = self._find_matching_effect_preset(self.instance.effects_config)
        if matching_preset:
            self.fields['effect_preset'].initial = matching_preset
    
    def clean_color_palette(self):
        """Aplica la paleta de colores seleccionada si existe"""
        palette_key = self.cleaned_data.get('color_palette')
        if palette_key and palette_key != '' and palette_key in COLOR_PALETTES:
            palette = COLOR_PALETTES[palette_key]
            self.cleaned_data['primary_color'] = palette['primary']
            self.cleaned_data['secondary_color'] = palette['secondary']
            self.cleaned_data['background_color'] = palette['background']
            self.cleaned_data['text_color'] = palette['text']
        return palette_key
    
    def clean_effect_preset(self):
        """Aplica el preset de efectos seleccionado"""
        preset_key = self.cleaned_data.get('effect_preset')
        if preset_key and preset_key != '' and preset_key in EFFECT_PRESETS:
            return EFFECT_PRESETS[preset_key]['config']
        return None
    
    def _build_card_config(self, instance, cleaned_data):
        """Construye la configuración de tarjetas a partir de los datos del formulario."""
        return {
            'background_color': cleaned_data.get('card_background_color') or instance.background_color or DEFAULT_BACKGROUND_COLOR,
            'title_color': cleaned_data.get('card_title_color') or instance.primary_color or DEFAULT_PRIMARY_COLOR,
            'price_color': cleaned_data.get('card_price_color') or instance.primary_color or DEFAULT_PRIMARY_COLOR,
            'badge_background': instance.primary_color or DEFAULT_PRIMARY_COLOR,
            'badge_text_color': DEFAULT_BADGE_TEXT_COLOR,
            'border_radius': cleaned_data.get('card_border_radius') or DEFAULT_BORDER_RADIUS,
            'shadow': cleaned_data.get('card_shadow') or DEFAULT_BOX_SHADOW,
            'hover_scale': float(cleaned_data.get('card_hover_scale') or DEFAULT_HOVER_SCALE),
            'show_category': cleaned_data.get('card_show_category', DEFAULT_SHOW_CATEGORY),
            'show_stock_badge': cleaned_data.get('card_show_stock_badge', DEFAULT_SHOW_STOCK_BADGE),
        }
    
    def _ensure_colors_config(self, style_config, instance):
        if 'colors' not in style_config:
            style_config['colors'] = {
                'primary': instance.primary_color or DEFAULT_PRIMARY_COLOR,
                'secondary': instance.secondary_color or DEFAULT_SECONDARY_COLOR,
                'background': instance.background_color or DEFAULT_BACKGROUND_COLOR,
                'text': instance.text_color or DEFAULT_TEXT_COLOR,
            }
        return style_config
    
    def _ensure_typography_config(self, style_config, instance):
        if 'typography' not in style_config:
            style_config['typography'] = {
                'title_font': instance.title_font or DEFAULT_TITLE_FONT,
            }
        return style_config
    
    def save(self, commit=True):
        # HU-015 | ESCENARIO 4 | H | Estilos visuales guardados exitosamente
        instance = super().save(commit=False)
        cleaned_data = self.cleaned_data

        # Actualizar campos del modelo
        instance.primary_color = cleaned_data.get('primary_color') or instance.primary_color
        instance.secondary_color = cleaned_data.get('secondary_color') or instance.secondary_color
        instance.background_color = cleaned_data.get('background_color') or instance.background_color
        instance.text_color = cleaned_data.get('text_color') or instance.text_color
        instance.title_font = cleaned_data.get('title_font') or instance.title_font
        
        # Actualizar configuración de efectos
        effect_config = cleaned_data.get('effect_preset')
        if effect_config:
            instance.effects_config = effect_config
        
        # Construir card_config
        card_config = self._build_card_config(instance, cleaned_data)
        
        # Construir style_config completo
        style_config = instance.style_config or {}
        style_config = self._ensure_colors_config(style_config, instance)
        style_config = self._ensure_typography_config(style_config, instance)
        style_config['card_config'] = card_config
        
        instance.style_config = style_config

        if commit:
            instance.save()
            self.save_m2m()
        
        return instance