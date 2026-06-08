from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, FormView, DetailView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
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

from .constants import (
    # URL Names
    URL_USER_LIST,
    URL_USER_TRASHCAN,
    URL_GROUP_LIST,
    URL_USER_PROFILE,
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
# USER CRUD VIEWS
# =============================================================================

class UserListView(PermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    model = User
    template_name = TEMPLATE_USER_LIST
    context_object_name = CONTEXT_USERS
    permission_required = 'users.view_user'
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
        qs = super().get_queryset()
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


class UserCreateView(PermissionRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = TEMPLATE_USER_FORM
    permission_required = 'users.add_user'
    success_url = reverse_lazy(URL_USER_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = URL_USER_LIST
        context[CONTEXT_TITLE] = TITLE_USER_CREATE
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, MSG_USER_CREATED.format(username=form.instance.username))
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, ERROR_USER_CREATE)
        return super().form_invalid(form)


class UserUpdateView(PermissionRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = TEMPLATE_USER_FORM
    permission_required = 'users.change_user'
    success_url = reverse_lazy(URL_USER_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = URL_USER_LIST
        context[CONTEXT_TITLE] = TITLE_USER_UPDATE.format(username=self.object.username)
        context[CONTEXT_SHOW_PASSWORD_CHANGE] = True
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, MSG_USER_UPDATED.format(username=form.instance.username))
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, ERROR_USER_UPDATE)
        return super().form_invalid(form)


class UserChangePasswordView(PermissionRequiredMixin, FormView):
    form_class = UserChangePasswordForm
    template_name = TEMPLATE_USER_CHANGE_PASSWORD
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
        context[CONTEXT_USER_OBJ] = self.user
        context[CONTEXT_CANCEL_URL] = URL_USER_LIST
        context[CONTEXT_CANCEL_ARGS] = [self.user.pk]
        return context
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, MSG_PASSWORD_CHANGED.format(username=self.user.username))
        return redirect(URL_USER_LIST, pk=self.user.pk)
    
    def form_invalid(self, form):
        messages.error(self.request, ERROR_PASSWORD_CHANGE)
        return super().form_invalid(form)


class UserDeleteView(PermissionRequiredMixin, FormView):
    form_class = UserDeleteForm
    template_name = TEMPLATE_USER_CONFIRM_DELETE
    permission_required = 'users.delete_user'
    
    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, pk=kwargs['pk'])
        
        if self.user.pk == request.user.pk:
            messages.error(request, ERROR_SELF_DELETE)
            return redirect(URL_USER_LIST)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_USER_OBJ] = self.user
        context[CONTEXT_CANCEL_URL] = URL_USER_LIST
        return context
    
    def form_valid(self, form):
        self.user.is_active = False
        self.user.save(update_fields=[FILTER_IS_ACTIVE])
        messages.success(self.request, MSG_USER_DELETED.format(username=self.user.username))
        return redirect(URL_USER_LIST)
    
    def form_invalid(self, form):
        messages.error(self.request, ERROR_USER_DELETE)
        return super().form_invalid(form)


class UserRestoreView(PermissionRequiredMixin, FormView):
    form_class = UserRestoreForm
    template_name = TEMPLATE_USER_RESTORE
    permission_required = 'users.change_user'
    
    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, pk=kwargs['pk'])
        
        if self.user.is_active:
            messages.warning(request, MSG_USER_ALREADY_ACTIVE.format(username=self.user.username))
            return redirect(URL_USER_LIST)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_USER_OBJ] = self.user
        context[CONTEXT_CANCEL_URL] = URL_USER_TRASHCAN
        return context
    
    def form_valid(self, form):
        self.user.is_active = True
        self.user.save(update_fields=[FILTER_IS_ACTIVE])
        messages.success(self.request, MSG_USER_RESTORED.format(username=self.user.username))
        return redirect(URL_USER_LIST)
    
    def form_invalid(self, form):
        messages.error(self.request, ERROR_USER_RESTORE)
        return super().form_invalid(form)


