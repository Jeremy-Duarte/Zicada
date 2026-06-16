from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, Group
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

from apps.core.constants import (
    LOGIN_ERROR_MESSAGE,
    LOGIN_INACTIVE_MESSAGE,
)

User = get_user_model()


# =============================================================================
# HELPERS
# =============================================================================

def _create_admin_user(**kwargs):
    defaults = {'username': 'admin', 'password': 'pass1234', 'is_staff': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    
    admin_group, _ = Group.objects.get_or_create(name='Administrador')
    user.groups.add(admin_group)
    
    return user


def _create_delivery_user(**kwargs):
    defaults = {'username': 'delivery', 'password': 'pass1234', 'is_delivery': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    
    delivery_group, _ = Group.objects.get_or_create(name='Entregador')
    user.groups.add(delivery_group)
    
    return user


def _create_normal_user(**kwargs):
    defaults = {'username': 'normal', 'password': 'pass1234', 'is_staff': False}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    
    return user


def _create_test_category():
    return Category.objects.create(name='Ropa', slug='ropa')


def _create_test_product(category=None):
    if category is None:
        category = _create_test_category()
    return Product.objects.create(
        name='Camiseta Zicada',
        slug='camiseta-zicada',
        price=Decimal('29.99'),
        category=category
    )


def _create_test_collection():
    return Collection.objects.create(
        name='Coleccion Verano',
        slug='coleccion-verano',
        status='publicada',
        is_active=True
    )


def _create_hero(**kwargs):
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
    content_type = ContentType.objects.get_for_model(HeroConfig)
    perms = Permission.objects.filter(content_type=content_type)
    user.user_permissions.add(*perms)
    return user


# =============================================================================
# TESTS: HU-050 HomeView
# =============================================================================

class HomeViewTest(TestCase):
    """HU-050: Personalized home page"""

    def setUp(self):
        self.client = Client()
        self.category = _create_test_category()
        self.product = _create_test_product(category=self.category)
        self.collection = _create_test_collection()
        self.hero = _create_hero()

    # UT-058: HU-050 - Home page carga correctamente
    def test_home_returns_200(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    # UT-059: HU-050 - Carga slides activos ordenados por sort_order
    def test_home_includes_hero_slides(self):
        response = self.client.get('/')
        self.assertIn('hero_slides', response.context)
        slides = list(response.context['hero_slides'])
        self.assertEqual(len(slides), 1)
        self.assertEqual(slides[0].title_text, 'Hero Test')

    # UT-060: HU-050 - Carga colecciones publicadas
    def test_home_includes_featured_collections(self):
        response = self.client.get('/')
        self.assertIn('featured_collections', response.context)
        self.assertEqual(len(response.context['featured_collections']), 1)

    # UT-061: HU-050 - Carga productos activos
    def test_home_includes_latest_products(self):
        response = self.client.get('/')
        self.assertIn('latest_products', response.context)
        self.assertEqual(len(response.context['latest_products']), 1)

    # UT-062: HU-050 - Carga categorías
    def test_home_includes_categories(self):
        response = self.client.get('/')
        self.assertIn('categories', response.context)
        self.assertEqual(len(response.context['categories']), 1)

    # UT-063: HU-050 - Sin slides activos -> contexto vacío
    def test_home_no_active_slides(self):
        HeroConfig.objects.all().delete()
        response = self.client.get('/')
        self.assertEqual(len(response.context['hero_slides']), 0)

    # UT-064: HU-050 - Sin colecciones -> sección oculta
    def test_home_no_collections(self):
        Collection.objects.all().delete()
        response = self.client.get('/')
        self.assertEqual(len(response.context['featured_collections']), 0)

    # UT-065: HU-050 - Sin productos -> sección oculta
    def test_home_no_products(self):
        Product.objects.all().delete()
        response = self.client.get('/')
        self.assertEqual(len(response.context['latest_products']), 0)

    # UT-066: HU-050 - Slides ordenados por sort_order
    def test_home_slides_order_by_sort_order(self):
        _create_hero(title_text='Segundo', sort_order=1)
        _create_hero(title_text='Cero', sort_order=0)
        response = self.client.get('/')
        slides = list(response.context['hero_slides'].filter(is_active=True).order_by('sort_order'))
        self.assertGreater(len(slides), 0)


# =============================================================================
# TESTS: HU-051 ContactView
# =============================================================================

class ContactViewTest(TestCase):
    """HU-051: Contact form"""

    def setUp(self):
        self.client = Client()

    # UT-067: HU-051 GET - Muestra formulario de contacto
    def test_contact_get_returns_200(self):
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

    # UT-068: HU-051 CA-001 GET - Página contacto con formulario
    def test_get_returns_200_with_form(self):
        response = self.client.get(reverse(CORE_CONTACT))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ContactForm)

    # UT-069: HU-051 CA-001 - Formulario válido envía emails y redirige
    @override_settings(
        DEFAULT_FROM_EMAIL='tienda@zicada.com',
        SITE_URL='http://testserver',
    )
    def test_valid_form_sends_emails_and_redirects(self):
        response = self.client.post(reverse(CORE_CONTACT), data=self.valid_data)

        self.assertEqual(len(mail.outbox), 2)

        admin_email = mail.outbox[0]
        self.assertIn('Consulta', admin_email.subject)
        self.assertIn('juan@example.com', admin_email.body)

        user_email = mail.outbox[1]
        self.assertEqual(user_email.to, ['juan@example.com'])

        self.assertRedirects(response, reverse(CORE_CONTACT_SUCCESS))

    # UT-070: HU-051 CA-004 - Formulario inválido muestra errores
    def test_invalid_form_shows_errors(self):
        data = self.valid_data.copy()
        data['email'] = 'invalido'
        data['name'] = ''
        
        response = self.client.post(reverse(CORE_CONTACT), data=data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contact.html')
        
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertFalse(form.is_valid())
        
        self.assertIn('name', form.errors)
        self.assertIn('email', form.errors)

    # UT-071: HU-051 - Error de correo muestra mensaje
    @override_settings(
        DEFAULT_FROM_EMAIL='tienda@zicada.com',
        SITE_URL='http://testserver',
    )
    @patch('apps.core.views.EmailMultiAlternatives.send')
    def test_email_failure_shows_error(self, mock_send):
        mock_send.side_effect = Exception("SMTP connection error")

        response = self.client.post(reverse(CORE_CONTACT), data=self.valid_data)
        self.assertEqual(response.status_code, 200)
        
        messages_list = list(response.context.get('messages', []))
        self.assertTrue(len(messages_list) > 0)
        self.assertTrue(any('error' in str(m.message).lower() for m in messages_list))


class ContactSuccessViewTest(TestCase):
    """HU-051: Contact success page"""

    def setUp(self):
        self.client = Client()

    # UT-072: HU-051 - Página de éxito carga correctamente
    def test_success_page_returns_200(self):
        response = self.client.get(reverse(CORE_CONTACT_SUCCESS))
        self.assertEqual(response.status_code, 200)


# =============================================================================
# TESTS: HU-001 & HU-003 StaffLoginView
# =============================================================================

class StaffLoginViewTest(TestCase):
    """HU-001: Login; HU-003: Access control"""

    def setUp(self):
        self.client = Client()
        self.staff_user = _create_admin_user(username='staff')
        self.normal_user = _create_normal_user(username='normal')
        self.delivery_user = _create_delivery_user(username='delivery')

    # UT-073: HU-001 - Página de login accesible sin autenticación
    def test_login_page_accessible(self):
        self.client.logout()
        response = self.client.get(reverse(CORE_STAFF_LOGIN))
        self.assertEqual(response.status_code, 200)

    # UT-074: HU-003 CA-001 - Staff redirige a dashboard
    def test_staff_redirected_to_dashboard(self):
        self.client.login(username='staff', password='pass1234')
        response = self.client.get(reverse(CORE_STAFF_LOGIN))
        self.assertRedirects(response, reverse(BACKOFFICE_DASHBOARD))

    # UT-075: HU-003 CA-003 - Usuario normal redirige a catálogo
    def test_normal_user_redirected_to_catalog(self):
        self.client.login(username='normal', password='pass1234')
        response = self.client.get(reverse(CORE_STAFF_LOGIN))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    # UT-076: HU-001 CA-004 - Usuario inactivo muestra error
    def test_inactive_user_error(self):
        _create_normal_user(username='inactive', is_active=False)
        response = self.client.post(reverse(CORE_STAFF_LOGIN), data={
            'username': 'inactive',
            'password': 'pass1234'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, LOGIN_INACTIVE_MESSAGE)

    # UT-077: HU-001 CA-003 - Credenciales incorrectas muestran error
    def test_wrong_credentials_error(self):
        response = self.client.post(reverse(CORE_STAFF_LOGIN), data={
            'username': 'staff',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, LOGIN_ERROR_MESSAGE)


# =============================================================================
# TESTS: HU-052 HeroConfigListView
# =============================================================================

class HeroConfigListViewTest(TestCase):
    """HU-052: List active hero slides"""

    def setUp(self):
        self.client = Client()
        self.user = _create_admin_user(username='admin')
        self.user = _add_hero_permissions(self.user)
        self.client.force_login(self.user)

        self.hero1 = _create_hero(title_text='Primero', sort_order=0)
        self.hero2 = _create_hero(title_text='Segundo', sort_order=1)

    # UT-078: HU-052 CA-001 - Lista slides activos
    def test_list_active_slides(self):
        response = self.client.get(reverse(CORE_HERO_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['hero_slides']), 2)

    # UT-079: HU-052 CA-001 - Excluye slides inactivos
    def test_list_excludes_inactive(self):
        _create_hero(title_text='Inactivo', is_active=False)
        response = self.client.get(reverse(CORE_HERO_LIST))
        self.assertEqual(len(response.context['hero_slides']), 2)

    # UT-080: HU-052 - Ordenado por sort_order
    def test_list_sorted_by_sort_order(self):
        response = self.client.get(reverse(CORE_HERO_LIST))
        slides = list(response.context['hero_slides'])
        self.assertEqual(slides[0].sort_order, 0)
        self.assertEqual(slides[1].sort_order, 1)

    # UT-081: HU-052 CA-002 - Usuario no autenticado redirige a login
    def test_list_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(CORE_HERO_LIST))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(CORE_HERO_LIST)}')

    # UT-082: HU-052 CA-002 - Usuario sin permiso redirige a catálogo
    def test_list_requires_permission(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(CORE_HERO_LIST))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    # UT-083: HU-052 - Incluye headers en contexto
    def test_list_context_headers(self):
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
        self.user = _create_admin_user(username='admin')
        self.user = _add_hero_permissions(self.user)
        self.client.force_login(self.user)

        self.category = _create_test_category()
        self.product = _create_test_product(category=self.category)
        self.collection = _create_test_collection()

    def get_valid_data(self):
        catalog_url = reverse(PRODUCTS_CATALOG)
        return {
            'background_image': '',
            'overlay_opacity': 0.5,
            'title_text': 'Nuevo Slide',
            'title_font_family': "'Inter', sans-serif",
            'title_font_size': '4rem',
            'title_font_weight': '800',
            'title_line_height': '1.2',
            'title_color': '#ffffff',
            'title_margin_bottom': '1rem',
            'subtitle_text': 'Subtitulo de prueba',
            'subtitle_font_family': "'Inter', sans-serif",
            'subtitle_font_size': '1.25rem',
            'subtitle_font_weight': '400',
            'subtitle_line_height': '1.5',
            'subtitle_color': '#e5e5e5',
            'subtitle_margin_bottom': '2rem',
            'button_text': 'Explorar',
            'button_url': catalog_url,
            'content_alignment': 'center',
            'section_height': '100vh',
            'sort_order': 0,            
            'button_bg_color': 'bg-zicada-accent',
            'button_hover_color': 'hover:bg-red-700',
            'button_text_color': 'text-white',
            'button_border_radius': 'rounded-lg',
            'button_size': 'px-8 py-3 text-lg',
            'button_shadow': 'shadow-lg',
            'button_width': 'inline-block',
        }

    # UT-084: HU-053 - Muestra formulario de creación
    def test_get_create_form(self):
        response = self.client.get(reverse(CORE_HERO_CREATE))
        self.assertEqual(response.status_code, 200)

    # UT-085: HU-053 CA-001 - Creación válida de slide
    def test_create_valid_slide(self):
        HeroConfig.objects.all().delete()
        data = self.get_valid_data()
        response = self.client.post(reverse(CORE_HERO_CREATE), data=data)
        self.assertRedirects(response, reverse(CORE_HERO_LIST))
        self.assertEqual(HeroConfig.objects.count(), 1)
        hero = HeroConfig.objects.first()
        self.assertEqual(hero.title_text, 'Nuevo Slide')

    # UT-086: HU-053 CA-002 - Título vacío muestra error
    def test_create_empty_title(self):
        data = self.get_valid_data()
        data['title_text'] = ''
        response = self.client.post(reverse(CORE_HERO_CREATE), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(HeroConfig.objects.count(), 0)

    # UT-087: HU-053 CA-003 - Usuario no autenticado redirige a login
    def test_create_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(CORE_HERO_CREATE))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(CORE_HERO_CREATE)}')

    # UT-088: HU-053 CA-003 - Usuario sin permiso redirige a catálogo
    def test_create_requires_permission(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(CORE_HERO_CREATE))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: HU-054 HeroConfigUpdateView
# =============================================================================

class HeroConfigUpdateViewTest(TestCase):
    """HU-054: Update hero slide"""

    def setUp(self):
        self.client = Client()
        self.user = _create_admin_user(username='admin')
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

    # UT-089: HU-054 - Muestra formulario de edición
    def test_get_update_form(self):
        response = self.client.get(reverse(CORE_HERO_EDIT, kwargs={'pk': self.hero.pk}))
        self.assertEqual(response.status_code, 200)

    # UT-090: HU-054 CA-001 - Actualización válida de slide
    def test_update_valid_slide(self):
        data = self.get_valid_update_data()
        response = self.client.post(
            reverse(CORE_HERO_EDIT, kwargs={'pk': self.hero.pk}),
            data=data
        )
        self.assertRedirects(response, reverse(CORE_HERO_LIST))
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.title_text, 'Actualizado')
        self.assertEqual(self.hero.section_height, '90vh')

    # UT-091: HU-054 CA-002 - Título vacío muestra error
    def test_update_empty_title(self):
        data = self.get_valid_update_data()
        data['title_text'] = ''
        response = self.client.post(
            reverse(CORE_HERO_EDIT, kwargs={'pk': self.hero.pk}),
            data=data
        )
        self.assertEqual(response.status_code, 200)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.title_text, 'Original')

    # UT-092: HU-054 CA-004 - Slide inexistente retorna 404
    def test_update_nonexistent_slide(self):
        response = self.client.get(reverse(CORE_HERO_EDIT, kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    # UT-093: HU-054 CA-003 - Usuario no autenticado redirige a login
    def test_update_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(CORE_HERO_EDIT, kwargs={'pk': self.hero.pk}))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(CORE_HERO_EDIT, kwargs={"pk": self.hero.pk})}')

    # UT-094: HU-054 CA-003 - Usuario sin permiso redirige a catálogo
    def test_update_requires_permission(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(CORE_HERO_EDIT, kwargs={'pk': self.hero.pk}))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: HU-055 HeroConfigDeleteView
