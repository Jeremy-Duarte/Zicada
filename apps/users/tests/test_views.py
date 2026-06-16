from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission 
from django.contrib.contenttypes.models import ContentType
from apps.users.models import Group, User
from django.urls import reverse
from unittest.mock import patch, Mock

from apps.core.url_names import (
    BACKOFFICE_DASHBOARD,
    PRODUCTS_CATALOG,
    CORE_STAFF_LOGIN,
    USERS_LIST,
    USERS_CREATE,
    USERS_EDIT,
    USERS_CHANGE_PASSWORD,
    USERS_DELETE,
    USERS_RESTORE,
    USERS_TRASHCAN,
    USERS_PROFILE,
    USERS_PROFILE_EDIT,
    USERS_PROFILE_PASSWORD,
    USERS_GROUP_LIST,
    USERS_GROUP_CREATE,
    USERS_GROUP_EDIT,
    USERS_GROUP_DETAIL,
    USERS_GROUP_DELETE,
)

from apps.users.constants import (
    MSG_USER_CREATED,
    MSG_USER_UPDATED,
    MSG_USER_DELETED,
    MSG_USER_RESTORED,
    MSG_PASSWORD_CHANGED,
    MSG_PROFILE_UPDATED,
    MSG_PASSWORD_UPDATED,
    MSG_GROUP_CREATED,
    MSG_GROUP_UPDATED,
    MSG_GROUP_DELETED,
    PERM_USER_VIEW,
    PERM_USER_ADD,
    PERM_USER_CHANGE,
    PERM_USER_DELETE,
    PERM_GROUP_VIEW,
    PERM_GROUP_ADD,
    PERM_GROUP_CHANGE,
    PERM_GROUP_DELETE,
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
    HEADERS_USER_LIST,
    HEADERS_USER_TRASHCAN,
    HEADERS_GROUP_LIST,
    ERROR_GROUP_DELETE,
)

User = get_user_model()


# =============================================================================
# HELPERS
# =============================================================================

