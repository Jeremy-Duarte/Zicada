from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group as BaseGroup
from django.utils.translation import gettext_lazy as _
from .models import User, Group

admin.site.unregister(BaseGroup)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'is_staff', 'is_delivery', 'is_active')
    list_filter = ('is_staff', 'is_delivery', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Información personal'), {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        (_('Permisos y roles'), {
            'fields': ('is_active', 'is_staff', 'is_delivery', 'groups', 'user_permissions'),
        }),
        (_('Fechas importantes'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2', 'is_staff', 'is_delivery'),
        }),
    )


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('permissions',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).using(admin.site._registry[BaseGroup].admin_site._registry[BaseGroup].model.objects.db_manager(None))