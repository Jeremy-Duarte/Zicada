import pandas as pd
import re
from typing import List, Dict, Any
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.crud.importers.base import BaseImporter
from apps.products.forms import ColorCreateForm
from apps.products.models import Color


class ColorImporter(BaseImporter):
    """Importador para el modelo Color."""
    
    model = Color
    form_class = ColorCreateForm
    required_columns = ['name', 'code']
    optional_columns = []
    
    field_mapping = {
        'name': 'name',
        'code': 'code',
    }
    
    unique_field = 'name'
    
    def validate_field(self, field_name: str, value: Any, row: pd.Series) -> Any:
        if field_name == 'name' and value:
            value = str(value).capitalize().strip()
        elif field_name == 'code' and value:
            value = str(value).strip()
            # Asegurar que empiece con #
            if not value.startswith('#'):
                value = f'#{value}'
            # Validar formato hexadecimal
            if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', value):
                raise ValidationError(f'"{value}" no es un código hexadecimal válido. Use formato #RRGGBB')
        return value
    
    def set_audit_fields(self, obj, is_new: bool):
        super().set_audit_fields(obj, is_new)
        
        if is_new:
            max_order = Color.objects.aggregate(max_order=models.Max('sort_order'))['max_order']
            obj.sort_order = (max_order or -1) + 1
    
    def get_template_headers(self) -> List[str]:
        return ['name', 'code']
    
    def get_example_data(self) -> List[Dict]:
        return [
            {'name': 'Negro', 'code': '#000000'},
            {'name': 'Blanco', 'code': '#FFFFFF'},
            {'name': 'Rojo', 'code': '#FF0000'},
            {'name': 'Azul', 'code': '#0000FF'},
            {'name': 'Verde', 'code': '#00FF00'},
        ]