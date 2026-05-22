from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, FormView, DetailView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import models
from apps.core.crud.mixins import PaginationMixin, FilterMixin
from .forms import (
    UserCreateForm, UserUpdateForm, UserChangePasswordForm,
    UserDeleteForm, UserRestoreForm
)

User = get_user_model()


def users_list(request):
    pass #TODO

def user_detail(request):
    pass #TODO

class UserListView(PermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    model = User
    template_name = 'backoffice/users/user_list.html'
    context_object_name = 'users'
    permission_required = 'users.view_user'
    paginate_by = 20
    
    filters = [
        ('username', 'username', 'icontains'),
        ('first_name', 'first_name', 'icontains'),
        ('last_name', 'last_name', 'icontains'),
        ('email', 'email', 'icontains'),
        ('is_delivery', 'is_delivery', 'exact'),
        ('is_active', 'is_active', 'exact'),
    ]
    
    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(
                models.Q(username__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(phone__icontains=search)
            )
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        for user in context['users']:
            # Badge de estado
            if user.is_active:
                status_badge = '<span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-700">Activo</span>'
            else:
                status_badge = '<span class="px-2 py-1 text-xs rounded-full bg-red-100 text-red-700">Inactivo</span>'
            
            # Badge de tipo
            if user.is_superuser:
                type_badge = '<span class="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-700">Superadmin</span>'
            elif user.is_staff:
                type_badge = '<span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-700">Staff</span>'
            elif user.is_delivery:
                type_badge = '<span class="px-2 py-1 text-xs rounded-full bg-orange-100 text-orange-700">Entregador</span>'
            else:
                type_badge = '<span class="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-700">Cliente</span>'
            
            rows.append({
                'pk': user.pk,
                'values': [
                    user.username,
                    user.get_full_name(),
                    user.email or '—',
                    user.phone or '—',
                    type_badge,
                    status_badge,
                    user.date_joined.strftime('%d/%m/%Y'),
                ],
            })
        context['rows'] = rows
        context['headers'] = ['Usuario', 'Nombre', 'Email', 'Teléfono', 'Tipo', 'Estado', 'Registro']
        return context


class UserCreateView(PermissionRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = 'backoffice/users/user_form.html'
    permission_required = 'users.add_user'
    success_url = reverse_lazy('users:user_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = 'users:user_list'
        context['title'] = 'Crear usuario'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Usuario "{form.instance.username}" creado exitosamente.')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Error al crear el usuario. Corrige los errores.')
        return super().form_invalid(form)


class UserUpdateView(PermissionRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'backoffice/users/user_form.html'
    permission_required = 'users.change_user'
    success_url = reverse_lazy('users:user_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = 'users:user_list'
        context['title'] = f'Editar usuario: {self.object.username}'
        context['show_password_change'] = True
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Usuario "{form.instance.username}" actualizado exitosamente.')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Error al actualizar el usuario.')
        return super().form_invalid(form)


class UserDetailView(PermissionRequiredMixin, DetailView):
    model = User
    template_name = 'backoffice/users/user_detail.html'
    context_object_name = 'user_obj'
    permission_required = 'users.view_user'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = 'users:user_list'
        return context


class UserChangePasswordView(PermissionRequiredMixin, FormView):
    form_class = UserChangePasswordForm
    template_name = 'backoffice/users/user_change_password.html'
    permission_required = 'users.change_user'
    
    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_obj'] = self.user
        context['cancel_url'] = 'users:user_detail'
        context['cancel_args'] = [self.user.pk]
        return context
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, f'Contraseña de "{self.user.username}" actualizada exitosamente.')
        return redirect('users:user_detail', pk=self.user.pk)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Error al cambiar la contraseña.')
        return super().form_invalid(form)


class UserDeleteView(PermissionRequiredMixin, FormView):
    form_class = UserDeleteForm
    template_name = 'backoffice/users/user_confirm_delete.html'
    permission_required = 'users.delete_user'
    
    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, pk=kwargs['pk'])
        # No permitir desactivar el propio usuario
        if self.user.pk == request.user.pk:
            messages.error(request, 'No puedes desactivar tu propio usuario.')
            return redirect('users:user_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_obj'] = self.user
        context['cancel_url'] = 'users:user_list'
        return context
    
    def form_valid(self, form):
        # Soft delete equivalente: desactivar usuario
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        messages.success(self.request, f'Usuario "{self.user.username}" desactivado exitosamente.')
        return redirect('users:user_list')
    
    def form_invalid(self, form):
        messages.error(self.request, 'Error al desactivar el usuario.')
        return super().form_invalid(form)


class UserRestoreView(PermissionRequiredMixin, FormView):
    form_class = UserRestoreForm
    template_name = 'backoffice/users/user_restore.html'
    permission_required = 'users.change_user'
    
    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, pk=kwargs['pk'])
        if self.user.is_active:
            messages.warning(request, f'El usuario "{self.user.username}" ya está activo.')
            return redirect('users:user_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_obj'] = self.user
        context['cancel_url'] = 'users:user_trashcan'
        return context
    
    def form_valid(self, form):
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])
        messages.success(self.request, f'Usuario "{self.user.username}" reactivado exitosamente.')
        return redirect('users:user_list')
    
    def form_invalid(self, form):
        messages.error(self.request, 'Error al reactivar el usuario.')
        return super().form_invalid(form)


class UserTrashcanView(PermissionRequiredMixin, PaginationMixin, ListView):
    """Vista de papelera (usuarios desactivados)"""
    model = User
    template_name = 'backoffice/users/user_trashcan.html'
    context_object_name = 'users'
    permission_required = 'users.view_user'
    paginate_by = 20
    
    def get_queryset(self):
        return User.objects.filter(is_active=False).order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        for user in context['users']:
            rows.append({
                'pk': user.pk,
                'values': [
                    user.username,
                    user.get_full_name(),
                    user.email or '—',
                    user.phone or '—',
                    user.date_joined.strftime('%d/%m/%Y'),
                ],
            })
        context['rows'] = rows
        context['headers'] = ['Usuario', 'Nombre', 'Email', 'Teléfono', 'Registro']
        return context