def _create_admin_user(**kwargs):
    from django.contrib.auth.models import Group as AuthGroup
    
    defaults = {'username': 'admin', 'password': 'pass1234', 'is_staff': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    is_delivery = defaults.pop('is_delivery', False)

    user = User(**defaults)
    user.set_password(password)
    user.save()

    if is_delivery and hasattr(user, 'is_delivery'):
        user.is_delivery = True
        user.save(update_fields=['is_delivery'])

    admin_group, _ = AuthGroup.objects.get_or_create(name='Administrador')
    user.groups.add(admin_group)

    return user


def _create_delivery_user(**kwargs):
    from django.contrib.auth.models import Group as AuthGroup
    
    defaults = {'username': 'delivery', 'password': 'pass1234', 'is_delivery': True}
    defaults.update(kwargs)
    password = defaults.pop('password')

    user = User(**defaults)
    user.set_password(password)
    user.save()

    delivery_group, _ = AuthGroup.objects.get_or_create(name='Entregador')
    user.groups.add(delivery_group)

    return user


def _create_normal_user(**kwargs):
    defaults = {'username': 'normal', 'password': 'pass1234', 'is_staff': False}
    defaults.update(kwargs)
    password = defaults.pop('password')
    is_delivery = defaults.pop('is_delivery', False)

    user = User(**defaults)
    user.set_password(password)
    user.save()

    if is_delivery and hasattr(user, 'is_delivery'):
        user.is_delivery = True
        user.save(update_fields=['is_delivery'])

    return user


def _add_user_permissions(user):
    content_type = ContentType.objects.get_for_model(User)
    perms = Permission.objects.filter(content_type=content_type)
    user.user_permissions.add(*perms)
    return user


def _add_group_permissions(user):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import Group as AuthGroup

    content_type = ContentType.objects.get_for_model(AuthGroup)
    perms = Permission.objects.filter(content_type=content_type)
    user.user_permissions.add(*perms)
    user.refresh_from_db()
    return user


def _create_group(name='Test Group'):
    from apps.users.models import Group
    return Group.objects.create(name=name)


# =============================================================================
# TESTS: HU-038 UserListView
# =============================================================================

class UserListViewTest(TestCase):
    """HU-038: Listar usuarios (admin)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.admin = _add_user_permissions(self.admin)
        self.client.force_login(self.admin)

        self.user1 = _create_normal_user(username='juan', first_name='Juan', last_name='Perez')
        self.user2 = _create_normal_user(username='maria', first_name='Maria', email='maria@test.com')
        self.user3 = _create_delivery_user(username='delivery1')

    # UT-531: HU-038 CA-001 - Lista de usuarios cargada exitosamente
    def test_list_returns_200(self):
        response = self.client.get(reverse(USERS_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_LIST)

    # UT-532: HU-038 - Excluye al propio usuario logueado
    def test_list_excludes_current_user(self):
        response = self.client.get(reverse(USERS_LIST))
        users = list(response.context['users'])
        self.assertNotIn(self.admin, users)

    # UT-533: HU-038 - Incluye otros usuarios
    def test_list_includes_other_users(self):
        response = self.client.get(reverse(USERS_LIST))
        users = list(response.context['users'])
        self.assertIn(self.user1, users)
        self.assertIn(self.user2, users)

    # UT-534: HU-038 CA-002 - Búsqueda por nombre de usuario
    def test_search_by_username(self):
        response = self.client.get(reverse(USERS_LIST), {'search': 'juan'})
        users = list(response.context['users'])
        self.assertIn(self.user1, users)
        self.assertNotIn(self.user2, users)

    # UT-535: HU-038 CA-002 - Búsqueda por correo
    def test_search_by_email(self):
        response = self.client.get(reverse(USERS_LIST), {'search': 'maria@test.com'})
        users = list(response.context['users'])
        self.assertIn(self.user2, users)
        self.assertNotIn(self.user1, users)

    # UT-536: HU-038 CA-003 - Filtro por rol (is_delivery)
    def test_filter_by_is_delivery(self):
        response = self.client.get(reverse(USERS_LIST), {'is_delivery': '1'})
        users = list(response.context['users'])
        self.assertIn(self.user3, users)
        self.assertNotIn(self.user1, users)

    # UT-537: HU-038 CA-004 - Filtro por estado (is_active=false)
    def test_filter_by_inactive(self):
        self.user1.is_active = False
        self.user1.save()
        response = self.client.get(reverse(USERS_LIST), {'is_active': '0'})
        users = list(response.context['users'])
        self.assertIn(self.user1, users)
        self.assertNotIn(self.user2, users)

    # UT-538: HU-038 CA-005 - Sin usuarios (excluyendo el actual)
    def test_list_empty_excluding_admin(self):
        User.objects.exclude(pk=self.admin.pk).delete()
        response = self.client.get(reverse(USERS_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['users']), 0)

    # UT-539: HU-038 CA-006 - Usuario no autenticado redirige a login
    def test_list_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(USERS_LIST))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_LIST)}')

    # UT-540: HU-038 CA-006 - Usuario sin permiso redirige a catálogo
    def test_list_requires_permission(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(USERS_LIST))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    # UT-541: HU-038 - Incluye headers en contexto
    def test_list_context_headers(self):
        response = self.client.get(reverse(USERS_LIST))
        self.assertEqual(response.context['headers'], HEADERS_USER_LIST)


# =============================================================================
# TESTS: HU-039 UserCreateView
# =============================================================================

class UserCreateViewTest(TestCase):
    """HU-039: Crear usuario (admin)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.admin = _add_user_permissions(self.admin)
        self.client.force_login(self.admin)

    def get_valid_data(self):
        return {
            'username': 'nuevo_user',
            'email': 'nuevo@test.com',
            'first_name': 'Nuevo',
            'last_name': 'Usuario',
            'password1': 'Compleja123!',
            'password2': 'Compleja123!',
            'is_staff': False,
            'is_delivery': True,
        }

    # UT-542: HU-039 - Muestra formulario de creación
    def test_get_create_form(self):
        response = self.client.get(reverse(USERS_CREATE))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_FORM)

    # UT-543: HU-039 CA-001 - Usuario creado exitosamente
    def test_create_valid_user(self):
        data = self.get_valid_data()
        response = self.client.post(reverse(USERS_CREATE), data=data)
        self.assertRedirects(response, reverse(USERS_LIST))
        self.assertTrue(User.objects.filter(username='nuevo_user').exists())

    # UT-544: HU-039 CA-003 - Correo duplicado da error
    def test_create_duplicate_email(self):
        _create_normal_user(email='nuevo@test.com')
        data = self.get_valid_data()
        response = self.client.post(reverse(USERS_CREATE), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='nuevo_user').exists())

    # UT-545: HU-039 CA-002 - Errores en el formulario
    def test_create_invalid_form(self):
        data = self.get_valid_data()
        data['username'] = ''
        response = self.client.post(reverse(USERS_CREATE), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='nuevo@test.com').exists())

    # UT-546: HU-039 CA-004 - Usuario no autenticado redirige a login
    def test_create_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(USERS_CREATE))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_CREATE)}')

    # UT-547: HU-039 CA-004 - Usuario sin permiso redirige a catálogo
    def test_create_requires_permission(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(USERS_CREATE))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: HU-040 UserUpdateView
