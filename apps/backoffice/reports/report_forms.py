from django import forms
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from apps.core.crud.mixins import FormStyleMixin
from apps.orders.models import Order
from apps.products.models import Product
from apps.users.models import User


class ReportForm(FormStyleMixin, forms.Form):
    """Formulario para generar reportes financieros."""
    
    REPORT_TYPES = [
        ('financial', 'Financiero'),
        ('products', 'Productos'),
        ('delivery', 'Entregadores'),
        ('orders', 'Pedidos'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        label='Tipo de reporte',
        initial='financial',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        label='Fecha desde',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    date_to = forms.DateField(
        label='Fecha hasta',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    include_charts = forms.BooleanField(
        label='Incluir gráficos',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_tables = forms.BooleanField(
        label='Incluir tablas detalladas',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean_date_from(self):
        """Validar que la fecha desde no sea futura."""
        date_from = self.cleaned_data.get('date_from')
        today = datetime.now().date()
        
        if date_from and date_from > today:
            raise ValidationError('La fecha "desde" no puede ser futura.')
        
        return date_from
    
    def clean_date_to(self):
        """Validar que la fecha hasta no sea futura."""
        date_to = self.cleaned_data.get('date_to')
        today = datetime.now().date()
        
        if date_to and date_to > today:
            raise ValidationError('La fecha "hasta" no puede ser futura.')
        
        return date_to
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        today = datetime.now().date()
        
        # Si no hay fechas, usar últimos 30 días
        if not date_from and not date_to:
            cleaned_data['date_from'] = today - timedelta(days=30)
            cleaned_data['date_to'] = today
            return cleaned_data
        
        # Validar que ambas fechas existen
        if not date_from:
            raise ValidationError('Debes seleccionar una fecha "desde".')
        
        if not date_to:
            raise ValidationError('Debes seleccionar una fecha "hasta".')
        
        # Validar que fecha_from <= fecha_to
        if date_from > date_to:
            raise ValidationError('La fecha "desde" no puede ser posterior a la fecha "hasta".')
        
        # Limitar rango máximo (no más de 365 días)
        days_diff = (date_to - date_from).days
        max_days = 365
        
        if days_diff > max_days:
            raise ValidationError(
                f'El rango de fechas no puede superar los {max_days} días. '
                f'Seleccionaste {days_diff} días.'
            )
        
        return cleaned_data