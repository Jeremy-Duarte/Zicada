import pandas as pd
from typing import List, Dict, Any
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.crud.importers.base import BaseImporter
from apps.products.forms import CategoryCreateForm
from apps.products.models import Category


class CategoryImporter(BaseImporter):
    """Importador para el modelo Category."""
    
    model = Category
    form_class = CategoryCreateForm
    required_columns = ['name']
    optional_columns = []
    
    field_mapping = {
        'name': 'name',
    }
    
    unique_field = 'name'
    
    def validate_field(self, field_name: str, value: Any, row: pd.Series) -> Any:
        if field_name == 'name' and value:
            value = str(value).strip()
        return value
    
    def set_audit_fields(self, obj, is_new: bool):
        """Asigna el slug y sort_order automáticamente."""
        super().set_audit_fields(obj, is_new)
        
        if is_new:
            # Generar slug a partir del nombre
            obj.slug = slugify(obj.name)
            
            # Asignar sort_order al final
            max_order = Category.objects.aggregate(max_order=models.Max('sort_order'))['max_order']
            obj.sort_order = (max_order or -1) + 1
    
    def get_template_headers(self) -> List[str]:
        return ['name']
    
    def get_example_data(self) -> List[Dict]:
        return [
            {'name': 'Camisetas'},
            {'name': 'Hoodies'},
            {'name': 'Pantalones'},
            {'name': 'Accesorios'},
            {'name': 'Chaquetas'},
        ]
