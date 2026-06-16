from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch, Mock
from django.http import HttpRequest
from decimal import Decimal

from apps.core.forms import (
    ContactForm,
    StaffLoginForm,
    HeroConfigCreateForm,
    HeroConfigUpdateForm,
    HeroConfigDeleteForm,
    HeroConfigRestoreForm,
    build_button_style,
    get_button_url_choices,
)
from apps.core.models import HeroConfig
from apps.core.url_names import (
    PRODUCTS_CATALOG,
    PRODUCTS_COLLECTION_DETAIL,
    PRODUCTS_DETAIL,
)
from apps.core.constants import (
    LOGIN_ERROR_MESSAGE,
    LOGIN_INACTIVE_MESSAGE,
)
from apps.products.models import Category, Product, Collection

User = get_user_model()


# =============================================================================
# HELPERS
# =============================================================================

def _create_test_user(**kwargs):
    """Crea un usuario con atributos extra (is_delivery)."""
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
        name='Colección Verano',
        slug='coleccion-verano',
        status='publicada',
        is_active=True
    )


def _create_hero(**kwargs):
    defaults = {
        'title_text': 'Hero Test',
        'subtitle_text': 'Subtítulo',
        'button_text': 'Ir',
        'button_url': reverse(PRODUCTS_CATALOG),
        'button_style': 'bg-zicada-accent hover:bg-red-700 text-white rounded-lg px-8 py-3 text-lg shadow-lg inline-block font-semibold transition-all duration-300 transform hover:scale-105 inline-block text-center',
        'sort_order': 0,
        'section_height': '100vh',
        'title_font_size': '4rem',
        'title_line_height': '1.2',
        'title_margin_bottom': '1rem',
        'subtitle_font_size': '1.25rem',
        'subtitle_line_height': '1.5',
        'subtitle_margin_bottom': '2rem',
        'is_active': True,
    }
    defaults.update(kwargs)
    return HeroConfig.objects.create(**defaults)


# =============================================================================
# TESTS: build_button_style (Helper)
# =============================================================================

class BuildButtonStyleTest(TestCase):
    """Pruebas para build_button_style (helper, sin HU directa)"""
    
    # UT-001: build_button_style - clases CSS correctas
    def test_returns_correct_classes(self):
        data = {
            'button_bg_color': 'bg-zicada-accent',
            'button_hover_color': 'hover:bg-red-700',
            'button_text_color': 'text-white',
            'button_border_radius': 'rounded-lg',
            'button_size': 'px-8 py-3 text-lg',
            'button_shadow': 'shadow-lg',
            'button_width': 'inline-block',
        }
        result = build_button_style(data)
        expected = 'bg-zicada-accent hover:bg-red-700 text-white rounded-lg px-8 py-3 text-lg shadow-lg inline-block font-semibold transition-all duration-300 transform hover:scale-105 inline-block text-center'
        self.assertEqual(result, expected)

    # UT-002: build_button_style - valores personalizados
    def test_custom_values(self):
        data = {
            'button_bg_color': 'bg-blue-600',
            'button_hover_color': 'hover:bg-blue-700',
            'button_text_color': 'text-gray-900',
            'button_border_radius': 'rounded-full',
            'button_size': 'px-4 py-2 text-base',
            'button_shadow': 'shadow-none',
            'button_width': 'w-full',
        }
        result = build_button_style(data)
        self.assertIn('bg-blue-600', result)
        self.assertIn('hover:bg-blue-700', result)
        self.assertIn('text-gray-900', result)
        self.assertIn('rounded-full', result)
        self.assertIn('px-4 py-2 text-base', result)
        self.assertIn('shadow-none', result)
        self.assertIn('w-full', result)


# =============================================================================
# TESTS: get_button_url_choices (Helper)
# =============================================================================

