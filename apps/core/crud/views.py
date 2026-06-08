from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from .mixins import AuditMixin, SoftDeleteMixin, FilterMixin, PaginationMixin


class BaseListView(PermissionRequiredMixin, FilterMixin, PaginationMixin, ListView):
    """Listado genérico con filtros y exportación"""
    template_name = 'backoffice/crud/list.html'
    context_object_name = 'items'
    exporter_class = None
    export_template = None
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
    def get(self, request, *args, **kwargs):
        # Manejar exportación
        if request.GET.get('export') and self.exporter_class:
            exporter = self.exporter_class()
            queryset = self.get_queryset()
            export_format = request.GET.get('export')
            
            if export_format == 'csv':
                return exporter.export_csv(queryset, request)
            elif export_format == 'excel':
                return exporter.export_excel(queryset, request)
            elif export_format == 'pdf' and self.export_template:
                return exporter.export_pdf(queryset, request, self.export_template)
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name_plural
        context['model_verbose'] = self.model._meta.verbose_name
        context['app_label'] = self.model._meta.app_label
        return context


class BaseCreateView(PermissionRequiredMixin, AuditMixin, CreateView):
    """Creación genérica"""
    template_name = 'backoffice/crud/form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Crear'
        context['model_name'] = self.model._meta.verbose_name
        return context


class BaseUpdateView(PermissionRequiredMixin, AuditMixin, UpdateView):
    """Edición genérica"""
    template_name = 'backoffice/crud/form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Editar'
        context['model_name'] = self.model._meta.verbose_name
        return context


class BaseDeleteView(PermissionRequiredMixin, DeleteView):
    """Eliminación (soft delete) genérica"""
    template_name = 'backoffice/crud/confirm_delete.html'
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete(user=request.user)
        return redirect(self.get_success_url())


class BaseImportView(PermissionRequiredMixin, TemplateView):
    """Importación genérica"""
    template_name = 'backoffice/crud/import.html'
    importer_class = None
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name_plural
        return context
    
    def post(self, request, *args, **kwargs):
        if not self.importer_class:
            messages.error(request, 'Importador no configurado')
            return redirect(request.path)
        
        file = request.FILES.get('file')
        update_existing = request.POST.get('update_existing') == 'on'
        
        importer = self.importer_class(request, update_existing=update_existing)
        importer.run(file)
        importer.add_messages()
        
        return redirect(self.get_success_url())