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


class CollectionCreateForm(FormStyleMixin, forms.ModelForm):
    class Meta:
        model = Collection
        fields = [
            'name', 'description', 'status', 'start_date', 'end_date',
            'cover_image', 'primary_color', 'secondary_color', 
            'background_color', 'text_color', 'background_image',
            'title_font', 'products', 'slug'
        ]
        widgets = {
            'name': forms.TextInput(),
            'description': forms.Textarea(attrs={'rows': 4}),
            'status': forms.Select(),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'cover_image': forms.ClearableFileInput(),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_INPUT}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_INPUT}),
            'background_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_INPUT}),
            'text_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_INPUT}),
            'background_image': forms.ClearableFileInput(),
            'title_font': forms.TextInput(attrs={"placeholder": "'Inter', sans-serif"}),
            'products': forms.SelectMultiple(attrs={'size': 10}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['products'].queryset = Product.objects.filter(is_active=True)
        self.fields['slug'].required = False
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        
        if Collection.all_objects.filter(name__iexact=name).exists():
            raise ValidationError('Ya existe una colección con ese nombre (activa o eliminada).')
        
        return name
    
    def clean(self):
        cleaned_data = super().clean()
        
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        status = cleaned_data.get('status')
        products = cleaned_data.get('products', [])
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError({
                'end_date': 'La fecha de fin debe ser posterior a la fecha de inicio.'
            })
        
        if status == 'publicada' and not products:
            raise ValidationError({
                'status': 'Una colección publicada debe tener al menos un producto asignado.'
            })
        
        return cleaned_data


class CollectionUpdateForm(FormStyleMixin, forms.ModelForm):
    class Meta:
        model = Collection
        fields = [
            'name', 'description', 'status', 'start_date', 'end_date',
            'cover_image', 'primary_color', 'secondary_color', 
            'background_color', 'text_color', 'background_image',
            'title_font', 'products', 'is_active', 'slug'
        ]
        widgets = {
            'name': forms.TextInput(),
            'description': forms.Textarea(attrs={'rows': 4}),
            'status': forms.Select(),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'cover_image': forms.ClearableFileInput(),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_INPUT}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_INPUT}),
            'background_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_INPUT}),
            'text_color': forms.TextInput(attrs={'type': 'color', 'style': STYLE_COLOR_INPUT}),
            'background_image': forms.ClearableFileInput(),
            'title_font': forms.TextInput(),
            'products': forms.SelectMultiple(attrs={'size': 10}),
            'is_active': forms.CheckboxInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['products'].queryset = Product.objects.filter(is_active=True)
        self.fields['slug'].required = False
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        qs = Collection.objects.filter(name__iexact=name)
        
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError('Ya existe una colección activa con ese nombre.')
        
        return name
    
    def clean(self):
        cleaned_data = super().clean()
        
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        status = cleaned_data.get('status')
        products = cleaned_data.get('products', [])
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError({
                'end_date': 'La fecha de fin debe ser posterior a la fecha de inicio.'
            })
        
        if status == 'publicada' and not products:
            raise ValidationError({
                'status': 'Una colección publicada debe tener al menos un producto asignado.'
            })
        
        if self.instance and self.instance.status != 'publicada' and status == 'publicada':
            conflicting = Collection.objects.filter(
                status='publicada', is_active=True, products__in=products
            ).exclude(pk=self.instance.pk).distinct()
            
            if conflicting.exists():
                product_names = []
                for collection in conflicting[:3]:
                    product_names.extend([p.name for p in collection.products.filter(is_active=True)[:2]])
                
                raise ValidationError({
                    'status': f'Los siguientes productos ya pertenecen a otra colección publicada: {", ".join(set(product_names)[:5])}'
                })
        
        return cleaned_data


class CollectionDeleteForm(FormStyleMixin, forms.Form):
    confirm = forms.CharField(
        required=True,
        label=CONFIRM_DELETE_COLLECTION,
        widget=forms.TextInput()
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
        
        return value


class CollectionRestoreForm(FormStyleMixin, forms.Form):
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que deseo restaurar esta colección'
    )
    restore_products_type = forms.BooleanField(
        required=False,
        initial=True,
        label='Actualizar tipo de productos',
        help_text='Si está activado, los productos de esta colección pasarán a "Colección limitada" si no están en otra colección publicada.'
    )
    
    def __init__(self, *args, **kwargs):
        self.collection = kwargs.pop('collection', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.collection:
            raise ValidationError(ERROR_COLLECTION_NOT_SPECIFIED)
        
        if Collection.objects.filter(slug=self.collection.slug).exists():
            raise ValidationError(f'Ya existe una colección activa con el slug "{self.collection.slug}".')
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError(ERROR_CONFIRM_RESTORE)
        
        return cleaned_data