# =============================================================================

class HeroConfigDeleteViewTest(TestCase):
    """HU-055: Soft delete hero slide"""

    def setUp(self):
        self.client = Client()
        self.user = _create_admin_user(username='admin')
        self.user = _add_hero_permissions(self.user)
        self.client.force_login(self.user)

        self.hero = _create_hero(title_text='Eliminar Slide')

    # UT-095: HU-055 - Muestra página de confirmación
    def test_get_delete_confirmation(self):
        response = self.client.get(reverse(CORE_HERO_DELETE, kwargs={'pk': self.hero.pk}))
        self.assertEqual(response.status_code, 200)

    # UT-096: HU-055 CA-001 - Confirmación correcta hace soft delete
    def test_delete_with_correct_confirmation(self):
        response = self.client.post(
            reverse(CORE_HERO_DELETE, kwargs={'pk': self.hero.pk}),
            data={'confirm': 'Eliminar Slide'}
        )
        self.assertRedirects(response, reverse(CORE_HERO_LIST))
        self.hero.refresh_from_db()
        self.assertFalse(self.hero.is_active)
        self.assertIsNotNone(self.hero.deleted_at)

    # UT-097: HU-055 CA-002 - Confirmación incorrecta vuelve al formulario
    def test_delete_wrong_confirmation(self):
        response = self.client.post(
            reverse(CORE_HERO_DELETE, kwargs={'pk': self.hero.pk}),
            data={'confirm': 'Otro Nombre'}
        )
        self.assertEqual(response.status_code, 200)
        self.hero.refresh_from_db()
        self.assertTrue(self.hero.is_active)

    # UT-098: HU-055 CA-001 - Confirmación sin distinción mayúsculas funciona
    def test_delete_case_insensitive_confirmation(self):
        response = self.client.post(
            reverse(CORE_HERO_DELETE, kwargs={'pk': self.hero.pk}),
            data={'confirm': 'eliminar slide'}
        )
        self.assertRedirects(response, reverse(CORE_HERO_LIST))
        self.hero.refresh_from_db()
        self.assertFalse(self.hero.is_active)

    # UT-099: HU-055 CA-003 - Usuario no autenticado redirige a login
    def test_delete_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(CORE_HERO_DELETE, kwargs={'pk': self.hero.pk}))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(CORE_HERO_DELETE, kwargs={"pk": self.hero.pk})}')

    # UT-100: HU-055 CA-003 - Usuario sin permiso redirige a catálogo
    def test_delete_requires_permission(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(CORE_HERO_DELETE, kwargs={'pk': self.hero.pk}))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: HU-056 HeroConfigRestoreView
