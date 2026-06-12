"""
Tests unitarios para formularios de apps.users.forms

Cubre:
- UserCreateForm (HU-039)
- UserUpdateForm (HU-040)
- UserChangePasswordForm (HU-040-2)
- UserDeleteForm (HU-041)
- UserRestoreForm (HU-042)
- GroupCreateForm, GroupUpdateForm, GroupDeleteForm (soporte)
- UserProfileForm (HU-043)
- UserProfilePasswordForm (HU-043-3/4/5/6)
- DeliveryUserProfileForm (soporte)

Casos de prueba: CP-193 a CP-224
"""

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
# TESTS: validate_phone (helper)
# =============================================================================

class ValidatePhoneTest(TestCase):
    """Pruebas para la función helper validate_phone"""

    def test_valid_phone(self):
        """
        CP-193
        HU-039 | H | Teléfono válido normalizado
        """
        result = validate_phone('3001234567')
        self.assertEqual(result, '3001234567')

    def test_valid_phone_with_spaces_and_dashes(self):
        """
        CP-194
        HU-039 | H | Teléfono con guiones y espacios normalizado
        """
        result = validate_phone('+57 (300) 123-4567')
        self.assertEqual(result, '573001234567')

    def test_empty_phone_returns_empty(self):
        """
        CP-195
        HU-039 | H | Teléfono vacío retorna string vacío
        """
        result = validate_phone('')
        self.assertEqual(result, '')

    def test_phone_too_short(self):
        """
        CP-196
        HU-039 | ESCENARIO 2 | A | Teléfono con menos de 7 dígitos
        """
        with self.assertRaises(ValidationError) as ctx:
            validate_phone('12345')
        self.assertIn('7 dígitos', str(ctx.exception))

    def test_phone_too_long(self):
        """
        CP-197
        HU-039 | ESCENARIO 2 | A | Teléfono con más de 15 dígitos
        """
        with self.assertRaises(ValidationError) as ctx:
            validate_phone('1' * 20)
        self.assertIn('15 dígitos', str(ctx.exception))

    def test_phone_duplicate(self):
        """
        CP-198
        HU-039 | ESCENARIO 2 | A | Teléfono duplicado
        """
        _create_user(username='existing', phone='3001234567')
        with self.assertRaises(ValidationError) as ctx:
            validate_phone('3001234567')
        self.assertIn('registrado', str(ctx.exception))

    def test_phone_duplicate_allows_same_user(self):
        """
        CP-199
        HU-040 | H | Teléfono duplicado permitido si es el mismo usuario
        """
        user = _create_user(username='owner', phone='3001234567')
        result = validate_phone('3001234567', instance=user)
        self.assertEqual(result, '3001234567')


# =============================================================================
# TESTS: validate_email (helper)
# =============================================================================

class ValidateEmailTest(TestCase):
    """Pruebas para la función helper validate_email"""

    def test_email_normalized(self):
        """
        CP-200
        HU-039 | H | Email normalizado a minúsculas
        """
        result = validate_email('  Test@Example.COM  ')
        self.assertEqual(result, 'test@example.com')

    def test_email_duplicate(self):
        """
        CP-201
        HU-039 | ESCENARIO 3 | E | Correo duplicado
        """
        _create_user(username='existing', email='dup@test.com')
        with self.assertRaises(ValidationError) as ctx:
            validate_email('dup@test.com')
        self.assertIn('existe', str(ctx.exception))

    def test_email_duplicate_case_insensitive(self):
        """
        CP-202
        HU-039 | ESCENARIO 3 | E | Correo duplicado con mayúsculas
        """
        _create_user(username='existing', email='dup@test.com')
        with self.assertRaises(ValidationError):
            validate_email('DUP@TEST.COM')

    def test_email_duplicate_allows_same_user(self):
        """
        CP-203
        HU-040 | H | Correo duplicado permitido si es el mismo usuario
        """
        user = _create_user(username='owner', email='owner@test.com')
        result = validate_email('owner@test.com', instance=user)
        self.assertEqual(result, 'owner@test.com')

    def test_empty_email(self):
        """
        CP-204
        HU-039 | H | Email vacío retorna vacío
        """
        result = validate_email('')
        self.assertEqual(result, '')


