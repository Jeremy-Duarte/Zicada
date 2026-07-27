"""
Migración para crear roles (Grupos) y asignar permisos según la matriz HU.
- Administrador: Todos los permisos CRUD
- Entregador: Permisos limitados
"""

from django.db import migrations


def create_roles_and_permissions(apps, schema_editor):
    """Crea los roles Administrador y Entregador con sus permisos."""
    
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('users', 'User')
    Permission = apps.get_model('auth', 'Permission')
    
    # ======================================================================
    # 1. CREAR ROL ADMINISTRADOR (todos los permisos)
    # ======================================================================
    admin_group, _ = Group.objects.get_or_create(name='Administrador')
    
    # Obtener TODOS los permisos del sistema
    all_perms = Permission.objects.all()
    admin_group.permissions.set(all_perms)
    
    # ======================================================================
    # 2. CREAR ROL ENTREGADOR (permisos limitados)
    # ======================================================================
    delivery_group, _ = Group.objects.get_or_create(name='Entregador')
    
    # Obtener permisos específicos para entregador
    delivery_perms = []
    
    # 2.1 Permisos de productos (solo lectura)
    product_models = ['product', 'collection', 'category', 'size', 'color', 'productcolor', 'productvariant']
    for model in product_models:
        codename = f'view_{model}'
        try:
            p = Permission.objects.get(codename=codename)
            delivery_perms.append(p)
        except Permission.DoesNotExist:
            pass
    
    # 2.2 Permisos de órdenes (ver órdenes + marcar entregado)
    try:
        p = Permission.objects.get(codename='view_order', content_type__app_label='orders')
        delivery_perms.append(p)
    except Permission.DoesNotExist:
        pass
    
    try:
        p = Permission.objects.get(codename='change_order', content_type__app_label='orders')
        delivery_perms.append(p)
    except Permission.DoesNotExist:
        pass
    
    # 2.3 Permisos de usuarios (solo ver y editar propio perfil)
    try:
        p = Permission.objects.get(codename='view_user', content_type__app_label='users')
        delivery_perms.append(p)
    except Permission.DoesNotExist:
        pass
    
    try:
        p = Permission.objects.get(codename='change_user', content_type__app_label='users')
        delivery_perms.append(p)
    except Permission.DoesNotExist:
        pass
    
    # 2.4 Permisos de core (solo ver hero slides)
    try:
        p = Permission.objects.get(codename='view_heroconfig', content_type__app_label='core')
        delivery_perms.append(p)
    except Permission.DoesNotExist:
        pass
    
    # Asignar permisos al grupo Entregador
    if delivery_perms:
        delivery_group.permissions.set(delivery_perms)
    
    # ======================================================================
    # 3. ASIGNAR USUARIOS EXISTENTES A SUS ROLES
    # ======================================================================
    
    # Asignar Administrador a usuarios con is_staff=True
    for user in User.objects.filter(is_staff=True):
        user.groups.add(admin_group)
    
    # Asignar Entregador a usuarios con is_delivery=True
    for user in User.objects.filter(is_delivery=True):
        user.groups.add(delivery_group)


def reverse_roles_and_permissions(apps, schema_editor):
    """Elimina los roles creados (rollback)."""
    Group = apps.get_model('users', 'Group')
    Group.objects.filter(name__in=['Administrador', 'Entregador']).delete()


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_roles_and_permissions, reverse_roles_and_permissions),
    ]