class GetButtonUrlChoicesTest(TestCase):
    """Pruebas para get_button_url_choices (helper, HU-053 indirecta)"""
    
    # UT-003: get_button_url_choices - incluye catálogos estáticos
    def test_includes_static_choices(self):
        choices = get_button_url_choices()
        urls = [c[0] for c in choices]
        catalog_url = reverse(PRODUCTS_CATALOG)
        self.assertIn(catalog_url, urls)

    # UT-004: HU-053 CA-001 - incluye colecciones activas
    def test_includes_collections(self):
        coll = _create_test_collection()
        choices = get_button_url_choices()
        expected_url = reverse(PRODUCTS_COLLECTION_DETAIL, kwargs={'slug': coll.slug})
        self.assertTrue(
            any(expected_url == c[0] for c in choices),
            f'La colección {coll.slug} debería estar en las opciones'
        )

    # UT-005: HU-053 CA-001 - incluye productos activos
    def test_includes_products(self):
        cat = _create_test_category()
        prod = _create_test_product(category=cat)
        choices = get_button_url_choices()
        expected_url = reverse(PRODUCTS_DETAIL, kwargs={'slug': prod.slug})
        self.assertTrue(
            any(expected_url == c[0] for c in choices),
            f'El producto {prod.slug} debería estar en las opciones'
        )


# =============================================================================
# TESTS: HU-051 ContactForm
# =============================================================================

class ContactFormTest(TestCase):
    """HU-051: Formulario de contacto"""

    VALID_DATA = {
        'name': 'Juan Pérez',
        'email': 'juan@example.com',
        'subject': 'Consulta sobre producto',
        'message': 'Quiero saber el precio de la camiseta negra.',
    }

    # UT-006: HU-051 CA-001 - válido con teléfono
    def test_valid_form(self):
        data = self.VALID_DATA.copy()
        data['phone'] = '3001234567'
        form = ContactForm(data=data)
        self.assertTrue(form.is_valid())

    # UT-007: HU-051 CA-001 - válido sin teléfono
    def test_valid_form_without_phone(self):
        form = ContactForm(data=self.VALID_DATA)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['phone'], '')

    # UT-008: HU-051 CA-004 - nombre vacío da error
    def test_name_required(self):
        data = self.VALID_DATA.copy()
        data['name'] = ''
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('Por favor ingresa tu nombre', str(form.errors['name']))

    # UT-009: HU-051 CA-004 - nombre corto da error
    def test_name_min_length(self):
        data = self.VALID_DATA.copy()
        data['name'] = 'A'
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('al menos 2 caracteres', str(form.errors['name']))

    # UT-010: HU-051 CA-004 - email vacío da error
    def test_email_required(self):
        data = self.VALID_DATA.copy()
        data['email'] = ''
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    # UT-011: HU-051 CA-004 - email inválido da error
    def test_email_invalid_format(self):
        data = self.VALID_DATA.copy()
        data['email'] = 'correo-sin-arroba'
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('válido', str(form.errors['email']).lower())

    # UT-012: HU-051 CA-004 - asunto vacío da error
    def test_subject_required(self):
        data = self.VALID_DATA.copy()
        data['subject'] = ''
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)
        self.assertIn('asunto', str(form.errors['subject']).lower())

    # UT-013: HU-051 CA-004 - mensaje vacío da error
    def test_message_required(self):
        data = self.VALID_DATA.copy()
        data['message'] = ''
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('message', form.errors)
        self.assertIn('mensaje', str(form.errors['message']).lower())

    # UT-014: HU-051 CA-004 - teléfono corto da error
    def test_phone_too_short(self):
        data = self.VALID_DATA.copy()
        data['phone'] = '12345'
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)
        self.assertIn('al menos 7 dígitos', str(form.errors['phone']))

    # UT-015: HU-051 CA-004 - teléfono con letras da error
    def test_phone_only_digits_are_counted(self):
        data = self.VALID_DATA.copy()
        data['phone'] = 'abc 12 def 3'
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    # UT-016: HU-051 CA-001 - teléfono válido con 7 dígitos
    def test_phone_valid_with_7_digits(self):
        data = self.VALID_DATA.copy()
        data['phone'] = '3001234'
        form = ContactForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['phone'], '3001234')

    # UT-017: HU-051 CA-001 - teléfono con formato mixto válido
    def test_phone_strips_non_digits(self):
        data = self.VALID_DATA.copy()
        data['phone'] = '+57 (300) 123-4567'
        form = ContactForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['phone'], '573001234567')


# =============================================================================
# TESTS: HU-001 & HU-003 StaffLoginForm
# =============================================================================

