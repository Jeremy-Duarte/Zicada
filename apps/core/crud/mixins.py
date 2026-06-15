from django import forms
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Max
from apps.core.crud.widgets import SortableOrderWidget
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin as BasePermissionRequiredMixin
from django.urls import reverse
from django.core.exceptions import ImproperlyConfigured

from apps.core.url_names import CORE_STAFF_LOGIN, PRODUCTS_CATALOG

import json

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

class SortableUpdateMixin:
    """
    Mixin para formularios de actualización que necesitan ordenamiento drag & drop.
    No afecta la creación.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_sortable_widget()

    def _setup_sortable_widget(self):
        """Configura el widget de orden solo para instancias existentes."""
        if not self.instance or not self.instance.pk:
            return

        qs = self.get_sortable_queryset()
        if not qs or not qs.exists():
            return

        field_name = getattr(self, 'sortable_widget_name', 'order_data')
        self.fields[field_name] = forms.CharField(
            required=False,
            widget=SortableOrderWidget(
                queryset=qs,
                item_label=self.get_sortable_label
            ),
            label=getattr(self, 'sortable_widget_label', 'Orden')
        )

    def get_sortable_queryset(self):
        """Retorna el queryset de elementos a ordenar."""
        if hasattr(self, 'sortable_queryset'):
            return self.sortable_queryset(self) if callable(self.sortable_queryset) else self.sortable_queryset

        model = self._meta.model
        qs = model.objects.all()
        if hasattr(model, 'is_active'):
            qs = qs.filter(is_active=True)
        return qs.order_by(self.get_sortable_order_field())

    def get_sortable_label(self, item):
        label_attr = getattr(self, 'sortable_label_attr', None)
        if label_attr:
            return label_attr(item) if callable(label_attr) else getattr(item, label_attr)
        return getattr(item, 'name', str(item))

    def get_sortable_order_field(self):
        return getattr(self, 'sortable_order_field', 'sort_order')

    def get_sortable_filter_kwargs(self):
        filter_field = getattr(self, 'sortable_filter_field', None)
        if filter_field and hasattr(self.instance, filter_field):
            return {filter_field: getattr(self.instance, filter_field)}
        return {}

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()

        field_name = getattr(self, 'sortable_widget_name', 'order_data')
        order_data = self.cleaned_data.get(field_name)
        if order_data:
            self._update_sort_order(order_data)

        return instance

    def _update_sort_order(self, order_data):
        try:
            ordered_ids = json.loads(order_data)
        except json.JSONDecodeError:
            return

        if not ordered_ids:
            return

        model = self._meta.model
        filter_kwargs = self.get_sortable_filter_kwargs()
        qs = model.objects.filter(**filter_kwargs)
        if hasattr(model, 'is_active'):
            qs = qs.filter(is_active=True)

        current_order = list(qs.values_list('pk', flat=True).order_by(self.get_sortable_order_field()))

        if ordered_ids != current_order:
            order_field = self.get_sortable_order_field()
            with transaction.atomic():
                for idx, obj_id in enumerate(ordered_ids):
                    model.objects.filter(pk=obj_id, **filter_kwargs).update(**{order_field:idx})

class SortableCreateMixin:
    """
    Mixin para formularios de creación que necesitan asignar orden automático.
    Coloca los nuevos elementos al final.
    """

    def get_next_order(self, filter_kwargs=None):
        """Obtiene el próximo número de orden disponible."""
        model = self._meta.model
        filter_kwargs = filter_kwargs or {}
        
        # Si hay un filtro contextual (ej. por producto)
        if hasattr(self, 'get_sortable_filter_kwargs'):
            filter_kwargs = self.get_sortable_filter_kwargs()
        
        max_order = model.objects.filter(**filter_kwargs).aggregate(
            max_order=Max('sort_order')
        )['max_order']
        return (max_order or -1) + 1

    def save(self, commit=True):
        """Asigna el orden antes de guardar."""
        if not self.instance.pk:  # Solo para nuevos objetos
            filter_kwargs = {}
            if hasattr(self, 'get_sortable_filter_kwargs'):
                filter_kwargs = self.get_sortable_filter_kwargs()
            self.instance.sort_order = self.get_next_order(filter_kwargs)
        
        return super().save(commit=commit)

class SortableDeleteMixin:
    """
    Mixin para vistas de eliminación que necesitan reordenar los elementos restantes.
    Asume que la vista tiene `model` o `queryset`.
    """

    def get_sortable_model(self):
        """Obtiene el modelo desde la vista."""
        if hasattr(self, 'model'):
            return self.model
        if hasattr(self, 'get_queryset'):
            return self.get_queryset().model
        raise AttributeError("SortableDeleteMixin requiere model o get_queryset en la vista")

    def get_sortable_order_field(self):
        """Nombre del campo de orden (por defecto 'sort_order')."""
        return getattr(self, 'sortable_order_field', 'sort_order')

    def get_sortable_filter_kwargs(self):
        """
        Retorna kwargs para filtrar los elementos a reordenar.
        Sobrescribe en la vista si es necesario (ej. {'product_id': self.object.product.pk}).
        """
        return getattr(self, 'sortable_filter_kwargs', {})

    def reorder_after_delete(self, deleted_order):
        """Reordena los elementos después de una eliminación."""
        model = self.get_sortable_model()
        order_field = self.get_sortable_order_field()
        filter_kwargs = self.get_sortable_filter_kwargs()

        model.objects.filter(
            **filter_kwargs,
            **{f'{order_field}__gt': deleted_order}
        ).update(**{order_field: F(order_field) - 1})

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        order_field = self.get_sortable_order_field()
        deleted_order = getattr(self.object, order_field, 0)

        response = super().delete(request, *args, **kwargs)

        self.reorder_after_delete(deleted_order)

        return response


class StaffPermissionRequiredMixin(BasePermissionRequiredMixin):
    """
    Mixin que verifica:
    1. Usuario autenticado
    2. Usuario tiene permisos requeridos
    3. Usuario tiene rol Administrador (is_staff o grupo Administrador)    
    """
    
    permission_denied_message = 'No tienes permisos para acceder a esta sección. Por favor, contacta al administrador.'
    authentication_required_message = 'Debes iniciar sesión para acceder a esta sección.'
    
    def has_permission(self):
        has_perm = super().has_permission()
        
        if has_perm:
            return True
        
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return True
        
        if user.is_authenticated and user.groups.filter(name='Administrador').exists():
            return True
        
        return False
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, self.authentication_required_message)
            return redirect(f'{reverse(CORE_STAFF_LOGIN)}?next={self.request.path}')
        
        messages.error(self.request, self.permission_denied_message)
        
        if self.request.user.groups.filter(name='Entregador').exists():
            return redirect(reverse(CORE_STAFF_LOGIN)) #TODO cambiar ruta a delivery dashboard cuando exista
        
        return redirect(reverse(PRODUCTS_CATALOG))