# =============================================================================

class UserUpdateViewTest(TestCase):
    """HU-040: Editar usuario (admin)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.admin = _add_user_permissions(self.admin)
        self.client.force_login(self.admin)
        self.target_user = _create_normal_user(username='target', first_name='Original')

    def get_valid_data(self):
        return {
            'username': 'target_updated',
            'email': 'target@updated.com',
            'first_name': 'Actualizado',
            'last_name': 'User',
            'is_staff': False,
            'is_delivery': False,
        }

    # UT-548: HU-040 - Muestra formulario de edición
    def test_get_update_form(self):
        response = self.client.get(reverse(USERS_EDIT, kwargs={'pk': self.target_user.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_FORM)

    # UT-549: HU-040 CA-001 - Usuario actualizado exitosamente
    def test_update_valid_user(self):
        data = self.get_valid_data()
        response = self.client.post(reverse(USERS_EDIT, kwargs={'pk': self.target_user.pk}), data=data)
        self.assertRedirects(response, reverse(USERS_LIST))
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.first_name, 'Actualizado')

    # UT-550: HU-040 CA-002 - Muestra enlace para cambiar contraseña
    def test_update_shows_password_change_link(self):
        response = self.client.get(reverse(USERS_EDIT, kwargs={'pk': self.target_user.pk}))
        self.assertTrue(response.context.get('show_password_change', False))

    # UT-551: HU-040 CA-003 - Correo duplicado al editar da error
    def test_update_duplicate_email(self):
        _create_normal_user(email='target@updated.com')
        data = self.get_valid_data()
        response = self.client.post(reverse(USERS_EDIT, kwargs={'pk': self.target_user.pk}), data=data)
        self.assertEqual(response.status_code, 200)
        self.target_user.refresh_from_db()
        self.assertNotEqual(self.target_user.email, 'target@updated.com')

    # UT-552: HU-040 CA-004 - Usuario no existe da 404
    def test_update_nonexistent_user(self):
        response = self.client.get(reverse(USERS_EDIT, kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    # UT-553: HU-040 CA-005 - Usuario no autenticado redirige a login
    def test_update_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(USERS_EDIT, kwargs={'pk': self.target_user.pk}))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_EDIT, kwargs={"pk": self.target_user.pk})}')

    # UT-554: HU-040 CA-005 - Usuario sin permiso redirige a catálogo
    def test_update_requires_permission(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(USERS_EDIT, kwargs={'pk': self.target_user.pk}))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    # UT-555: HU-040 CA-002 - Formulario inválido muestra errores
    def test_update_invalid_form(self):
        data = self.get_valid_data()
        data['email'] = 'invalido'
        response = self.client.post(reverse(USERS_EDIT, kwargs={'pk': self.target_user.pk}), data=data)
        self.assertEqual(response.status_code, 200)
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.first_name, 'Original')


# =============================================================================
# TESTS: HU-040 UserChangePasswordView
# =============================================================================

class UserChangePasswordViewTest(TestCase):
    """HU-040 CA-002: Cambiar contraseña (admin)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.admin = _add_user_permissions(self.admin)
        self.client.force_login(self.admin)
        self.target_user = _create_normal_user(username='target', password='OldPass123!')

    # UT-556: HU-040 - Muestra formulario de cambio de contraseña
    def test_get_change_password_form(self):
        response = self.client.get(reverse(USERS_CHANGE_PASSWORD, kwargs={'pk': self.target_user.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_CHANGE_PASSWORD)

    # UT-557: HU-040 CA-002 - Contraseña cambiada exitosamente
    def test_change_password_valid(self):
        data = {'password1': 'NewComplex123!', 'password2': 'NewComplex123!'}
        response = self.client.post(
            reverse(USERS_CHANGE_PASSWORD, kwargs={'pk': self.target_user.pk}), 
            data=data
        )
        self.assertRedirects(response, reverse(USERS_LIST))
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.check_password('NewComplex123!'))

    # UT-558: Contraseñas no coinciden da error
    def test_change_password_mismatch(self):
        data = {'password1': 'NewComplex123!', 'password2': 'Different456!'}
        response = self.client.post(
            reverse(USERS_CHANGE_PASSWORD, kwargs={'pk': self.target_user.pk}), 
            data=data
        )
        self.assertEqual(response.status_code, 200)
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.check_password('OldPass123!'))

    # UT-559: HU-040 - Usuario no existe da 404
    def test_change_password_nonexistent_user(self):
        response = self.client.get(reverse(USERS_CHANGE_PASSWORD, kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)


# =============================================================================
# TESTS: HU-041 UserDeleteView
# =============================================================================

class UserDeleteViewTest(TestCase):
    """HU-041: Archivar usuario (soft delete)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.admin = _add_user_permissions(self.admin)
        self.client.force_login(self.admin)
        self.target = _create_normal_user(username='target')

    # UT-560: HU-041 - Muestra pantalla de confirmación
    def test_get_delete_confirmation(self):
        response = self.client.get(reverse(USERS_DELETE, kwargs={'pk': self.target.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_CONFIRM_DELETE)

    # UT-561: HU-041 CA-001 - Usuario archivado exitosamente
    def test_delete_valid_user(self):
        response = self.client.post(
            reverse(USERS_DELETE, kwargs={'pk': self.target.pk}), 
            {'confirm': 'target'}
        )
        self.assertRedirects(response, reverse(USERS_LIST))
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)

    # UT-562: HU-041 CA-002 - Archivar al propio usuario no permitido
    def test_delete_self_not_allowed(self):
        response = self.client.post(
            reverse(USERS_DELETE, kwargs={'pk': self.admin.pk}), 
            {'confirm': 'admin'}
        )
        self.assertRedirects(response, reverse(USERS_LIST))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    # UT-563: HU-041 CA-004 - Cancelar archivación
    def test_delete_without_confirmation(self):
        response = self.client.post(
            reverse(USERS_DELETE, kwargs={'pk': self.target.pk}), 
            {'confirm': 'wrong_name'}
        )
        self.assertEqual(response.status_code, 200)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)

    # UT-564: HU-041 CA-005 - Usuario no autenticado redirige a login
    def test_delete_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(USERS_DELETE, kwargs={'pk': self.target.pk}))
        self.assertRedirects(
            response, 
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_DELETE, kwargs={"pk": self.target.pk})}'
        )

    # UT-565: HU-041 CA-005 - Usuario sin permiso redirige a catálogo
    def test_delete_requires_permission(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(USERS_DELETE, kwargs={'pk': self.target.pk}))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: HU-042 UserRestoreView
# =============================================================================

class UserRestoreViewTest(TestCase):
    """HU-042: Reincorporar usuario (reactivar)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.admin = _add_user_permissions(self.admin)
        self.client.force_login(self.admin)
        self.target = _create_normal_user(username='target', is_active=False)

    # UT-566: HU-042 - Muestra pantalla de restauración
    def test_get_restore_confirmation(self):
        response = self.client.get(reverse(USERS_RESTORE, kwargs={'pk': self.target.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_RESTORE)

    # UT-567: HU-042 CA-001 - Usuario reincorporado exitosamente
    def test_restore_valid_user(self):
        response = self.client.post(reverse(USERS_RESTORE, kwargs={'pk': self.target.pk}), {'confirm': True})
        self.assertRedirects(response, reverse(USERS_LIST))
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)

    # UT-568: HU-042 CA-002 - Usuario ya activo redirige
    def test_restore_already_active(self):
        active_user = _create_normal_user(username='active_user')
        response = self.client.get(reverse(USERS_RESTORE, kwargs={'pk': active_user.pk}))
        self.assertEqual(response.status_code, 302)
        active_user.refresh_from_db()
        self.assertTrue(active_user.is_active)

    # UT-569: HU-042 CA-003 - Usuario no autenticado redirige a login
    def test_restore_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(USERS_RESTORE, kwargs={'pk': self.target.pk}))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_RESTORE, kwargs={"pk": self.target.pk})}')

    # UT-570: HU-042 CA-003 - Usuario sin permiso redirige a catálogo
    def test_restore_requires_permission(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(USERS_RESTORE, kwargs={'pk': self.target.pk}))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: UserTrashcanView
