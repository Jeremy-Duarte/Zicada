"""
Tests para vistas de apps.users.views

Cubre:
- HU-038: UserListView
- HU-039: UserCreateView
- HU-040: UserUpdateView, UserChangePasswordView
- HU-041: UserDeleteView, UserTrashcanView
- HU-042: UserRestoreView
- HU-043: UserProfileView, UserProfileUpdateView, UserProfilePasswordView
- Group CRUD (soporte)

Casos de prueba: CP-116 a CP-177
"""

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

def _create_user(**kwargs):
    defaults = {'username': 'testuser', 'password': 'pass1234', 'is_active': True}
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


def _create_staff_user(**kwargs):
    defaults = {'is_staff': True}
    defaults.update(kwargs)
    return _create_user(**defaults)


def _add_user_permissions(user):
    """Añade permisos de usuario a un usuario staff."""
    content_type = ContentType.objects.get_for_model(User)
    perms = Permission.objects.filter(content_type=content_type)
    user.user_permissions.add(*perms)
    return user


def _add_group_permissions(user):
    """
    Añade permisos de grupo a un usuario staff.
    Usa el modelo original auth.Group para los permisos.
    """
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import Group as AuthGroup

    content_type = ContentType.objects.get_for_model(AuthGroup)
    perms = Permission.objects.filter(content_type=content_type)
    user.user_permissions.add(*perms)
    user.refresh_from_db()
    return user


def _create_group(name='Test Group'):
    """Crea un grupo usando el modelo proxy de apps.users."""
    from apps.users.models import Group
    return Group.objects.create(name=name)


# =============================================================================
# TESTS: HU-038 UserListView
# =============================================================================