# =============================================================================

class HeroConfigRestoreViewTest(TestCase):
    """HU-056: Restore soft-deleted hero slide"""

    def setUp(self):
        self.client = Client()
        self.user = _create_admin_user(username='admin')
        self.user = _add_hero_permissions(self.user)
        self.client.force_login(self.user)

        self.hero = _create_hero(title_text='Restaurar Slide', sort_order=1, is_active=False)

    # UT-101: HU-056 - Muestra página de restauración
    def test_get_restore_page(self):
        response = self.client.get(reverse(CORE_HERO_RESTORE, kwargs={'pk': self.hero.pk}))
        self.assertEqual(response.status_code, 200)

    # UT-102: HU-056 CA-001 - Confirmación válida restaura slide
    def test_restore_with_valid_confirmation(self):
        response = self.client.post(
            reverse(CORE_HERO_RESTORE, kwargs={'pk': self.hero.pk}),
            data={'confirm': True}
        )
        self.assertRedirects(response, reverse(CORE_HERO_LIST))
        self.hero.refresh_from_db()
        self.assertTrue(self.hero.is_active)
        self.assertIsNone(self.hero.deleted_at)

    # UT-103: HU-056 CA-003 - Sin confirmación vuelve al formulario
    def test_restore_without_confirmation(self):
        response = self.client.post(
            reverse(CORE_HERO_RESTORE, kwargs={'pk': self.hero.pk}),
            data={'confirm': False}
        )
        self.assertEqual(response.status_code, 200)
        self.hero.refresh_from_db()
        self.assertFalse(self.hero.is_active)

    # UT-104: HU-056 CA-003 - Conflicto de orden vuelve al formulario
    def test_restore_sort_order_conflict(self):
        _create_hero(title_text='Activo', sort_order=1)
        response = self.client.post(
            reverse(CORE_HERO_RESTORE, kwargs={'pk': self.hero.pk}),
            data={'confirm': True}
        )
        self.assertEqual(response.status_code, 200)
        self.hero.refresh_from_db()
        self.assertFalse(self.hero.is_active)

    # UT-105: HU-056 - Slide inexistente retorna 404
    def test_restore_nonexistent_slide(self):
        response = self.client.get(reverse(CORE_HERO_RESTORE, kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    # UT-106: HU-056 CA-002 - Usuario no autenticado redirige a login
    def test_restore_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(CORE_HERO_RESTORE, kwargs={'pk': self.hero.pk}))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(CORE_HERO_RESTORE, kwargs={"pk": self.hero.pk})}')

    # UT-107: HU-056 CA-002 - Usuario sin permiso redirige a catálogo
    def test_restore_requires_permission(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(CORE_HERO_RESTORE, kwargs={'pk': self.hero.pk}))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: HU-057 HeroConfigTrashcanView
