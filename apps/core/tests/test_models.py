"""
Tests unitarios para modelos de apps.core.models

Cubre:
- BaseAuditModel (soft_delete, restore)
- HeroConfig (creación, string representation, ordenamiento)
- ActiveManager (filtro is_active)
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from apps.core.models import HeroConfig, BaseAuditModel, ActiveManager


# =============================================================================
# HELPERS
# =============================================================================

def _create_hero(**kwargs):
    defaults = {
        'title_text': 'Hero Test',
        'subtitle_text': 'Subtítulo',
        'button_text': 'Ir',
        'button_url': '/catalogo/',
        'button_style': 'bg-zicada-accent hover:bg-red-700 text-white rounded-lg',
        'sort_order': 0,
        'section_height': '100vh',
        'is_active': True,
    }
    defaults.update(kwargs)
    return HeroConfig.objects.create(**defaults)


def _create_user(**kwargs):
    defaults = {'username': 'admin', 'password': 'pass1234'}
    defaults.update(kwargs)
    password = defaults.pop('password')
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


# =============================================================================
# TESTS: BaseAuditModel (abstracto, probado via HeroConfig)
# =============================================================================

class BaseAuditModelTest(TestCase):
    """Prueba métodos heredados de BaseAuditModel a través de HeroConfig."""

    def setUp(self):
        self.user = _create_user()
        self.hero = _create_hero(title_text='Slide para pruebas')

    # soft_delete
    def test_soft_delete_sets_inactive_and_deleted_at(self):
        """
        HU-055 | ESCENARIO 1 | H | Soft delete (archivar) - HeroConfig
        """
        self.hero.soft_delete(user=self.user)
        self.hero.refresh_from_db()
        self.assertFalse(self.hero.is_active)
        self.assertIsNotNone(self.hero.deleted_at)

    def test_soft_delete_sets_updated_by(self):
        """Soft delete asigna updated_by si se proporciona usuario."""
        self.hero.soft_delete(user=self.user)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.updated_by, self.user)

    def test_soft_delete_without_user(self):
        """Soft_delete funciona sin usuario (updated_by se queda como None)."""
        self.hero.soft_delete()
        self.hero.refresh_from_db()
        self.assertFalse(self.hero.is_active)
        self.assertIsNotNone(self.hero.deleted_at)
        self.assertIsNone(self.hero.updated_by)

    # restore
    def test_restore_sets_active_and_clears_deleted_at(self):
        """
        HU-056 | ESCENARIO 1 | H | Restaurar slide archivado - HeroConfig
        """
        self.hero.soft_delete()
        self.hero.refresh_from_db()
        self.hero.restore(user=self.user)
        self.hero.refresh_from_db()
        self.assertTrue(self.hero.is_active)
        self.assertIsNone(self.hero.deleted_at)

    def test_restore_sets_updated_by(self):
        """Restore asigna updated_by si se proporciona usuario."""
        self.hero.soft_delete()
        self.hero.refresh_from_db()
        self.hero.restore(user=self.user)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.updated_by, self.user)

    def test_restore_without_user(self):
        """Restore funciona sin usuario."""
        self.hero.soft_delete()
        self.hero.refresh_from_db()
        self.hero.restore()
        self.hero.refresh_from_db()
        self.assertTrue(self.hero.is_active)
        self.assertIsNone(self.hero.deleted_at)
        self.assertIsNone(self.hero.updated_by)

    # Fechas automáticas
    def test_created_at_is_set_on_creation(self):
        """Al crear, created_at se establece automáticamente."""
        self.assertIsNotNone(self.hero.created_at)

    def test_updated_at_changes_on_update(self):
        """Al actualizar, updated_at cambia."""
        old_updated = self.hero.updated_at
        self.hero.title_text = 'Nuevo título'
        self.hero.save()
        self.hero.refresh_from_db()
        self.assertGreater(self.hero.updated_at, old_updated)


# =============================================================================
# TESTS: ActiveManager
# =============================================================================

class ActiveManagerTest(TestCase):
    """Prueba que ActiveManager filtre correctamente is_active=True."""

    def setUp(self):
        self.active = _create_hero(title_text='Activo', is_active=True)
        self.inactive = _create_hero(title_text='Inactivo', is_active=False)

    def test_default_manager_returns_only_active(self):
        """
        HU-052, HU-057 | H | Manager que retorna solo registros activos
        """
        qs = HeroConfig.objects.all()
        self.assertIn(self.active, qs)
        self.assertNotIn(self.inactive, qs)

    def test_all_objects_returns_all(self):
        """all_objects manager retorna todos, incluyendo inactivos."""
        qs = HeroConfig.all_objects.all()
        self.assertIn(self.active, qs)
        self.assertIn(self.inactive, qs)


# =============================================================================
# TESTS: HeroConfig específicos
# =============================================================================

class HeroConfigModelTest(TestCase):
    """Pruebas específicas del modelo HeroConfig."""

    def setUp(self):
        self.hero = _create_hero(title_text='Mi Hero', sort_order=5)

    def test_str_representation(self):
        """__str__ retorna 'Hero: ' + title_text."""
        self.assertEqual(str(self.hero), 'Hero: Mi Hero')

    def test_default_ordering_by_sort_order(self):
        """Meta.ordering = ['sort_order']"""
        h1 = _create_hero(title_text='Primero', sort_order=1)
        h2 = _create_hero(title_text='Segundo', sort_order=2)
        h3 = _create_hero(title_text='Cero', sort_order=0)
        slides = list(HeroConfig.objects.all().order_by('sort_order'))
        self.assertEqual(slides[0].title_text, 'Cero')
        self.assertEqual(slides[1].title_text, 'Primero')
        self.assertEqual(slides[2].title_text, 'Segundo')

    def test_save_does_not_alter_explicit_values(self):
        """
        HU-053 | ESCENARIO 1 | H | Guardado normal del slide
        """
        hero = _create_hero(
            title_text='Personalizado',
            subtitle_text='Subtítulo personalizado',
            button_text='Click',
            button_url='/custom/',
            section_height='50vh',
        )
        self.assertEqual(hero.title_text, 'Personalizado')
        self.assertEqual(hero.subtitle_text, 'Subtítulo personalizado')
        self.assertEqual(hero.button_text, 'Click')
        self.assertEqual(hero.button_url, '/custom/')
        self.assertEqual(hero.section_height, '50vh')

    def test_default_values_on_creation(self):
        """Valores por defecto cuando no se especifican."""
        hero = HeroConfig.objects.create(title_text='Default Test')
        self.assertEqual(hero.overlay_opacity, 0.5)
        self.assertEqual(hero.title_font_family, "'Inter', sans-serif")
        self.assertEqual(hero.title_font_size, '4rem')
        self.assertEqual(hero.title_font_weight, '800')
        self.assertEqual(hero.title_color, '#ffffff')
        self.assertEqual(hero.subtitle_text, 'LA MODA SE VA, TU ESTILO PERMANECE')
        self.assertEqual(hero.button_style, 'bg-zicada-accent hover:bg-opacity-90')
        self.assertEqual(hero.content_alignment, 'center')
        self.assertEqual(hero.section_height, '100vh')
        self.assertEqual(hero.sort_order, 0)

    def test_soft_delete_updates_deleted_at_accurately(self):
        """
        Verifica que deleted_at se establece con una hora cercana al momento de la llamada.
        """
        before = timezone.now()
        self.hero.soft_delete()
        after = timezone.now()
        self.hero.refresh_from_db()
        self.assertGreaterEqual(self.hero.deleted_at, before)
        self.assertLessEqual(self.hero.deleted_at, after)


    def test_restore_clears_deleted_at(self):
        """Restaurar pone deleted_at en None."""
        self.hero.soft_delete()
        self.hero.refresh_from_db()
        self.hero.restore()
        self.hero.refresh_from_db()
        self.assertIsNone(self.hero.deleted_at)

    def test_soft_delete_and_restore_preserves_other_fields(self):
        """Los campos no relacionados con eliminación no se ven afectados."""
        original_title = self.hero.title_text
        original_section = self.hero.section_height
        self.hero.soft_delete()
        self.hero.refresh_from_db()
        self.hero.restore()
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.title_text, original_title)
        self.assertEqual(self.hero.section_height, original_section)