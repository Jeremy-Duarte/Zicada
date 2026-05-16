import pandas as pd
from django.core.exceptions import ValidationError
from django.contrib import messages


class CSVImporter:
    """
    Importador que usa ModelForm para validar cada fila.
    Configurar con modelo, form_class, field_mapping (csv_col -> form_field).
    """
    def __init__(self, request, model, form_class, field_mapping, unique_field=None, update_existing=False):
        self.request = request
        self.model = model
        self.form_class = form_class
        self.field_mapping = field_mapping  # {csv_col: form_field}
        self.unique_field = unique_field
        self.update_existing = update_existing
        self.results = {'created': 0, 'updated': 0, 'errors': []}

    def read_file(self, file_obj):
        ext = file_obj.name.split('.')[-1].lower()
        if ext == 'csv':
            return pd.read_csv(file_obj)
        else:
            return pd.read_excel(file_obj)

    def run(self, file_obj):
        if not file_obj:
            self.results['errors'].append("No se ha seleccionado ningún archivo.")
            return

        try:
            df = self.read_file(file_obj)
        except Exception as e:
            self.results['errors'].append(f"Error al leer archivo: {str(e)}")
            return

        df.columns = df.columns.str.strip()
        for idx, row in df.iterrows():
            data = {}
            for csv_col, form_field in self.field_mapping.items():
                val = row.get(csv_col)
                if pd.isna(val):
                    val = None
                data[form_field] = val

            # Buscar instancia existente si update_existing
            instance = None
            if self.update_existing and self.unique_field:
                unique_val = data.get(self.unique_field)
                if unique_val:
                    instance = self.model.objects.filter(**{self.unique_field: unique_val}).first()

            form = self.form_class(data, instance=instance)
            if form.is_valid():
                obj = form.save(commit=False)
                if hasattr(obj, 'created_by') and not instance:
                    obj.created_by = self.request.user
                if hasattr(obj, 'updated_by'):
                    obj.updated_by = self.request.user
                obj.save()
                if instance:
                    self.results['updated'] += 1
                else:
                    self.results['created'] += 1
            else:
                errors = "; ".join([f"{field}: {err}" for field, err in form.errors.items()])
                self.results['errors'].append(f"Fila {idx+2}: {errors}")

    def add_messages(self):
        if self.results['created']:
            messages.success(self.request, f"{self.results['created']} registros creados.")
        if self.results['updated']:
            messages.info(self.request, f"{self.results['updated']} registros actualizados.")
        if self.results['errors']:
            for err in self.results['errors'][:5]:
                messages.error(self.request, err)
            if len(self.results['errors']) > 5:
                messages.warning(self.request, f"Y {len(self.results['errors']) - 5} errores más.")