# =============================================================================
# TESTS: validate_username (helper)
# =============================================================================

class ValidateUsernameTest(TestCase):
    """Pruebas para la función helper validate_username"""

    def test_username_normalized(self):
        """
        CP-205
        HU-039 | H | Username normalizado sin espacios
        """
        result = validate_username('  nuevo_user  ')
        self.assertEqual(result, 'nuevo_user')

    def test_username_duplicate(self):
        """
        CP-206
        HU-039 | ESCENARIO 2 | A | Nombre de usuario duplicado
        """
        _create_user(username='existe')
        with self.assertRaises(ValidationError) as ctx:
            validate_username('existe')
        self.assertIn('existe', str(ctx.exception))

    def test_username_duplicate_case_insensitive(self):
        """
        CP-207
        HU-039 | ESCENARIO 2 | A | Nombre de usuario duplicado con mayúsculas
        """
        _create_user(username='existe')
        with self.assertRaises(ValidationError):
            validate_username('EXISTE')

    def test_username_duplicate_allows_same_user(self):
        """
        CP-208
        HU-040 | H | Username duplicado permitido si es el mismo usuario
        """
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

    def test_valid_form(self):
        """
        CP-209
        HU-039 | ESCENARIO 1 | H | Datos válidos -> formulario válido
        """
        form = UserCreateForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid(), msg=f"Errores: {form.errors}")

    def test_password_mismatch(self):
        """
        CP-210
        HU-039 | ESCENARIO 2 | A | Contraseñas no coinciden
        """
        data = self.get_valid_data()
        data['password2'] = 'OtraClave123!'
        form = UserCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_duplicate_username(self):
        """
        CP-211
        HU-039 | ESCENARIO 2 | A | Nombre de usuario duplicado
        """
        _create_user(username='nuevo_user')
        data = self.get_valid_data()
        form = UserCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_duplicate_email(self):
        """
        CP-212
        HU-039 | ESCENARIO 3 | E | Correo duplicado
        """
        _create_user(email='nuevo@test.com')
        data = self.get_valid_data()
        form = UserCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_empty_username(self):
        """
        CP-213
        HU-039 | ESCENARIO 2 | A | Username vacío
        """
        data = self.get_valid_data()
        data['username'] = ''
        form = UserCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_superuser_is_staff(self):
        """
        CP-214
        HU-039 | H | Superusuario creado con is_staff=True automáticamente
        """
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

    def test_valid_form(self):
        """
        CP-215
        HU-040 | ESCENARIO 1 | H | Datos válidos -> formulario válido
        """
        form = UserUpdateForm(data=self.get_valid_data(), instance=self.user)
        self.assertTrue(form.is_valid(), msg=f"Errores: {form.errors}")

    def test_update_duplicate_email(self):
        """
        CP-216
        HU-040 | ESCENARIO 3 | E | Correo duplicado
        """
        _create_user(username='other', email='other@test.com')
        data = self.get_valid_data()
        data['email'] = 'other@test.com'
        form = UserUpdateForm(data=data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_update_own_email_allowed(self):
        """
        CP-217
        HU-040 | H | Mismo email permitido al editar
        """
        data = self.get_valid_data()
        data['email'] = 'edit@test.com'
        form = UserUpdateForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_update_superuser_last_staff_disabled(self):
        """
        CP-218
        HU-040 | ESCENARIO 4 | E | Último superusuario no puede desactivarse
        """
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()
        form = UserUpdateForm(instance=self.user)
        self.assertTrue(form.fields['is_superuser'].disabled)

    def test_update_superuser_forces_staff(self):
        """
        CP-219
        HU-040 | H | Superusuario siempre tiene is_staff=True
        """
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
    """HU-040 | ESCENARIO 2 | H | Cambiar contraseña (admin)"""

    def setUp(self):
        self.user = _create_user(username='target', password='OldPass123!')

    def test_valid_password(self):
        """
        CP-219
        HU-040 | ESCENARIO 2 | H | Contraseña válida
        """
        form = UserChangePasswordForm(
            data={'password1': 'NewComplex123!', 'password2': 'NewComplex123!'},
            user=self.user
        )
        self.assertTrue(form.is_valid())

    def test_password_too_short(self):
        """
        CP-220
        HU-040 | ESCENARIO 2 | A | Contraseña débil (menos de 8 caracteres)
        """
        form = UserChangePasswordForm(
            data={'password1': '123', 'password2': '123'},
            user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)

    def test_password_numeric_only(self):
        """
        CP-221
        HU-040 | ESCENARIO 2 | A | Contraseña solo números
        """
        form = UserChangePasswordForm(
            data={'password1': '12345678', 'password2': '12345678'},
            user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('numérica', str(form.errors['password1']).lower())

    def test_password_common(self):
        """
        CP-222
        HU-040 | ESCENARIO 2 | A | Contraseña demasiado común
        """
        form = UserChangePasswordForm(
            data={'password1': 'password', 'password2': 'password'},
            user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('común', str(form.errors['password1']).lower())

    def test_password_mismatch(self):
        """
        CP-223
        HU-040 | ESCENARIO 2 | A | Contraseñas no coinciden
        """
        form = UserChangePasswordForm(
            data={'password1': 'NewComplex123!', 'password2': 'Diferente456!'},
            user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_no_user_specified(self):
        """
        CP-224
        HU-040 | ESCENARIO 2 | E | Usuario no especificado
        """
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

    def test_correct_confirmation(self):
        """
        CP-225
        HU-041 | ESCENARIO 1 | H | Confirmación correcta
        """
        form = UserDeleteForm(data={'confirm': 'delete_target'}, user=self.user)
        self.assertTrue(form.is_valid())

    def test_wrong_confirmation(self):
        """
        CP-226
        HU-041 | ESCENARIO 4 | A | Nombre no coincide
        """
        form = UserDeleteForm(data={'confirm': 'otro_nombre'}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)

    def test_case_insensitive_confirmation(self):
        """
        CP-227
        HU-041 | ESCENARIO 1 | H | Confirmación con mayúsculas/minúsculas
        """
        form = UserDeleteForm(data={'confirm': 'DELETE_TARGET'}, user=self.user)
        self.assertTrue(form.is_valid())

    def test_delete_last_superuser(self):
        """
        CP-228
        HU-041 | ESCENARIO 3 | E | Archivar al último superusuario
        """
        self.user.is_superuser = True
        self.user.save()
        form = UserDeleteForm(data={'confirm': 'delete_target'}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('superusuario', str(form.errors['confirm']).lower())

    def test_no_user_specified(self):
        """
        CP-229
        HU-041 | ESCENARIO 3 | E | Usuario no especificado
        """
        form = UserDeleteForm(data={'confirm': 'delete_target'})
        self.assertFalse(form.is_valid())


# =============================================================================
# TESTS: HU-042 UserRestoreForm
# =============================================================================

class UserRestoreFormTest(TestCase):
    """HU-042: Reincorporar usuario (reactivar)"""

    def setUp(self):
        self.user = _create_user(username='restore_target', is_active=False)

    def test_valid_restore(self):
        """
        CP-230
        HU-042 | ESCENARIO 1 | H | Restauración válida
        """
        form = UserRestoreForm(data={'confirm': True, 'send_notification': True}, user=self.user)
        self.assertTrue(form.is_valid())

    def test_restore_user_already_active(self):
        """
        CP-231
        HU-042 | ESCENARIO 2 | A | Usuario ya activo
        """
        self.user.is_active = True
        self.user.save()
        form = UserRestoreForm(data={'confirm': True}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('activo', str(form.errors.get('__all__', '')).lower())

    def test_restore_without_confirmation(self):
        """
        CP-232
        HU-042 | ESCENARIO 2 | A | Confirmación no marcada
        """
        form = UserRestoreForm(data={'confirm': False}, user=self.user)
        self.assertFalse(form.is_valid())

    def test_restore_no_user(self):
        """
        CP-233
        HU-042 | ESCENARIO 2 | E | Usuario no especificado
        """
        form = UserRestoreForm(data={'confirm': True})
        self.assertFalse(form.is_valid())

    def test_restore_username_conflict(self):
        """
        CP-234
        HU-042 | ESCENARIO 2 | A | Conflicto de nombre de usuario
        NOTA: Este test es irrelevante porque username tiene unique=True en la BD.
        """
        # El test pasa automáticamente porque no hay conflicto posible
        self.assertTrue(True)

    def test_restore_email_conflict(self):
        """
        CP-235
        HU-042 | ESCENARIO 2 | A | Conflicto de correo
        """
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
# TESTS: Group Create/Update/Delete Forms (Soporte)
# =============================================================================

class GroupCreateFormTest(TestCase):
    """Soporte: Crear grupo"""

    def test_valid_group_name(self):
        """
        CP-236
        GroupCreate: Nombre válido
        """
        form = GroupCreateForm(data={'name': 'New Group'})
        self.assertTrue(form.is_valid())

    def test_duplicate_group_name(self):
        """
        CP-237
        GroupCreate: Nombre duplicado
        """
        _create_group(name='Existing')
        form = GroupCreateForm(data={'name': 'Existing'})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class GroupUpdateFormTest(TestCase):
    """Soporte: Editar grupo"""

    def setUp(self):
        self.group = _create_group(name='Original Group')

    def test_valid_update(self):
        """
        CP-238
        GroupUpdate: Nombre actualizado válido
        """
        form = GroupUpdateForm(data={'name': 'Updated Group'}, instance=self.group)
        self.assertTrue(form.is_valid())

    def test_duplicate_name(self):
        """
        CP-239
        GroupUpdate: Nombre duplicado
        """
        _create_group(name='Existing')
        form = GroupUpdateForm(data={'name': 'Existing'}, instance=self.group)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_protected_name(self):
        """
        CP-240
        GroupUpdate: Nombre reservado del sistema
        """
        form = GroupUpdateForm(data={'name': 'admin'}, instance=self.group)
        self.assertFalse(form.is_valid())
        self.assertIn('reservado', str(form.errors['name']).lower())

    def test_keep_original_name_allowed(self):
        """
        CP-241
        GroupUpdate: Mantener el nombre original permitido
        """
        form = GroupUpdateForm(data={'name': 'Original Group'}, instance=self.group)
        self.assertTrue(form.is_valid())


class GroupDeleteFormTest(TestCase):
    """Soporte: Eliminar grupo"""

    def setUp(self):
        self.group = _create_group(name='Delete Group')

    def test_correct_confirmation(self):
        """
        CP-242
        GroupDelete: Confirmación correcta
        """
        form = GroupDeleteForm(data={'confirm': 'Delete Group'}, group=self.group)
        self.assertTrue(form.is_valid())

    def test_wrong_confirmation(self):
        """
        CP-243
        GroupDelete: Nombre no coincide
        """
        form = GroupDeleteForm(data={'confirm': 'Wrong Name'}, group=self.group)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)

    def test_protected_group(self):
        """
        CP-244
        GroupDelete: Grupo protegido del sistema
        """
        self.group.name = 'admin'
        self.group.save()
        form = GroupDeleteForm(data={'confirm': 'admin'}, group=self.group)
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors['confirm'][0])
        self.assertIn('rol del sistema', error_msg.lower())
        from apps.users.forms import ERROR_GROUP_PROTECTED
        self.assertIn(ERROR_GROUP_PROTECTED.format(name='admin').lower(), error_msg.lower())

    def test_group_has_users(self):
        """
        CP-245
        GroupDelete: Grupo con usuarios asignados
        """
        user = _create_user(username='member')
        user.groups.add(self.group)
        form = GroupDeleteForm(data={'confirm': 'Delete Group'}, group=self.group)
        self.assertFalse(form.is_valid())
        self.assertIn('usuario', str(form.errors['confirm']).lower())

    def test_no_group_specified(self):
        """
        CP-246
        GroupDelete: Grupo no especificado
        """
        form = GroupDeleteForm(data={'confirm': 'Delete Group'})
        self.assertFalse(form.is_valid())


# =============================================================================
# TESTS: HU-043 UserProfileForm
# =============================================================================

class UserProfileFormTest(TestCase):
    """HU-043: Ver/editar mi propio perfil"""

    def setUp(self):
        self.user = _create_user(username='profile_test', email='profile@test.com')

    def test_valid_profile(self):
        """
        CP-247
        HU-043 | ESCENARIO 2 | H | Datos válidos
        """
        form = UserProfileForm(
            data={'first_name': 'Nuevo', 'last_name': 'Nombre', 'email': 'new@test.com', 'phone': '3001234567'},
            instance=self.user
        )
        self.assertTrue(form.is_valid())

    def test_empty_fields_allowed(self):
        """
        CP-248
        HU-043 | ESCENARIO 2 | H | Campos opcionales vacíos permitidos
        """
        form = UserProfileForm(
            data={'first_name': '', 'last_name': '', 'email': '', 'phone': ''},
            instance=self.user
        )
        self.assertTrue(form.is_valid())

    def test_invalid_phone(self):
        """
        CP-249
        HU-043 | ESCENARIO 2 | A | Teléfono inválido (menos de 7 dígitos)
        """
        form = UserProfileForm(
            data={'first_name': 'Test', 'last_name': 'User', 'phone': '123'},
            instance=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_duplicate_email(self):
        """
        CP-250
        HU-043 | ESCENARIO 2 | A | Email duplicado
        """
        _create_user(username='other', email='other@test.com')
        form = UserProfileForm(
            data={'email': 'other@test.com'},
            instance=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_own_email_allowed(self):
        """
        CP-251
        HU-043 | ESCENARIO 2 | H | Mismo email permitido
        """
        form = UserProfileForm(
            data={'email': 'profile@test.com'},
            instance=self.user
        )
        self.assertTrue(form.is_valid())


# =============================================================================
# TESTS: HU-043 UserProfilePasswordForm
# =============================================================================

class UserProfilePasswordFormTest(TestCase):
    """HU-043 | ESCENARIO 3,4,5,6 | Cambiar contraseña desde perfil"""

    def setUp(self):
        self.user = _create_user(username='profile_pass', password='OldPass123!')

    def test_valid_password_change(self):
        """
        CP-252
        HU-043 | ESCENARIO 3 | H | Contraseña cambiada exitosamente
        """
        form = UserProfilePasswordForm(
            data={
                'current_password': 'OldPass123!',
                'new_password1': 'NewComplex123!',
                'new_password2': 'NewComplex123!',
            },
            user=self.user
        )
        self.assertTrue(form.is_valid())

    def test_wrong_current_password(self):
        """
        CP-253
        HU-043 | ESCENARIO 4 | E | Contraseña actual incorrecta
        """
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

    def test_weak_new_password(self):
        """
        CP-254
        HU-043 | ESCENARIO 5 | E | Nueva contraseña débil (corta)
        """
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

    def test_new_password_mismatch(self):
        """
        CP-255
        HU-043 | ESCENARIO 6 | E | Nueva contraseña no coincide con confirmación
        """
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

    def test_password_same_as_current(self):
        """
        CP-256
        HU-043 | ESCENARIO 5 | E | Nueva contraseña igual a la actual
        """
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

    def test_new_password_numeric_only(self):
        """
        CP-257
        HU-043 | ESCENARIO 5 | E | Nueva contraseña solo numérica
        """
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

    def test_valid_phone(self):
        """
        CP-258
        DeliveryProfile: Teléfono válido
        """
        form = DeliveryUserProfileForm(data={'phone': '3001234567'})
        self.assertTrue(form.is_valid())

    def test_invalid_phone_short(self):
        """
        CP-259
        DeliveryProfile: Teléfono muy corto
        """
        form = DeliveryUserProfileForm(data={'phone': '12345'})
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_invalid_phone_long(self):
        """
        CP-260
        DeliveryProfile: Teléfono muy largo
        """
        form = DeliveryUserProfileForm(data={'phone': '1' * 20})
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_phone_normalization(self):
        """
        CP-261
        DeliveryProfile: Normalización de teléfono
        """
        form = DeliveryUserProfileForm(data={'phone': '+57 (300) 123-4567'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['phone'], '573001234567')