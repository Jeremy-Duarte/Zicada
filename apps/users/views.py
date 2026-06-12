from django.urls import reverse_lazy
from apps.core.crud.mixins import StaffPermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, FormView, DetailView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.db import models
from django.utils.safestring import mark_safe

from apps.core.crud.mixins import PaginationMixin, FilterMixin
from .forms import (
    UserCreateForm, UserUpdateForm, UserChangePasswordForm,
    UserDeleteForm, UserRestoreForm, GroupCreateForm, GroupUpdateForm, GroupDeleteForm
)
from django.contrib.auth.models import Group
from apps.users.forms import UserProfileForm, UserProfilePasswordForm

User = get_user_model()

from apps.core.url_names import (
    USERS_LIST,
    USERS_TRASHCAN,
    USERS_GROUP_LIST,
    USERS_PROFILE,
)

from .constants import (
    # Template Paths
    TEMPLATE_USER_LIST,
    TEMPLATE_USER_FORM,
    TEMPLATE_USER_CHANGE_PASSWORD,
    TEMPLATE_USER_CONFIRM_DELETE,
    TEMPLATE_USER_RESTORE,
    TEMPLATE_USER_TRASHCAN,
    TEMPLATE_USER_PROFILE,
    TEMPLATE_USER_PROFILE_EDIT,
    TEMPLATE_USER_PROFILE_PASSWORD,
    TEMPLATE_GROUP_LIST,
    TEMPLATE_GROUP_FORM,
    TEMPLATE_GROUP_DETAIL,
    TEMPLATE_GROUP_CONFIRM_DELETE,
    # Context Keys
    CONTEXT_CANCEL_URL,
    CONTEXT_CANCEL_ARGS,
    CONTEXT_TITLE,
    CONTEXT_SHOW_PASSWORD_CHANGE,
    CONTEXT_USER_OBJ,
    CONTEXT_USERS,
    CONTEXT_GROUP,
    CONTEXT_GROUPS,
    CONTEXT_USER_COUNT,
    CONTEXT_ROWS,
    CONTEXT_HEADERS,
    # Table Headers
    HEADER_USERNAME,
    HEADER_FULL_NAME,
    HEADER_EMAIL,
    HEADER_PHONE,
    HEADER_USER_TYPE,
    HEADER_STATUS,
    HEADER_REGISTRATION,
    HEADER_GROUP_NAME,
    HEADER_ASSIGNED_USERS,
    # Table Header Lists
    HEADERS_USER_LIST,
    HEADERS_USER_TRASHCAN,
    HEADERS_GROUP_LIST,
    # Filter Names
    FILTER_USERNAME,
    FILTER_FIRST_NAME,
    FILTER_LAST_NAME,
    FILTER_EMAIL,
    FILTER_IS_DELIVERY,
    FILTER_IS_ACTIVE,
    FILTER_GROUP_NAME,
    # Order By
    ORDER_BY_USERNAME_DESC,
    # Query Parameters
    QUERY_PARAM_SEARCH,
    # User Types
    USER_TYPE_SUPERUSER,
    USER_TYPE_STAFF,
    USER_TYPE_DELIVERY,
    USER_TYPE_CUSTOMER,
    # User Type Badges
    USER_TYPE_BADGES,
    # Status Badges
    STATUS_ACTIVE_BADGE,
    STATUS_INACTIVE_BADGE,
    # Date Format
    DATE_FORMAT_DISPLAY,
    # Pagination
    PAGINATE_BY_DEFAULT,
    # Form Context Values
    CONTEXT_IS_CREATE,
    CONTEXT_IS_UPDATE,
    # Title Templates
    TITLE_USER_CREATE,
    TITLE_USER_UPDATE,
    TITLE_GROUP_CREATE,
    TITLE_GROUP_UPDATE,
    # Success Messages
    MSG_USER_CREATED,
    MSG_USER_UPDATED,
    MSG_USER_DELETED,
    MSG_USER_RESTORED,
    MSG_USER_ALREADY_ACTIVE,
    MSG_PASSWORD_CHANGED,
    MSG_GROUP_CREATED,
    MSG_GROUP_UPDATED,
    MSG_GROUP_DELETED,
    MSG_PROFILE_UPDATED,
    MSG_PASSWORD_UPDATED,
    # Error Messages
    ERROR_USER_CREATE,
    ERROR_USER_UPDATE,
    ERROR_USER_DELETE,
    ERROR_USER_RESTORE,
    ERROR_PASSWORD_CHANGE,
    ERROR_GROUP_DELETE,
    ERROR_SELF_DELETE,
    ERROR_PASSWORD_UPDATE,
    # HTML Templates
    STATUS_BADGE_TEMPLATE,
    # Default values
    DEFAULT_EMPTY_VALUE,
    # Perms
    PERM_USER_VIEW,
    PERM_USER_ADD,
    PERM_USER_CHANGE,
    PERM_USER_DELETE,
    PERM_GROUP_VIEW,
    PERM_GROUP_ADD,
    PERM_GROUP_CHANGE,
    PERM_GROUP_DELETE,    
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_user_type_badge(user) -> str:
    """Get HTML badge for user type."""
    if user.is_superuser:
        user_type = USER_TYPE_SUPERUSER
    elif user.is_staff:
        user_type = USER_TYPE_STAFF
    elif user.is_delivery:
        user_type = USER_TYPE_DELIVERY
    else:
        user_type = USER_TYPE_CUSTOMER
    
    label, badge_class = USER_TYPE_BADGES[user_type]
    return mark_safe(STATUS_BADGE_TEMPLATE.format(badge_class=badge_class, badge_text=label))


def get_status_badge(is_active: bool) -> str:
    """Get HTML badge for user status."""
    label, badge_class = STATUS_ACTIVE_BADGE if is_active else STATUS_INACTIVE_BADGE
    return mark_safe(STATUS_BADGE_TEMPLATE.format(badge_class=badge_class, badge_text=label))


# =============================================================================
# USER CRUD VIEWS (HU-038, HU-039, HU-040, HU-041, HU-042)
# =============================================================================

class UserListView(StaffPermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    """
    HU-038: Listar usuarios (admin)
    """
    model = User
    template_name = TEMPLATE_USER_LIST
    context_object_name = CONTEXT_USERS
    permission_required = PERM_USER_VIEW  # HU-038 | ESCENARIO 6 | E | Sin permisos
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        (FILTER_USERNAME, FILTER_USERNAME, 'icontains'),
        (FILTER_FIRST_NAME, FILTER_FIRST_NAME, 'icontains'),
        (FILTER_LAST_NAME, FILTER_LAST_NAME, 'icontains'),
        (FILTER_EMAIL, FILTER_EMAIL, 'icontains'),
        (FILTER_IS_DELIVERY, FILTER_IS_DELIVERY, 'exact'),
        (FILTER_IS_ACTIVE, FILTER_IS_ACTIVE, 'exact'),
    ]
    
    def get_queryset(self):
        # HU-038 | ESCENARIO 2 | H | Búsqueda por nombre o correo
        # HU-038 | ESCENARIO 3 | H | Filtro por rol (is_delivery, is_staff, is_superuser)
        # HU-038 | ESCENARIO 4 | H | Filtro por estado (is_active)
        qs = super().get_queryset()
        # Excluir al propio usuario logueado de la lista
        qs = qs.exclude(pk=self.request.user.pk)
        search = self.request.GET.get(QUERY_PARAM_SEARCH, '')
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
        # HU-038 | ESCENARIO 1 | H | Lista de usuarios cargada exitosamente
        # HU-038 | ESCENARIO 5 | A | Sin usuarios (excluyendo el actual) → template muestra mensaje
        context = super().get_context_data(**kwargs)
        rows = []
        
        for user in context[CONTEXT_USERS]:
            rows.append({
                'pk': user.pk,
                'values': [
                    user.username,
                    user.get_full_name(),
                    user.email or DEFAULT_EMPTY_VALUE,
                    user.phone or DEFAULT_EMPTY_VALUE,
                    get_user_type_badge(user),
                    get_status_badge(user.is_active),
                    user.date_joined.strftime(DATE_FORMAT_DISPLAY),
                ],
            })
        
        context[CONTEXT_ROWS] = rows
        context[CONTEXT_HEADERS] = HEADERS_USER_LIST
        return context


class UserCreateView(StaffPermissionRequiredMixin, CreateView):
    """
    HU-039: Crear usuario (admin)
    """
    model = User
    form_class = UserCreateForm
    template_name = TEMPLATE_USER_FORM
    permission_required = PERM_USER_ADD  # HU-039 | ESCENARIO 4 | E | Sin permisos
    success_url = reverse_lazy(USERS_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = USERS_LIST
        context[CONTEXT_TITLE] = TITLE_USER_CREATE
        return context
    
    def form_valid(self, form):
        # HU-039 | ESCENARIO 1 | H | Usuario creado exitosamente
        response = super().form_valid(form)
        messages.success(self.request, MSG_USER_CREATED.format(username=form.instance.username))
        return response
    
    def form_invalid(self, form):
        # HU-039 | ESCENARIO 2 | A | Errores en el formulario
        messages.error(self.request, ERROR_USER_CREATE)
        return super().form_invalid(form)
    # HU-039 | ESCENARIO 3 | E | Correo duplicado (validación en UserCreateForm.clean_email)


class UserUpdateView(StaffPermissionRequiredMixin, UpdateView):
    """
    HU-040: Editar usuario (admin)
    """
    model = User
    form_class = UserUpdateForm
    template_name = TEMPLATE_USER_FORM
    permission_required = PERM_USER_CHANGE  # HU-040 | ESCENARIO 5 | E | Sin permisos
    success_url = reverse_lazy(USERS_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = USERS_LIST
        context[CONTEXT_TITLE] = TITLE_USER_UPDATE.format(username=self.object.username)
        context[CONTEXT_SHOW_PASSWORD_CHANGE] = True  # HU-040 | ESCENARIO 2 | H | Cambiar contraseña
        return context
    
    def form_valid(self, form):
        # HU-040 | ESCENARIO 1 | H | Usuario actualizado exitosamente
        response = super().form_valid(form)
        messages.success(self.request, MSG_USER_UPDATED.format(username=form.instance.username))
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, ERROR_USER_UPDATE)
        return super().form_invalid(form)
    # HU-040 | ESCENARIO 3 | E | Correo duplicado al editar (validación en UserUpdateForm)
    # HU-040 | ESCENARIO 4 | E | Usuario no existe → 404


class UserChangePasswordView(StaffPermissionRequiredMixin, FormView):
    """
    HU-040 | ESCENARIO 2 | H | Cambiar contraseña (admin)
    """
    form_class = UserChangePasswordForm
    template_name = TEMPLATE_USER_CHANGE_PASSWORD
    permission_required = PERM_USER_CHANGE
    
    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_USER_OBJ] = self.user
        context[CONTEXT_CANCEL_URL] = USERS_LIST
        context[CONTEXT_CANCEL_ARGS] = []
        return context
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, MSG_PASSWORD_CHANGED.format(username=self.user.username))
        return redirect(USERS_LIST)
    
    def form_invalid(self, form):
        messages.error(self.request, ERROR_PASSWORD_CHANGE)
        return super().form_invalid(form)


