from django.shortcuts import get_object_or_404, redirect

class AuditMixin:
    """Maneja campos de auditoría (created_by, updated_by)"""
    
    def form_valid(self, form):
        if not form.instance.pk:  # Creando
            form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class SoftDeleteMixin:
    """Maneja soft delete"""
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete(user=request.user)
        return redirect(self.get_success_url())


class RestoreMixin:
    """Restaura objetos eliminados suavemente"""
    
    def restore(self, request, pk):
        obj = get_object_or_404(self.model.all_objects, pk=pk, is_active=False)
        obj.restore(user=request.user)
        return redirect(self.get_success_url())


class PaginationMixin:
    """Paginación configurable"""
    paginate_by = 20
    paginate_orphans = 5


class FilterMixin:
    """Filtros dinámicos basados en GET params"""
    filters = []  # Lista de (param_name, field_name, lookup)
    
    def get_queryset(self):
        qs = super().get_queryset()
        for param, field, lookup in self.filters:
            value = self.request.GET.get(param)
            if value:
                qs = qs.filter(**{f'{field}__{lookup}': value})
        return qs