class StaffLoginFormTest(TestCase):
    """HU-001: Inicio de sesión; HU-003: Control de acceso por permisos"""

    def setUp(self):
        self.user_staff = _create_test_user(username='staff', is_staff=True)
        self.user_delivery = _create_test_user(username='delivery', is_delivery=True)
        self.user_normal = _create_test_user(username='normal', is_staff=False)
        self.user_inactive = _create_test_user(username='inactive', is_staff=True, is_active=False)

        self.request = Mock(spec=HttpRequest)
        self.request.POST = {}

    # UT-018: HU-003 CA-001 - usuario staff permitido
    @patch('django.contrib.auth.forms.authenticate')
    def test_staff_user_allowed(self, mock_auth):
        mock_auth.return_value = self.user_staff
        form = StaffLoginForm(
            request=self.request,
            data={'username': 'staff', 'password': 'pass1234'}
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.user_cache, self.user_staff)

    # UT-019: HU-003 CA-002 - usuario delivery permitido
    @patch('django.contrib.auth.forms.authenticate')
    def test_delivery_user_allowed(self, mock_auth):
        mock_auth.return_value = self.user_delivery
        form = StaffLoginForm(
            request=self.request,
            data={'username': 'delivery', 'password': 'pass1234'}
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.user_cache, self.user_delivery)

    # UT-020: HU-003 CA-003 - usuario normal denegado
    @patch('django.contrib.auth.forms.authenticate')
    def test_normal_user_denied(self, mock_auth):
        mock_auth.return_value = self.user_normal
        form = StaffLoginForm(
            request=self.request,
            data={'username': 'normal', 'password': 'pass1234'}
        )
        self.assertFalse(form.is_valid())
        non_field_errors = form.non_field_errors()
        self.assertTrue(
            any('permisos' in str(error).lower() for error in non_field_errors)
        )

    # UT-021: HU-001 CA-004 - usuario inactivo denegado
    @patch('django.contrib.auth.forms.authenticate')
    def test_inactive_user_denied(self, mock_auth):
        mock_auth.return_value = self.user_inactive
        form = StaffLoginForm(
            request=self.request,
            data={'username': 'inactive', 'password': 'pass1234'}
        )
        self.assertFalse(form.is_valid())
        non_field_errors = form.non_field_errors()
        self.assertTrue(
            any(LOGIN_INACTIVE_MESSAGE.lower() in str(error).lower() for error in non_field_errors)
        )

    # UT-022: HU-001 CA-003 - credenciales incorrectas
    @patch('django.contrib.auth.forms.authenticate')
    def test_wrong_credentials(self, mock_auth):
        mock_auth.return_value = None
        form = StaffLoginForm(
            request=self.request,
            data={'username': 'staff', 'password': 'wrong'}
        )
        self.assertFalse(form.is_valid())
        non_field_errors = form.non_field_errors()
        self.assertTrue(
            any(LOGIN_ERROR_MESSAGE.lower() in str(error).lower() for error in non_field_errors)
        )

    # UT-023: HU-001 CA-003 - username vacío
    @patch('django.contrib.auth.forms.authenticate')
    def test_empty_username(self, mock_auth):
        mock_auth.return_value = None
        form = StaffLoginForm(
            request=self.request,
            data={'username': '', 'password': 'pass1234'}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('requerido', str(form.errors['username']).lower())

    # UT-024: HU-001 CA-003 - password vacío
    @patch('django.contrib.auth.forms.authenticate')
    def test_empty_password(self, mock_auth):
        mock_auth.return_value = None
        form = StaffLoginForm(
            request=self.request,
            data={'username': 'staff', 'password': ''}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
        self.assertIn('requerido', str(form.errors['password']).lower())

    # UT-025: HU-001 CA-003 - usuario inexistente
    @patch('django.contrib.auth.forms.authenticate')
    def test_nonexistent_user(self, mock_auth):
        mock_auth.return_value = None
        form = StaffLoginForm(
            request=self.request,
            data={'username': 'nonexistent', 'password': 'pass1234'}
        )
        self.assertFalse(form.is_valid())
        non_field_errors = form.non_field_errors()
        self.assertTrue(
            any(LOGIN_ERROR_MESSAGE.lower() in str(error).lower() for error in non_field_errors)
        )


# =============================================================================
# TESTS: HU-053 HeroConfigCreateForm
# =============================================================================

class HeroConfigCreateFormTest(TestCase):
    """HU-053: Crear slide del hero"""

    def setUp(self):
        self.category = _create_test_category()
        self.product = _create_test_product(category=self.category)
        self.collection = _create_test_collection()

    def get_valid_data(self):
        catalog_url = reverse(PRODUCTS_CATALOG)
        return {
            'background_image': '',
            'overlay_opacity': 0.5,
            'title_text': 'Hero de prueba',
            'title_font_family': "'Inter', sans-serif",
            'title_font_size': '4rem',
            'title_font_weight': '800',
            'title_line_height': '1.2',
            'title_color': '#ffffff',
            'title_margin_bottom': '1rem',
            'subtitle_text': 'Subtítulo de prueba',
            'subtitle_font_family': "'Inter', sans-serif",
            'subtitle_font_size': '1.25rem',
            'subtitle_font_weight': '400',
            'subtitle_line_height': '1.5',
            'subtitle_color': '#e5e5e5',
            'subtitle_margin_bottom': '2rem',
            'button_text': 'Explorar',
            'button_url': catalog_url,
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
        }

    # UT-026: HU-053 CA-001 - datos válidos crea slide
    def test_create_valid_slide(self):
        data = self.get_valid_data()
        form = HeroConfigCreateForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Errores: {form.errors}")
        hero = form.save()
        self.assertEqual(hero.title_text, 'Hero de prueba')
        self.assertIn('bg-zicada-accent', hero.button_style)
        self.assertEqual(hero.sort_order, 0)

    # UT-027: HU-053 CA-002 - título vacío da error
    def test_title_required(self):
        data = self.get_valid_data()
        data['title_text'] = ''
        form = HeroConfigCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('title_text', form.errors)
        self.assertIn('requerido', str(form.errors['title_text']).lower())

    # UT-028: HU-053 CA-001 - save construye button_style
    def test_save_builds_button_style(self):
        data = self.get_valid_data()
        data['button_bg_color'] = 'bg-blue-600'
        data['button_hover_color'] = 'hover:bg-blue-700'
        form = HeroConfigCreateForm(data=data)
        self.assertTrue(form.is_valid())
        hero = form.save()
        self.assertIn('bg-blue-600', hero.button_style)
        self.assertIn('hover:bg-blue-700', hero.button_style)


# =============================================================================
# TESTS: HU-054 HeroConfigUpdateForm
# =============================================================================

class HeroConfigUpdateFormTest(TestCase):
    """HU-054: Editar slide del hero"""

    def setUp(self):
        self.category = _create_test_category()
        self.product = _create_test_product(category=self.category)
        self.collection = _create_test_collection()
        self.hero = _create_hero(
            title_text='Original',
            button_style='bg-zicada-accent hover:bg-red-700 text-white rounded-lg px-8 py-3 text-lg shadow inline-block font-semibold transition-all duration-300 transform hover:scale-105 inline-block text-center'
        )
        self.hero.sort_order = 0
        self.hero.save()

    def get_update_data(self):
        catalog_url = reverse(PRODUCTS_CATALOG)
        return {
            'background_image': '',
            'overlay_opacity': 0.7,
            'title_text': 'Actualizado',
            'title_font_family': "'Inter', sans-serif",
            'title_font_size': '3rem',
            'title_font_weight': '700',
            'title_line_height': '1.4',
            'title_color': '#000000',
            'title_margin_bottom': '0.5rem',
            'subtitle_text': 'Nuevo subtítulo',
            'subtitle_font_family': "'Roboto', sans-serif",
            'subtitle_font_size': '1rem',
            'subtitle_font_weight': '500',
            'subtitle_line_height': '1.6',
            'subtitle_color': '#333333',
            'subtitle_margin_bottom': '1rem',
            'button_text': 'Ir ahora',
            'button_url': catalog_url,
            'button_bg_color': 'bg-black',
            'button_hover_color': 'hover:bg-gray-700',
            'button_text_color': 'text-gray-900',
            'button_border_radius': 'rounded-full',
            'button_size': 'px-6 py-2.5 text-base',
            'button_shadow': 'shadow-md',
            'button_width': 'w-48',
            'content_alignment': 'left',
            'section_height': '90vh',
            'is_active': True,
        }

    # UT-029: HU-054 CA-001 - actualización válida
    def test_update_valid_slide(self):
        data = self.get_update_data()
        form = HeroConfigUpdateForm(data=data, instance=self.hero)
        self.assertTrue(form.is_valid(), msg=f"Errores: {form.errors}")
        hero = form.save()
        self.assertEqual(hero.title_text, 'Actualizado')
        self.assertEqual(hero.section_height, '90vh')

    # UT-030: HU-054 CA-001 - parsea button_style existente
    def test_parse_button_style_from_instance(self):
        form = HeroConfigUpdateForm(instance=self.hero)
        self.assertEqual(form.fields['button_bg_color'].initial, 'bg-zicada-accent')
        self.assertEqual(form.fields['button_hover_color'].initial, 'hover:bg-red-700')
        self.assertEqual(form.fields['button_text_color'].initial, 'text-white')

    # UT-031: HU-054 CA-001 - save actualiza button_style
    def test_save_updates_button_style(self):
        data = self.get_update_data()
        data['button_bg_color'] = 'bg-purple-600'
        data['button_hover_color'] = 'hover:bg-purple-700'
        form = HeroConfigUpdateForm(data=data, instance=self.hero)
        self.assertTrue(form.is_valid())
        hero = form.save()
        self.assertIn('bg-purple-600', hero.button_style)
        self.assertIn('hover:bg-purple-700', hero.button_style)

    # UT-032: HU-054 CA-002 - datos inválidos da error
    def test_invalid_data(self):
        data = self.get_update_data()
        data['title_text'] = ''
        form = HeroConfigUpdateForm(data=data, instance=self.hero)
        self.assertFalse(form.is_valid())
        self.assertIn('title_text', form.errors)


# =============================================================================
# TESTS: HU-055 HeroConfigDeleteForm
# =============================================================================

class HeroConfigDeleteFormTest(TestCase):
    """HU-055: Archivar slide del hero"""

    def setUp(self):
        self.hero = _create_hero(title_text='Eliminar Slide')

    # UT-033: HU-055 CA-001 - confirmación correcta
    def test_correct_confirmation(self):
        form = HeroConfigDeleteForm(data={'confirm': 'Eliminar Slide'}, slide=self.hero)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['confirm'], 'eliminar slide')

    # UT-034: HU-055 CA-002 - confirmación incorrecta
    def test_wrong_confirmation(self):
        form = HeroConfigDeleteForm(data={'confirm': 'Otro Nombre'}, slide=self.hero)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)
        self.assertIn('no coincide', str(form.errors['confirm']).lower())

    # UT-035: HU-055 CA-001 - case insensitive
    def test_case_insensitive(self):
        form = HeroConfigDeleteForm(data={'confirm': 'eliminar slide'}, slide=self.hero)
        self.assertTrue(form.is_valid())

    # UT-036: HU-055 CA-003 - sin slide da error
    def test_no_slide_provided(self):
        form = HeroConfigDeleteForm(data={'confirm': 'Eliminar Slide'})
        self.assertFalse(form.is_valid())
        self.assertIn('Slide no especificado', str(form.errors.get('confirm', '')))


