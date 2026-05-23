from django import forms
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
    
class FormStyleMixin:
    """
    Aplica estilos consistentes a todos los campos del formulario.
    Soporta TextInput, EmailInput, PasswordInput, Textarea, Select, CheckboxInput, etc.
    """
    
    # Clases CSS por defecto
    default_input_class = 'w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-zicada-accent focus:outline-none transition'
    default_textarea_class = 'w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-zicada-accent focus:outline-none transition resize-none'
    default_select_class = 'w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-zicada-accent focus:outline-none transition appearance-none bg-white'
    default_checkbox_class = 'w-5 h-5 rounded border-gray-300 text-zicada-accent focus:ring-zicada-accent focus:ring-2'
    default_radio_class = 'w-5 h-5 border-gray-300 text-zicada-accent focus:ring-zicada-accent'
    
    # Clases para contenedor de checkbox/radio
    checkbox_wrapper_class = 'flex items-center gap-3'
    checkbox_label_class = 'text-gray-700 font-medium cursor-pointer'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_form_styles()
    
    def _apply_form_styles(self):
        """Aplica estilos a todos los campos del formulario"""
        for field_name, field in self.fields.items():
            self._apply_field_style(field)
    
    def _apply_field_style(self, field):
        """Aplica estilos específicos según el tipo de widget"""
        widget = field.widget
        
        # TextInput, EmailInput, NumberInput, PasswordInput, URLInput
        if isinstance(widget, (forms.TextInput, forms.EmailInput, forms.NumberInput, 
                               forms.PasswordInput, forms.URLInput)):
            widget.attrs['class'] = self.default_input_class
            if not widget.attrs.get('placeholder'):
                widget.attrs['placeholder'] = f'Ingresa {field.label.lower()}'
        
        # Textarea
        elif isinstance(widget, forms.Textarea):
            widget.attrs['class'] = self.default_textarea_class
            widget.attrs['rows'] = widget.attrs.get('rows', 4)
            if not widget.attrs.get('placeholder'):
                widget.attrs['placeholder'] = f'Escribe {field.label.lower()} aquí...'
        
        # Select (incluye SelectMultiple)
        elif isinstance(widget, forms.Select):
            widget.attrs['class'] = self.default_select_class
        
        # SelectMultiple
        elif isinstance(widget, forms.SelectMultiple):
            widget.attrs['class'] = f'{self.default_select_class} h-32'
        
        # CheckboxInput
        elif isinstance(widget, forms.CheckboxInput):
            widget.attrs['class'] = self.default_checkbox_class
            # El label se maneja en el template, no añadimos wrapper aquí
        
        # RadioSelect
        elif isinstance(widget, forms.RadioSelect):
            widget.attrs['class'] = self.default_radio_class
    
    def get_field_html(self, field_name):
        """
        Helper para obtener HTML de un campo con su label y errores.
        Útil para templates personalizados.
        """
        field = self[field_name]
        return {
            'label': field.label,
            'field': field,
            'errors': field.errors,
            'help_text': field.help_text,
            'is_checkbox': isinstance(field.field.widget, forms.CheckboxInput),
            'is_radio': isinstance(field.field.widget, forms.RadioSelect),
        }


class FormSetStyleMixin:
    """Aplica estilos a todos los formularios en un FormSet"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            if hasattr(form, '_apply_form_styles'):
                form._apply_form_styles()