class UserTrashcanView(PermissionRequiredMixin, PaginationMixin, ListView):
    model = User
    template_name = TEMPLATE_USER_TRASHCAN
    context_object_name = CONTEXT_USERS
    permission_required = 'users.view_user'
    paginate_by = PAGINATE_BY_DEFAULT
    
    def get_queryset(self):
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
# GROUP CRUD VIEWS
# =============================================================================

class GroupListView(PermissionRequiredMixin, PaginationMixin, FilterMixin, ListView):
    model = Group
    template_name = TEMPLATE_GROUP_LIST
    context_object_name = CONTEXT_GROUPS
    permission_required = 'users.view_group'
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


class GroupCreateView(PermissionRequiredMixin, CreateView):
    model = Group
    form_class = GroupCreateForm
    template_name = TEMPLATE_GROUP_FORM
    permission_required = 'users.add_group'
    success_url = reverse_lazy(URL_GROUP_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = URL_GROUP_LIST
        context[CONTEXT_TITLE] = TITLE_GROUP_CREATE
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, MSG_GROUP_CREATED.format(name=form.instance.name))
        return response


class GroupUpdateView(PermissionRequiredMixin, UpdateView):
    model = Group
    form_class = GroupUpdateForm
    template_name = TEMPLATE_GROUP_FORM
    permission_required = 'users.change_group'
    success_url = reverse_lazy(URL_GROUP_LIST)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = URL_GROUP_LIST
        context[CONTEXT_TITLE] = TITLE_GROUP_UPDATE.format(name=self.object.name)
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, MSG_GROUP_UPDATED.format(name=form.instance.name))
        return response


class GroupDetailView(PermissionRequiredMixin, DetailView):
    model = Group
    template_name = TEMPLATE_GROUP_DETAIL
    context_object_name = CONTEXT_GROUP
    permission_required = 'users.view_group'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = URL_GROUP_LIST
        context[CONTEXT_USERS] = self.object.user_set.all().order_by(FILTER_USERNAME)
        return context


class GroupDeleteView(PermissionRequiredMixin, FormView):
    form_class = GroupDeleteForm
    template_name = TEMPLATE_GROUP_CONFIRM_DELETE
    permission_required = 'users.delete_group'
    
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
        context[CONTEXT_CANCEL_URL] = URL_GROUP_LIST
        return context
    
    def form_valid(self, form):
        group_name = self.group.name
        self.group.delete()
        messages.success(self.request, MSG_GROUP_DELETED.format(name=group_name))
        return redirect(URL_GROUP_LIST)
    
    def form_invalid(self, form):
        messages.error(self.request, ERROR_GROUP_DELETE)
        return super().form_invalid(form)


# =============================================================================
# USER PROFILE VIEWS
# =============================================================================

class UserProfileView(DetailView):
    model = User
    template_name = TEMPLATE_USER_PROFILE
    context_object_name = CONTEXT_USER_OBJ
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = URL_USER_PROFILE
        return context


class UserProfileUpdateView(UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = TEMPLATE_USER_PROFILE_EDIT
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = URL_USER_PROFILE
        return context
    
    def form_valid(self, form):
        messages.success(self.request, MSG_PROFILE_UPDATED)
        return redirect(URL_USER_PROFILE)
    
    def get_success_url(self):
        return reverse_lazy(URL_USER_PROFILE)


class UserProfilePasswordView(FormView):
    form_class = UserProfilePasswordForm
    template_name = TEMPLATE_USER_PROFILE_PASSWORD
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[CONTEXT_CANCEL_URL] = URL_USER_PROFILE
        return context
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, MSG_PASSWORD_UPDATED)
        return redirect(URL_USER_PROFILE)
    
    def form_invalid(self, form):
        messages.error(self.request, ERROR_PASSWORD_UPDATE)
        return super().form_invalid(form)