"""
Tests for apps.core.views

Covers:
- HU-050: Home
- HU-051: Contact/ContactSubmit
- HU-001/003: StaffLogin
- HU-052: HeroConfigListView
- HU-053: HeroConfigCreateView
- HU-054: HeroConfigUpdateView
- HU-055: HeroConfigDeleteView
- HU-056: HeroConfigRestoreView
- HU-057: HeroConfigTrashcanView
"""

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.core import mail
from unittest.mock import patch
from decimal import Decimal

from apps.core.models import HeroConfig
from apps.products.models import Category, Product, Collection
from apps.core.forms import ContactForm
from apps.core.url_names import (
    CORE_ABOUT,
    CORE_CONTACT,
    CORE_CONTACT_SUBMIT,
    CORE_CONTACT_SUCCESS,
    CORE_RETURNS_POLICY,
    CORE_PRIVACY_POLICY,
    CORE_TERMS,
    CORE_STAFF_LOGIN,
    CORE_STAFF_LOGOUT,
    CORE_HERO_LIST,
    CORE_HERO_CREATE,
    CORE_HERO_EDIT,
    CORE_HERO_DELETE,
    CORE_HERO_RESTORE,
    CORE_HERO_TRASHCAN,
    PRODUCTS_CATALOG,
    BACKOFFICE_DASHBOARD,
)


# =============================================================================
# HELPERS
# =============================================================================

def _create_test_user(**kwargs):
    """Create a test user with optional attributes."""
    defaults = {'username': 'testuser', 'password': 'pass1234'}
    defaults.update(kwargs)
    password = defaults.pop('password')
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


def _create_test_category():
    """Create a test category."""
    return Category.objects.create(name='Ropa', slug='ropa')


def _create_test_product(category=None):
    """Create a test product."""
    if category is None:
        category = _create_test_category()
    return Product.objects.create(
        name='Camiseta Zicada',
        slug='camiseta-zicada',
        price=Decimal('29.99'),
        category=category
    )


def _create_test_collection():
    """Create a test collection."""
    return Collection.objects.create(
        name='Coleccion Verano',
        slug='coleccion-verano',
        status='publicada',
        is_active=True
    )


def _create_hero(**kwargs):
    """Create a test hero slide."""
    defaults = {
        'title_text': 'Hero Test',
        'subtitle_text': 'Subtitulo',
        'button_text': 'Ir',
        'button_url': '/catalogo/',
        'button_style': 'bg-zicada-accent hover:bg-red-700 text-white rounded-lg px-8 py-3 text-lg shadow-lg inline-block font-semibold transition-all duration-300 transform hover:scale-105 inline-block text-center',
        'sort_order': 0,
        'section_height': '100vh',
        'is_active': True,
    }
    defaults.update(kwargs)
    return HeroConfig.objects.create(**defaults)


def _add_hero_permissions(user):
    """Add hero permissions to a user."""
    content_type = ContentType.objects.get_for_model(HeroConfig)
    perms = Permission.objects.filter(content_type=content_type)
    user.user_permissions.add(*perms)
    return user


# =============================================================================
# TESTS: HU-050 Home View
# =============================================================================

