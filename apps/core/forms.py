from django import forms
from django.contrib.auth.forms import AuthenticationForm

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        min_length=2,
        required=True,
        label='Nombre completo',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-zicada-accent focus:border-transparent transition',
            'placeholder': 'Tu nombre'
        }),
        error_messages={
            'required': 'Por favor ingresa tu nombre',
            'min_length': 'El nombre debe tener al menos 2 caracteres'
        }
    )
    
    email = forms.EmailField(
        required=True,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-zicada-accent focus:border-transparent transition',
            'placeholder': 'tu@email.com'
        }),
        error_messages={
            'required': 'Por favor ingresa tu correo electrónico',
            'invalid': 'Ingresa un correo electrónico válido'
        }
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-zicada-accent focus:border-transparent transition',
            'placeholder': 'Tu número de contacto'
        })
    )
    
    subject = forms.CharField(
        max_length=200,
        required=True,
        label='Asunto',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-zicada-accent focus:border-transparent transition',
            'placeholder': '¿Sobre qué nos quieres contactar?'
        }),
        error_messages={
            'required': 'Por favor ingresa un asunto'
        }
    )
    
    message = forms.CharField(
        required=True,
        label='Mensaje',
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-zicada-accent focus:border-transparent transition resize-none',
            'rows': 5,
            'placeholder': 'Cuéntanos en qué podemos ayudarte...'
        }),
        error_messages={
            'required': 'Por favor ingresa tu mensaje'
        }
    )
    
    def clean_phone(self):
        """Limpia y valida el teléfono"""
        phone = self.cleaned_data.get('phone', '')
        if phone:
            # Eliminar caracteres no numéricos
            digits = ''.join(c for c in phone if c.isdigit())
            if len(digits) < 7 and len(digits) > 0:
                raise forms.ValidationError('El número de teléfono debe tener al menos 7 dígitos')
            return digits
        return ''
    


class StaffLoginForm(AuthenticationForm):    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-zicada-accent focus:border-transparent transition',
            'placeholder': 'Ingresa tu usuario',
            'autofocus': True
        })
        self.fields['password'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-zicada-accent focus:border-transparent transition',
            'placeholder': 'Ingresa tu contraseña'
        })
    
    def confirm_login_allowed(self, user):
        if not (user.is_staff or getattr(user, 'is_delivery', False)):
            raise forms.ValidationError(
                'No tienes permisos para acceder a esta área.',
                code='no_permission',
            )
        super().confirm_login_allowed(user)