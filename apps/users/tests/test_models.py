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

    # UT-516: HU-039 CA-001 - Creación de usuario con todos los campos
    def test_create_user_with_all_fields(self):
        self.assertEqual(self.user.username, 'juanperez')
        self.assertEqual(self.user.first_name, 'Juan')
        self.assertEqual(self.user.last_name, 'Perez')
        self.assertEqual(self.user.email, 'juan@example.com')
        self.assertEqual(self.user.phone, '3001234567')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_delivery)

    # UT-517: HU-039 CA-001 - Creación solo con campos obligatorios
    def test_create_user_minimal_fields(self):
        user = User.objects.create_user(username='minimal', password='pass1234')
        self.assertEqual(user.username, 'minimal')
        self.assertEqual(user.phone, '')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_delivery)

    # UT-518: HU-039 CA-001 - Creación de usuario con rol entregador
    def test_create_delivery_user(self):
        delivery = _create_user(username='delivery1', is_delivery=True)
        self.assertTrue(delivery.is_delivery)

    # UT-519: HU-038 CA-001 / HU-043 CA-002 - __str__ retorna nombre completo
    def test_user_str_with_full_name(self):
        self.assertEqual(str(self.user), 'Juan Perez')

    # UT-520: HU-038 CA-001 - __str__ retorna username sin nombre
    def test_user_str_without_full_name(self):
        user = _create_user(username='solo_username')
        self.assertEqual(str(user), 'solo_username')

    # UT-521: HU-038 CA-001 - get_full_name retorna nombre y apellido
    def test_get_full_name_with_both_names(self):
        self.assertEqual(self.user.get_full_name(), 'Juan Perez')

    # UT-522: HU-038 CA-001 - get_full_name retorna username si faltan nombres
    def test_get_full_name_without_last_name(self):
        user = _create_user(username='onlyfirst', first_name='Only')
        self.assertEqual(user.get_full_name(), 'onlyfirst')

    # UT-523: HU-038 - Orden por defecto -date_joined
    def test_user_default_ordering(self):
        older = _create_user(username='older_user')
        newer = _create_user(username='newer_user')
        qs = User.objects.all()
        first = qs.first()
        self.assertEqual(first.username, 'newer_user')

    # UT-524: HU-038 - Meta.verbose_name correcto
    def test_user_verbose_names(self):
        self.assertEqual(User._meta.verbose_name, 'Usuario')
        self.assertEqual(User._meta.verbose_name_plural, 'Usuarios')

    # UT-525: HU-043 - Teléfono opcional blank=True
    def test_user_phone_blank_by_default(self):
        user = User.objects.create_user(username='nophone', password='pass1234')
        self.assertEqual(user.phone, '')

    # UT-526: HU-039 - is_delivery por defecto False
    def test_user_is_delivery_false_by_default(self):
        user = User.objects.create_user(username='normal', password='pass1234')
        self.assertFalse(user.is_delivery)


# =============================================================================
# TESTS: Group Model (Proxy)
# =============================================================================

class GroupModelTest(TestCase):
    """Soporte: Grupo/Rol"""

    # UT-527: Group - Creación de grupo/rol
    def test_create_group(self):
        group = Group.objects.create(name='Administradores')
        self.assertEqual(str(group), 'Administradores')
        self.assertEqual(group.name, 'Administradores')

    # UT-528: Group - Es un proxy de auth.Group
    def test_group_proxy(self):
        self.assertTrue(Group._meta.proxy)
        self.assertEqual(Group._meta.verbose_name, 'Rol')
        self.assertEqual(Group._meta.verbose_name_plural, 'Roles')

    # UT-529: Group - Asignación de usuarios a grupos
    def test_group_assign_users(self):
        group = Group.objects.create(name='Entregadores')
        user = _create_user(username='delivery_user')
        user.groups.add(group)
        self.assertIn(group, user.groups.all())
        self.assertIn(user, group.user_set.all())

    # UT-530: Group - __str__ retorna el nombre
    def test_group_str(self):
        group = Group.objects.create(name='Test Group')
        self.assertEqual(str(group), 'Test Group')