class UserDeleteView(StaffPermissionRequiredMixin, FormView):
    """
    HU-041: Archivar usuario (soft delete)
    """
    form_class = UserDeleteForm
    template_name = TEMPLATE_USER_CONFIRM_DELETE
    permission_required = PERM_USER_DELETE  # HU-041 | ESCENARIO 5 | E | Sin permisos
    
    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, pk=kwargs['pk'])
        
        # HU-041 | ESCENARIO 2 | E | Archivar al propio usuario
        if self.user.pk == request.user.pk:
            messages.error(request, ERROR_SELF_DELETE)
            return redirect(USERS_LIST)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_USER_OBJ] = self.user
        context[CONTEXT_CANCEL_URL] = USERS_LIST
        return context
    
    def form_valid(self, form):
        # HU-041 | ESCENARIO 1 | H | Usuario archivado exitosamente
        self.user.is_active = False
        self.user.save(update_fields=[FILTER_IS_ACTIVE])
        messages.success(self.request, MSG_USER_DELETED.format(username=self.user.username))
        return redirect(USERS_LIST)
        # HU-041 | ESCENARIO 3 | E | Archivar al último Administrador (validación en UserDeleteForm)
    
    def form_invalid(self, form):
        # HU-041 | ESCENARIO 4 | A | Cancelar archivación
        messages.error(self.request, ERROR_USER_DELETE)
        return super().form_invalid(form)


