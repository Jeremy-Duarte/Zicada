from django import forms
from django.contrib.auth.forms import AuthenticationForm
from apps.core.crud.mixins import FormStyleMixin, SortableUpdateMixin
from django.core.exceptions import ValidationError
from .models import HeroConfig
from apps.products.models import Collection, Product
from apps.core.crud.widgets import CloudinarySingleImageWidget, SortableOrderWidget
from apps.core.utils import safe_reverse

# =============================================================================
# CONSTANTS
# =============================================================================

# Valores por defecto para botón
DEFAULT_BUTTON_BG = 'bg-zicada-accent'
DEFAULT_BUTTON_HOVER = 'hover:bg-red-700'
DEFAULT_BUTTON_TEXT_COLOR = 'text-white'
DEFAULT_BUTTON_BORDER_RADIUS = 'rounded-lg'
DEFAULT_BUTTON_SIZE = 'px-8 py-3 text-lg'
DEFAULT_BUTTON_SHADOW = 'shadow-lg'
DEFAULT_BUTTON_WIDTH = 'inline-block'

# Textos de opciones duplicados
LABEL_WHITE = '⚪ Blanco'
LABEL_RED_DARKER = '🔴 Rojo más oscuro'
LABEL_LARGE_RECOMMENDED = 'Grande (recomendado)'

# Valores para parseo de estilos
FALLBACK_BUTTON_BG = 'bg-zicada-accent'
FALLBACK_BUTTON_HOVER = 'hover:bg-red-700'
FALLBACK_BUTTON_TEXT_COLOR = 'text-white'
FALLBACK_BUTTON_BORDER_RADIUS = 'rounded-lg'
FALLBACK_BUTTON_SIZE = 'px-8 py-3 text-lg'
FALLBACK_BUTTON_SHADOW = 'shadow-lg'
FALLBACK_BUTTON_WIDTH = 'inline-block'


# =============================================================================
# HELPERS
# =============================================================================

def build_button_style(cleaned_data):
    # HU-053 | ESCENARIO 1 | H | Construye clases CSS del botón a partir de campos individuales
    bg = cleaned_data['button_bg_color']
    hover = cleaned_data['button_hover_color']
    text = cleaned_data['button_text_color']
    rounded = cleaned_data['button_border_radius']
    size = cleaned_data['button_size']
    shadow = cleaned_data['button_shadow']
    width = cleaned_data['button_width']
    
    return f'{bg} {hover} {text} {rounded} {size} {shadow} {width} font-semibold transition-all duration-300 transform hover:scale-105 inline-block text-center'


# =============================================================================
# HU-051: CONTACT FORM
# =============================================================================

class ContactForm(FormStyleMixin, forms.Form):
    """
    HU-051: Enviar mensaje de contacto
    Escenarios: H (formulario válido), A (campos inválidos), E (teléfono inválido)
    """
    
    # HU-051 | ESCENARIO 2 | H | Nombre válido (min 2, max 200 caracteres)
    # HU-051 | ESCENARIO 4A | A | Nombre vacío → error 'required'
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
    
    # HU-051 | ESCENARIO 2 | H | Email válido
    # HU-051 | ESCENARIO 4C | A | Email inválido (falta @, dominio inválido) → error 'invalid'
    email = forms.EmailField(
        required=True,
        label='Correo electrónico',
        error_messages={
            'required': 'Por favor ingresa tu correo electrónico',
            'invalid': 'Ingresa un correo electrónico válido'
        }
    )
    
    # HU-051 | ESCENARIO 4B | A | Teléfono con menos de 7 dígitos → error en clean_phone
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='Teléfono',
    )
    
    # HU-051 | ESCENARIO 2 | H | Asunto válido
    # HU-051 | ESCENARIO 4A | A | Asunto vacío → error 'required'
    subject = forms.CharField(
        max_length=200,
        required=True,
        label='Asunto',
        error_messages={
            'required': 'Por favor ingresa un asunto'
        }
    )
    
    # HU-051 | ESCENARIO 2 | H | Mensaje válido
    # HU-051 | ESCENARIO 4A | A | Mensaje vacío → error 'required'
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
        """
        HU-051 | ESCENARIO 4B | A | Teléfono inválido (menos de 7 dígitos)
        HU-051 | ESCENARIO 2 | H | Teléfono opcional válido (vacío o 7-15 dígitos)
        """
        phone = self.cleaned_data.get('phone', '')
        if phone:
            digits = ''.join(c for c in phone if c.isdigit())
            if len(digits) < 7 and len(digits) > 0:
                raise forms.ValidationError('El número de teléfono debe tener al menos 7 dígitos')
            return digits
        return ''


