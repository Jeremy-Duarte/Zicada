import csv
from datetime import timezone
import pandas as pd
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from io import BytesIO


class BaseExporter:
    """Exportador base"""
    filename = 'export'
    fields = []  # Lista de (header, field_name)
    
    def get_queryset(self, queryset):
        return queryset
    
    def get_row_data(self, obj):
        return {field: getattr(obj, field, '') for _, field in self.fields}
    
    def export_csv(self, queryset, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{self.filename}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([header for header, _ in self.fields])
        
        for obj in self.get_queryset(queryset):
            row = [self.get_row_data(obj).get(field, '') for _, field in self.fields]
            writer.writerow(row)
        
        return response
    
    def export_excel(self, queryset, request):
        data = []
        for obj in self.get_queryset(queryset):
            data.append(self.get_row_data(obj))
        
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{self.filename}.xlsx"'
        
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Datos')
        
        return response
    
    def export_pdf(self, queryset, request, template_path):
        context = self.get_pdf_context(queryset, request)
        html_string = render_to_string(template_path, context)
        pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{self.filename}.pdf"'
        return response
    
    def get_pdf_context(self, queryset, request):
        return {
            'items': self.get_queryset(queryset),
            'total': self.get_queryset(queryset).count(),
            'usuario': request.user,
            'fecha_exportacion': timezone.now(),
        }


class ModelExporter(BaseExporter):
    """Exportador genérico para modelos"""
    
    def __init__(self, model, fields, filename=None):
        self.model = model
        self.fields = fields
        self.filename = filename or model._meta.model_name


class CSVImporter:
    """Importador simple usando pandas"""
    
    def __init__(self, model, field_mapping, unique_field=None, update_existing=False):
        self.model = model
        self.field_mapping = field_mapping  # {csv_column: model_field}
        self.unique_field = unique_field
        self.update_existing = update_existing
        self.results = {'created': 0, 'updated': 0, 'errors': []}
    
    def read_file(self, file_obj):
        ext = file_obj.name.split('.')[-1].lower()
        if ext == 'csv':
            return pd.read_csv(file_obj)
        return pd.read_excel(file_obj)
    
    def process_row(self, data):
        instance = None
        if self.unique_field and self.update_existing:
            unique_value = data.get(self.unique_field)
            if unique_value:
                instance = self.model.objects.filter(**{self.unique_field: unique_value}).first()
        
        if instance:
            for csv_col, model_field in self.field_mapping.items():
                if csv_col in data:
                    setattr(instance, model_field, data[csv_col])
            instance.save()
            self.results['updated'] += 1
        else:
            instance = self.model(**data)
            instance.save()
            self.results['created'] += 1
    
    def run(self, file_obj):
        df = self.read_file(file_obj)
        df.columns = df.columns.str.strip()
        
        for _, row in df.iterrows():
            try:
                data = {model_field: row[csv_col] for csv_col, model_field in self.field_mapping.items() if csv_col in row}
                self.process_row(data)
            except Exception as e:
                self.results['errors'].append(str(e))
        
        return self.results