class UserListViewTest(TestCase):
    """HU-038: Listar usuarios (admin)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_staff_user(username='admin')
        self.admin = _add_user_permissions(self.admin)
        self.client.force_login(self.admin)

        self.user1 = _create_user(username='juan', first_name='Juan', last_name='Perez')
        self.user2 = _create_user(username='maria', first_name='Maria', email='maria@test.com')
        self.user3 = _create_user(username='delivery1', is_delivery=True)

    def test_list_returns_200(self):
        """CP-116 | HU-038 | ESCENARIO 1 | H | Lista de usuarios cargada exitosamente"""
        response = self.client.get(reverse(USERS_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_LIST)

    def test_list_excludes_current_user(self):
        """CP-117 | HU-038 | H | Excluye al propio usuario logueado de la lista"""
        response = self.client.get(reverse(USERS_LIST))
        users = list(response.context['users'])
        self.assertNotIn(self.admin, users)

    def test_list_includes_other_users(self):
        """CP-118 | HU-038 | H | Incluye otros usuarios"""
        response = self.client.get(reverse(USERS_LIST))
        users = list(response.context['users'])
        self.assertIn(self.user1, users)
        self.assertIn(self.user2, users)

    def test_search_by_username(self):
        """CP-119 | HU-038 | ESCENARIO 2 | H | Búsqueda por nombre de usuario"""
        response = self.client.get(reverse(USERS_LIST), {'search': 'juan'})
        users = list(response.context['users'])
        self.assertIn(self.user1, users)
        self.assertNotIn(self.user2, users)

    def test_search_by_email(self):
        """CP-120 | HU-038 | ESCENARIO 2 | H | Búsqueda por correo"""
        response = self.client.get(reverse(USERS_LIST), {'search': 'maria@test.com'})
        users = list(response.context['users'])
        self.assertIn(self.user2, users)
        self.assertNotIn(self.user1, users)

    def test_filter_by_is_delivery(self):
        """CP-121 | HU-038 | ESCENARIO 3 | H | Filtro por rol (is_delivery)"""
        response = self.client.get(reverse(USERS_LIST), {'is_delivery': '1'})
        users = list(response.context['users'])
        self.assertIn(self.user3, users)
        self.assertNotIn(self.user1, users)

    def test_filter_by_inactive(self):
        """CP-122 | HU-038 | ESCENARIO 4 | H | Filtro por estado (is_active=false)"""
        self.user1.is_active = False
        self.user1.save()
        response = self.client.get(reverse(USERS_LIST), {'is_active': '0'})
        users = list(response.context['users'])
        self.assertIn(self.user1, users)
        self.assertNotIn(self.user2, users)

    def test_list_empty_excluding_admin(self):
        """CP-123 | HU-038 | ESCENARIO 5 | A | Sin usuarios (excluyendo el actual)"""
        User.objects.exclude(pk=self.admin.pk).delete()
        response = self.client.get(reverse(USERS_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['users']), 0)

    def test_list_requires_authentication(self):
        """CP-124a | HU-038 | ESCENARIO 6 | E | Usuario no autenticado -> login"""
        self.client.logout()
        response = self.client.get(reverse(USERS_LIST))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_LIST)}')

    def test_list_requires_permission(self):
        """CP-124b | HU-038 | ESCENARIO 6 | E | Usuario autenticado sin permiso -> catálogo"""
        normal_user = _create_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(USERS_LIST))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_list_context_headers(self):
        """CP-125 | HU-038 | H | Incluye headers en contexto"""
        response = self.client.get(reverse(USERS_LIST))
        self.assertEqual(response.context['headers'], HEADERS_USER_LIST)


# =============================================================================
# TESTS: HU-039 UserCreateView
# =============================================================================

class UserCreateViewTest(TestCase):
    """HU-039: Crear usuario (admin)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_staff_user(username='admin')
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

    def test_get_create_form(self):
        """CP-126 | HU-039 | GET | Muestra formulario de creación"""
        response = self.client.get(reverse(USERS_CREATE))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_FORM)

    def test_create_valid_user(self):
        """CP-127 | HU-039 | ESCENARIO 1 | H | Usuario creado exitosamente"""
        data = self.get_valid_data()
        response = self.client.post(reverse(USERS_CREATE), data=data)
        self.assertRedirects(response, reverse(USERS_LIST))
        self.assertTrue(User.objects.filter(username='nuevo_user').exists())

    def test_create_duplicate_email(self):
        """CP-128 | HU-039 | ESCENARIO 3 | E | Correo duplicado"""
        _create_user(email='nuevo@test.com')
        data = self.get_valid_data()
        response = self.client.post(reverse(USERS_CREATE), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='nuevo_user').exists())

    def test_create_invalid_form(self):
        """CP-129 | HU-039 | ESCENARIO 2 | A | Errores en el formulario"""
        data = self.get_valid_data()
        data['username'] = ''
        response = self.client.post(reverse(USERS_CREATE), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='nuevo@test.com').exists())

    def test_create_requires_authentication(self):
        """CP-130a | HU-039 | ESCENARIO 4 | E | Usuario no autenticado -> login"""
        self.client.logout()
        response = self.client.get(reverse(USERS_CREATE))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_CREATE)}')

    def test_create_requires_permission(self):
        """CP-130b | HU-039 | ESCENARIO 4 | E | Usuario autenticado sin permiso -> catálogo"""
        normal_user = _create_user(username='normal')
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
        self.admin = _create_staff_user(username='admin')
        self.admin = _add_user_permissions(self.admin)
        self.client.force_login(self.admin)
        self.target_user = _create_user(username='target', first_name='Original')

    def get_valid_data(self):
        return {
            'username': 'target_updated',
            'email': 'target@updated.com',
            'first_name': 'Actualizado',
            'last_name': 'User',
            'is_staff': False,
            'is_delivery': False,
        }

    def test_get_update_form(self):
        """CP-131 | HU-040 | GET | Muestra formulario de edición"""
        response = self.client.get(reverse(USERS_EDIT, kwargs={'pk': self.target_user.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_FORM)

    def test_update_valid_user(self):
        """CP-132 | HU-040 | ESCENARIO 1 | H | Usuario actualizado exitosamente"""
        data = self.get_valid_data()
        response = self.client.post(reverse(USERS_EDIT, kwargs={'pk': self.target_user.pk}), data=data)
        self.assertRedirects(response, reverse(USERS_LIST))
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.first_name, 'Actualizado')

    def test_update_shows_password_change_link(self):
        """CP-133 | HU-040 | ESCENARIO 2 | H | Muestra enlace para cambiar contraseña"""
        response = self.client.get(reverse(USERS_EDIT, kwargs={'pk': self.target_user.pk}))
        self.assertTrue(response.context.get('show_password_change', False))

    def test_update_duplicate_email(self):
        """CP-134 | HU-040 | ESCENARIO 3 | E | Correo duplicado al editar"""
        _create_user(email='target@updated.com')
        data = self.get_valid_data()
        response = self.client.post(reverse(USERS_EDIT, kwargs={'pk': self.target_user.pk}), data=data)
        self.assertEqual(response.status_code, 200)
        self.target_user.refresh_from_db()
        self.assertNotEqual(self.target_user.email, 'target@updated.com')

    def test_update_nonexistent_user(self):
        """CP-135 | HU-040 | ESCENARIO 4 | E | Usuario no existe -> 404"""
        response = self.client.get(reverse(USERS_EDIT, kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_update_requires_authentication(self):
        """CP-136a | HU-040 | ESCENARIO 5 | E | Usuario no autenticado -> login"""
        self.client.logout()
        response = self.client.get(reverse(USERS_EDIT, kwargs={'pk': self.target_user.pk}))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_EDIT, kwargs={"pk": self.target_user.pk})}')

    def test_update_requires_permission(self):
        """CP-136b | HU-040 | ESCENARIO 5 | E | Usuario autenticado sin permiso -> catálogo"""
        normal_user = _create_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(USERS_EDIT, kwargs={'pk': self.target_user.pk}))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_update_invalid_form(self):
        """CP-137 | HU-040 | ESCENARIO 2 | A | Formulario inválido"""
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
    """HU-040 | ESCENARIO 2 | H | Cambiar contraseña (admin)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_staff_user(username='admin')
        self.admin = _add_user_permissions(self.admin)
        self.client.force_login(self.admin)
        self.target_user = _create_user(username='target', password='OldPass123!')

    def test_get_change_password_form(self):
        """CP-138 | HU-040 | GET | Muestra formulario de cambio de contraseña"""
        response = self.client.get(reverse(USERS_CHANGE_PASSWORD, kwargs={'pk': self.target_user.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_CHANGE_PASSWORD)

    def test_change_password_valid(self):
        """CP-139 | HU-040 | ESCENARIO 2 | H | Contraseña cambiada exitosamente"""
        data = {'password1': 'NewComplex123!', 'password2': 'NewComplex123!'}
        response = self.client.post(
            reverse(USERS_CHANGE_PASSWORD, kwargs={'pk': self.target_user.pk}), 
            data=data
        )
        self.assertRedirects(response, reverse(USERS_LIST))
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.check_password('NewComplex123!'))

    def test_change_password_mismatch(self):
        """CP-140 | Contraseñas no coinciden"""
        data = {'password1': 'NewComplex123!', 'password2': 'Different456!'}
        response = self.client.post(
            reverse(USERS_CHANGE_PASSWORD, kwargs={'pk': self.target_user.pk}), 
            data=data
        )
        self.assertEqual(response.status_code, 200)
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.check_password('OldPass123!'))

    def test_change_password_nonexistent_user(self):
        """CP-141 | HU-040 | ESCENARIO 4 | E | Usuario no existe -> 404"""
        response = self.client.get(reverse(USERS_CHANGE_PASSWORD, kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)


# =============================================================================
# TESTS: HU-041 UserDeleteView
# =============================================================================

class UserDeleteViewTest(TestCase):
    """HU-041: Archivar usuario (soft delete)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_staff_user(username='admin')
        self.admin = _add_user_permissions(self.admin)
        self.client.force_login(self.admin)
        self.target = _create_user(username='target')

    def test_get_delete_confirmation(self):
        """CP-142 | HU-041 | GET | Muestra pantalla de confirmación"""
        response = self.client.get(reverse(USERS_DELETE, kwargs={'pk': self.target.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_CONFIRM_DELETE)

    def test_delete_valid_user(self):
        """CP-143 | HU-041 | ESCENARIO 1 | H | Usuario archivado exitosamente"""
        response = self.client.post(
            reverse(USERS_DELETE, kwargs={'pk': self.target.pk}), 
            {'confirm': 'target'}  # ← Nombre de usuario correcto
        )
        self.assertRedirects(response, reverse(USERS_LIST))
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)

    def test_delete_self_not_allowed(self):
        """CP-144 | HU-041 | ESCENARIO 2 | E | Archivar al propio usuario"""
        response = self.client.post(
            reverse(USERS_DELETE, kwargs={'pk': self.admin.pk}), 
            {'confirm': 'admin'}
        )
        self.assertRedirects(response, reverse(USERS_LIST))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_delete_without_confirmation(self):
        """CP-145 | HU-041 | ESCENARIO 4 | A | Cancelar archivación"""
        response = self.client.post(
            reverse(USERS_DELETE, kwargs={'pk': self.target.pk}), 
            {'confirm': 'wrong_name'}  # ← Nombre incorrecto
        )
        self.assertEqual(response.status_code, 200)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)

    def test_delete_requires_authentication(self):
        """CP-146a | HU-041 | ESCENARIO 5 | E | Usuario no autenticado -> login"""
        self.client.logout()
        response = self.client.get(reverse(USERS_DELETE, kwargs={'pk': self.target.pk}))
        self.assertRedirects(
            response, 
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_DELETE, kwargs={"pk": self.target.pk})}'
        )

    def test_delete_requires_permission(self):
        """CP-146b | HU-041 | ESCENARIO 5 | E | Usuario autenticado sin permiso -> catálogo"""
        normal_user = _create_user(username='normal')
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
        self.admin = _create_staff_user(username='admin')
        self.admin = _add_user_permissions(self.admin)
        self.client.force_login(self.admin)
        self.target = _create_user(username='target', is_active=False)

    def test_get_restore_confirmation(self):
        """CP-147 | HU-042 | GET | Muestra pantalla de restauración"""
        response = self.client.get(reverse(USERS_RESTORE, kwargs={'pk': self.target.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_RESTORE)

    def test_restore_valid_user(self):
        """CP-148 | HU-042 | ESCENARIO 1 | H | Usuario reincorporado exitosamente"""
        response = self.client.post(reverse(USERS_RESTORE, kwargs={'pk': self.target.pk}), {'confirm': True})
        self.assertRedirects(response, reverse(USERS_LIST))
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)

    def test_restore_already_active(self):
        """CP-149 | HU-042 | ESCENARIO 2 | A | Usuario ya activo -> redirige"""
        active_user = _create_user(username='active_user')
        response = self.client.get(reverse(USERS_RESTORE, kwargs={'pk': active_user.pk}))
        self.assertEqual(response.status_code, 302)
        active_user.refresh_from_db()
        self.assertTrue(active_user.is_active)

    def test_restore_requires_authentication(self):
        """CP-150a | HU-042 | ESCENARIO 3 | E | Usuario no autenticado -> login"""
        self.client.logout()
        response = self.client.get(reverse(USERS_RESTORE, kwargs={'pk': self.target.pk}))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_RESTORE, kwargs={"pk": self.target.pk})}')

    def test_restore_requires_permission(self):
        """CP-150b | HU-042 | ESCENARIO 3 | E | Usuario autenticado sin permiso -> catálogo"""
        normal_user = _create_user(username='normal')
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
        self.admin = _create_staff_user(username='admin')
        self.admin = _add_user_permissions(self.admin)
        self.client.force_login(self.admin)

        self.inactive1 = _create_user(username='deleted1', is_active=False)
        self.inactive2 = _create_user(username='deleted2', is_active=False)
        self.active = _create_user(username='active', is_active=True)

    def test_trashcan_shows_only_inactive(self):
        """CP-151 | HU-041 | A | Papelera muestra solo usuarios inactivos"""
        response = self.client.get(reverse(USERS_TRASHCAN))
        users = list(response.context['users'])
        self.assertIn(self.inactive1, users)
        self.assertIn(self.inactive2, users)
        self.assertNotIn(self.active, users)
        self.assertTemplateUsed(response, TEMPLATE_USER_TRASHCAN)

    def test_trashcan_empty(self):
        """CP-152 | HU-041 | A | Papelera vacía"""
        User.objects.filter(is_active=False).delete()
        response = self.client.get(reverse(USERS_TRASHCAN))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['users']), 0)

    def test_trashcan_context_headers(self):
        """CP-153 | HU-041 | H | Incluye headers en contexto"""
        response = self.client.get(reverse(USERS_TRASHCAN))
        self.assertEqual(response.context['headers'], HEADERS_USER_TRASHCAN)

    def test_trashcan_requires_authentication(self):
        """CP-154a | HU-041 | E | Usuario no autenticado -> login"""
        self.client.logout()
        response = self.client.get(reverse(USERS_TRASHCAN))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_TRASHCAN)}')

    def test_trashcan_requires_permission(self):
        """CP-154b | HU-041 | E | Usuario autenticado sin permiso -> catálogo"""
        normal_user = _create_user(username='normal')
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
        self.user = _create_user(username='profile_user', first_name='Perfil')
        self.client.force_login(self.user)

    def test_profile_returns_200(self):
        """CP-155 | HU-043 | ESCENARIO 1 | H | Perfil cargado exitosamente"""
        response = self.client.get(reverse(USERS_PROFILE))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user_obj'].pk, self.user.pk)
        self.assertTemplateUsed(response, TEMPLATE_USER_PROFILE)

    def test_profile_requires_login(self):
        """CP-156 | HU-043 | ESCENARIO 7 | E | Sin autenticación -> redirige al login"""
        self.client.logout()
        response = self.client.get(reverse(USERS_PROFILE))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_PROFILE)}')