# =============================================================================
# HU-001 & HU-003: STAFF LOGIN FORM
# =============================================================================

class StaffLoginForm(FormStyleMixin, AuthenticationForm):
    """
    HU-001: Inicio de sesión
    HU-003: Control de acceso por permisos
    Escenarios: H (credenciales correctas + permisos), E (credenciales incorrectas, usuario inactivo, sin permisos)
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Usuario'
        self.fields['password'].widget.attrs['placeholder'] = 'Contraseña'
    
    def confirm_login_allowed(self, user):
        """
        HU-001 | ESCENARIO 3 | E | Credenciales incorrectas (validado en AuthenticationForm)
        HU-001 | ESCENARIO 4 | E | Usuario inactivo (validado en AuthenticationForm)
        HU-003 | ESCENARIO 3 | E | Usuario sin permisos (ni staff ni delivery)
        HU-003 | ESCENARIO 1 y 2 | H | Usuario con permisos (staff o delivery)
        """
        if not (user.is_staff or getattr(user, 'is_delivery', False)):
            raise forms.ValidationError(
                'No tienes permisos para acceder a esta área.',
                code='no_permission',
            )
        super().confirm_login_allowed(user)


# =============================================================================
# OPCIONES DE ESTILOS (sin HU específica, soporte para HU-053 a HU-056)
# =============================================================================

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

# Opciones para botones (HU-053, HU-054)
BUTTON_BG_CHOICES = [
    (DEFAULT_BUTTON_BG, '🔴 Rojo Zicada'),
    ('bg-black', '⚫ Negro'),
    ('bg-white', LABEL_WHITE),
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
    (DEFAULT_BUTTON_HOVER, LABEL_RED_DARKER),
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
    (DEFAULT_BUTTON_TEXT_COLOR, LABEL_WHITE),
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
    (DEFAULT_BUTTON_SIZE, LABEL_LARGE_RECOMMENDED),
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
    """
    HU-053 | ESCENARIO 1 | H | Carga dinámica de opciones de URL para el botón
    """
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


# =============================================================================
# HU-053: HERO CONFIG CREATE FORM
# =============================================================================

class HeroConfigCreateForm(FormStyleMixin, forms.ModelForm):
    """
    HU-053: Crear slide del hero
    Escenarios: H (datos válidos), A (título vacío o sort_order duplicado), E (sin permisos)
    """
    
    # Campo para URL del botón (usando la misma función)
    # HU-053 | ESCENARIO 1 | H | URL válida seleccionada
    button_url = forms.ChoiceField(choices=[], required=True, label='Destino del botón', help_text='Selecciona a dónde irá el usuario')
    
    # Campos para construcción del botón
    # HU-053 | ESCENARIO 1 | H | Estilos de botón configurados
    button_bg_color = forms.ChoiceField(choices=BUTTON_BG_CHOICES, required=True, label='Color de fondo')
    button_hover_color = forms.ChoiceField(choices=BUTTON_HOVER_CHOICES, required=True, label='Color al pasar el mouse')
    button_text_color = forms.ChoiceField(choices=BUTTON_TEXT_COLOR_CHOICES, required=True, label='Color del texto')
    button_border_radius = forms.ChoiceField(choices=BUTTON_BORDER_CHOICES, required=True, label='Bordes')
    button_size = forms.ChoiceField(choices=BUTTON_SIZE_CHOICES, required=True, label='Tamaño')
    button_shadow = forms.ChoiceField(choices=BUTTON_SHADOW_CHOICES, required=True, label='Sombra')
    button_width = forms.ChoiceField(choices=BUTTON_WIDTH_CHOICES, required=True, label='Ancho del botón')
    
    class Meta:
        model = HeroConfig
        fields = [
            'background_image',
            'overlay_opacity',
            'title_text',
            'title_font_family',
            'title_font_size',
            'title_font_weight',
            'title_line_height',
            'title_color',
            'title_margin_bottom',
            'subtitle_text',
            'subtitle_font_family',
            'subtitle_font_size',
            'subtitle_font_weight',
            'subtitle_line_height',
            'subtitle_color',
            'subtitle_margin_bottom',
            'button_text',
            'button_url',
            'content_alignment',
            'section_height',
            'sort_order',
        ]
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
        self.fields['button_bg_color'].initial = DEFAULT_BUTTON_BG
        self.fields['button_hover_color'].initial = DEFAULT_BUTTON_HOVER
        self.fields['button_text_color'].initial = DEFAULT_BUTTON_TEXT_COLOR
        self.fields['button_border_radius'].initial = DEFAULT_BUTTON_BORDER_RADIUS
        self.fields['button_size'].initial = DEFAULT_BUTTON_SIZE
        self.fields['button_shadow'].initial = DEFAULT_BUTTON_SHADOW
        self.fields['button_width'].initial = DEFAULT_BUTTON_WIDTH
    
    def clean_title_text(self):
        """
        HU-053 | ESCENARIO 1 | H | Título no vacío
        HU-053 | ESCENARIO 2 | A | Título vacío → error
        """
        title = self.cleaned_data.get('title_text', '').strip()
        if not title:
            raise ValidationError('El título es obligatorio.')
        return title
    
    def clean_sort_order(self):
        """
        HU-053 | ESCENARIO 1 | H | sort_order único
        HU-053 | ESCENARIO 2 | A | sort_order duplicado → error
        """
        sort_order = self.cleaned_data.get('sort_order', 0)
        if HeroConfig.objects.filter(sort_order=sort_order).exists():
            raise ValidationError(f'Ya existe un slide con el orden {sort_order}. Usa otro valor.')
        return sort_order
    
    def save(self, commit=True):
        # HU-053 | ESCENARIO 1 | H | Guarda slide y construye button_style
        instance = super().save(commit=False)
        instance.button_style = build_button_style(self.cleaned_data)
        
        if commit:
            instance.save()
        return instance


# =============================================================================
# HU-054: HERO CONFIG UPDATE FORM
# =============================================================================

class HeroConfigUpdateForm(FormStyleMixin, SortableUpdateMixin, forms.ModelForm):
    """
    HU-054: Editar slide del hero
    Escenarios: H (datos válidos), A (datos inválidos), E (slide no existe)
    """
    
    # Definición de mapping para parseo de estilos
    BUTTON_STYLE_FIELDS = [
        ('button_bg_color', BUTTON_BG_CHOICES, FALLBACK_BUTTON_BG),
        ('button_hover_color', BUTTON_HOVER_CHOICES, FALLBACK_BUTTON_HOVER),
        ('button_text_color', BUTTON_TEXT_COLOR_CHOICES, FALLBACK_BUTTON_TEXT_COLOR),
        ('button_border_radius', BUTTON_BORDER_CHOICES, FALLBACK_BUTTON_BORDER_RADIUS),
        ('button_size', BUTTON_SIZE_CHOICES, FALLBACK_BUTTON_SIZE),
        ('button_shadow', BUTTON_SHADOW_CHOICES, FALLBACK_BUTTON_SHADOW),
        ('button_width', BUTTON_WIDTH_CHOICES, FALLBACK_BUTTON_WIDTH),
    ]
    
    class Meta:
        model = HeroConfig
        fields = [
            'background_image',
            'overlay_opacity',
            'title_text',
            'title_font_family',
            'title_font_size',
            'title_font_weight',
            'title_line_height',
            'title_color',
            'title_margin_bottom',
            'subtitle_text',
            'subtitle_font_family',
            'subtitle_font_size',
            'subtitle_font_weight',
            'subtitle_line_height',
            'subtitle_color',
            'subtitle_margin_bottom',
            'button_text',
            'button_url',
            'content_alignment',
            'section_height',
            'is_active',
        ]
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
        
        default_button_style = f'{DEFAULT_BUTTON_BG} {DEFAULT_BUTTON_HOVER} {DEFAULT_BUTTON_TEXT_COLOR} {DEFAULT_BUTTON_BORDER_RADIUS} {DEFAULT_BUTTON_SIZE} {DEFAULT_BUTTON_SHADOW} {DEFAULT_BUTTON_WIDTH} font-semibold transition-all duration-300 transform hover:scale-105 inline-block text-center'

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
            
            current_style = self.instance.button_style or default_button_style
            self._parse_button_style(current_style)
    
    def _parse_button_style(self, style):
        """
        HU-054 | ESCENARIO 1 | H | Parsea el estilo del botón e inicializa los campos correspondientes
        """
        for field_name, choices, fallback in self.BUTTON_STYLE_FIELDS:
            for choice_value, _ in choices:
                if choice_value in style:
                    self.fields[field_name].initial = choice_value
                    break
            else:
                self.fields[field_name].initial = fallback
        
    def save(self, commit=True):
        # HU-054 | ESCENARIO 1 | H | Guarda cambios del slide
        instance = super().save(commit=False)
        instance.section_height = self.cleaned_data['section_height']
        instance.title_font_size = self.cleaned_data['title_font_size']
        instance.title_line_height = self.cleaned_data['title_line_height']
        instance.title_margin_bottom = self.cleaned_data['title_margin_bottom']
        instance.subtitle_font_size = self.cleaned_data['subtitle_font_size']
        instance.subtitle_line_height = self.cleaned_data['subtitle_line_height']
        instance.subtitle_margin_bottom = self.cleaned_data['subtitle_margin_bottom']
        instance.button_url = self.cleaned_data['button_url']
        instance.button_style = build_button_style(self.cleaned_data)
        
        if commit:
            instance.save()
        return instance


# =============================================================================
# HU-055: HERO CONFIG DELETE FORM
# =============================================================================

class HeroConfigDeleteForm(FormStyleMixin, forms.Form):
    """
    HU-055: Archivar slide del hero (soft delete)
    Escenarios: H (confirmación correcta), A (cancelar), E (sin permisos)
    """
    confirm = forms.CharField(
        required=True,
        label='Escribe el nombre del slide para confirmar',
        widget=forms.TextInput(attrs={'placeholder': 'Escribe el título del slide'})
    )
    
    def __init__(self, *args, **kwargs):
        self.slide = kwargs.pop('slide', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        """
        HU-055 | ESCENARIO 1 | H | Confirmación correcta
        HU-055 | ESCENARIO 2 | A | Confirmación incorrecta (nombre no coincide)
        """
        value = self.cleaned_data.get('confirm', '').strip().lower()
        if not self.slide:
            raise ValidationError('Slide no especificado.')
        if self.slide.title_text.lower() != value:
            raise ValidationError('El nombre del slide no coincide.')
        return value


# =============================================================================
# HU-056: HERO CONFIG RESTORE FORM
# =============================================================================

class HeroConfigRestoreForm(FormStyleMixin, forms.Form):
    """
    HU-056: Restaurar slide archivado
    Escenarios: H (restauración válida), A (conflicto de orden o confirmación inválida), E (sin permisos)
    """
    confirm = forms.BooleanField(required=True, label='Confirmo que deseo restaurar este slide')
    
    def __init__(self, *args, **kwargs):
        self.slide = kwargs.pop('slide', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        """
        HU-056 | ESCENARIO 1 | H | Restauración válida
        HU-056 | ESCENARIO 3 | A | Confirmación inválida o conflicto de orden
        """
        cleaned_data = super().clean()
        if not self.slide:
            raise ValidationError('Slide no especificado.')
        # HU-056 | ESCENARIO 3 | A | Conflicto de orden
        if HeroConfig.objects.filter(sort_order=self.slide.sort_order, is_active=True).exists():
            raise ValidationError(f'Ya existe un slide activo con el orden {self.slide.sort_order}. Cambia el orden antes de restaurar.')
        # HU-056 | ESCENARIO 3 | A | Confirmación no marcada
        if not cleaned_data.get('confirm'):
            raise ValidationError('Debes confirmar la restauración.')
        return cleaned_data