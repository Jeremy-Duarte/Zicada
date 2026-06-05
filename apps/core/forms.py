from django import forms
from django.contrib.auth.forms import AuthenticationForm
from apps.core.crud.mixins import FormStyleMixin, SortableUpdateMixin
from django.core.exceptions import ValidationError
from .models import HeroConfig
from apps.products.models import Collection, Product
from apps.core.crud.widgets import CloudinarySingleImageWidget, SortableOrderWidget
from apps.core.utils import safe_reverse

class ContactForm(FormStyleMixin, forms.Form):
    
    name = forms.CharField(
        max_length=200,
        min_length=2,
        required=True,
        label='Nombre completo',
        error_messages={
            'required': 'Por favor ingresa tu nombre',
            'min_length': 'El nombre debe tener al menos 2 caracteres'
        }
    )
    
    email = forms.EmailField(
        required=True,
        label='Correo electrónico',
        error_messages={
            'required': 'Por favor ingresa tu correo electrónico',
            'invalid': 'Ingresa un correo electrónico válido'
        }
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='Teléfono',
    )
    
    subject = forms.CharField(
        max_length=200,
        required=True,
        label='Asunto',
        error_messages={
            'required': 'Por favor ingresa un asunto'
        }
    )
    
    message = forms.CharField(
        required=True,
        label='Mensaje',
        widget=forms.Textarea(attrs={'rows': 5}),
        error_messages={
            'required': 'Por favor ingresa tu mensaje'
        }
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = 'Tu nombre'
        self.fields['email'].widget.attrs['placeholder'] = 'tu@email.com'
        self.fields['phone'].widget.attrs['placeholder'] = 'Tu número de contacto'
        self.fields['subject'].widget.attrs['placeholder'] = '¿Sobre qué nos quieres contactar?'
        self.fields['message'].widget.attrs['placeholder'] = 'Cuéntanos en qué podemos ayudarte...'
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if phone:
            digits = ''.join(c for c in phone if c.isdigit())
            if len(digits) < 7 and len(digits) > 0:
                raise forms.ValidationError('El número de teléfono debe tener al menos 7 dígitos')
            return digits
        return ''


class StaffLoginForm(FormStyleMixin, AuthenticationForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Usuario'
        self.fields['password'].widget.attrs['placeholder'] = 'Contraseña'
    
    def confirm_login_allowed(self, user):
        if not (user.is_staff or getattr(user, 'is_delivery', False)):
            raise forms.ValidationError(
                'No tienes permisos para acceder a esta área.',
                code='no_permission',
            )
        super().confirm_login_allowed(user)

# Opciones de fuentes predefinidas
FONT_FAMILY_CHOICES = [
    ("'Inter', sans-serif", "Inter"),
    ("'Roboto', sans-serif", "Roboto"),
    ("'Poppins', sans-serif", "Poppins"),
    ("'Montserrat', sans-serif", "Montserrat"),
    ("'Open Sans', sans-serif", "Open Sans"),
    ("'Playfair Display', serif", "Playfair Display"),
    ("'Merriweather', serif", "Merriweather"),
]

# Opciones de peso de fuente
FONT_WEIGHT_CHOICES = [
    ('300', 'Light (300)'),
    ('400', 'Regular (400)'),
    ('500', 'Medium (500)'),
    ('600', 'Semi Bold (600)'),
    ('700', 'Bold (700)'),
    ('800', 'Extra Bold (800)'),
    ('900', 'Black (900)'),
]

# Opciones de alineación
ALIGNMENT_CHOICES = [
    ('center', 'Centrado'),
    ('left', 'Izquierda'),
    ('right', 'Derecha'),
]

# Opciones de altura de sección
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
    ('6rem', 'Extra gigante (6rem)'),
    ('10rem', 'Masivo (10rem)'),
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

BUTTON_BG_CHOICES = [
    ('bg-zicada-accent', '🔴 Rojo Zicada'),
    ('bg-black', '⚫ Negro'),
    ('bg-white', '⚪ Blanco'),
    ('bg-gray-800', '🌑 Gris oscuro'),
    ('bg-gray-100', '☁️ Gris claro'),
    ('bg-blue-600', '💙 Azul'),
    ('bg-green-600', '💚 Verde'),
    ('bg-purple-600', '💜 Morado'),
    ('bg-amber-600', '🟠 Ámbar'),
    ('bg-transparent', '✨ Transparente'),
]

# Opciones para colores hover
BUTTON_HOVER_CHOICES = [
    ('hover:bg-red-700', '🔴 Rojo más oscuro'),
    ('hover:bg-gray-700', '⚫ Negro más oscuro'),
    ('hover:bg-gray-100', '⚪ Gris claro'),
    ('hover:bg-gray-900', '🌑 Negro intenso'),
    ('hover:bg-blue-700', '💙 Azul más oscuro'),
    ('hover:bg-green-700', '💚 Verde más oscuro'),
    ('hover:bg-purple-700', '💜 Morado más oscuro'),
    ('hover:bg-amber-700', '🟠 Ámbar más oscuro'),
    ('hover:bg-white', '⚪ Blanco'),
    ('hover:bg-opacity-90', '🎨 90% opacidad'),
]

# Opciones para color de texto
BUTTON_TEXT_COLOR_CHOICES = [
    ('text-white', '⚪ Blanco'),
    ('text-gray-900', '⚫ Negro'),
    ('text-gray-700', '🌑 Gris oscuro'),
    ('text-gray-500', '🌫️ Gris medio'),
    ('text-zicada-accent', '🔴 Rojo Zicada'),
    ('text-blue-600', '💙 Azul'),
]

# Opciones para bordes
BUTTON_BORDER_CHOICES = [
    ('rounded-none', '🔲 Cuadrado'),
    ('rounded-md', '📐 Medianamente redondeado'),
    ('rounded-lg', '🟨 Redondeado'),
    ('rounded-xl', '🟩 Muy redondeado'),
    ('rounded-2xl', '🟢 Extra redondeado'),
    ('rounded-full', '⚪ Círculo completo'),
]

# Opciones para tamaño
BUTTON_SIZE_CHOICES = [
    ('px-3 py-1.5 text-sm', 'Pequeño'),
    ('px-4 py-2 text-base', 'Mediano'),
    ('px-6 py-2.5 text-base', 'Mediano-grande'),
    ('px-8 py-3 text-lg', 'Grande (recomendado)'),
    ('px-10 py-4 text-xl', 'Muy grande'),
]

# Opciones para sombra
BUTTON_SHADOW_CHOICES = [
    ('shadow-none', 'Sin sombra'),
    ('shadow-sm', 'Sombra suave'),
    ('shadow', 'Sombra normal'),
    ('shadow-md', 'Sombra media'),
    ('shadow-lg', 'Sombra grande'),
    ('shadow-xl', 'Sombra extra grande'),
]

# Opciones para ancho
BUTTON_WIDTH_CHOICES = [
    ('inline-block', 'Automático (según el texto)'),
    ('w-full', 'Ancho completo'),
    ('w-48', 'Fijo (192px)'),
    ('w-56', 'Fijo (224px)'),
    ('w-64', 'Fijo (256px)'),
]

def get_button_url_choices():
    choices = [
        (safe_reverse('products:catalog'), '📦 Catálogo general'),
        (safe_reverse('products:collections_list'), '🎨 Todas las colecciones'),
    ]
    
    for collection in Collection.objects.filter(is_active=True, status='publicada')[:15]:
        choices.append((
            safe_reverse('products:collection_detail', kwargs={'slug': collection.slug}),
            f'📁 Colección: {collection.name}'
        ))
    
    for product in Product.objects.filter(is_active=True).select_related('category')[:10]:
        choices.append((
            safe_reverse('products:product_detail', kwargs={'slug': product.slug}),
            f'👕 Producto: {product.name}'
        ))
    
    return choices


class HeroConfigCreateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para crear slides del hero (carrusel)"""
    
    # Campo para URL del botón (usando la misma función)
    button_url = forms.ChoiceField(choices=[], required=True, label='Destino del botón', help_text='Selecciona a dónde irá el usuario')
    
    # Campos para construcción del botón
    button_bg_color = forms.ChoiceField(choices=BUTTON_BG_CHOICES, required=True, label='Color de fondo')
    button_hover_color = forms.ChoiceField(choices=BUTTON_HOVER_CHOICES, required=True, label='Color al pasar el mouse')
    button_text_color = forms.ChoiceField(choices=BUTTON_TEXT_COLOR_CHOICES, required=True, label='Color del texto')
    button_border_radius = forms.ChoiceField(choices=BUTTON_BORDER_CHOICES, required=True, label='Bordes')
    button_size = forms.ChoiceField(choices=BUTTON_SIZE_CHOICES, required=True, label='Tamaño')
    button_shadow = forms.ChoiceField(choices=BUTTON_SHADOW_CHOICES, required=True, label='Sombra')
    button_width = forms.ChoiceField(choices=BUTTON_WIDTH_CHOICES, required=True, label='Ancho del botón')
    
    class Meta:
        model = HeroConfig
        fields = '__all__'
        exclude = ['button_style']  # Excluir button_style porque lo construimos
        widgets = {
            'background_image': CloudinarySingleImageWidget(),
            'overlay_opacity': forms.NumberInput(attrs={'min': 0, 'max': 1, 'step': 0.1}),
            'title_text': forms.TextInput(attrs={'placeholder': 'Ej: ZICADA'}),
            'title_font_family': forms.Select(choices=FONT_FAMILY_CHOICES),
            'title_font_size': forms.Select(choices=SIZE_CHOICES),
            'title_font_weight': forms.Select(choices=FONT_WEIGHT_CHOICES),
            'title_line_height': forms.Select(choices=LINE_HEIGHT_CHOICES),
            'title_color': forms.TextInput(attrs={'type': 'color'}),
            'title_margin_bottom': forms.Select(choices=MARGIN_CHOICES),
            'subtitle_text': forms.Textarea(attrs={'rows': 2, 'placeholder': 'LA MODA SE VA, TU ESTILO PERMANECE'}),
            'subtitle_font_family': forms.Select(choices=FONT_FAMILY_CHOICES),
            'subtitle_font_size': forms.Select(choices=SIZE_CHOICES),
            'subtitle_font_weight': forms.Select(choices=FONT_WEIGHT_CHOICES),
            'subtitle_line_height': forms.Select(choices=LINE_HEIGHT_CHOICES),
            'subtitle_color': forms.TextInput(attrs={'type': 'color'}),
            'subtitle_margin_bottom': forms.Select(choices=MARGIN_CHOICES),
            'button_text': forms.TextInput(attrs={'placeholder': 'Explorar Catálogo'}),
            'content_alignment': forms.RadioSelect(choices=ALIGNMENT_CHOICES),
            'section_height': forms.Select(choices=SECTION_HEIGHT_CHOICES),
            'sort_order': forms.NumberInput(attrs={'min': 0}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Cargar choices para button_url
        self.fields['button_url'].choices = get_button_url_choices()
        
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ not in ['CheckboxInput', 'RadioSelect']:
                field.widget.attrs.setdefault('class', 'w-full')
        
        # Valores por defecto para los campos del botón
        self.fields['button_bg_color'].initial = 'bg-zicada-accent'
        self.fields['button_hover_color'].initial = 'hover:bg-red-700'
        self.fields['button_text_color'].initial = 'text-white'
        self.fields['button_border_radius'].initial = 'rounded-lg'
        self.fields['button_size'].initial = 'px-8 py-3 text-lg'
        self.fields['button_shadow'].initial = 'shadow-lg'
        self.fields['button_width'].initial = 'inline-block'
    
    def clean_title_text(self):
        title = self.cleaned_data.get('title_text', '').strip()
        if not title:
            raise ValidationError('El título es obligatorio.')
        return title
    
    def clean_sort_order(self):
        sort_order = self.cleaned_data.get('sort_order', 0)
        if HeroConfig.objects.filter(sort_order=sort_order).exists():
            raise ValidationError(f'Ya existe un slide con el orden {sort_order}. Usa otro valor.')
        return sort_order
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Construir button_style a partir de los campos individuales
        bg = self.cleaned_data['button_bg_color']
        hover = self.cleaned_data['button_hover_color']
        text = self.cleaned_data['button_text_color']
        rounded = self.cleaned_data['button_border_radius']
        size = self.cleaned_data['button_size']
        shadow = self.cleaned_data['button_shadow']
        width = self.cleaned_data['button_width']
        
        instance.button_style = f'{bg} {hover} {text} {rounded} {size} {shadow} {width} font-semibold transition-all duration-300 transform hover:scale-105 inline-block text-center'
        
        if commit:
            instance.save()
        return instance


class HeroConfigUpdateForm(FormStyleMixin, SortableUpdateMixin, forms.ModelForm):
    class Meta:
        model = HeroConfig
        exclude = ['sort_order', 'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by', 'button_style']
        widgets = {
            'background_image': CloudinarySingleImageWidget(),
            'overlay_opacity': forms.NumberInput(attrs={'min': 0, 'max': 1, 'step': 0.1, 'class': 'w-full'}),
            'title_text': forms.TextInput(attrs={'class': 'w-full'}),
            'title_font_family': forms.Select(choices=FONT_FAMILY_CHOICES, attrs={'class': 'w-full'}),
            'title_font_weight': forms.Select(choices=FONT_WEIGHT_CHOICES, attrs={'class': 'w-full'}),
            'title_color': forms.TextInput(attrs={'type': 'color', 'class': 'w-16 h-10 p-1'}),
            'subtitle_text': forms.Textarea(attrs={'rows': 2, 'class': 'w-full'}),
            'subtitle_font_family': forms.Select(choices=FONT_FAMILY_CHOICES, attrs={'class': 'w-full'}),
            'subtitle_font_weight': forms.Select(choices=FONT_WEIGHT_CHOICES, attrs={'class': 'w-full'}),
            'subtitle_color': forms.TextInput(attrs={'type': 'color', 'class': 'w-16 h-10 p-1'}),
            'button_text': forms.TextInput(attrs={'class': 'w-full'}),
            'content_alignment': forms.RadioSelect(choices=ALIGNMENT_CHOICES, attrs={'class': 'flex gap-4'}),
            'is_active': forms.CheckboxInput(),
        }
    
    # Campos existentes
    section_height = forms.ChoiceField(choices=SECTION_HEIGHT_CHOICES, required=False, label='Altura de la sección')
    title_font_size = forms.ChoiceField(choices=SIZE_CHOICES, required=False, label='Tamaño del título')
    title_line_height = forms.ChoiceField(choices=LINE_HEIGHT_CHOICES, required=False, label='Altura de línea del título')
    title_margin_bottom = forms.ChoiceField(choices=MARGIN_CHOICES, required=False, label='Margen inferior del título')
    subtitle_font_size = forms.ChoiceField(choices=SIZE_CHOICES, required=False, label='Tamaño del subtítulo')
    subtitle_line_height = forms.ChoiceField(choices=LINE_HEIGHT_CHOICES, required=False, label='Altura de línea del subtítulo')
    subtitle_margin_bottom = forms.ChoiceField(choices=MARGIN_CHOICES, required=False, label='Margen inferior del subtítulo')
    button_url = forms.ChoiceField(choices=[], required=True, label='Destino del botón', help_text='Selecciona a dónde irá el usuario')
    
    # Nuevos campos para construcción del botón
    button_bg_color = forms.ChoiceField(choices=BUTTON_BG_CHOICES, required=True, label='Color de fondo')
    button_hover_color = forms.ChoiceField(choices=BUTTON_HOVER_CHOICES, required=True, label='Color al pasar el mouse')
    button_text_color = forms.ChoiceField(choices=BUTTON_TEXT_COLOR_CHOICES, required=True, label='Color del texto')
    button_border_radius = forms.ChoiceField(choices=BUTTON_BORDER_CHOICES, required=True, label='Bordes')
    button_size = forms.ChoiceField(choices=BUTTON_SIZE_CHOICES, required=True, label='Tamaño')
    button_shadow = forms.ChoiceField(choices=BUTTON_SHADOW_CHOICES, required=True, label='Sombra')
    button_width = forms.ChoiceField(choices=BUTTON_WIDTH_CHOICES, required=True, label='Ancho del botón')
    
    sortable_queryset = None
    sortable_label_attr = 'title_text'
    sortable_widget_name = 'hero_order'
    sortable_widget_label = 'Orden de slides'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['button_url'].choices = get_button_url_choices()
        self.sortable_queryset = HeroConfig.objects.filter(is_active=True).order_by('sort_order')
        self._setup_sortable_widget()
        
        # Valores por defecto para los campos del botón
        default_button_style = 'bg-zicada-accent hover:bg-red-700 text-white rounded-lg px-8 py-3 text-lg shadow-lg inline-block'
        
        if self.instance.pk:
            self.fields['section_height'].initial = self.instance.section_height
            self.fields['title_font_size'].initial = self.instance.title_font_size
            self.fields['title_line_height'].initial = self.instance.title_line_height
            self.fields['title_margin_bottom'].initial = self.instance.title_margin_bottom
            self.fields['subtitle_font_size'].initial = self.instance.subtitle_font_size
            self.fields['subtitle_line_height'].initial = self.instance.subtitle_line_height
            self.fields['subtitle_margin_bottom'].initial = self.instance.subtitle_margin_bottom
            
            current_url = self.instance.button_url
            url_choices = [choice[0] for choice in self.fields['button_url'].choices]
            if current_url and current_url not in url_choices:
                self.fields['button_url'].choices = list(self.fields['button_url'].choices) + [(current_url, current_url[:50] + '...')]
                self.fields['button_url'].initial = current_url
            
            # Parsear estilos actuales del botón
            current_style = self.instance.button_style or default_button_style
            self._parse_button_style(current_style)
    
    def _parse_button_style(self, style):
        """Parsea el estilo actual del botón para inicializar los campos"""
        for choice in BUTTON_BG_CHOICES:
            if choice[0] in style:
                self.fields['button_bg_color'].initial = choice[0]
                break
        else:
            self.fields['button_bg_color'].initial = 'bg-zicada-accent'
        
        for choice in BUTTON_HOVER_CHOICES:
            if choice[0] in style:
                self.fields['button_hover_color'].initial = choice[0]
                break
        else:
            self.fields['button_hover_color'].initial = 'hover:bg-red-700'
        
        for choice in BUTTON_TEXT_COLOR_CHOICES:
            if choice[0] in style:
                self.fields['button_text_color'].initial = choice[0]
                break
        else:
            self.fields['button_text_color'].initial = 'text-white'
        
        for choice in BUTTON_BORDER_CHOICES:
            if choice[0] in style:
                self.fields['button_border_radius'].initial = choice[0]
                break
        else:
            self.fields['button_border_radius'].initial = 'rounded-lg'
        
        for choice in BUTTON_SIZE_CHOICES:
            if choice[0] in style:
                self.fields['button_size'].initial = choice[0]
                break
        else:
            self.fields['button_size'].initial = 'px-8 py-3 text-lg'
        
        for choice in BUTTON_SHADOW_CHOICES:
            if choice[0] in style:
                self.fields['button_shadow'].initial = choice[0]
                break
        else:
            self.fields['button_shadow'].initial = 'shadow-lg'
        
        for choice in BUTTON_WIDTH_CHOICES:
            if choice[0] in style:
                self.fields['button_width'].initial = choice[0]
                break
        else:
            self.fields['button_width'].initial = 'inline-block'
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.section_height = self.cleaned_data['section_height']
        instance.title_font_size = self.cleaned_data['title_font_size']
        instance.title_line_height = self.cleaned_data['title_line_height']
        instance.title_margin_bottom = self.cleaned_data['title_margin_bottom']
        instance.subtitle_font_size = self.cleaned_data['subtitle_font_size']
        instance.subtitle_line_height = self.cleaned_data['subtitle_line_height']
        instance.subtitle_margin_bottom = self.cleaned_data['subtitle_margin_bottom']
        instance.button_url = self.cleaned_data['button_url']
        
        bg = self.cleaned_data['button_bg_color']
        hover = self.cleaned_data['button_hover_color']
        text = self.cleaned_data['button_text_color']
        rounded = self.cleaned_data['button_border_radius']
        size = self.cleaned_data['button_size']
        shadow = self.cleaned_data['button_shadow']
        width = self.cleaned_data['button_width']
        
        instance.button_style = f'{bg} {hover} {text} {rounded} {size} {shadow} {width} font-semibold transition-all duration-300 transform hover:scale-105 inline-block text-center'
        
        if commit:
            instance.save()
        return instance

class HeroConfigDeleteForm(FormStyleMixin, forms.Form):
    confirm = forms.CharField(
        required=True,
        label='Escribe el nombre del slide para confirmar',
        widget=forms.TextInput(attrs={'placeholder': 'Escribe el título del slide'})
    )
    
    def __init__(self, *args, **kwargs):
        self.slide = kwargs.pop('slide', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        value = self.cleaned_data.get('confirm', '').strip().lower()
        if not self.slide:
            raise ValidationError('Slide no especificado.')
        if self.slide.title_text.lower() != value:
            raise ValidationError('El nombre del slide no coincide.')
        return value


class HeroConfigRestoreForm(FormStyleMixin, forms.Form):
    confirm = forms.BooleanField(required=True, label='Confirmo que deseo restaurar este slide')
    
    def __init__(self, *args, **kwargs):
        self.slide = kwargs.pop('slide', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        if not self.slide:
            raise ValidationError('Slide no especificado.')
        if HeroConfig.objects.filter(sort_order=self.slide.sort_order, is_active=True).exists():
            raise ValidationError(f'Ya existe un slide activo con el orden {self.slide.sort_order}. Cambia el orden antes de restaurar.')
        if not cleaned_data.get('confirm'):
            raise ValidationError('Debes confirmar la restauración.')
        return cleaned_data