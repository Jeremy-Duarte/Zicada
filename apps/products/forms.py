from datetime import timezone

from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .models import (
    Size, Category, Color, Product, ProductVariant, 
    Collection, ProductColor, ProductImage
)
from apps.core.crud.mixins import FormStyleMixin, SortableCreateMixin, SortableUpdateMixin
from apps.core.crud.widgets import CloudinaryImageSelectWidget, CloudinaryFeaturedImageWidget, SortableOrderWidget
import re

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

# ========== FORMULARIOS PARA CATÁLOGOS ESTÁTICOS ==========

class SizeCreateForm(FormStyleMixin, SortableCreateMixin, forms.ModelForm):
    class Meta:
        model = Size
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ej: XS, S, M, L, XL'}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').upper().strip()
        if Size.objects.filter(name=name).exists():
            raise ValidationError(f'La talla "{name}" ya existe.')
        return name


class SizeUpdateForm(FormStyleMixin, SortableUpdateMixin, forms.ModelForm):
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
        name = self.cleaned_data.get('name', '').upper().strip()
        qs = Size.objects.filter(name=name)
        
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError(f'La talla "{name}" ya existe.')
        
        return name


class SizeDeleteForm(FormStyleMixin, forms.Form):
    confirm = forms.CharField(
        required=True,
        label=CONFIRM_DELETE_SIZE,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: M'})
    )
    
    def __init__(self, *args, **kwargs):
        self.size = kwargs.pop('size', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
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


class CategoryCreateForm(FormStyleMixin, SortableCreateMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ej: Camisetas, Hoodies'}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        
        if Category.objects.filter(name__iexact=name).exists():
            raise ValidationError(f'La categoría "{name}" ya existe.')
        
        return name


class CategoryUpdateForm(FormStyleMixin, SortableUpdateMixin, forms.ModelForm):
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
        name = self.cleaned_data.get('name', '').strip()
        qs = Category.objects.filter(name__iexact=name)
        
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError(f'La categoría "{name}" ya existe.')
        
        return name
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.slug = slugify(instance.name)
        
        if commit:
            instance.save()
        
        return instance


class CategoryDeleteForm(FormStyleMixin, forms.Form):
    confirm = forms.CharField(
        required=True,
        label=CONFIRM_DELETE_CATEGORY,
        widget=forms.TextInput()
    )
    
    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
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


class CategoryImportForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if Category.objects.filter(name__iexact=name).exists():
            raise ValidationError(f'La categoría "{name}" ya existe.')
        return name


class ColorCreateForm(FormStyleMixin, SortableCreateMixin, forms.ModelForm):
    class Meta:
        model = Color
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(),
            'code': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_INPUT}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip().capitalize()
        if Color.objects.filter(name__iexact=name).exists():
            raise ValidationError(f'El color "{name}" ya existe.')
        return name
    
    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if not code.startswith('#'):
            code = f'#{code}'
        
        if not re.match(HEX_COLOR_PATTERN, code):
            raise ValidationError('El código debe ser un color hexadecimal válido (ej: #FF0000, #F00)')
        
        if Color.objects.filter(code__iexact=code).exists():
            raise ValidationError(f'El código de color "{code}" ya está en uso.')
        
        return code


class ColorUpdateForm(FormStyleMixin, SortableUpdateMixin, forms.ModelForm):
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
        name = self.cleaned_data.get('name', '').strip().capitalize()
        qs = Color.objects.filter(name__iexact=name)
        
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError(f'El color "{name}" ya existe.')
        
        return name
    
    def clean_code(self):
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


class ColorDeleteForm(FormStyleMixin, forms.Form):
    confirm = forms.CharField(
        required=True,
        label=CONFIRM_DELETE_COLOR,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Rojo'})
    )
    
    def __init__(self, *args, **kwargs):
        self.color = kwargs.pop('color', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
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


class ColorImportForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ['name', 'code']
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').capitalize().strip()
        if Color.objects.filter(name__iexact=name).exists():
            raise ValidationError(f'El color "{name}" ya existe.')
        return name
    
    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if not code.startswith('#'):
            code = f'#{code}'
        if not re.match(HEX_COLOR_PATTERN, code):
            raise ValidationError(f'"{code}" no es un código hexadecimal válido.')
        if Color.objects.filter(code__iexact=code).exists():
            raise ValidationError(f'El código de color "{code}" ya está en uso.')
        return code


class ProductImageCreateForm(FormStyleMixin, forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'alt_text': forms.TextInput(attrs={'placeholder': 'Descripción de la imagen para SEO'}),
        }
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        
        if image:
            if image.size > MAX_IMAGE_SIZE:
                raise ValidationError(IMAGE_SIZE_ERROR)
            
            import os
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                raise ValidationError(IMAGE_EXTENSION_ERROR)
        
        return image


class ProductImageUpdateForm(FormStyleMixin, forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['alt_text']
        widgets = {
            'alt_text': forms.TextInput(),
        }


class ProductImageDeleteForm(FormStyleMixin, forms.Form):
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que deseo eliminar esta imagen permanentemente'
    )
    
    def __init__(self, *args, **kwargs):
        self.image = kwargs.pop('image', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.image:
            raise ValidationError(ERROR_IMAGE_NOT_SPECIFIED)
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError(ERROR_CONFIRM_REQUIRED)
        
        return cleaned_data


class ProductCreateForm(FormStyleMixin, forms.ModelForm):
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
        name = self.cleaned_data.get('name', '').strip()
        
        if Product.all_objects.filter(name__iexact=name).exists():
            raise ValidationError('Ya existe un producto con ese nombre (activo o eliminado).')
        
        return name
    
    def clean_price(self):
        price = self.cleaned_data.get('price', 0)
        
        if price <= 0:
            raise ValidationError(PRICE_ERROR_POSITIVE)
        
        if price > MAX_PRICE:
            raise ValidationError(PRICE_ERROR_MAX)
        
        return price


class ProductUpdateForm(FormStyleMixin, forms.ModelForm):
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
        name = self.cleaned_data.get('name', '').strip()
        qs = Product.objects.filter(name__iexact=name)
        
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError('Ya existe un producto activo con ese nombre.')
        
        return name
    
    def clean_price(self):
        price = self.cleaned_data.get('price', 0)
        
        if price <= 0:
            raise ValidationError(PRICE_ERROR_POSITIVE)
        
        if price > MAX_PRICE:
            raise ValidationError(PRICE_ERROR_MAX)
        
        return price


class ProductDeleteForm(FormStyleMixin, forms.Form):
    confirm = forms.CharField(
        required=True,
        label=CONFIRM_DELETE_PRODUCT,
        widget=forms.TextInput()
    )
    
    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
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


class ProductRestoreForm(FormStyleMixin, forms.Form):
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que deseo restaurar este producto'
    )
    
    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.product:
            raise ValidationError(ERROR_PRODUCT_NOT_SPECIFIED)
        
        if Product.objects.filter(name__iexact=self.product.name).exists():
            raise ValidationError('Ya existe un producto activo con este nombre.')
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError(ERROR_CONFIRM_RESTORE)
        
        return cleaned_data


class ProductColorCreateForm(FormStyleMixin, SortableCreateMixin, forms.ModelForm):
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


class ProductColorUpdateForm(FormStyleMixin, SortableUpdateMixin, forms.ModelForm):
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
        cleaned_data = super().clean()
        featured_image = cleaned_data.get('featured_image')
        images = cleaned_data.get('images', [])
        if featured_image and featured_image not in images:
            raise ValidationError('La imagen destacada debe estar seleccionada en la lista de imágenes.')
        return cleaned_data


class ProductColorDeleteForm(FormStyleMixin, forms.Form):
    confirm = forms.CharField(
        required=True,
        label=CONFIRM_DELETE_COLOR,
        widget=forms.TextInput()
    )
    
    def __init__(self, *args, **kwargs):
        self.product_color = kwargs.pop('product_color', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
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


class ProductVariantCreateForm(FormStyleMixin, forms.ModelForm):
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
        cleaned_data = super().clean()
        
        if not self.product:
            raise ValidationError(ERROR_PRODUCT_NOT_SPECIFIED)
        
        product_color = cleaned_data.get('product_color')
        size = cleaned_data.get('size')
        
        if product_color and size and ProductVariant.all_objects.filter(
            product=self.product, product_color=product_color, size=size).exists():
            raise ValidationError(
                f'Ya existe una variante para {product_color.color.name} - Talla {size.name}. '
                f'Use el formulario de actualización para modificar el stock.'
            )
        
        return cleaned_data

class ProductVariantUpdateForm(FormStyleMixin, forms.ModelForm):
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
        new_stock = self.cleaned_data.get('stock', 0)
        
        if new_stock < 0:
            raise ValidationError('El stock no puede ser negativo.')
        
        return new_stock


class ProductVariantDeleteForm(FormStyleMixin, forms.Form):
    confirm = forms.CharField(
        required=True,
        label=CONFIRM_DELETE_VARIANT,
        widget=forms.TextInput(attrs={'placeholder': 'ELIMINAR'})
    )
    
    def __init__(self, *args, **kwargs):
        self.variant = kwargs.pop('variant', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
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


class ProductVariantRestoreForm(FormStyleMixin, forms.Form):
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que deseo restaurar esta variante'
    )
    
    def __init__(self, *args, **kwargs):
        self.variant = kwargs.pop('variant', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
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


class CollectionCreateForm(FormStyleMixin, forms.ModelForm):
    """Formulario robusto para crear colecciones."""

    class Meta:
        model = Collection
        fields = [
            'name', 'slug', 'description', 'status', 'products',
            'start_date', 'end_date',
            'cover_image',
            'primary_color', 'secondary_color', 'background_color', 'text_color',
            'background_image',
            'title_font',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full', 'placeholder': 'Ej: Colección Verano 2024'}),
            'slug': forms.TextInput(attrs={'class': 'w-full', 'readonly': 'readonly'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'w-full'}),
            'status': forms.Select(attrs={'class': 'w-full'}),
            'products': forms.SelectMultiple(attrs={'class': 'w-full', 'size': 8}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full'}),
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
        self.fields['products'].queryset = Product.objects.filter(is_active=True)
        self.fields['slug'].required = False
        self.fields['slug'].help_text = MSG_COLLECTION_SLUG_GENERATED

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError('El nombre de la colección es obligatorio.')

        if Collection.all_objects.filter(name__iexact=name).exists():
            raise ValidationError(MSG_COLLECTION_NAME_EXISTS_DELETED)
        return name

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        if slug and Collection.all_objects.filter(slug__iexact=slug).exists():
            raise ValidationError(MSG_COLLECTION_SLUG_EXISTS)
        return slug

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date and start_date < timezone.now():
            raise ValidationError(MSG_COLLECTION_DATE_PAST_ERROR)
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        if end_date and end_date < timezone.now():
            raise ValidationError(MSG_COLLECTION_DATE_PAST_ERROR)
        return end_date

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        status = cleaned_data.get('status')
        products = cleaned_data.get('products', [])

        if start_date and end_date and start_date >= end_date:
            self.add_error('end_date', MSG_COLLECTION_END_DATE_AFTER_START)

        if status == 'publicada' and not products:
            self.add_error('status', MSG_COLLECTION_PUBLISHED_NO_PRODUCTS)

        return cleaned_data


class CollectionUpdateForm(FormStyleMixin, forms.ModelForm):
    """Formulario robusto para actualizar colecciones."""

    class Meta:
        model = Collection
        fields = [
            'name', 'slug', 'description', 'status', 'products',
            'start_date', 'end_date',
            'cover_image',
            'primary_color', 'secondary_color', 'background_color', 'text_color',
            'background_image',
            'title_font',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full'}),
            'slug': forms.TextInput(attrs={'class': 'w-full', 'readonly': 'readonly'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'w-full'}),
            'status': forms.Select(attrs={'class': 'w-full'}),
            'products': forms.SelectMultiple(attrs={'class': 'w-full', 'size': 8}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full'}),
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
        self.fields['products'].queryset = Product.objects.filter(is_active=True)
        self.fields['slug'].required = False
        self.fields['slug'].help_text = MSG_COLLECTION_SLUG_GENERATED

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError('El nombre de la colección es obligatorio.')

        qs = Collection.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(MSG_COLLECTION_NAME_EXISTS_ACTIVE)
        return name

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        qs = Collection.objects.filter(slug__iexact=slug)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(MSG_COLLECTION_SLUG_EXISTS)
        return slug

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date and start_date < timezone.now():
            raise ValidationError(MSG_COLLECTION_DATE_PAST_ERROR)
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        if end_date and end_date < timezone.now():
            raise ValidationError(MSG_COLLECTION_DATE_PAST_ERROR)
        return end_date

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        status = cleaned_data.get('status')
        products = cleaned_data.get('products', [])

        if start_date and end_date and start_date >= end_date:
            self.add_error('end_date', MSG_COLLECTION_END_DATE_AFTER_START)

        if status == 'publicada' and not products:
            self.add_error('status', MSG_COLLECTION_PUBLISHED_NO_PRODUCTS)

        if self.instance and self.instance.status != 'publicada' and status == 'publicada':
            conflicting = Collection.objects.filter(
                status='publicada',
                is_active=True,
                products__in=products
            ).exclude(pk=self.instance.pk).distinct()

            if conflicting.exists():
                product_names = []
                for collection in conflicting[:3]:
                    product_names.extend([p.name for p in collection.products.filter(is_active=True)[:2]])
                self.add_error(
                    'status',
                    MSG_COLLECTION_PRODUCTS_IN_OTHER_PUBLISHED.format(', '.join(set(product_names)[:5]))
                )

        return cleaned_data


class CollectionDeleteForm(FormStyleMixin, forms.Form):
    """Formulario para soft-delete de colección."""

    confirm = forms.CharField(
        required=True,
        label=CONFIRM_DELETE_COLLECTION,
        widget=forms.TextInput(attrs={'class': 'w-full', 'placeholder': 'Escribe el nombre de la colección'})
    )

    def __init__(self, *args, **kwargs):
        self.collection = kwargs.pop('collection', None)
        super().__init__(*args, **kwargs)

    def clean_confirm(self):
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


class CollectionRestoreForm(FormStyleMixin, forms.Form):
    """Formulario para restaurar colección eliminada."""

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
        cleaned_data = super().clean()

        if not self.collection:
            raise ValidationError(ERROR_COLLECTION_NOT_SPECIFIED)

        if Collection.objects.filter(slug=self.collection.slug, is_active=True).exists():
            raise ValidationError(MSG_COLLECTION_RESTORE_ACTIVE_SLUG.format(self.collection.slug))

        if not cleaned_data.get('confirm'):
            raise ValidationError(ERROR_CONFIRM_RESTORE)

        return cleaned_data


class CollectionStyleForm(forms.ModelForm):
    """Formulario para estilos y configuración de tarjetas de colección."""

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
    card_border_radius = forms.CharField(
        max_length=20,
        required=False,
        initial=DEFAULT_BORDER_RADIUS,
        label=LABEL_CARD_BORDER_RADIUS,
        help_text='Ej: 0.5rem, 1rem, 8px, 12px'
    )
    card_shadow = forms.CharField(
        max_length=200,
        required=False,
        initial=DEFAULT_BOX_SHADOW,
        label=LABEL_CARD_SHADOW,
        help_text='CSS box-shadow. Ej: 0 10px 15px -3px rgba(0,0,0,0.1)'
    )
    card_hover_scale = forms.DecimalField(
        required=False,
        initial=DEFAULT_HOVER_SCALE,
        max_digits=4,
        decimal_places=2,
        label=LABEL_CARD_HOVER_SCALE,
        help_text='Ej: 1.05 (5% más grande), 1.1 (10% más grande)'
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
        help_text='Muestra el estado del stock (disponible, agotado, últimas unidades)'
    )

    class Meta:
        model = Collection
        fields = [
            'name', 'slug', 'description', 'status', 'products',
            'start_date', 'end_date',
            'cover_image',
            'primary_color', 'secondary_color', 'background_color', 'text_color',
            'background_image',
            'title_font',
            'effects_config',
            'custom_css',
            'style_config',
            'is_active',
        ]
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}),
            'background_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}),
            'text_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_PICKER}),
            'custom_css': forms.Textarea(attrs={'rows': 8, 'class': 'w-full font-mono'}),
            'effects_config': forms.Textarea(attrs={'rows': 6, 'class': 'w-full font-mono', 'placeholder': '{\n  "hover_effect": "zoom",\n  "animation": "fadeIn"\n}'}),
            'slug': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['products'].queryset = Product.objects.filter(is_active=True)
        self.fields['slug'].required = False

        if self.instance and self.instance.style_config:
            card_config = self.instance.style_config.get('card_config', {})
            self.fields['card_background_color'].initial = card_config.get('background_color', self.instance.background_color or DEFAULT_BACKGROUND_COLOR)
            self.fields['card_title_color'].initial = card_config.get('title_color', self.instance.primary_color or DEFAULT_PRIMARY_COLOR)
            self.fields['card_price_color'].initial = card_config.get('price_color', self.instance.primary_color or DEFAULT_PRIMARY_COLOR)
            self.fields['card_border_radius'].initial = card_config.get('border_radius', DEFAULT_BORDER_RADIUS)
            self.fields['card_shadow'].initial = card_config.get('shadow', DEFAULT_BOX_SHADOW)
            self.fields['card_hover_scale'].initial = card_config.get('hover_scale', DEFAULT_HOVER_SCALE)
            self.fields['card_show_category'].initial = card_config.get('show_category', DEFAULT_SHOW_CATEGORY)
            self.fields['card_show_stock_badge'].initial = card_config.get('show_stock_badge', DEFAULT_SHOW_STOCK_BADGE)

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
        """Asegura que la configuración de colores exista en style_config."""
        if 'colors' not in style_config:
            style_config['colors'] = {
                'primary': instance.primary_color or DEFAULT_PRIMARY_COLOR,
                'secondary': instance.secondary_color or DEFAULT_SECONDARY_COLOR,
                'background': instance.background_color or DEFAULT_BACKGROUND_COLOR,
                'text': instance.text_color or DEFAULT_TEXT_COLOR,
            }
        return style_config

    def _ensure_typography_config(self, style_config, instance):
        """Asegura que la configuración de tipografía exista en style_config."""
        if 'typography' not in style_config:
            style_config['typography'] = {
                'title_font': instance.title_font or DEFAULT_TITLE_FONT,
            }
        return style_config

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        status = cleaned_data.get('status')
        products = cleaned_data.get('products', [])

        if start_date and end_date and start_date >= end_date:
            self.add_error('end_date', MSG_COLLECTION_END_DATE_AFTER_START)

        if status == 'publicada' and not products:
            self.add_error('status', MSG_COLLECTION_PUBLISHED_NO_PRODUCTS)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        cleaned_data = self.cleaned_data

        card_config = self._build_card_config(instance, cleaned_data)

        style_config = instance.style_config or {}
        style_config = self._ensure_colors_config(style_config, instance)
        style_config = self._ensure_typography_config(style_config, instance)
        style_config['card_config'] = card_config

        instance.style_config = style_config

        if commit:
            instance.save()
        return instance