# =============================================================================

class UserTrashcanViewTest(TestCase):
    """HU-041 (parte) + HU-042: Ver papelera de usuarios"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.admin = _add_user_permissions(self.admin)
        self.client.force_login(self.admin)

        self.inactive1 = _create_normal_user(username='deleted1', is_active=False)
        self.inactive2 = _create_normal_user(username='deleted2', is_active=False)
        self.active = _create_normal_user(username='active', is_active=True)

    # UT-571: HU-041 - Papelera muestra solo usuarios inactivos
    def test_trashcan_shows_only_inactive(self):
        response = self.client.get(reverse(USERS_TRASHCAN))
        users = list(response.context['users'])
        self.assertIn(self.inactive1, users)
        self.assertIn(self.inactive2, users)
        self.assertNotIn(self.active, users)
        self.assertTemplateUsed(response, TEMPLATE_USER_TRASHCAN)

    # UT-572: HU-041 - Papelera vacía
    def test_trashcan_empty(self):
        User.objects.filter(is_active=False).delete()
        response = self.client.get(reverse(USERS_TRASHCAN))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['users']), 0)

    # UT-573: HU-041 - Incluye headers en contexto
    def test_trashcan_context_headers(self):
        response = self.client.get(reverse(USERS_TRASHCAN))
        self.assertEqual(response.context['headers'], HEADERS_USER_TRASHCAN)

    # UT-574: HU-041 - Usuario no autenticado redirige a login
    def test_trashcan_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(USERS_TRASHCAN))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_TRASHCAN)}')

    # UT-575: HU-041 - Usuario sin permiso redirige a catálogo
    def test_trashcan_requires_permission(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(USERS_TRASHCAN))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: HU-043 UserProfileView
# =============================================================================

class UserProfileViewTest(TestCase):
    """HU-043: Ver mi propio perfil"""

    def setUp(self):
        self.client = Client()
        self.user = _create_normal_user(username='profile_user', first_name='Perfil')
        self.client.force_login(self.user)

    # UT-576: HU-043 CA-001 - Perfil cargado exitosamente
    def test_profile_returns_200(self):
        response = self.client.get(reverse(USERS_PROFILE))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user_obj'].pk, self.user.pk)
        self.assertTemplateUsed(response, TEMPLATE_USER_PROFILE)

    # UT-577: HU-043 CA-007 - Sin autenticación redirige a login
    def test_profile_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse(USERS_PROFILE))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_PROFILE)}')


class UserProfileUpdateViewTest(TestCase):
    """HU-043 CA-002: Actualizar nombre y teléfono"""

    def setUp(self):
        self.client = Client()
        self.user = _create_normal_user(username='profile_user', first_name='Original')
        self.client.force_login(self.user)

    # UT-578: HU-043 - Muestra formulario de edición de perfil
    def test_get_profile_edit_form(self):
        response = self.client.get(reverse(USERS_PROFILE_EDIT))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_PROFILE_EDIT)

    # UT-579: HU-043 CA-002 - Actualizar nombre exitosamente
    def test_update_profile_valid(self):
        data = {'first_name': 'NuevoNombre', 'last_name': 'NuevoApellido', 'email': self.user.email}
        response = self.client.post(reverse(USERS_PROFILE_EDIT), data=data)
        self.assertRedirects(response, reverse(USERS_PROFILE))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'NuevoNombre')


class UserProfilePasswordViewTest(TestCase):
    """HU-043 CA-003/004/005/006: Cambiar contraseña desde perfil"""

    def setUp(self):
        self.client = Client()
        self.user = _create_normal_user(username='profile_user', password='OldPass123!')
        self.client.force_login(self.user)

    # UT-580: HU-043 - Muestra formulario de cambio de contraseña
    def test_get_password_form(self):
        response = self.client.get(reverse(USERS_PROFILE_PASSWORD))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_PROFILE_PASSWORD)

    # UT-581: HU-043 CA-003 - Contraseña cambiada exitosamente
    def test_change_password_valid(self):
        data = {
            'current_password': 'OldPass123!', 
            'new_password1': 'NewComplex123!', 
            'new_password2': 'NewComplex123!'
        }
        response = self.client.post(reverse(USERS_PROFILE_PASSWORD), data=data)
        self.assertRedirects(response, reverse(USERS_PROFILE))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewComplex123!'))

    # UT-582: HU-043 - Cambiar contraseña mantiene sesión activa
    def test_change_password_keeps_session(self):
        self.client.login(username='profile_user', password='OldPass123!')
        
        response = self.client.get(reverse(USERS_PROFILE))
        self.assertEqual(response.status_code, 200)
        
        data = {
            'current_password': 'OldPass123!', 
            'new_password1': 'NewComplex123!', 
            'new_password2': 'NewComplex123!'
        }
        response = self.client.post(reverse(USERS_PROFILE_PASSWORD), data=data)
        
        self.assertRedirects(response, reverse(USERS_PROFILE))
        
        response = self.client.get(reverse(USERS_PROFILE))
        self.assertEqual(response.status_code, 200)
        
        self.client.logout()
        login_success = self.client.login(username='profile_user', password='NewComplex123!')
        self.assertTrue(login_success)

    # UT-583: HU-043 CA-004 - Contraseña actual incorrecta da error
    def test_change_password_wrong_old(self):
        data = {
            'current_password': 'WrongOld!', 
            'new_password1': 'NewComplex123!', 
            'new_password2': 'NewComplex123!'
        }
        response = self.client.post(reverse(USERS_PROFILE_PASSWORD), data=data)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPass123!'))
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertIn('current_password', form.errors)

    # UT-584: HU-043 CA-005 - Nueva contraseña débil da error
    def test_change_password_weak(self):
        data = {'old_password': 'OldPass123!', 'new_password1': '123', 'new_password2': '123'}
        response = self.client.post(reverse(USERS_PROFILE_PASSWORD), data=data)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPass123!'))

    # UT-585: HU-043 CA-006 - Nueva contraseña no coincide da error
    def test_change_password_mismatch(self):
        data = {'old_password': 'OldPass123!', 'new_password1': 'NewComplex123!', 'new_password2': 'Different456!'}
        response = self.client.post(reverse(USERS_PROFILE_PASSWORD), data=data)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPass123!'))


# =============================================================================
# TESTS: Group CRUD Views (Soporte)
# =============================================================================

class GroupListViewTest(TestCase):
    """Soporte: Listar grupos/roles"""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Group as AuthGroup

        content_type = ContentType.objects.get_for_model(AuthGroup)
        permissions = ['view_group', 'add_group', 'change_group', 'delete_group']
        for perm in permissions:
            Permission.objects.get_or_create(
                codename=perm,
                content_type=content_type,
                defaults={'name': f'Can {perm}'}
            )

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.admin = _add_group_permissions(self.admin)
        self.client.force_login(self.admin)
        self.group1 = _create_group(name='Admin Group')
        self.group2 = _create_group(name='Delivery Group')

    # UT-586: Group - Lista de grupos cargada exitosamente
    def test_group_list_returns_200(self):
        response = self.client.get(reverse(USERS_GROUP_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_GROUP_LIST)

    # UT-587: Group - Incluye todos los grupos
    def test_group_list_includes_groups(self):
        response = self.client.get(reverse(USERS_GROUP_LIST))
        groups = list(response.context['groups'])
        self.assertIn(self.group1, groups)
        self.assertIn(self.group2, groups)

    # UT-588: Group - Búsqueda por nombre
    def test_group_list_search(self):
        response = self.client.get(reverse(USERS_GROUP_LIST), {'search': 'Delivery'})
        groups = list(response.context['groups'])
        self.assertIn(self.group2, groups)
        self.assertNotIn(self.group1, groups)

    # UT-589: Group - Incluye headers en contexto
    def test_group_list_context_headers(self):
        response = self.client.get(reverse(USERS_GROUP_LIST))
        self.assertEqual(response.context['headers'], HEADERS_GROUP_LIST)


class GroupCreateViewTest(TestCase):
    """Soporte: Crear grupo/rol"""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Group as AuthGroup

        content_type = ContentType.objects.get_for_model(AuthGroup)
        permissions = ['view_group', 'add_group', 'change_group', 'delete_group']
        for perm in permissions:
            Permission.objects.get_or_create(
                codename=perm,
                content_type=content_type,
                defaults={'name': f'Can {perm}'}
            )

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.admin = _add_group_permissions(self.admin)
        self.client.force_login(self.admin)

    # UT-590: Group - Muestra formulario de creación
    def test_get_create_form(self):
        response = self.client.get(reverse(USERS_GROUP_CREATE))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_GROUP_FORM)

    # UT-591: Group - Grupo creado exitosamente
    def test_create_valid_group(self):
        data = {'name': 'New Group', 'permissions': []}
        response = self.client.post(reverse(USERS_GROUP_CREATE), data=data)
        self.assertRedirects(response, reverse(USERS_GROUP_LIST))
        self.assertTrue(Group.objects.filter(name='New Group').exists())


class GroupUpdateViewTest(TestCase):
    """Soporte: Editar grupo/rol"""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Group as AuthGroup

        content_type = ContentType.objects.get_for_model(AuthGroup)
        permissions = ['view_group', 'add_group', 'change_group', 'delete_group']
        for perm in permissions:
            Permission.objects.get_or_create(
                codename=perm,
                content_type=content_type,
                defaults={'name': f'Can {perm}'}
            )

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.admin = _add_group_permissions(self.admin)
        self.client.force_login(self.admin)
        self.group = _create_group(name='Original Group')

    # UT-592: Group - Muestra formulario de edición
    def test_get_update_form(self):
        response = self.client.get(reverse(USERS_GROUP_EDIT, kwargs={'pk': self.group.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_GROUP_FORM)

    # UT-593: Group - Grupo actualizado exitosamente
    def test_update_valid_group(self):
        data = {'name': 'Updated Group', 'permissions': []}
        response = self.client.post(reverse(USERS_GROUP_EDIT, kwargs={'pk': self.group.pk}), data=data)
        self.assertRedirects(response, reverse(USERS_GROUP_LIST))
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, 'Updated Group')


class GroupDetailViewTest(TestCase):
    """Soporte: Ver detalle de grupo/rol"""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Group as AuthGroup

        content_type = ContentType.objects.get_for_model(AuthGroup)
        permissions = ['view_group', 'add_group', 'change_group', 'delete_group']
        for perm in permissions:
            Permission.objects.get_or_create(
                codename=perm,
                content_type=content_type,
                defaults={'name': f'Can {perm}'}
            )

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.admin = _add_group_permissions(self.admin)
        self.client.force_login(self.admin)
        self.group = _create_group(name='Detail Group')

    # UT-594: Group - Detalle de grupo cargado exitosamente
    def test_detail_returns_200(self):
        response = self.client.get(reverse(USERS_GROUP_DETAIL, kwargs={'pk': self.group.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['group'].pk, self.group.pk)
        self.assertTemplateUsed(response, TEMPLATE_GROUP_DETAIL)


class GroupDeleteViewTest(TestCase):
    """Soporte: Eliminar grupo/rol"""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Group as AuthGroup

        content_type = ContentType.objects.get_for_model(AuthGroup)
        permissions = ['view_group', 'add_group', 'change_group', 'delete_group']
        for perm in permissions:
            Permission.objects.get_or_create(
                codename=perm,
                content_type=content_type,
                defaults={'name': f'Can {perm}'}
            )

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.admin = _add_group_permissions(self.admin)
        self.client.force_login(self.admin)
        self.group = _create_group(name='Delete Group')

    # UT-595: Group - Muestra pantalla de confirmación
    def test_get_delete_confirmation(self):
        response = self.client.get(reverse(USERS_GROUP_DELETE, kwargs={'pk': self.group.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_GROUP_CONFIRM_DELETE)

    # UT-596: Group - Grupo eliminado exitosamente
    def test_delete_valid_group(self):
        response = self.client.post(
            reverse(USERS_GROUP_DELETE, kwargs={'pk': self.group.pk}), 
            {'confirm': self.group.name}
        )
        self.assertRedirects(response, reverse(USERS_GROUP_LIST))
        self.assertFalse(Group.objects.filter(pk=self.group.pk).exists())

    # UT-597: Group - Eliminar grupo con usuarios asignados muestra error
    def test_delete_group_with_users(self):
        user = _create_normal_user(username='member')
        user.groups.add(self.group)
        self.assertTrue(self.group.user_set.count() > 0)
        
        response = self.client.post(
            reverse(USERS_GROUP_DELETE, kwargs={'pk': self.group.pk}), 
            {'confirm': self.group.name}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Group.objects.filter(pk=self.group.pk).exists())
        
        messages_list = list(response.context.get('messages', []))
        self.assertTrue(
            any(ERROR_GROUP_DELETE.lower() in str(m.message).lower() for m in messages_list),
            f"Mensaje '{ERROR_GROUP_DELETE}' no encontrado"
        )

    # UT-598: Group - Usuario no autenticado redirige a login
    def test_delete_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(USERS_GROUP_DELETE, kwargs={'pk': self.group.pk}))
        self.assertRedirects(
            response, 
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_GROUP_DELETE, kwargs={"pk": self.group.pk})}'
        )

    # UT-599: Group - Usuario sin permiso redirige a catálogo
    def test_delete_requires_permission(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(USERS_GROUP_DELETE, kwargs={'pk': self.group.pk}))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    # UT-600: Group - Grupo no existe da 404
    def test_delete_nonexistent_group(self):
        response = self.client.get(reverse(USERS_GROUP_DELETE, kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)