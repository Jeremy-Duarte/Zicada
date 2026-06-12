"""
Tests unitarios para modelos de apps.users.models

Cubre:
- HU-038/039/040/041/042/043: User (AbstractUser extendido)
- Group (proxy para roles)

Casos de prueba: CP-178 a CP-190
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as AuthGroup

from apps.users.models import Group

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


# =============================================================================
# TESTS: User Model
# =============================================================================

class UserModelTest(TestCase):
    """
    HU-038: Listar usuarios (admin)
    HU-039: Crear usuario (admin)
    HU-040: Editar usuario (admin)
    HU-041: Archivar usuario (admin)
    HU-042: Reincorporar usuario (admin)
    HU-043: Ver/editar mi propio perfil
    """

    def setUp(self):
        self.user = _create_user(
            username='juanperez',
            first_name='Juan',
            last_name='Perez',
            email='juan@example.com',
            phone='3001234567',
        )

    def test_create_user_with_all_fields(self):
        """
        CP-178
        HU-039 | ESCENARIO 1 | H | Creación de usuario con todos los campos
        """
        self.assertEqual(self.user.username, 'juanperez')
        self.assertEqual(self.user.first_name, 'Juan')
        self.assertEqual(self.user.last_name, 'Perez')
        self.assertEqual(self.user.email, 'juan@example.com')
        self.assertEqual(self.user.phone, '3001234567')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_delivery)

    def test_create_user_minimal_fields(self):
        """
        CP-179
        HU-039 | ESCENARIO 1 | H | Creación de usuario solo con campos obligatorios
        """
        user = User.objects.create_user(username='minimal', password='pass1234')
        self.assertEqual(user.username, 'minimal')
        self.assertEqual(user.phone, '')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_delivery)

    def test_create_delivery_user(self):
        """
        CP-180
        HU-039 | ESCENARIO 1 | H | Creación de usuario con rol de entregador
        """
        delivery = _create_user(username='delivery1', is_delivery=True)
        self.assertTrue(delivery.is_delivery)

    def test_user_str_with_full_name(self):
        """
        CP-181
        HU-038 | ESCENARIO 1 | H | __str__ retorna nombre completo cuando existe
        HU-043 | ESCENARIO 2 | H | Obtiene nombre completo para perfil
        """
        self.assertEqual(str(self.user), 'Juan Perez')

    def test_user_str_without_full_name(self):
        """
        CP-182
        HU-038 | ESCENARIO 1 | H | __str__ retorna username cuando no hay nombre
        """
        user = _create_user(username='solo_username')
        self.assertEqual(str(user), 'solo_username')

    def test_get_full_name_with_both_names(self):
        """
        CP-183
        HU-038 | ESCENARIO 1 | H | get_full_name retorna nombre y apellido
        """
        self.assertEqual(self.user.get_full_name(), 'Juan Perez')

    def test_get_full_name_without_last_name(self):
        """
        CP-184
        HU-038 | ESCENARIO 1 | H | get_full_name retorna username si faltan nombres
        """
        user = _create_user(username='onlyfirst', first_name='Only')
        self.assertEqual(user.get_full_name(), 'onlyfirst')

    def test_user_default_ordering(self):
        """
        CP-185
        HU-038 | H | Orden por defecto es -date_joined (más reciente primero)
        """
        older = _create_user(username='older_user')
        newer = _create_user(username='newer_user')
        # older se creó antes que newer
        qs = User.objects.all()
        first = qs.first()
        self.assertEqual(first.username, 'newer_user')  # el más reciente primero

    def test_user_verbose_names(self):
        """
        CP-186
        HU-038 | H | Meta.verbose_name y verbose_name_plural correctos
        """
        self.assertEqual(User._meta.verbose_name, 'Usuario')
        self.assertEqual(User._meta.verbose_name_plural, 'Usuarios')

    def test_user_phone_blank_by_default(self):
        """
        CP-187
        HU-043 | H | Teléfono opcional, blank=True
        """
        user = User.objects.create_user(username='nophone', password='pass1234')
        self.assertEqual(user.phone, '')

    def test_user_is_delivery_false_by_default(self):
        """
        CP-188
        HU-039 | H | is_delivery por defecto es False
        """
        user = User.objects.create_user(username='normal', password='pass1234')
        self.assertFalse(user.is_delivery)


# =============================================================================
# TESTS: Group Model (Proxy)
# =============================================================================

class GroupModelTest(TestCase):
    """Soporte: Grupo/Rol"""

    def test_create_group(self):
        """
        CP-189
        Group: Creación de grupo/rol
        """
        group = Group.objects.create(name='Administradores')
        self.assertEqual(str(group), 'Administradores')
        self.assertEqual(group.name, 'Administradores')

    def test_group_proxy(self):
        """
        CP-190
        Group: Es un proxy de auth.Group
        """
        self.assertTrue(Group._meta.proxy)
        self.assertEqual(Group._meta.verbose_name, 'Rol')
        self.assertEqual(Group._meta.verbose_name_plural, 'Roles')

    def test_group_assign_users(self):
        """
        CP-191
        Group: Asignación de usuarios a grupos
        """
        group = Group.objects.create(name='Entregadores')
        user = _create_user(username='delivery_user')
        user.groups.add(group)
        self.assertIn(group, user.groups.all())
        self.assertIn(user, group.user_set.all())

    def test_group_str(self):
        """
        CP-192
        Group: __str__ retorna el nombre
        """
        group = Group.objects.create(name='Test Group')
        self.assertEqual(str(group), 'Test Group')