class HomeViewTest(TestCase):
    """HU-050: Personalized home page"""

    def setUp(self):
        self.client = Client()
        self.category = _create_test_category()
        self.product = _create_test_product(category=self.category)
        self.collection = _create_test_collection()
        self.hero = _create_hero()

    def test_home_returns_200(self):
        """HU-050 | H | Home page loads correctly"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_includes_hero_slides(self):
        """HU-050 | H | Loads active slides ordered by sort_order"""
        response = self.client.get('/')
        self.assertIn('hero_slides', response.context)
        slides = list(response.context['hero_slides'])
        self.assertEqual(len(slides), 1)
        self.assertEqual(slides[0].title_text, 'Hero Test')

    def test_home_includes_featured_collections(self):
        """HU-050 | H | Loads published collections"""
        response = self.client.get('/')
        self.assertIn('featured_collections', response.context)
        self.assertEqual(len(response.context['featured_collections']), 1)

    def test_home_includes_latest_products(self):
        """HU-050 | H | Loads active products"""
        response = self.client.get('/')
        self.assertIn('latest_products', response.context)
        self.assertEqual(len(response.context['latest_products']), 1)

    def test_home_includes_categories(self):
        """HU-050 | H | Loads categories"""
        response = self.client.get('/')
        self.assertIn('categories', response.context)
        self.assertEqual(len(response.context['categories']), 1)

    def test_home_no_active_slides(self):
        """HU-050-ALT-1: No active slides -> empty context"""
        HeroConfig.objects.all().delete()
        response = self.client.get('/')
        self.assertEqual(len(response.context['hero_slides']), 0)

    def test_home_no_collections(self):
        """HU-050-ALT-2: No collections -> section hidden"""
        Collection.objects.all().delete()
        response = self.client.get('/')
        self.assertEqual(len(response.context['featured_collections']), 0)

    def test_home_no_products(self):
        """HU-050-ALT-3: No products -> section hidden"""
        Product.objects.all().delete()
        response = self.client.get('/')
        self.assertEqual(len(response.context['latest_products']), 0)

    def test_home_slides_order_by_sort_order(self):
        """HU-050 | H | Slides ordered by sort_order"""
        _create_hero(title_text='Segundo', sort_order=1)
        _create_hero(title_text='Cero', sort_order=0)
        response = self.client.get('/')
        slides = list(response.context['hero_slides'].filter(is_active=True).order_by('sort_order'))
        self.assertGreater(len(slides), 0)


# =============================================================================
# TESTS: HU-051 Contact Views
# =============================================================================

class ContactViewTest(TestCase):
    """HU-051: Contact form"""

    def setUp(self):
        self.client = Client()

    def test_contact_get_returns_200(self):
        """HU-051 | GET | Displays contact form"""
        response = self.client.get(reverse(CORE_CONTACT))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ContactForm)


class ContactSubmitViewTest(TestCase):
    """HU-051: Contact form submission"""

    def setUp(self):
        self.client = Client()
        self.valid_data = {
            'name': 'Juan Perez',
            'email': 'juan@example.com',
            'subject': 'Consulta',
            'message': 'Mensaje de prueba.',
        }

    def test_get_redirects_to_contact(self):
        """HU-051 | SCENARIO 1 | E | GET redirects to contact form"""
        response = self.client.get(reverse(CORE_CONTACT_SUBMIT))
        self.assertRedirects(response, reverse(CORE_CONTACT))

    @override_settings(
        DEFAULT_FROM_EMAIL='tienda@zicada.com',
        SITE_URL='http://testserver',
    )
    def test_valid_form_sends_emails_and_redirects(self):
        """HU-051 | SCENARIO 2 | H | Valid form sends emails and redirects to success"""
        response = self.client.post(reverse(CORE_CONTACT_SUBMIT), data=self.valid_data)

        self.assertEqual(len(mail.outbox), 2)

        admin_email = mail.outbox[0]
        self.assertIn('Consulta', admin_email.subject)
        self.assertIn('juan@example.com', admin_email.body)

        user_email = mail.outbox[1]
        self.assertEqual(user_email.to, ['juan@example.com'])

        self.assertRedirects(response, reverse(CORE_CONTACT_SUCCESS))

    def test_invalid_form_redirects_with_errors(self):
        """HU-051 | SCENARIO 4 | A | Invalid form redirects with errors"""
        data = self.valid_data.copy()
        data['email'] = 'invalido'
        data['name'] = ''
        response = self.client.post(reverse(CORE_CONTACT_SUBMIT), data=data)

        self.assertRedirects(response, reverse(CORE_CONTACT))

        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('obligatorio' in str(m).lower() for m in messages))
        self.assertTrue(any('valido' in str(m).lower() for m in messages))

    @override_settings(
        DEFAULT_FROM_EMAIL='tienda@zicada.com',
        SITE_URL='http://testserver',
    )
    @patch('apps.core.views.EmailMultiAlternatives.send')
    def test_email_failure_shows_error(self, mock_send):
        """HU-051 | SCENARIO 3 | E | Email failure shows error message"""
        mock_send.side_effect = Exception("SMTP connection error")

        response = self.client.post(reverse(CORE_CONTACT_SUBMIT), data=self.valid_data)

        self.assertRedirects(response, reverse(CORE_CONTACT))

        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('error' in str(m).lower() for m in messages))


class ContactSuccessViewTest(TestCase):
    """HU-051: Contact success page"""

    def setUp(self):
        self.client = Client()

    def test_success_page_returns_200(self):
        """HU-051 | H | Success page loads correctly"""
        response = self.client.get(reverse(CORE_CONTACT_SUCCESS))
        self.assertEqual(response.status_code, 200)


# =============================================================================
# TESTS: HU-001 & HU-003 StaffLoginView
# =============================================================================

class StaffLoginViewTest(TestCase):
    """HU-001: Login; HU-003: Access control"""

    def setUp(self):
        self.client = Client()
        self.staff_user = _create_test_user(username='staff', is_staff=True)
        self.normal_user = _create_test_user(username='normal', is_staff=False)
        self.delivery_user = _create_test_user(username='delivery')
        self.delivery_user.is_delivery = True
        self.delivery_user.save()

    def test_login_page_accessible(self):
        """HU-001 | H | Login page accessible without authentication"""
        self.client.logout()
        response = self.client.get(reverse(CORE_STAFF_LOGIN))
        self.assertEqual(response.status_code, 200)

    def test_staff_redirected_to_dashboard(self):
        """HU-001 | SCENARIO 1 | H | Staff login redirects to dashboard"""
        self.client.login(username='staff', password='pass1234')
        response = self.client.get(reverse(CORE_STAFF_LOGIN))
        self.assertRedirects(response, reverse(BACKOFFICE_DASHBOARD))

    def test_delivery_redirected_to_dashboard(self):
        """HU-001 | SCENARIO 2 | H | Delivery login redirects to dashboard"""
        self.client.login(username='delivery', password='pass1234')
        response = self.client.get(reverse(CORE_STAFF_LOGIN))
        self.assertRedirects(response, reverse(BACKOFFICE_DASHBOARD))

    def test_normal_user_redirected_to_catalog(self):
        """HU-003 | SCENARIO 3 | E | Normal user redirected to catalog"""
        self.client.login(username='normal', password='pass1234')
        response = self.client.get(reverse(CORE_STAFF_LOGIN))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_inactive_user_error(self):
        """HU-001 | SCENARIO 4 | E | Inactive user shows error"""
        _create_test_user(username='inactive', is_staff=True, is_active=False)
        response = self.client.post(reverse(CORE_STAFF_LOGIN), data={
            'username': 'inactive',
            'password': 'pass1234'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('inactiva', response.content.decode().lower())

    def test_wrong_credentials_error(self):
        """HU-001 | SCENARIO 3 | E | Wrong credentials show error"""
        response = self.client.post(reverse(CORE_STAFF_LOGIN), data={
            'username': 'staff',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.content.decode().lower())


# =============================================================================
# TESTS: HU-052 HeroConfigListView
# =============================================================================

class HeroConfigListViewTest(TestCase):
    """HU-052: List active hero slides"""

    def setUp(self):
        self.client = Client()
        self.user = _create_test_user(username='admin', is_staff=True)
        self.user = _add_hero_permissions(self.user)
        self.client.force_login(self.user)

        self.hero1 = _create_hero(title_text='Primero', sort_order=0)
        self.hero2 = _create_hero(title_text='Segundo', sort_order=1)

    def test_list_active_slides(self):
        """HU-052 | SCENARIO 1 | H | Lists active slides"""
        response = self.client.get(reverse(CORE_HERO_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['hero_slides']), 2)

    def test_list_excludes_inactive(self):
        """HU-052 | SCENARIO 1 | H | Excludes inactive slides"""
        _create_hero(title_text='Inactivo', is_active=False)
        response = self.client.get(reverse(CORE_HERO_LIST))
        self.assertEqual(len(response.context['hero_slides']), 2)

    def test_list_sorted_by_sort_order(self):
        """HU-052 | H | Sorted by sort_order"""
        response = self.client.get(reverse(CORE_HERO_LIST))
        slides = list(response.context['hero_slides'])
        self.assertEqual(slides[0].sort_order, 0)
        self.assertEqual(slides[1].sort_order, 1)

    def test_list_requires_permission(self):
        """HU-052 | SCENARIO 2 | E | No permission redirects to login"""
        self.client.logout()
        normal_user = _create_test_user(username='normal', is_staff=False)
        self.client.force_login(normal_user)
        response = self.client.get(reverse(CORE_HERO_LIST))
        self.assertEqual(response.status_code, 302)

    def test_list_context_headers(self):
        """HU-052 | H | Includes headers in context"""
        response = self.client.get(reverse(CORE_HERO_LIST))
        self.assertIn('headers', response.context)
        self.assertIn('rows', response.context)


# =============================================================================
# TESTS: HU-053 HeroConfigCreateView
# =============================================================================

class HeroConfigCreateViewTest(TestCase):
    """HU-053: Create hero slide"""

    def setUp(self):
        self.client = Client()
        self.user = _create_test_user(username='admin', is_staff=True)
        self.user = _add_hero_permissions(self.user)
        self.client.force_login(self.user)

        self.category = _create_test_category()
        self.product = _create_test_product(category=self.category)
        self.collection = _create_test_collection()

    def get_valid_data(self):
        return {
            'title_text': 'Nuevo Slide',
            'subtitle_text': 'Subtitulo',
            'button_text': 'Explorar',
            'button_url': '/catalogo/',
            'button_bg_color': 'bg-zicada-accent',
            'button_hover_color': 'hover:bg-red-700',
            'button_text_color': 'text-white',
            'button_border_radius': 'rounded-lg',
            'button_size': 'px-8 py-3 text-lg',
            'button_shadow': 'shadow-lg',
            'button_width': 'inline-block',
            'content_alignment': 'center',
            'section_height': '100vh',
            'sort_order': 0,
            'overlay_opacity': 0.5,
            'title_font_family': "'Inter', sans-serif",
            'title_font_size': '4rem',
            'title_font_weight': '800',
            'title_line_height': '1.2',
            'title_color': '#ffffff',
            'title_margin_bottom': '1rem',
            'subtitle_font_family': "'Inter', sans-serif",
            'subtitle_font_size': '1.25rem',
            'subtitle_font_weight': '400',
            'subtitle_line_height': '1.5',
            'subtitle_color': '#e5e5e5',
            'subtitle_margin_bottom': '2rem',
        }

    def test_get_create_form(self):
        """HU-053 | GET | Displays create form"""
        response = self.client.get(reverse(CORE_HERO_CREATE))
        self.assertEqual(response.status_code, 200)

    def test_create_valid_slide(self):
        """HU-053 | SCENARIO 1 | H | Valid slide creation"""
        data = self.get_valid_data()
        response = self.client.post(reverse(CORE_HERO_CREATE), data=data)

        self.assertRedirects(response, reverse(CORE_HERO_LIST))
        self.assertEqual(HeroConfig.objects.count(), 1)

        hero = HeroConfig.objects.first()
        self.assertEqual(hero.title_text, 'Nuevo Slide')

    def test_create_duplicate_sort_order(self):
        """HU-053 | SCENARIO 2 | A | Duplicate sort_order shows error"""
        _create_hero(sort_order=0)
        data = self.get_valid_data()
        data['sort_order'] = 0
        response = self.client.post(reverse(CORE_HERO_CREATE), data=data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(HeroConfig.objects.count(), 1)

    def test_create_empty_title(self):
        """HU-053 | SCENARIO 2 | A | Empty title shows error"""
        data = self.get_valid_data()
        data['title_text'] = ''
        response = self.client.post(reverse(CORE_HERO_CREATE), data=data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(HeroConfig.objects.count(), 0)

    def test_create_requires_permission(self):
        """HU-053 | SCENARIO 3 | E | No permission redirects"""
        self.client.logout()
        normal_user = _create_test_user(username='normal', is_staff=False)
        self.client.force_login(normal_user)

        response = self.client.get(reverse(CORE_HERO_CREATE))
        self.assertEqual(response.status_code, 302)


# =============================================================================
# TESTS: HU-054 HeroConfigUpdateView
# =============================================================================

class HeroConfigUpdateViewTest(TestCase):
    """HU-054: Update hero slide"""

    def setUp(self):
        self.client = Client()
        self.user = _create_test_user(username='admin', is_staff=True)
        self.user = _add_hero_permissions(self.user)
        self.client.force_login(self.user)

        self.hero = _create_hero(title_text='Original')
        self.hero.sort_order = 0
        self.hero.save()

    def get_valid_update_data(self):
        return {
            'title_text': 'Actualizado',
            'subtitle_text': 'Nuevo subtitulo',
            'button_text': 'Ir ahora',
            'button_url': '/catalogo/',
            'button_bg_color': 'bg-black',
            'button_hover_color': 'hover:bg-gray-700',
            'button_text_color': 'text-white',
            'button_border_radius': 'rounded-lg',
            'button_size': 'px-8 py-3 text-lg',
            'button_shadow': 'shadow-lg',
            'button_width': 'inline-block',
            'content_alignment': 'center',
            'section_height': '90vh',
            'overlay_opacity': 0.7,
            'is_active': True,
            'title_font_family': "'Inter', sans-serif",
            'title_font_size': '3rem',
            'title_font_weight': '700',
            'title_line_height': '1.4',
            'title_color': '#000000',
            'title_margin_bottom': '0.5rem',
            'subtitle_font_family': "'Roboto', sans-serif",
            'subtitle_font_size': '1rem',
            'subtitle_font_weight': '500',
            'subtitle_line_height': '1.6',
            'subtitle_color': '#333333',
            'subtitle_margin_bottom': '1rem',
        }

    def test_get_update_form(self):
        """HU-054 | GET | Displays update form"""
        response = self.client.get(reverse(CORE_HERO_EDIT, kwargs={'pk': self.hero.pk}))
        self.assertEqual(response.status_code, 200)

    def test_update_valid_slide(self):
        """HU-054 | SCENARIO 1 | H | Valid slide update"""
        data = self.get_valid_update_data()
        response = self.client.post(
            reverse(CORE_HERO_EDIT, kwargs={'pk': self.hero.pk}),
            data=data
        )

        self.assertRedirects(response, reverse(CORE_HERO_LIST))

        self.hero.refresh_from_db()
        self.assertEqual(self.hero.title_text, 'Actualizado')
        self.assertEqual(self.hero.section_height, '90vh')

    def test_update_empty_title(self):
        """HU-054 | SCENARIO 2 | A | Empty title shows error"""
        data = self.get_valid_update_data()
        data['title_text'] = ''
        response = self.client.post(
            reverse(CORE_HERO_EDIT, kwargs={'pk': self.hero.pk}),
            data=data
        )

        self.assertEqual(response.status_code, 200)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.title_text, 'Original')

    def test_update_nonexistent_slide(self):
        """HU-054 | SCENARIO 4 | E | Nonexistent slide returns 404"""
        response = self.client.get(reverse(CORE_HERO_EDIT, kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_update_requires_permission(self):
        """HU-054 | SCENARIO 3 | E | No permission redirects"""
        self.client.logout()
        response = self.client.get(reverse(CORE_HERO_EDIT, kwargs={'pk': self.hero.pk}))
        self.assertEqual(response.status_code, 302)


# =============================================================================
# TESTS: HU-055 HeroConfigDeleteView (Soft Delete)
# =============================================================================

class HeroConfigDeleteViewTest(TestCase):
    """HU-055: Soft delete hero slide"""

    def setUp(self):
        self.client = Client()
        self.user = _create_test_user(username='admin', is_staff=True)
        self.user = _add_hero_permissions(self.user)
        self.client.force_login(self.user)

        self.hero = _create_hero(title_text='Eliminar Slide')

    def test_get_delete_confirmation(self):
        """HU-055 | GET | Displays delete confirmation page"""
        response = self.client.get(reverse(CORE_HERO_DELETE, kwargs={'pk': self.hero.pk}))
        self.assertEqual(response.status_code, 200)

    def test_delete_with_correct_confirmation(self):
        """HU-055 | SCENARIO 1 | H | Correct confirmation performs soft delete"""
        response = self.client.post(
            reverse(CORE_HERO_DELETE, kwargs={'pk': self.hero.pk}),
            data={'confirm': 'Eliminar Slide'}
        )

        self.assertRedirects(response, reverse(CORE_HERO_LIST))

        self.hero.refresh_from_db()
        self.assertFalse(self.hero.is_active)
        self.assertIsNotNone(self.hero.deleted_at)

    def test_delete_wrong_confirmation(self):
        """HU-055 | SCENARIO 2 | A | Wrong confirmation returns to form"""
        response = self.client.post(
            reverse(CORE_HERO_DELETE, kwargs={'pk': self.hero.pk}),
            data={'confirm': 'Otro Nombre'}
        )

        self.assertEqual(response.status_code, 200)

        self.hero.refresh_from_db()
        self.assertTrue(self.hero.is_active)

    def test_delete_case_insensitive_confirmation(self):
        """HU-055 | SCENARIO 1 | H | Case-insensitive confirmation works"""
        response = self.client.post(
            reverse(CORE_HERO_DELETE, kwargs={'pk': self.hero.pk}),
            data={'confirm': 'eliminar slide'}
        )
        self.assertRedirects(response, reverse(CORE_HERO_LIST))

        self.hero.refresh_from_db()
        self.assertFalse(self.hero.is_active)

    def test_delete_requires_permission(self):
        """HU-055 | SCENARIO 3 | E | No permission redirects"""
        self.client.logout()
        response = self.client.get(reverse(CORE_HERO_DELETE, kwargs={'pk': self.hero.pk}))
        self.assertEqual(response.status_code, 302)


# =============================================================================
# TESTS: HU-056 HeroConfigRestoreView
# =============================================================================

class HeroConfigRestoreViewTest(TestCase):
    """HU-056: Restore soft-deleted hero slide"""

    def setUp(self):
        self.client = Client()
        self.user = _create_test_user(username='admin', is_staff=True)
        self.user = _add_hero_permissions(self.user)
        self.client.force_login(self.user)

        self.hero = _create_hero(title_text='Restaurar Slide', sort_order=1, is_active=False)

    def test_get_restore_page(self):
        """HU-056 | GET | Displays restore page"""
        response = self.client.get(reverse(CORE_HERO_RESTORE, kwargs={'pk': self.hero.pk}))
        self.assertEqual(response.status_code, 200)

    def test_restore_with_valid_confirmation(self):
        """HU-056 | SCENARIO 1 | H | Valid confirmation restores slide"""
        response = self.client.post(
            reverse(CORE_HERO_RESTORE, kwargs={'pk': self.hero.pk}),
            data={'confirm': True}
        )

        self.assertRedirects(response, reverse(CORE_HERO_LIST))

        self.hero.refresh_from_db()
        self.assertTrue(self.hero.is_active)
        self.assertIsNone(self.hero.deleted_at)

    def test_restore_without_confirmation(self):
        """HU-056 | SCENARIO 3 | A | No confirmation returns to form"""
        response = self.client.post(
            reverse(CORE_HERO_RESTORE, kwargs={'pk': self.hero.pk}),
            data={'confirm': False}
        )

        self.assertEqual(response.status_code, 200)

        self.hero.refresh_from_db()
        self.assertFalse(self.hero.is_active)

    def test_restore_sort_order_conflict(self):
        """HU-056 | SCENARIO 3 | A | Sort order conflict returns to form"""
        _create_hero(title_text='Activo', sort_order=1)

        response = self.client.post(
            reverse(CORE_HERO_RESTORE, kwargs={'pk': self.hero.pk}),
            data={'confirm': True}
        )

        self.assertEqual(response.status_code, 200)
        self.hero.refresh_from_db()
        self.assertFalse(self.hero.is_active)

    def test_restore_nonexistent_slide(self):
        """HU-056 | E | Nonexistent slide returns 404"""
        response = self.client.get(reverse(CORE_HERO_RESTORE, kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_restore_requires_permission(self):
        """HU-056 | SCENARIO 2 | E | No permission redirects"""
        self.client.logout()
        response = self.client.get(reverse(CORE_HERO_RESTORE, kwargs={'pk': self.hero.pk}))
        self.assertEqual(response.status_code, 302)


# =============================================================================
# TESTS: HU-057 HeroConfigTrashcanView
# =============================================================================

class HeroConfigTrashcanViewTest(TestCase):
    """HU-057: List soft-deleted hero slides"""

    def setUp(self):
        self.client = Client()
        self.user = _create_test_user(username='admin', is_staff=True)
        self.user = _add_hero_permissions(self.user)
        self.client.force_login(self.user)

        self.hero1 = _create_hero(title_text='Eliminado 1', is_active=False)
        self.hero2 = _create_hero(title_text='Activo', is_active=True)

    def test_trashcan_shows_inactive_slides(self):
        """HU-057 | SCENARIO 1 | H | Shows only inactive slides"""
        response = self.client.get(reverse(CORE_HERO_TRASHCAN))
        self.assertEqual(response.status_code, 200)

        slides = list(response.context['hero_slides'])
        self.assertEqual(len(slides), 1)
        self.assertEqual(slides[0].title_text, 'Eliminado 1')

    def test_trashcan_empty(self):
        """HU-057 | SCENARIO 3 | A | Empty trashcan"""
        HeroConfig.all_objects.filter(is_active=False).delete()
        response = self.client.get(reverse(CORE_HERO_TRASHCAN))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['hero_slides']), 0)

    def test_trashcan_context_headers(self):
        """HU-057 | H | Includes headers in context"""
        response = self.client.get(reverse(CORE_HERO_TRASHCAN))
        self.assertIn('headers', response.context)
        self.assertIn('rows', response.context)

    def test_trashcan_requires_permission(self):
        """HU-057 | SCENARIO 2 | E | No permission redirects"""
        self.client.logout()
        response = self.client.get(reverse(CORE_HERO_TRASHCAN))
        self.assertEqual(response.status_code, 302)


# =============================================================================
# TESTS: Staff Logout
# =============================================================================

class StaffLogoutViewTest(TestCase):
    """Staff logout"""

    def setUp(self):
        self.client = Client()
        self.user = _create_test_user(username='staff', is_staff=True)
        self.client.force_login(self.user)

    def test_logout_redirects_to_catalog(self):
        """Logout redirects to catalog"""
        response = self.client.post(reverse(CORE_STAFF_LOGOUT))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

        self.assertFalse(response.wsgi_request.user.is_authenticated)


# =============================================================================
# TESTS: Static Pages
# =============================================================================

class StaticPagesViewTest(TestCase):
    """Static pages (About, Returns, Privacy, Terms)"""

    def setUp(self):
        self.client = Client()

    def test_about_page(self):
        """About page"""
        response = self.client.get(reverse(CORE_ABOUT))
        self.assertEqual(response.status_code, 200)

    def test_returns_page(self):
        """Returns policy page"""
        response = self.client.get(reverse(CORE_RETURNS_POLICY))
        self.assertEqual(response.status_code, 200)

    def test_privacy_page(self):
        """Privacy policy page"""
        response = self.client.get(reverse(CORE_PRIVACY_POLICY))
        self.assertEqual(response.status_code, 200)

    def test_terms_page(self):
        """Terms and conditions page"""
        response = self.client.get(reverse(CORE_TERMS))
        self.assertEqual(response.status_code, 200)


# =============================================================================
# TESTS: PWA Manifest
# =============================================================================

class PWAManifestViewTest(TestCase):
    """PWA Manifest"""

    def setUp(self):
        self.client = Client()

    def test_manifest_returns_json(self):
        """PWA manifest returns JSON"""
        response = self.client.get(reverse('pwa_manifest'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        data = response.json()
        self.assertIn('name', data)
        self.assertIn('short_name', data)
        self.assertIn('start_url', data)
        self.assertIn('display', data)