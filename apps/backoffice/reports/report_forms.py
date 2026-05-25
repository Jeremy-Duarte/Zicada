# apps/backoffice/report_forms.py
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
            'class': 'form-control',
            'max': datetime.now().strftime('%Y-%m-%d'),
            'min': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        })
    )
    
    date_to = forms.DateField(
        label='Fecha hasta',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'max': datetime.now().strftime('%Y-%m-%d')
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Actualizar dinámicamente los límites de fechas (por si cambia el día)
        today = datetime.now().date()
        one_year_ago = today - timedelta(days=365)
        
        self.fields['date_from'].widget.attrs.update({
            'max': today.strftime('%Y-%m-%d'),
            'min': one_year_ago.strftime('%Y-%m-%d')
        })
        self.fields['date_to'].widget.attrs.update({
            'max': today.strftime('%Y-%m-%d')
        })
    
    def clean_date_from(self):
        """Validar que la fecha desde no sea futura y no sea mayor a 1 año atrás."""
        date_from = self.cleaned_data.get('date_from')
        today = datetime.now().date()
        one_year_ago = today - timedelta(days=365)
        
        if date_from:
            if date_from > today:
                raise ValidationError(f'La fecha "desde" no puede ser futura. Máximo: {today.strftime("%d/%m/%Y")}')
            
            if date_from < one_year_ago:
                raise ValidationError(f'La fecha "desde" no puede ser anterior a {one_year_ago.strftime("%d/%m/%Y")} (máximo 1 año).')
        
        return date_from
    
    def clean_date_to(self):
        """Validar que la fecha hasta no sea futura."""
        date_to = self.cleaned_data.get('date_to')
        today = datetime.now().date()
        
        if date_to and date_to > today:
            raise ValidationError(f'La fecha "hasta" no puede ser futura. Máximo: {today.strftime("%d/%m/%Y")}')
        
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
        
        if date_from > date_to:
            raise ValidationError(
                f'La fecha "desde" ({date_from.strftime("%d/%m/%Y")}) no puede ser '
                f'posterior a la fecha "hasta" ({date_to.strftime("%d/%m/%Y")}).'
            )
        
        days_diff = (date_to - date_from).days
        max_days = 365
        
        if days_diff > max_days:
            raise ValidationError(
                f'El rango de fechas no puede superar los {max_days} días. '
                f'Seleccionaste {days_diff} días ({date_from.strftime("%d/%m/%Y")} - {date_to.strftime("%d/%m/%Y")}).'
            )
        
        return cleaned_data