class UserRestoreView(StaffPermissionRequiredMixin, FormView):
    """
    HU-042: Reincorporar usuario (reactivar)
    """
    form_class = UserRestoreForm
    template_name = TEMPLATE_USER_RESTORE
    permission_required = PERM_USER_CHANGE  # HU-042 | ESCENARIO 3 | E | Sin permisos
    
    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, pk=kwargs['pk'])
        
        # HU-042 | ESCENARIO 2 | A | Usuario ya activo (redirige con advertencia)
        if self.user.is_active:
            messages.warning(request, MSG_USER_ALREADY_ACTIVE.format(username=self.user.username))
            return redirect(USERS_LIST)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_USER_OBJ] = self.user
        context[CONTEXT_CANCEL_URL] = USERS_TRASHCAN
        return context
    
    def form_valid(self, form):
        # HU-042 | ESCENARIO 1 | H | Usuario reincorporado exitosamente
        self.user.is_active = True
        self.user.save(update_fields=[FILTER_IS_ACTIVE])
        messages.success(self.request, MSG_USER_RESTORED.format(username=self.user.username))
        return redirect(USERS_LIST)
    
    def form_invalid(self, form):
        messages.error(self.request, ERROR_USER_RESTORE)
        return super().form_invalid(form)


class UserTrashcanView(StaffPermissionRequiredMixin, PaginationMixin, ListView):
    """
    HU-041 (parte) + HU-042: Ver papelera de usuarios (usuarios archivados)
    """
    model = User
    template_name = TEMPLATE_USER_TRASHCAN
    context_object_name = CONTEXT_USERS
    permission_required = PERM_USER_VIEW
    paginate_by = PAGINATE_BY_DEFAULT
    
    def get_queryset(self):
        # HU-041 | ESCENARIO 1,2,3 | A | Usuarios archivados visibles en papelera
        return User.objects.filter(is_active=False).order_by(ORDER_BY_USERNAME_DESC)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        
        for user in context[CONTEXT_USERS]:
            rows.append({
                'pk': user.pk,
                'values': [
                    user.username,
                    user.get_full_name(),
                    user.email or DEFAULT_EMPTY_VALUE,
                    user.phone or DEFAULT_EMPTY_VALUE,
                    user.date_joined.strftime(DATE_FORMAT_DISPLAY),
                ],
            })
        
        context[CONTEXT_ROWS] = rows
        context[CONTEXT_HEADERS] = HEADERS_USER_TRASHCAN
        return context


