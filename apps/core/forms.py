from django import forms
from django.contrib.auth.forms import AuthenticationForm
from apps.core.crud.mixins import FormStyleMixin


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