class UserProfileUpdateViewTest(TestCase):
    """HU-043 | ESCENARIO 2 | H | Actualizar nombre y teléfono"""

    def setUp(self):
        self.client = Client()
        self.user = _create_user(username='profile_user', first_name='Original')
        self.client.force_login(self.user)

    def test_get_profile_edit_form(self):
        """CP-157 | HU-043 | GET | Muestra formulario de edición de perfil"""
        response = self.client.get(reverse(USERS_PROFILE_EDIT))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_PROFILE_EDIT)

    def test_update_profile_valid(self):
        """CP-158 | HU-043 | ESCENARIO 2 | H | Actualizar nombre exitosamente"""
        data = {'first_name': 'NuevoNombre', 'last_name': 'NuevoApellido', 'email': self.user.email}
        response = self.client.post(reverse(USERS_PROFILE_EDIT), data=data)
        self.assertRedirects(response, reverse(USERS_PROFILE))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'NuevoNombre')


class UserProfilePasswordViewTest(TestCase):
    """HU-043 | ESCENARIO 3,4,5,6 | Cambiar contraseña desde perfil"""

    def setUp(self):
        self.client = Client()
        self.user = _create_user(username='profile_user', password='OldPass123!')
        self.client.force_login(self.user)

    def test_get_password_form(self):
        """CP-159 | HU-043 | GET | Muestra formulario de cambio de contraseña"""
        response = self.client.get(reverse(USERS_PROFILE_PASSWORD))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_USER_PROFILE_PASSWORD)

    def test_change_password_valid(self):
        """CP-160 | HU-043 | ESCENARIO 3 | H | Contraseña cambiada exitosamente"""
        data = {
            'current_password': 'OldPass123!', 
            'new_password1': 'NewComplex123!', 
            'new_password2': 'NewComplex123!'
        }
        response = self.client.post(reverse(USERS_PROFILE_PASSWORD), data=data)
        self.assertRedirects(response, reverse(USERS_PROFILE))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewComplex123!'))

    def test_change_password_keeps_session(self):
        """CP-160b | HU-043 | H | Cambiar contraseña mantiene la sesión activa"""
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

    def test_change_password_wrong_old(self):
        """CP-161 | HU-043 | ESCENARIO 4 | E | Contraseña actual incorrecta"""
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

    def test_change_password_weak(self):
        """CP-162 | HU-043 | ESCENARIO 5 | E | Nueva contraseña débil"""
        data = {'old_password': 'OldPass123!', 'new_password1': '123', 'new_password2': '123'}
        response = self.client.post(reverse(USERS_PROFILE_PASSWORD), data=data)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPass123!'))

    def test_change_password_mismatch(self):
        """CP-163 | HU-043 | ESCENARIO 6 | E | Nueva contraseña no coincide"""
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
        """Configuración a nivel de clase - se ejecuta una sola vez."""
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
        self.admin = _create_staff_user(username='admin')
        self.admin = _add_group_permissions(self.admin)
        self.client.force_login(self.admin)
        self.group1 = _create_group(name='Admin Group')
        self.group2 = _create_group(name='Delivery Group')

    def test_group_list_returns_200(self):
        """CP-164 | Group: Lista de grupos cargada exitosamente"""
        response = self.client.get(reverse(USERS_GROUP_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_GROUP_LIST)

    def test_group_list_includes_groups(self):
        """CP-165 | Group: Incluye todos los grupos"""
        response = self.client.get(reverse(USERS_GROUP_LIST))
        groups = list(response.context['groups'])
        self.assertIn(self.group1, groups)
        self.assertIn(self.group2, groups)

    def test_group_list_search(self):
        """CP-166 | Group: Búsqueda por nombre"""
        response = self.client.get(reverse(USERS_GROUP_LIST), {'search': 'Delivery'})
        groups = list(response.context['groups'])
        self.assertIn(self.group2, groups)
        self.assertNotIn(self.group1, groups)

    def test_group_list_context_headers(self):
        """CP-177 | Group: Incluye headers en contexto"""
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
        self.admin = _create_staff_user(username='admin')
        self.admin = _add_group_permissions(self.admin)
        self.client.force_login(self.admin)

    def test_get_create_form(self):
        """CP-167 | Group: Muestra formulario de creación"""
        response = self.client.get(reverse(USERS_GROUP_CREATE))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_GROUP_FORM)

    def test_create_valid_group(self):
        """CP-168 | Group: Grupo creado exitosamente"""
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
        self.admin = _create_staff_user(username='admin')
        self.admin = _add_group_permissions(self.admin)
        self.client.force_login(self.admin)
        self.group = _create_group(name='Original Group')

    def test_get_update_form(self):
        """CP-169 | Group: Muestra formulario de edición"""
        response = self.client.get(reverse(USERS_GROUP_EDIT, kwargs={'pk': self.group.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_GROUP_FORM)

    def test_update_valid_group(self):
        """CP-170 | Group: Grupo actualizado exitosamente"""
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
        self.admin = _create_staff_user(username='admin')
        self.admin = _add_group_permissions(self.admin)
        self.client.force_login(self.admin)
        self.group = _create_group(name='Detail Group')

    def test_detail_returns_200(self):
        """CP-171 | Group: Detalle de grupo cargado exitosamente"""
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
        self.admin = _create_staff_user(username='admin')
        self.admin = _add_group_permissions(self.admin)
        self.client.force_login(self.admin)
        self.group = _create_group(name='Delete Group')

    def test_get_delete_confirmation(self):
        """CP-172 | Group: Muestra pantalla de confirmación"""
        response = self.client.get(reverse(USERS_GROUP_DELETE, kwargs={'pk': self.group.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_GROUP_CONFIRM_DELETE)

    def test_delete_valid_group(self):
        """CP-173 | Group: Grupo eliminado exitosamente"""
        response = self.client.post(
            reverse(USERS_GROUP_DELETE, kwargs={'pk': self.group.pk}), 
            {'confirm': self.group.name}
        )
        self.assertRedirects(response, reverse(USERS_GROUP_LIST))
        self.assertFalse(Group.objects.filter(pk=self.group.pk).exists())

    def test_delete_group_with_users(self):
        """CP-174 | Group: Eliminar grupo que tiene usuarios asignados - debe mostrar error"""
        user = _create_user(username='member')
        user.groups.add(self.group)
        self.assertTrue(self.group.user_set.count() > 0)
        
        response = self.client.post(
            reverse(USERS_GROUP_DELETE, kwargs={'pk': self.group.pk}), 
            {'confirm': self.group.name}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Group.objects.filter(pk=self.group.pk).exists())
        
        # ✅ Verificar que el mensaje es ERROR_GROUP_DELETE
        messages_list = list(response.context.get('messages', []))
        self.assertTrue(
            any(ERROR_GROUP_DELETE.lower() in str(m.message).lower() for m in messages_list),
            f"Mensaje '{ERROR_GROUP_DELETE}' no encontrado. Mensajes: {[str(m.message) for m in messages_list]}"
        )

    def test_delete_requires_authentication(self):
        """CP-175a | Group: Usuario no autenticado -> login"""
        self.client.logout()
        response = self.client.get(reverse(USERS_GROUP_DELETE, kwargs={'pk': self.group.pk}))
        self.assertRedirects(
            response, 
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(USERS_GROUP_DELETE, kwargs={"pk": self.group.pk})}'
        )

    def test_delete_requires_permission(self):
        """CP-175b | Group: Usuario autenticado sin permiso -> catálogo"""
        normal_user = _create_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(USERS_GROUP_DELETE, kwargs={'pk': self.group.pk}))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_delete_nonexistent_group(self):
        """CP-176 | Group: Grupo no existe -> 404"""
        response = self.client.get(reverse(USERS_GROUP_DELETE, kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)