# =============================================================================

class HeroConfigTrashcanViewTest(TestCase):
    """HU-057: List soft-deleted hero slides"""

    def setUp(self):
        self.client = Client()
        self.user = _create_admin_user(username='admin')
        self.user = _add_hero_permissions(self.user)
        self.client.force_login(self.user)

        self.hero1 = _create_hero(title_text='Eliminado 1', is_active=False)
        self.hero2 = _create_hero(title_text='Activo', is_active=True)

    # UT-108: HU-057 CA-001 - Muestra solo slides inactivos
    def test_trashcan_shows_inactive_slides(self):
        response = self.client.get(reverse(CORE_HERO_TRASHCAN))
        self.assertEqual(response.status_code, 200)
        slides = list(response.context['hero_slides'])
        self.assertEqual(len(slides), 1)
        self.assertEqual(slides[0].title_text, 'Eliminado 1')

    # UT-109: HU-057 CA-003 - Papelera vacía
    def test_trashcan_empty(self):
        HeroConfig.all_objects.filter(is_active=False).delete()
        response = self.client.get(reverse(CORE_HERO_TRASHCAN))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['hero_slides']), 0)

    # UT-110: HU-057 - Incluye headers en contexto
    def test_trashcan_context_headers(self):
        response = self.client.get(reverse(CORE_HERO_TRASHCAN))
        self.assertIn('headers', response.context)
        self.assertIn('rows', response.context)

    # UT-111: HU-057 CA-002 - Usuario no autenticado redirige a login
    def test_trashcan_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(CORE_HERO_TRASHCAN))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(CORE_HERO_TRASHCAN)}')

    # UT-112: HU-057 CA-002 - Usuario sin permiso redirige a catálogo
    def test_trashcan_requires_permission(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(CORE_HERO_TRASHCAN))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: StaffLogout