# =============================================================================
# TESTS: HU-056 HeroConfigRestoreForm
# =============================================================================

class HeroConfigRestoreFormTest(TestCase):
    """HU-056: Restaurar slide archivado"""

    def setUp(self):
        self.hero = _create_hero(title_text='Restaurar Slide', sort_order=1, is_active=False)

    # UT-037: HU-056 CA-001 - restauración válida
    def test_correct_confirmation(self):
        HeroConfig.objects.filter(is_active=True, sort_order=1).update(sort_order=999)
        form = HeroConfigRestoreForm(data={'confirm': True}, slide=self.hero)
        self.assertTrue(form.is_valid(), f"Errores: {form.errors}")

    # UT-038: HU-056 CA-003 - confirmación no marcada
    def test_confirmation_not_checked(self):
        form = HeroConfigRestoreForm(data={'confirm': False}, slide=self.hero)
        self.assertFalse(form.is_valid())
        self.assertIn('confirmar', str(form.errors.get('__all__', '')).lower())

    # UT-039: HU-056 CA-003 - conflicto de orden
    def test_sort_order_conflict(self):
        _create_hero(title_text='Activo', sort_order=1)
        form = HeroConfigRestoreForm(data={'confirm': True}, slide=self.hero)
        self.assertFalse(form.is_valid())
        self.assertIn('Ya existe un slide activo', str(form.errors.get('__all__', '')))

    # UT-040: HU-056 CA-004 - sin slide da error
    def test_no_slide_provided(self):
        form = HeroConfigRestoreForm(data={'confirm': True})
        self.assertFalse(form.is_valid())
        self.assertIn('Slide no especificado', str(form.errors.get('__all__', '')))