# =============================================================================
# GROUP CRUD VIEWS (Grupos/Roles - no están en HU originales, son soporte)
# =============================================================================

class GroupListView(StaffPermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    """
    Soporte: Listar grupos/roles (no tiene HU asignada, pero es necesario para HU-039)
    """
    model = Group
    template_name = TEMPLATE_GROUP_LIST
    context_object_name = CONTEXT_GROUPS
    permission_required = PERM_GROUP_VIEW
    paginate_by = PAGINATE_BY_DEFAULT
    
    filters = [
        (FILTER_GROUP_NAME, FILTER_GROUP_NAME, 'icontains'),
    ]
    
    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get(QUERY_PARAM_SEARCH, '')
        if search:
            qs = qs.filter(name__icontains=search)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        
        for group in context[CONTEXT_GROUPS]:
            user_count = group.user_set.count()
            rows.append({
                'pk': group.pk,
                'values': [
                    group.name,
                    user_count,
                ],
            })
        
        context[CONTEXT_ROWS] = rows
        context[CONTEXT_HEADERS] = HEADERS_GROUP_LIST
        return context


class GroupCreateView(StaffPermissionRequiredMixin, CreateView):
    """Soporte: Crear grupo/rol (no tiene HU asignada)"""
    model = Group
    form_class = GroupCreateForm
    template_name = TEMPLATE_GROUP_FORM
    permission_required = PERM_GROUP_ADD
    success_url = reverse_lazy(USERS_GROUP_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = USERS_GROUP_LIST
        context[CONTEXT_TITLE] = TITLE_GROUP_CREATE
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, MSG_GROUP_CREATED.format(name=form.instance.name))
        return response


class GroupUpdateView(StaffPermissionRequiredMixin, UpdateView):
    """Soporte: Editar grupo/rol (no tiene HU asignada)"""
    model = Group
    form_class = GroupUpdateForm
    template_name = TEMPLATE_GROUP_FORM
    permission_required = PERM_GROUP_CHANGE
    success_url = reverse_lazy(USERS_GROUP_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = USERS_GROUP_LIST
        context[CONTEXT_TITLE] = TITLE_GROUP_UPDATE.format(name=self.object.name)
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, MSG_GROUP_UPDATED.format(name=form.instance.name))
        return response


class GroupDetailView(StaffPermissionRequiredMixin, DetailView):
    """Soporte: Ver detalle de grupo/rol (no tiene HU asignada)"""
    model = Group
    template_name = TEMPLATE_GROUP_DETAIL
    context_object_name = CONTEXT_GROUP
    permission_required = PERM_GROUP_VIEW
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = USERS_GROUP_LIST
        context[CONTEXT_USERS] = self.object.user_set.all().order_by(FILTER_USERNAME)
        return context


class GroupDeleteView(StaffPermissionRequiredMixin, FormView):
    """Soporte: Eliminar grupo/rol (no tiene HU asignada)"""
    form_class = GroupDeleteForm
    template_name = TEMPLATE_GROUP_CONFIRM_DELETE
    permission_required = PERM_GROUP_DELETE
    
    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(Group, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['group'] = self.group
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_GROUP] = self.group
        context[CONTEXT_USER_COUNT] = self.group.user_set.count()
        context[CONTEXT_CANCEL_URL] = USERS_GROUP_LIST
        return context
    
    def form_valid(self, form):
        group_name = self.group.name
        self.group.delete()
        messages.success(self.request, MSG_GROUP_DELETED.format(name=group_name))
        return redirect(USERS_GROUP_LIST)
    
    def form_invalid(self, form):
        messages.error(self.request, ERROR_GROUP_DELETE)
        return super().form_invalid(form)


# =============================================================================
# USER PROFILE VIEWS (HU-043)
# =============================================================================

class UserProfileView(DetailView):
    """
    HU-043: Ver/editar mi propio perfil (vista de detalle)
    """
    model = User
    template_name = TEMPLATE_USER_PROFILE
    context_object_name = CONTEXT_USER_OBJ
    
    def get_object(self, queryset=None):
        # HU-043 | ESCENARIO 1 | H | Perfil cargado exitosamente
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = USERS_PROFILE
        return context


class UserProfileUpdateView(UpdateView):
    """
    HU-043 | ESCENARIO 2 | H | Actualizar nombre y teléfono
    """
    model = User
    form_class = UserProfileForm
    template_name = TEMPLATE_USER_PROFILE_EDIT
    success_url = reverse_lazy(USERS_PROFILE)
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = USERS_PROFILE
        return context
    
    def form_valid(self, form):
        messages.success(self.request, MSG_PROFILE_UPDATED)
        return redirect(USERS_PROFILE)
    
    def get_success_url(self):
        return reverse_lazy(USERS_PROFILE)


class UserProfilePasswordView(FormView):
    """
    HU-043 | ESCENARIO 3,4,5,6 | H/A/E | Cambiar contraseña desde perfil
    """
    form_class = UserProfilePasswordForm
    template_name = TEMPLATE_USER_PROFILE_PASSWORD
    success_url = reverse_lazy(USERS_PROFILE)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = USERS_PROFILE
        return context
    
    def form_valid(self, form):
        # HU-043 | ESCENARIO 3 | H | Contraseña cambiada exitosamente
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, MSG_PASSWORD_UPDATED)
        return redirect(USERS_PROFILE)
    
    def form_invalid(self, form):
        # HU-043 | ESCENARIO 4 | E | Contraseña actual incorrecta
        # HU-043 | ESCENARIO 5 | E | Nueva contraseña débil
        # HU-043 | ESCENARIO 6 | E | Nueva contraseña no coincide con confirmación
        messages.error(self.request, ERROR_PASSWORD_UPDATE)
        return super().form_invalid(form)

    # HU-043 | ESCENARIO 7 | E | Sin permisos (usuario no autenticado) - manejado por @login_required en URLs