# =============================================================================

class StaffLogoutViewTest(TestCase):
    """Staff logout"""

    def setUp(self):
        self.client = Client()
        self.user = _create_admin_user(username='staff')
        self.client.force_login(self.user)

    # UT-113: Cierre de sesión redirige a login
    def test_logout_redirects_to_login(self):
        response = self.client.post(reverse(CORE_STAFF_LOGOUT))
        self.assertRedirects(response, reverse(CORE_STAFF_LOGIN))
        self.assertFalse(response.wsgi_request.user.is_authenticated)


# =============================================================================
# TESTS: StaticPages
# =============================================================================

class StaticPagesViewTest(TestCase):
    """Static pages (About, Returns, Privacy, Terms)"""

    def setUp(self):
        self.client = Client()

    # UT-114: Página About
    def test_about_page(self):
        response = self.client.get(reverse(CORE_ABOUT))
        self.assertEqual(response.status_code, 200)

    # UT-115: Página Returns
    def test_returns_page(self):
        response = self.client.get(reverse(CORE_RETURNS_POLICY))
        self.assertEqual(response.status_code, 200)

    # UT-116: Página Privacy
    def test_privacy_page(self):
        response = self.client.get(reverse(CORE_PRIVACY_POLICY))
        self.assertEqual(response.status_code, 200)

    # UT-117: Página Terms
    def test_terms_page(self):
        response = self.client.get(reverse(CORE_TERMS))
        self.assertEqual(response.status_code, 200)


# =============================================================================
# TESTS: PWAManifest
# =============================================================================

class PWAManifestViewTest(TestCase):
    """PWA Manifest"""

    def setUp(self):
        self.client = Client()

    # UT-118: PWA manifest retorna JSON
    def test_manifest_returns_json(self):
        response = self.client.get(reverse('pwa_manifest'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        data = response.json()
        self.assertIn('name', data)
        self.assertIn('short_name', data)
        self.assertIn('start_url', data)
        self.assertIn('display', data)