import pandas as pd
from typing import List, Dict, Any
from django.db import models

from apps.core.crud.importers.base import BaseImporter
from apps.products.forms import SizeCreateForm
from apps.products.models import Size


class SizeImporter(BaseImporter):
    """Importador para el modelo Size."""
    
    model = Size
    form_class = SizeCreateForm
    required_columns = ['name']
    optional_columns = []
    
    field_mapping = {
        'name': 'name',
    }
    
    unique_field = 'name'
    
    def validate_field(self, field_name: str, value: Any, row: pd.Series) -> Any:
        if field_name == 'name' and value:
            value = str(value).upper().strip()
        return value
    
    def set_audit_fields(self, obj, is_new: bool):
        """Asigna el sort_order automáticamente."""
        super().set_audit_fields(obj, is_new)
        
        if is_new:
            max_order = Size.objects.aggregate(max_order=models.Max('sort_order'))['max_order']
            obj.sort_order = (max_order or -1) + 1
    
    def get_template_headers(self) -> List[str]:
        return ['name']
    
    def get_example_data(self) -> List[Dict]:
        return [
            {'name': 'XS'},
            {'name': 'S'},
            {'name': 'M'},
            {'name': 'L'},
            {'name': 'XL'},
        ]