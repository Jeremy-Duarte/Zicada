from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .models import (
    Size, Category, Color, Product, ProductVariant, 
    Collection, ProductColor, ProductImage
)
from apps.core.crud.mixins import FormStyleMixin
from apps.core.crud.widgets import CloudinaryImageSelectWidget, CloudinaryFeaturedImageWidget

# ========== FORMULARIOS PARA CATÁLOGOS ESTÁTICOS ==========

class SizeCreateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para crear tallas"""
    
    class Meta:
        model = Size
        fields = ['name', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ej: XS, S, M, L, XL'}),
            'sort_order': forms.NumberInput(attrs={'min': 0}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').upper().strip()
        if Size.objects.filter(name=name).exists():
            raise ValidationError(f'La talla "{name}" ya existe.')
        return name


class SizeUpdateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para actualizar tallas"""
    
    class Meta:
        model = Size
        fields = ['name', 'sort_order']
        widgets = {
            'name': forms.TextInput(),
            'sort_order': forms.NumberInput(attrs={'min': 0}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').upper().strip()
        qs = Size.objects.filter(name=name)
        
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError(f'La talla "{name}" ya existe.')
        
        return name


class SizeDeleteForm(FormStyleMixin, forms.Form):
    """Formulario para eliminar talla (con verificación de uso)"""
    
    confirm = forms.CharField(
        required=True,
        label='Escribe el nombre de la talla para confirmar',
        widget=forms.TextInput(attrs={'placeholder': 'Ej: M'})
    )
    
    def __init__(self, *args, **kwargs):
        self.size = kwargs.pop('size', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        value = self.cleaned_data.get('confirm', '').upper().strip()
        
        if not self.size:
            raise ValidationError('Talla no especificada.')
        
        if self.size.name != value:
            raise ValidationError('El nombre de la talla no coincide.')
        
        # Verificar si hay variantes usando esta talla
        if self.size.variants.filter(is_active=True).exists():
            raise ValidationError(
                f'No se puede eliminar la talla "{self.size.name}" porque está siendo usada '
                f'en {self.size.variants.count()} variante(s) activas.'
            )
        
        return value


# ========== CATEGORY FORMS ==========

class CategoryCreateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para crear categorías (slug automático por el modelo)"""
    
    class Meta:
        model = Category
        fields = ['name', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ej: Camisetas, Hoodies'}),
            'sort_order': forms.NumberInput(attrs={'min': 0}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        
        if Category.objects.filter(name__iexact=name).exists():
            raise ValidationError(f'La categoría "{name}" ya existe.')
        
        return name


class CategoryUpdateForm(FormStyleMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'sort_order']
        widgets = {
            'name': forms.TextInput(),
            'sort_order': forms.NumberInput(attrs={'min': 0}),
        }
    
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
    """Formulario para eliminar categoría (con verificación de productos)"""
    
    confirm = forms.CharField(
        required=True,
        label='Escribe el nombre de la categoría para confirmar',
        widget=forms.TextInput()
    )
    
    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        value = self.cleaned_data.get('confirm', '').strip().lower()
        
        if not self.category:
            raise ValidationError('Categoría no especificada.')
        
        if self.category.name.lower() != value:
            raise ValidationError('El nombre de la categoría no coincide.')
        
        # Verificar productos activos en esta categoría
        active_products = self.category.products.filter(is_active=True)
        if active_products.exists():
            raise ValidationError(
                f'No se puede eliminar la categoría "{self.category.name}" porque tiene '
                f'{active_products.count()} producto(s) activo(s).'
            )
        
        return value


# ========== COLOR FORMS (Catálogo) ==========

class ColorCreateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para crear colores"""
    
    class Meta:
        model = Color
        fields = ['name', 'code', 'sort_order']
        widgets = {
            'name': forms.TextInput(),
            'code': forms.TextInput(attrs={'type': 'color', 'style': 'height: 40px;'}),
            'sort_order': forms.NumberInput(attrs={'min': 0}),
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
        
        # Validar formato hexadecimal
        import re
        if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', code):
            raise ValidationError('El código debe ser un color hexadecimal válido (ej: #FF0000, #F00)')
        
        if Color.objects.filter(code__iexact=code).exists():
            raise ValidationError(f'El código de color "{code}" ya está en uso.')
        
        return code


class ColorUpdateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para actualizar colores"""
    
    class Meta:
        model = Color
        fields = ['name', 'code', 'sort_order']
        widgets = {
            'name': forms.TextInput(),
            'code': forms.TextInput(attrs={'type': 'color', 'style': 'height: 40px;'}),
            'sort_order': forms.NumberInput(attrs={'min': 0}),
        }
    
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
        
        import re
        if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', code):
            raise ValidationError('El código debe ser un color hexadecimal válido (ej: #FF0000, #F00)')
        
        qs = Color.objects.filter(code__iexact=code)
        
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError(f'El código de color "{code}" ya está en uso.')
        
        return code


class ColorDeleteForm(FormStyleMixin, forms.Form):
    """Formulario para eliminar color (con verificación de uso)"""
    
    confirm = forms.CharField(
        required=True,
        label='Escribe el nombre del color para confirmar',
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Rojo'})
    )
    
    def __init__(self, *args, **kwargs):
        self.color = kwargs.pop('color', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        value = self.cleaned_data.get('confirm', '').strip().capitalize()
        
        if not self.color:
            raise ValidationError('Color no especificado.')
        
        if self.color.name != value:
            raise ValidationError('El nombre del color no coincide.')
        
        if self.color.product_colors.filter(is_active=True).exists():
            count = self.color.product_colors.filter(is_active=True).count()
            raise ValidationError(
                f'No se puede eliminar el color "{self.color.name}" porque está siendo usado '
                f'en {count} variante(s) de producto(s).'
            )
        
        return value


# ========== PRODUCT IMAGE FORMS ==========

class ProductImageCreateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para subir imágenes de productos"""
    
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
            # Validar tamaño máximo (5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('La imagen no puede superar los 5MB.')
            
            # Validar extensiones
            import os
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                raise ValidationError('Formato no soportado. Usa JPG, PNG, WEBP o GIF.')
        
        return image


class ProductImageUpdateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para actualizar metadatos de imagen"""
    
    class Meta:
        model = ProductImage
        fields = ['alt_text']
        widgets = {
            'alt_text': forms.TextInput(),
        }


class ProductImageDeleteForm(FormStyleMixin, forms.Form):
    """Formulario para eliminar imagen"""
    
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
            raise ValidationError('Imagen no especificada.')
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError('Debes confirmar la eliminación.')
        
        return cleaned_data


# ========== PRODUCT FORMS ==========

class ProductCreateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para crear productos"""
    
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
            raise ValidationError('El precio debe ser mayor a 0.')
        
        if price > 10000000:  # 10 millones COP
            raise ValidationError('El precio no puede superar los $10,000,000 COP.')
        
        return price


class ProductUpdateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para actualizar productos"""
    
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
            raise ValidationError('El precio debe ser mayor a 0.')
        
        if price > 10000000:
            raise ValidationError('El precio no puede superar los $10,000,000 COP.')
        
        return price


class ProductDeleteForm(FormStyleMixin, forms.Form):
    """Formulario para soft-delete de producto"""
    
    confirm = forms.CharField(
        required=True,
        label='Escribe el nombre del producto para confirmar',
        widget=forms.TextInput()
    )
    
    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        value = self.cleaned_data.get('confirm', '').strip().lower()
        
        if not self.product:
            raise ValidationError('Producto no especificado.')
        
        if self.product.name.lower() != value:
            raise ValidationError('El nombre del producto no coincide.')
        
        # Verificar si tiene pedidos asociados (no cancelados)
        has_orders = self.product.variants.filter(
            order_items__order__status__in=['pendiente', 'confirmado', 'preparando', 'listo', 'en_camino']
        ).exists()
        
        if has_orders:
            raise ValidationError(
                'No se puede eliminar este producto porque tiene pedidos en curso asociados. '
                'Considere desactivarlo en lugar de eliminarlo.'
            )
        
        return value


class ProductRestoreForm(FormStyleMixin, forms.Form):
    """Formulario para restaurar producto (soft-delete)"""
    
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
            raise ValidationError('Producto no especificado.')
        
        # Verificar si ya existe un producto activo con el mismo nombre
        if Product.objects.filter(name__iexact=self.product.name).exists():
            raise ValidationError('Ya existe un producto activo con este nombre.')
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError('Debes confirmar la restauración.')
        
        return cleaned_data


# ========== PRODUCT COLOR FORMS ==========

class ProductColorCreateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para asignar colores a un producto"""
    
    class Meta:
        model = ProductColor
        fields = ['color', 'images', 'featured_image', 'sort_order']
        widgets = {
            'color': forms.Select(),
            'images': CloudinaryImageSelectWidget(),
            'featured_image': CloudinaryFeaturedImageWidget(images_widget_name='images'),
            'sort_order': forms.NumberInput(attrs={'min': 0}),
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
            raise ValidationError('Producto no especificado.')
        
        color = cleaned_data.get('color')
        
        if color and ProductColor.all_objects.filter(product=self.product, color=color).exists():
            raise ValidationError(f'El color {color.name} ya está asignado a este producto.')
        
        featured_image = cleaned_data.get('featured_image')
        images = cleaned_data.get('images', [])
        
        if featured_image and featured_image not in images:
            raise ValidationError('La imagen destacada debe estar seleccionada en la lista de imágenes.')
        
        return cleaned_data


class ProductColorUpdateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para actualizar colores de producto"""
    
    class Meta:
        model = ProductColor
        fields = ['images', 'featured_image', 'sort_order', 'is_active']
        widgets = {
            'images': CloudinaryImageSelectWidget(),
            'featured_image': CloudinaryFeaturedImageWidget(images_widget_name='images'),
            'sort_order': forms.NumberInput(attrs={'min': 0}),
            'is_active': forms.CheckboxInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            self.fields['featured_image'].queryset = ProductImage.objects.all()
            self.fields['images'].queryset = ProductImage.objects.all()
    
    def clean(self):
        cleaned_data = super().clean()
        
        featured_image = cleaned_data.get('featured_image')
        images = cleaned_data.get('images', [])
        
        if featured_image and featured_image not in images:
            raise ValidationError('La imagen destacada debe estar seleccionada en la lista de imágenes.')
        
        return cleaned_data


class ProductColorDeleteForm(FormStyleMixin, forms.Form):
    """Formulario para eliminar color de producto"""
    
    confirm = forms.CharField(
        required=True,
        label='Escribe el nombre del color para confirmar',
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
        
        # Verificar variantes activas
        active_variants = self.product_color.variants.filter(is_active=True)
        if active_variants.exists():
            raise ValidationError(
                f'No se puede eliminar el color {self.product_color.color.name} porque tiene '
                f'{active_variants.count()} variante(s) activa(s). Desactive las variantes primero.'
            )
        
        return value


# ========== PRODUCT VARIANT FORMS ==========

class ProductVariantCreateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para crear variantes de producto"""
    
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
            raise ValidationError('Producto no especificado.')
        
        product_color = cleaned_data.get('product_color')
        size = cleaned_data.get('size')
        
        if product_color and size:
            # Verificar si ya existe la variante
            if ProductVariant.all_objects.filter(
                product=self.product, product_color=product_color, size=size
            ).exists():
                raise ValidationError(
                    f'Ya existe una variante para {product_color.color.name} - Talla {size.name}. '
                    f'Use el formulario de actualización para modificar el stock.'
                )
        
        return cleaned_data


class ProductVariantUpdateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para actualizar variantes"""
    
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
    """Formulario para soft-delete de variante"""
    
    confirm = forms.CharField(
        required=True,
        label='Escribe "ELIMINAR" para confirmar',
        widget=forms.TextInput(attrs={'placeholder': 'ELIMINAR'})
    )
    
    def __init__(self, *args, **kwargs):
        self.variant = kwargs.pop('variant', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        value = self.cleaned_data.get('confirm', '').upper().strip()
        
        if not self.variant:
            raise ValidationError('Variante no especificada.')
        
        if value != 'ELIMINAR':
            raise ValidationError('Debes escribir "ELIMINAR" para confirmar.')
        
        # Verificar si tiene pedidos no entregados
        pending_orders = self.variant.order_items.filter(
            order__status__in=['pendiente', 'confirmado', 'preparando', 'listo', 'en_camino']
        ).exists()
        
        if pending_orders:
            raise ValidationError(
                'No se puede eliminar esta variante porque tiene pedidos pendientes asociados.'
            )
        
        return value


class ProductVariantRestoreForm(FormStyleMixin, forms.Form):
    """Formulario para restaurar variante"""
    
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
            raise ValidationError('Variante no especificada.')
        
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
            raise ValidationError('Debes confirmar la restauración.')
        
        return cleaned_data


# ========== COLLECTION FORMS ==========

class CollectionCreateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para crear colecciones"""
    
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
            'primary_color': forms.TextInput(attrs={'type': 'color', 'style': 'height: 40px;'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'style': 'height: 40px;'}),
            'background_color': forms.TextInput(attrs={'type': 'color', 'style': 'height: 40px;'}),
            'text_color': forms.TextInput(attrs={'type': 'color', 'style': 'height: 40px;'}),
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
    """Formulario para actualizar colecciones"""
    
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
            'primary_color': forms.TextInput(attrs={'type': 'color', 'style': 'height: 40px;'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'style': 'height: 40px;'}),
            'background_color': forms.TextInput(attrs={'type': 'color', 'style': 'height: 40px;'}),
            'text_color': forms.TextInput(attrs={'type': 'color', 'style': 'height: 40px;'}),
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
        
        # Si la colección pasa a publicada, verificar que no haya conflictos
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
    """Formulario para soft-delete de colección"""
    
    confirm = forms.CharField(
        required=True,
        label='Escribe el nombre de la colección para confirmar',
        widget=forms.TextInput()
    )
    
    def __init__(self, *args, **kwargs):
        self.collection = kwargs.pop('collection', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        value = self.cleaned_data.get('confirm', '').strip().lower()
        
        if not self.collection:
            raise ValidationError('Colección no especificada.')
        
        if self.collection.name.lower() != value:
            raise ValidationError('El nombre de la colección no coincide.')
        
        return value


class CollectionRestoreForm(FormStyleMixin, forms.Form):
    """Formulario para restaurar colección"""
    
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
            raise ValidationError('Colección no especificada.')
        
        # Verificar si ya existe una colección activa con el mismo slug
        if Collection.objects.filter(slug=self.collection.slug).exists():
            raise ValidationError(f'Ya existe una colección activa con el slug "{self.collection.slug}".')
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError('Debes confirmar la restauración.')
        
        return cleaned_data