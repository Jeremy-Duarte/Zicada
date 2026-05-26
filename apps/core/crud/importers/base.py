import pandas as pd
from abc import ABC, abstractmethod
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import transaction
from typing import Dict, List, Any, Optional, Tuple


class BaseImporter(ABC):
    """Importador base con funcionalidades comunes."""
    
    # Configuración básica
    model = None
    form_class = None
    required_columns = []
    optional_columns = []
    
    # Mapeo de columnas CSV -> campos del modelo
    field_mapping: Dict[str, str] = {}
    
    # Campo único para identificar registros (update)
    unique_field: Optional[str] = None
    
    # Columnas que deben ser únicas en el sistema
    unique_columns: List[str] = []
    
    def __init__(self, request, file_obj, update_existing=False, dry_run=False):
        self.request = request
        self.file_obj = file_obj
        self.update_existing = update_existing
        self.dry_run = dry_run  # Modo prueba, no guarda en BD
        self.results = {
            'created': 0,
            'updated': 0,
            'errors': [],
            'warnings': [],
            'rows_processed': 0,
        }
        self.df = None
    
    def validate_file(self) -> bool:
        """Valida que el archivo exista y tenga extensión válida."""
        if not self.file_obj:
            self.results['errors'].append('No se ha seleccionado ningún archivo.')
            return False
        
        ext = self.file_obj.name.split('.')[-1].lower()
        if ext not in ['csv', 'xlsx', 'xls']:
            self.results['errors'].append(f'Formato no soportado: {ext}. Use CSV o Excel.')
            return False
        
        return True
    
    def read_file(self) -> bool:
        """Lee el archivo y lo convierte en DataFrame."""
        try:
            ext = self.file_obj.name.split('.')[-1].lower()
            if ext == 'csv':
                self.df = pd.read_csv(self.file_obj, encoding='utf-8')
            else:
                self.df = pd.read_excel(self.file_obj)
            
            # Limpiar nombres de columnas
            self.df.columns = self.df.columns.str.strip().str.lower()
            return True
            
        except Exception as e:
            self.results['errors'].append(f'Error al leer archivo: {str(e)}')
            return False
    
    def validate_columns(self) -> bool:
        """Valida que las columnas requeridas estén presentes."""
        df_columns = set(self.df.columns)
        required = set(self.required_columns)
        missing = required - df_columns
        
        if missing:
            self.results['errors'].append(
                f'Columnas requeridas faltantes: {", ".join(missing)}. '
                f'Columnas encontradas: {", ".join(df_columns)}'
            )
            return False
        
        # Advertir sobre columnas extra
        extra = df_columns - required - set(self.optional_columns)
        if extra:
            self.results['warnings'].append(
                f'Columnas ignoradas: {", ".join(extra)}'
            )
        
        return True
    
    def clean_row(self, row: pd.Series, row_num: int) -> Tuple[Dict, List[str]]:
        """Limpia una fila y retorna datos + errores."""
        data = {}
        errors = []
        
        for csv_col, model_field in self.field_mapping.items():
            if csv_col not in row:
                continue
                
            value = row[csv_col]
            
            # Manejar valores nulos/NaN
            if pd.isna(value):
                value = None
            elif isinstance(value, str):
                value = value.strip()
            
            # Validaciones específicas por campo (sobrescribir en subclase)
            try:
                validated_value = self.validate_field(model_field, value, row)
                data[model_field] = validated_value
            except ValidationError as e:
                errors.append(f'{csv_col}: {"; ".join(e.messages)}')
        
        return data, errors
    
    def validate_field(self, field_name: str, value: Any, row: pd.Series) -> Any:
        """Valida un campo específico (sobrescribir en subclase)."""
        return value
    
    def get_existing_instance(self, data: Dict) -> Optional[Any]:
        """Busca una instancia existente para actualizar."""
        if not self.update_existing or not self.unique_field:
            return None
        
        unique_value = data.get(self.unique_field)
        if unique_value:
            try:
                return self.model.objects.get(**{self.unique_field: unique_value})
            except self.model.DoesNotExist:
                pass
        return None
    
    def process_row(self, row: pd.Series, row_num: int) -> bool:
        """Procesa una fila individual."""
        data, errors = self.clean_row(row, row_num)
        
        if errors:
            self.results['errors'].extend([f'Fila {row_num}: {err}' for err in errors])
            return False
        
        instance = self.get_existing_instance(data)
        
        # Crear formulario
        if instance:
            form = self.form_class(data, instance=instance)
        else:
            form = self.form_class(data)
        
        if not form.is_valid():
            for field, err_list in form.errors.items():
                self.results['errors'].append(f'Fila {row_num} - {field}: {"; ".join(err_list)}')
            return False
        
        # En modo dry-run, no guardar
        if self.dry_run:
            self.results['rows_processed'] += 1
            if instance:
                self.results['updated'] += 1
            else:
                self.results['created'] += 1
            return True
        
        # Guardar
        try:
            with transaction.atomic():
                obj = form.save(commit=False)
                self.set_audit_fields(obj, instance is None)
                obj.save()
                form.save_m2m()
                
                if instance:
                    self.results['updated'] += 1
                else:
                    self.results['created'] += 1
                    
        except Exception as e:
            self.results['errors'].append(f'Fila {row_num}: Error al guardar - {str(e)}')
            return False
        
        return True
    
    def set_audit_fields(self, obj, is_new: bool):
        """Establece campos de auditoría."""
        if hasattr(obj, 'created_by') and is_new:
            obj.created_by = self.request.user
        if hasattr(obj, 'updated_by'):
            obj.updated_by = self.request.user
    
    def run(self) -> Dict:
        """Ejecuta el proceso de importación."""
        if not self.validate_file():
            return self.results
        
        if not self.read_file():
            return self.results
        
        if not self.validate_columns():
            return self.results
        
        for idx, row in self.df.iterrows():
            self.process_row(row, idx + 2)  # +2 porque pandas es 0-index y fila1 es encabezado
        
        return self.results
    
    def add_messages(self):
        """Agrega mensajes a la request."""
        if self.results['created']:
            messages.success(self.request, f"✅ {self.results['created']} registros creados.")
        if self.results['updated']:
            messages.info(self.request, f"🔄 {self.results['updated']} registros actualizados.")
        if self.results['warnings']:
            for warn in self.results['warnings'][:3]:
                messages.warning(self.request, warn)
        if self.results['errors']:
            for err in self.results['errors'][:5]:
                messages.error(self.request, err)
            if len(self.results['errors']) > 5:
                messages.warning(self.request, f"⚠️ Y {len(self.results['errors']) - 5} errores más.")
    
    @abstractmethod
    def get_template_headers(self) -> List[str]:
        """Retorna los encabezados de la plantilla de ejemplo."""
        pass
    
    @abstractmethod
    def get_example_data(self) -> List[Dict]:
        """Retorna datos de ejemplo para la plantilla."""
        pass