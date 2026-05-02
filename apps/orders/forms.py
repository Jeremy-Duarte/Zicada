from django import forms
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.exceptions import ValidationError


class CheckoutOrderForm(forms.Form):
    # Formulario para la creación de un pedido en el checkout.
    customer_name = forms.CharField(
        max_length=200,
        min_length=3,
        required=True,
        label='Nombre completo',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ej: María Gómez Rodríguez',
            'id': 'customer_name'
        }),
        error_messages={
            'required': 'Por favor ingresa tu nombre completo.',
            'min_length': 'El nombre debe tener al menos 3 caracteres.',
            'max_length': 'El nombre no puede exceder los 200 caracteres.'
        }
    )
    
    customer_phone = forms.CharField(
        max_length=20,
        required=True,
        label='Teléfono',
        validators=[
            RegexValidator(
                regex=r'^[\d\s\-\(\)\+]+$',
                message='Ingresa un número de teléfono válido.'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ej: 3001234567',
            'id': 'customer_phone'
        }),
        error_messages={
            'required': 'Por favor ingresa tu número de teléfono.'
        }
    )
    
    customer_email = forms.EmailField(
        required=False,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ej: maria@correo.com',
            'id': 'customer_email'
        }),
        error_messages={
            'invalid': 'Ingresa un correo electrónico válido.'
        }
    )
    
    shipping_address = forms.CharField(
        required=True,
        label='Dirección de envío',
        min_length=5,
        validators=[
            MinLengthValidator(5, 'La dirección debe tener al menos 5 caracteres.')
        ],
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 3,
            'placeholder': 'Calle, número, barrio, ciudad, referencia',
            'id': 'shipping_address'
        }),
        error_messages={
            'required': 'Por favor ingresa tu dirección de envío completa.'
        }
    )
    
    delivery_notes = forms.CharField(
        required=False,
        label='Notas adicionales',
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 2,
            'placeholder': 'Ej: Dejar con el portero, llamar antes de llegar...',
            'id': 'delivery_notes'
        })
    )
    
    def clean_customer_phone(self):
        # Limpia y normaliza el teléfono eliminando caracteres no numéricos.
        phone = self.cleaned_data.get('customer_phone', '')
        # Solo eliminar caracteres no numéricos para almacenar limpio
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) < 7 or len(digits) > 15:
            raise ValidationError('El número de teléfono debe tener entre 7 y 15 dígitos.')
        return digits
    
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data