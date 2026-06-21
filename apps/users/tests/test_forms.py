from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as AuthGroup
from django.core.exceptions import ValidationError

from apps.users.forms import (
    UserCreateForm,
    UserUpdateForm,
    UserChangePasswordForm,
    UserDeleteForm,
    UserRestoreForm,
    GroupCreateForm,
    GroupUpdateForm,
    GroupDeleteForm,
    UserProfileForm,
    UserProfilePasswordForm,
    DeliveryUserProfileForm,
    validate_phone,
    validate_email,
    validate_username,
)

User = get_user_model()


# =============================================================================
# HELPERS
# =============================================================================

def _create_user(**kwargs):
    defaults = {'username': 'testuser', 'password': 'pass1234'}
    defaults.update(kwargs)
    password = defaults.pop('password')
    is_delivery = defaults.pop('is_delivery', False)
    user = User(**defaults)
    user.set_password(password)
    user.save()
    if is_delivery and hasattr(user, 'is_delivery'):
        user.is_delivery = True
        user.save()
    return user


def _create_group(name='Test Group'):
    from apps.users.models import Group
    return Group.objects.create(name=name)


# =============================================================================
# TESTS: validate_phone (Helper)
# =============================================================================

class ValidatePhoneTest(TestCase):
    """Pruebas para la función helper validate_phone"""

    # UT-447: HU-039 - Teléfono válido normalizado
    def test_valid_phone(self):
        result = validate_phone('3001234567')
        self.assertEqual(result, '3001234567')

    # UT-448: HU-039 - Teléfono con guiones y espacios normalizado
    def test_valid_phone_with_spaces_and_dashes(self):
        result = validate_phone('+57 (300) 123-4567')
        self.assertEqual(result, '573001234567')

    # UT-449: HU-039 - Teléfono vacío retorna string vacío
    def test_empty_phone_returns_empty(self):
        result = validate_phone('')
        self.assertEqual(result, '')

    # UT-450: HU-039 CA-002 - Teléfono con menos de 7 dígitos
    def test_phone_too_short(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_phone('12345')
        self.assertIn('7 dígitos', str(ctx.exception))

    # UT-451: HU-039 CA-002 - Teléfono con más de 15 dígitos
    def test_phone_too_long(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_phone('1' * 20)
        self.assertIn('15 dígitos', str(ctx.exception))

    # UT-452: HU-039 CA-002 - Teléfono duplicado
    def test_phone_duplicate(self):
        _create_user(username='existing', phone='3001234567')
        with self.assertRaises(ValidationError) as ctx:
            validate_phone('3001234567')
        self.assertIn('registrado', str(ctx.exception))

    # UT-453: HU-040 - Teléfono duplicado permitido si es el mismo usuario
    def test_phone_duplicate_allows_same_user(self):
        user = _create_user(username='owner', phone='3001234567')
        result = validate_phone('3001234567', instance=user)
        self.assertEqual(result, '3001234567')


# =============================================================================
# TESTS: validate_email (Helper)
# =============================================================================

class ValidateEmailTest(TestCase):
    """Pruebas para la función helper validate_email"""

    # UT-454: HU-039 - Email normalizado a minúsculas
    def test_email_normalized(self):
        result = validate_email('  Test@Example.COM  ')
        self.assertEqual(result, 'test@example.com')

    # UT-455: HU-039 CA-003 - Correo duplicado
    def test_email_duplicate(self):
        _create_user(username='existing', email='dup@test.com')
        with self.assertRaises(ValidationError) as ctx:
            validate_email('dup@test.com')
        self.assertIn('existe', str(ctx.exception))

    # UT-456: HU-039 CA-003 - Correo duplicado con mayúsculas
    def test_email_duplicate_case_insensitive(self):
        _create_user(username='existing', email='dup@test.com')
        with self.assertRaises(ValidationError):
            validate_email('DUP@TEST.COM')

    # UT-457: HU-040 - Correo duplicado permitido si es el mismo usuario
    def test_email_duplicate_allows_same_user(self):
        user = _create_user(username='owner', email='owner@test.com')
        result = validate_email('owner@test.com', instance=user)
        self.assertEqual(result, 'owner@test.com')

    # UT-458: HU-039 - Email vacío retorna vacío
    def test_empty_email(self):
        result = validate_email('')
        self.assertEqual(result, '')


# =============================================================================
# TESTS: validate_username (Helper)
# =============================================================================

class ValidateUsernameTest(TestCase):
    """Pruebas para la función helper validate_username"""

    # UT-459: HU-039 - Username normalizado sin espacios
    def test_username_normalized(self):
        result = validate_username('  nuevo_user  ')
        self.assertEqual(result, 'nuevo_user')

    # UT-460: HU-039 CA-002 - Nombre de usuario duplicado
    def test_username_duplicate(self):
        _create_user(username='existe')
        with self.assertRaises(ValidationError) as ctx:
            validate_username('existe')
        self.assertIn('existe', str(ctx.exception))

    # UT-461: HU-039 CA-002 - Nombre de usuario duplicado con mayúsculas
    def test_username_duplicate_case_insensitive(self):
        _create_user(username='existe')
        with self.assertRaises(ValidationError):
            validate_username('EXISTE')

    # UT-462: HU-040 - Username duplicado permitido si es el mismo usuario
    def test_username_duplicate_allows_same_user(self):
        user = _create_user(username='owner')
        result = validate_username('owner', instance=user)
        self.assertEqual(result, 'owner')


# =============================================================================
# TESTS: HU-039 UserCreateForm
# =============================================================================

class UserCreateFormTest(TestCase):
    """HU-039: Crear usuario (admin)"""

    def get_valid_data(self):
        return {
            'username': 'nuevo_user',
            'email': 'nuevo@test.com',
            'first_name': 'Nuevo',
            'last_name': 'Usuario',
            'password1': 'Compleja123!',
            'password2': 'Compleja123!',
            'is_delivery': True,
        }

    # UT-463: HU-039 CA-001 - Datos válidos formulario válido
    def test_valid_form(self):
        form = UserCreateForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid())

    # UT-464: HU-039 CA-002 - Contraseñas no coinciden
    def test_password_mismatch(self):
        data = self.get_valid_data()
        data['password2'] = 'OtraClave123!'
        form = UserCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    # UT-465: HU-039 CA-002 - Nombre de usuario duplicado
    def test_duplicate_username(self):
        _create_user(username='nuevo_user')
        data = self.get_valid_data()
        form = UserCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    # UT-466: HU-039 CA-003 - Correo duplicado
    def test_duplicate_email(self):
        _create_user(email='nuevo@test.com')
        data = self.get_valid_data()
        form = UserCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    # UT-467: HU-039 CA-002 - Username vacío
    def test_empty_username(self):
        data = self.get_valid_data()
        data['username'] = ''
        form = UserCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    # UT-468: HU-039 - Superusuario creado con is_staff=True automáticamente
    def test_superuser_is_staff(self):
        data = self.get_valid_data()
        data['is_superuser'] = True
        data['is_staff'] = False
        form = UserCreateForm(data=data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


# =============================================================================
# TESTS: HU-040 UserUpdateForm
# =============================================================================

class UserUpdateFormTest(TestCase):
    """HU-040: Editar usuario (admin)"""

    def setUp(self):
        self.user = _create_user(username='edit_user', email='edit@test.com', first_name='Original')

    def get_valid_data(self):
        return {
            'username': 'edit_user_updated',
            'email': 'edit_updated@test.com',
            'first_name': 'Actualizado',
            'last_name': 'User',
            'is_delivery': False,
        }

    # UT-469: HU-040 CA-001 - Datos válidos formulario válido
    def test_valid_form(self):
        form = UserUpdateForm(data=self.get_valid_data(), instance=self.user)
        self.assertTrue(form.is_valid())

    # UT-470: HU-040 CA-003 - Correo duplicado da error
    def test_update_duplicate_email(self):
        _create_user(username='other', email='other@test.com')
        data = self.get_valid_data()
        data['email'] = 'other@test.com'
        form = UserUpdateForm(data=data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    # UT-471: HU-040 - Mismo email permitido al editar
    def test_update_own_email_allowed(self):
        data = self.get_valid_data()
        data['email'] = 'edit@test.com'
        form = UserUpdateForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid())

    # UT-472: HU-040 CA-004 - Último superusuario no puede desactivarse
    def test_update_superuser_last_staff_disabled(self):
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()
        form = UserUpdateForm(instance=self.user)
        self.assertTrue(form.fields['is_superuser'].disabled)

    # UT-473: HU-040 - Superusuario siempre tiene is_staff=True
    def test_update_superuser_forces_staff(self):
        data = self.get_valid_data()
        data['is_superuser'] = True
        data['is_staff'] = False
        form = UserUpdateForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.is_staff)


# =============================================================================
# TESTS: HU-040 UserChangePasswordForm
# =============================================================================

class UserChangePasswordFormTest(TestCase):
    """HU-040 CA-002: Cambiar contraseña (admin)"""

    def setUp(self):
        self.user = _create_user(username='target', password='OldPass123!')

    # UT-474: HU-040 CA-002 - Contraseña válida
    def test_valid_password(self):
        form = UserChangePasswordForm(
            data={'password1': 'NewComplex123!', 'password2': 'NewComplex123!'},
            user=self.user
        )
        self.assertTrue(form.is_valid())

    # UT-475: HU-040 CA-002 - Contraseña débil (menos de 8 caracteres)
    def test_password_too_short(self):
        form = UserChangePasswordForm(
            data={'password1': '123', 'password2': '123'},
            user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)

    # UT-476: HU-040 CA-002 - Contraseña solo números
    def test_password_numeric_only(self):
        form = UserChangePasswordForm(
            data={'password1': '12345678', 'password2': '12345678'},
            user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('numérica', str(form.errors['password1']).lower())

    # UT-477: HU-040 CA-002 - Contraseña demasiado común
    def test_password_common(self):
        form = UserChangePasswordForm(
            data={'password1': 'password', 'password2': 'password'},
            user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('común', str(form.errors['password1']).lower())

    # UT-478: HU-040 CA-002 - Contraseñas no coinciden
    def test_password_mismatch(self):
        form = UserChangePasswordForm(
            data={'password1': 'NewComplex123!', 'password2': 'Diferente456!'},
            user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    # UT-479: HU-040 CA-002 - Usuario no especificado da error
    def test_no_user_specified(self):
        form = UserChangePasswordForm(
            data={'password1': 'NewComplex123!', 'password2': 'NewComplex123!'}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('Usuario no especificado', str(form.errors))


# =============================================================================
# TESTS: HU-041 UserDeleteForm
# =============================================================================

class UserDeleteFormTest(TestCase):
    """HU-041: Archivar usuario (soft delete)"""

    def setUp(self):
        self.user = _create_user(username='delete_target')

    # UT-480: HU-041 CA-001 - Confirmación correcta
    def test_correct_confirmation(self):
        form = UserDeleteForm(data={'confirm': 'delete_target'}, user=self.user)
        self.assertTrue(form.is_valid())

    # UT-481: HU-041 CA-002 - Nombre no coincide
    def test_wrong_confirmation(self):
        form = UserDeleteForm(data={'confirm': 'otro_nombre'}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)

    # UT-482: HU-041 CA-001 - Confirmación con mayúsculas/minúsculas
    def test_case_insensitive_confirmation(self):
        form = UserDeleteForm(data={'confirm': 'DELETE_TARGET'}, user=self.user)
        self.assertTrue(form.is_valid())

    # UT-483: HU-041 CA-003 - Archivar al último superusuario da error
    def test_delete_last_superuser(self):
        self.user.is_superuser = True
        self.user.save()
        form = UserDeleteForm(data={'confirm': 'delete_target'}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('superusuario', str(form.errors['confirm']).lower())

    # UT-484: HU-041 CA-003 - Usuario no especificado da error
    def test_no_user_specified(self):
        form = UserDeleteForm(data={'confirm': 'delete_target'})
        self.assertFalse(form.is_valid())


# =============================================================================
# TESTS: HU-042 UserRestoreForm
# =============================================================================

class UserRestoreFormTest(TestCase):
    """HU-042: Reincorporar usuario (reactivar)"""

    def setUp(self):
        self.user = _create_user(username='restore_target', is_active=False)

    # UT-485: HU-042 CA-001 - Restauración válida
    def test_valid_restore(self):
        form = UserRestoreForm(data={'confirm': True, 'send_notification': True}, user=self.user)
        self.assertTrue(form.is_valid())

    # UT-486: HU-042 CA-002 - Usuario ya activo da error
    def test_restore_user_already_active(self):
        self.user.is_active = True
        self.user.save()
        form = UserRestoreForm(data={'confirm': True}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('activo', str(form.errors.get('__all__', '')).lower())

    # UT-487: HU-042 CA-002 - Confirmación no marcada da error
    def test_restore_without_confirmation(self):
        form = UserRestoreForm(data={'confirm': False}, user=self.user)
        self.assertFalse(form.is_valid())

    # UT-488: HU-042 CA-002 - Usuario no especificado da error
    def test_restore_no_user(self):
        form = UserRestoreForm(data={'confirm': True})
        self.assertFalse(form.is_valid())

    # UT-489: HU-042 CA-002 - Conflicto de correo da error
    def test_restore_email_conflict(self):
        self.user.email = 'dup@test.com'
        self.user.save()
        _create_user(username='other', email='dup@test.com', is_active=True)
        form = UserRestoreForm(data={'confirm': True}, user=self.user)
        self.assertFalse(form.is_valid())
        errors_str = str(form.errors.get('__all__', ''))
        self.assertTrue(
            any(term in errors_str.lower() for term in ['correo', 'email']),
            f"Error de email no encontrado. Errores: {form.errors}"
        )


# =============================================================================
# TESTS: Group Forms (Soporte)
# =============================================================================

class GroupCreateFormTest(TestCase):
    """Soporte: Crear grupo"""

    # UT-490: GroupCreate - Nombre válido
    def test_valid_group_name(self):
        form = GroupCreateForm(data={'name': 'New Group'})
        self.assertTrue(form.is_valid())

    # UT-491: GroupCreate - Nombre duplicado da error
    def test_duplicate_group_name(self):
        _create_group(name='Existing')
        form = GroupCreateForm(data={'name': 'Existing'})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class GroupUpdateFormTest(TestCase):
    """Soporte: Editar grupo"""

    def setUp(self):
        self.group = _create_group(name='Original Group')

    # UT-492: GroupUpdate - Nombre actualizado válido
    def test_valid_update(self):
        form = GroupUpdateForm(data={'name': 'Updated Group'}, instance=self.group)
        self.assertTrue(form.is_valid())

    # UT-493: GroupUpdate - Nombre duplicado da error
    def test_duplicate_name(self):
        _create_group(name='Existing')
        form = GroupUpdateForm(data={'name': 'Existing'}, instance=self.group)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    # UT-494: GroupUpdate - Nombre reservado del sistema da error
    def test_protected_name(self):
        form = GroupUpdateForm(data={'name': 'admin'}, instance=self.group)
        self.assertFalse(form.is_valid())
        self.assertIn('reservado', str(form.errors['name']).lower())

    # UT-495: GroupUpdate - Mantener el nombre original permitido
    def test_keep_original_name_allowed(self):
        form = GroupUpdateForm(data={'name': 'Original Group'}, instance=self.group)
        self.assertTrue(form.is_valid())


class GroupDeleteFormTest(TestCase):
    """Soporte: Eliminar grupo"""

    def setUp(self):
        self.group = _create_group(name='Delete Group')

    # UT-496: GroupDelete - Confirmación correcta
    def test_correct_confirmation(self):
        form = GroupDeleteForm(data={'confirm': 'Delete Group'}, group=self.group)
        self.assertTrue(form.is_valid())

    # UT-497: GroupDelete - Nombre no coincide da error
    def test_wrong_confirmation(self):
        form = GroupDeleteForm(data={'confirm': 'Wrong Name'}, group=self.group)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)

    # UT-498: GroupDelete - Grupo protegido del sistema da error
    def test_protected_group(self):
        self.group.name = 'admin'
        self.group.save()
        form = GroupDeleteForm(data={'confirm': 'admin'}, group=self.group)
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors['confirm'][0])
        self.assertIn('rol del sistema', error_msg.lower())

    # UT-499: GroupDelete - Grupo con usuarios asignados da error
    def test_group_has_users(self):
        user = _create_user(username='member')
        user.groups.add(self.group)
        form = GroupDeleteForm(data={'confirm': 'Delete Group'}, group=self.group)
        self.assertFalse(form.is_valid())
        self.assertIn('usuario', str(form.errors['confirm']).lower())

    # UT-500: GroupDelete - Grupo no especificado da error
    def test_no_group_specified(self):
        form = GroupDeleteForm(data={'confirm': 'Delete Group'})
        self.assertFalse(form.is_valid())


# =============================================================================
# TESTS: HU-043 UserProfileForm
# =============================================================================

class UserProfileFormTest(TestCase):
    """HU-043: Ver/editar mi propio perfil"""

    def setUp(self):
        self.user = _create_user(username='profile_test', email='profile@test.com')

    # UT-501: HU-043 CA-002 - Datos válidos
    def test_valid_profile(self):
        form = UserProfileForm(
            data={'first_name': 'Nuevo', 'last_name': 'Nombre', 'email': 'new@test.com', 'phone': '3001234567'},
            instance=self.user
        )
        self.assertTrue(form.is_valid())

    # UT-502: HU-043 CA-002 - Campos opcionales vacíos permitidos
    def test_empty_fields_allowed(self):
        form = UserProfileForm(
            data={'first_name': '', 'last_name': '', 'email': '', 'phone': ''},
            instance=self.user
        )
        self.assertTrue(form.is_valid())

    # UT-503: HU-043 CA-002 - Teléfono inválido da error
    def test_invalid_phone(self):
        form = UserProfileForm(
            data={'first_name': 'Test', 'last_name': 'User', 'phone': '123'},
            instance=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    # UT-504: HU-043 CA-002 - Email duplicado da error
    def test_duplicate_email(self):
        _create_user(username='other', email='other@test.com')
        form = UserProfileForm(
            data={'email': 'other@test.com'},
            instance=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    # UT-505: HU-043 CA-002 - Mismo email permitido
    def test_own_email_allowed(self):
        form = UserProfileForm(
            data={'email': 'profile@test.com'},
            instance=self.user
        )
        self.assertTrue(form.is_valid())


# =============================================================================
# TESTS: HU-043 UserProfilePasswordForm
# =============================================================================

class UserProfilePasswordFormTest(TestCase):
    """HU-043 CA-003/004/005/006: Cambiar contraseña desde perfil"""

    def setUp(self):
        self.user = _create_user(username='profile_pass', password='OldPass123!')

    # UT-506: HU-043 CA-003 - Contraseña cambiada exitosamente
    def test_valid_password_change(self):
        form = UserProfilePasswordForm(
            data={
                'current_password': 'OldPass123!',
                'new_password1': 'NewComplex123!',
                'new_password2': 'NewComplex123!',
            },
            user=self.user
        )
        self.assertTrue(form.is_valid())

    # UT-507: HU-043 CA-004 - Contraseña actual incorrecta da error
    def test_wrong_current_password(self):
        form = UserProfilePasswordForm(
            data={
                'current_password': 'WrongOldPass!',
                'new_password1': 'NewComplex123!',
                'new_password2': 'NewComplex123!',
            },
            user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('current_password', form.errors)

    # UT-508: HU-043 CA-005 - Nueva contraseña débil da error
    def test_weak_new_password(self):
        form = UserProfilePasswordForm(
            data={
                'current_password': 'OldPass123!',
                'new_password1': '123',
                'new_password2': '123',
            },
            user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('new_password1', form.errors)

    # UT-509: HU-043 CA-006 - Nueva contraseña no coincide con confirmación
    def test_new_password_mismatch(self):
        form = UserProfilePasswordForm(
            data={
                'current_password': 'OldPass123!',
                'new_password1': 'NewComplex123!',
                'new_password2': 'Different456!',
            },
            user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('new_password2', form.errors)

    # UT-510: HU-043 CA-005 - Nueva contraseña igual a la actual da error
    def test_password_same_as_current(self):
        form = UserProfilePasswordForm(
            data={
                'current_password': 'OldPass123!',
                'new_password1': 'OldPass123!',
                'new_password2': 'OldPass123!',
            },
            user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('new_password1', form.errors)

    # UT-511: HU-043 CA-005 - Nueva contraseña solo numérica da error
    def test_new_password_numeric_only(self):
        form = UserProfilePasswordForm(
            data={
                'current_password': 'OldPass123!',
                'new_password1': '12345678',
                'new_password2': '12345678',
            },
            user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('numérica', str(form.errors['new_password1']).lower())


# =============================================================================
# TESTS: DeliveryUserProfileForm (Soporte)
# =============================================================================

class DeliveryUserProfileFormTest(TestCase):
    """Soporte: Formulario para entregadores"""

    # UT-512: DeliveryProfile - Teléfono válido
    def test_valid_phone(self):
        form = DeliveryUserProfileForm(data={'phone': '3001234567'})
        self.assertTrue(form.is_valid())

    # UT-513: DeliveryProfile - Teléfono muy corto da error
    def test_invalid_phone_short(self):
        form = DeliveryUserProfileForm(data={'phone': '12345'})
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    # UT-514: DeliveryProfile - Teléfono muy largo da error
    def test_invalid_phone_long(self):
        form = DeliveryUserProfileForm(data={'phone': '1' * 20})
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    # UT-515: DeliveryProfile - Normalización de teléfono
    def test_phone_normalization(self):
        form = DeliveryUserProfileForm(data={'phone': '+57 (300) 123-4567'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['phone'], '573001234567')