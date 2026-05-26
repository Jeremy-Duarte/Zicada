from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class BaseImportView(LoginRequiredMixin, TemplateView):
    """
    Vista base para importación de datos.
    Las subclases deben definir:
        - importer_class: Clase de importador
        - model_name: nombre del modelo (para templates)
        - success_url: URL a redirigir después de importar
    """
    
    importer_class = None
    model_name = None
    success_url = None
    template_name = 'backoffice/components/crud/import_form.html'
    
    def get_importer(self, file_obj=None, update_existing=False):
        """Retorna una instancia del importador."""
        return self.importer_class(self.request, file_obj, update_existing=update_existing)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        importer = self.get_importer()
        context.update({
            'model_name': self.model_name,
            'model_verbose': importer.model._meta.verbose_name_plural,
            'required_columns': importer.required_columns,
            'optional_columns': importer.optional_columns,
            'example_data': importer.get_example_data(),
            'template_headers': importer.get_template_headers(),
        })
        return context
    
    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        update_existing = request.POST.get('update_existing') == 'on'
        
        if not file_obj:
            messages.error(request, 'Por favor selecciona un archivo.')
            return redirect(request.path)
        
        importer = self.get_importer(file_obj, update_existing)
        results = importer.run()
        importer.add_messages()
        
        # Guardar resultados en sesión para detalle
        request.session['import_results'] = results
        
        return redirect(self.success_url or reverse('backoffice:import_dashboard'))