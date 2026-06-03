from django import forms
from django.contrib.auth.forms import AuthenticationForm
from apps.core.crud.mixins import FormStyleMixin
from django.core.exceptions import ValidationError
from .models import HeroConfig


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

# Opciones de fuentes predefinidas (basadas en Tailwind + opciones comunes)
FONT_FAMILY_CHOICES = [
    ("'Inter', sans-serif", "Inter (sans-serif)"),
    ("'Roboto', sans-serif", "Roboto (sans-serif)"),
    ("'Poppins', sans-serif", "Poppins (sans-serif)"),
    ("'Montserrat', sans-serif", "Montserrat (sans-serif)"),
    ("'Open Sans', sans-serif", "Open Sans (sans-serif)"),
    ("'Lato', sans-serif", "Lato (sans-serif)"),
    ("'Playfair Display', serif", "Playfair Display (serif)"),
    ("'Merriweather', serif", "Merriweather (serif)"),
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


class HeroConfigCreateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para crear slides del hero (carrusel)"""
    
    class Meta:
        model = HeroConfig
        fields = '__all__'
        widgets = {
            'background_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'overlay_opacity': forms.NumberInput(attrs={'min': 0, 'max': 1, 'step': 0.1}),
            'title_text': forms.TextInput(attrs={'placeholder': 'Ej: ZICADA'}),
            'title_font_family': forms.Select(choices=FONT_FAMILY_CHOICES),
            'title_font_size': forms.TextInput(attrs={'placeholder': '4rem', 'help_text': 'Ej: 4rem, 64px, 3vw'}),
            'title_font_weight': forms.Select(choices=FONT_WEIGHT_CHOICES),
            'title_line_height': forms.TextInput(attrs={'placeholder': '1.2'}),
            'title_color': forms.TextInput(attrs={'type': 'color'}),
            'title_margin_bottom': forms.TextInput(attrs={'placeholder': '1rem'}),
            'subtitle_text': forms.Textarea(attrs={'rows': 2, 'placeholder': 'LA MODA SE VA, TU ESTILO PERMANECE'}),
            'subtitle_font_family': forms.Select(choices=FONT_FAMILY_CHOICES),
            'subtitle_font_size': forms.TextInput(attrs={'placeholder': '1.25rem'}),
            'subtitle_font_weight': forms.Select(choices=FONT_WEIGHT_CHOICES),
            'subtitle_line_height': forms.TextInput(attrs={'placeholder': '1.5'}),
            'subtitle_color': forms.TextInput(attrs={'type': 'color'}),
            'subtitle_margin_bottom': forms.TextInput(attrs={'placeholder': '2rem'}),
            'button_text': forms.TextInput(attrs={'placeholder': 'Explorar Catálogo'}),
            'button_url': forms.TextInput(attrs={'placeholder': '/catalogo/'}),
            'button_style': forms.TextInput(attrs={'placeholder': 'bg-zicada-accent hover:bg-opacity-90'}),
            'content_alignment': forms.RadioSelect(choices=ALIGNMENT_CHOICES),
            'section_height': forms.TextInput(attrs={'placeholder': '100vh'}),
            'order': forms.NumberInput(attrs={'min': 0}),
        }
    
    def clean_title_text(self):
        title = self.cleaned_data.get('title_text', '').strip()
        if not title:
            raise ValidationError('El título es obligatorio.')
        return title
    
    def clean_button_url(self):
        url = self.cleaned_data.get('button_url', '').strip()
        if not url:
            raise ValidationError('La URL del botón es obligatoria.')
        return url
    
    def clean_order(self):
        order = self.cleaned_data.get('order', 0)
        # Validar que el orden no esté duplicado
        if HeroConfig.objects.filter(order=order).exists():
            raise ValidationError(f'Ya existe un slide con el orden {order}. Usa otro valor.')
        return order


class HeroConfigUpdateForm(FormStyleMixin, forms.ModelForm):
    """Formulario para actualizar slides del hero"""
    
    class Meta:
        model = HeroConfig
        fields = '__all__'
        widgets = {
            'background_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'overlay_opacity': forms.NumberInput(attrs={'min': 0, 'max': 1, 'step': 0.1}),
            'title_text': forms.TextInput(),
            'title_font_family': forms.Select(choices=FONT_FAMILY_CHOICES),
            'title_font_size': forms.TextInput(),
            'title_font_weight': forms.Select(choices=FONT_WEIGHT_CHOICES),
            'title_line_height': forms.TextInput(),
            'title_color': forms.TextInput(attrs={'type': 'color'}),
            'title_margin_bottom': forms.TextInput(),
            'subtitle_text': forms.Textarea(attrs={'rows': 2}),
            'subtitle_font_family': forms.Select(choices=FONT_FAMILY_CHOICES),
            'subtitle_font_size': forms.TextInput(),
            'subtitle_font_weight': forms.Select(choices=FONT_WEIGHT_CHOICES),
            'subtitle_line_height': forms.TextInput(),
            'subtitle_color': forms.TextInput(attrs={'type': 'color'}),
            'subtitle_margin_bottom': forms.TextInput(),
            'button_text': forms.TextInput(),
            'button_url': forms.TextInput(),
            'button_style': forms.TextInput(),
            'content_alignment': forms.RadioSelect(choices=ALIGNMENT_CHOICES),
            'section_height': forms.TextInput(),
            'order': forms.NumberInput(attrs={'min': 0}),
            'is_active': forms.CheckboxInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clases CSS para estilos
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ not in ['CheckboxInput', 'RadioSelect']:
                field.widget.attrs.setdefault('class', 'form-control w-full')
    
    def clean_order(self):
        order = self.cleaned_data.get('order', 0)
        qs = HeroConfig.objects.filter(order=order)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f'Ya existe otro slide con el orden {order}. Usa otro valor.')
        return order


class HeroConfigDeleteForm(FormStyleMixin, forms.Form):
    """Formulario para eliminar slide del hero"""
    
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
    """Formulario para restaurar slide eliminado (soft-delete)"""
    
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que deseo restaurar este slide'
    )
    
    def __init__(self, *args, **kwargs):
        self.slide = kwargs.pop('slide', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.slide:
            raise ValidationError('Slide no especificado.')
        
        # Verificar si ya existe un slide activo con el mismo orden
        if HeroConfig.objects.filter(order=self.slide.order).exists():
            raise ValidationError(f'Ya existe un slide activo con el orden {self.slide.order}. Cambia el orden antes de restaurar.')
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError('Debes confirmar la restauración.')
        
        return cleaned_data