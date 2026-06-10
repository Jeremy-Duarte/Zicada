"""
Tests unitarios para formularios de apps.core.forms

Cubre:
- HU-051: ContactForm
- HU-001 y HU-003: StaffLoginForm
- HU-053: HeroConfigCreateForm
- HU-054: HeroConfigUpdateForm
- HU-055: HeroConfigDeleteForm
- HU-056: HeroConfigRestoreForm
- build_button_style (helper)
- get_button_url_choices (helper)
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch, Mock
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
from apps.products.models import Category, Product, Collection

User = get_user_model()


# =============================================================================
# HELPERS COMUNES
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
    
    # Si el modelo tiene campo is_delivery (opcional)
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
# TESTS: build_button_style
# =============================================================================

class BuildButtonStyleTest(TestCase):
    """Pruebas unitarias para la función build_button_style (helper, no HU)"""

    def test_returns_correct_classes(self):
        """HU-053 | ESCENARIO 1 | H | Construye clases CSS del botón a partir de campos individuales"""
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

    def test_custom_values(self):
        """Verifica que valores personalizados se reflejen en el resultado"""
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
# TESTS: get_button_url_choices
# =============================================================================

class GetButtonUrlChoicesTest(TestCase):
    """Pruebas para la función que genera opciones de URL del botón (helper)"""

    def test_includes_static_choices(self):
        """Verifica que los catálogos estáticos estén presentes"""
        choices = get_button_url_choices()
        urls = [c[0] for c in choices]
        catalog_url = reverse(PRODUCTS_CATALOG)
        self.assertIn(catalog_url, urls)

    def test_includes_collections(self):
        """HU-053 | ESCENARIO 1 | H | Carga colecciones activas y publicadas"""
        coll = _create_test_collection()
        choices = get_button_url_choices()
        expected_url = reverse(PRODUCTS_COLLECTION_DETAIL, kwargs={'slug': coll.slug})
        
        self.assertTrue(
            any(expected_url == c[0] for c in choices),
            f'La colección {coll.slug} debería estar en las opciones con URL {expected_url}'
        )

    def test_includes_products(self):
        """HU-053 | ESCENARIO 1 | H | Carga productos activos"""
        cat = _create_test_category()
        prod = _create_test_product(category=cat)
        choices = get_button_url_choices()
        expected_url = reverse(PRODUCTS_DETAIL, kwargs={'slug': prod.slug})
        
        self.assertTrue(
            any(expected_url == c[0] for c in choices),
            f'El producto {prod.slug} debería estar en las opciones con URL {expected_url}'
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

    def test_valid_form(self):
        """HU-051 | ESCENARIO 2 | H | Formulario válido con nombre, email, asunto, mensaje y teléfono opcional"""
        data = self.VALID_DATA.copy()
        data['phone'] = '3001234567'
        form = ContactForm(data=data)
        self.assertTrue(form.is_valid())

    def test_valid_form_without_phone(self):
        """HU-051 | ESCENARIO 2 | H | Formulario válido sin teléfono"""
        form = ContactForm(data=self.VALID_DATA)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['phone'], '')

    def test_name_required(self):
        """HU-051 | ESCENARIO 4A | A | Nombre vacío → error 'required'"""
        data = self.VALID_DATA.copy()
        data['name'] = ''
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('Por favor ingresa tu nombre', str(form.errors['name']))

    def test_name_min_length(self):
        """HU-051 | ESCENARIO 4A | A | Nombre con menos de 2 caracteres"""
        data = self.VALID_DATA.copy()
        data['name'] = 'A'
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('al menos 2 caracteres', str(form.errors['name']))

    def test_email_required(self):
        """HU-051 | ESCENARIO 4A | A | Email vacío → error 'required'"""
        data = self.VALID_DATA.copy()
        data['email'] = ''
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_email_invalid_format(self):
        """HU-051 | ESCENARIO 4C | A | Email inválido (falta @) → error 'invalid'"""
        data = self.VALID_DATA.copy()
        data['email'] = 'correo-sin-arroba'
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('válido', str(form.errors['email']).lower())

    def test_subject_required(self):
        """HU-051 | ESCENARIO 4A | A | Asunto vacío → error 'required'"""
        data = self.VALID_DATA.copy()
        data['subject'] = ''
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)
        self.assertIn('asunto', str(form.errors['subject']).lower())

    def test_message_required(self):
        """HU-051 | ESCENARIO 4A | A | Mensaje vacío → error 'required'"""
        data = self.VALID_DATA.copy()
        data['message'] = ''
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('message', form.errors)
        self.assertIn('mensaje', str(form.errors['message']).lower())

    def test_phone_too_short(self):
        """HU-051 | ESCENARIO 4B | A | Teléfono con menos de 7 dígitos → error en clean_phone"""
        data = self.VALID_DATA.copy()
        data['phone'] = '12345'
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)
        self.assertIn('al menos 7 dígitos', str(form.errors['phone']))

    def test_phone_only_digits_are_counted(self):
        """HU-051 | ESCENARIO 4B | A | Teléfono con letras y dígitos insuficientes"""
        data = self.VALID_DATA.copy()
        data['phone'] = 'abc 12 def 3'
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_phone_valid_with_7_digits(self):
        """HU-051 | ESCENARIO 2 | H | Teléfono opcional válido con exactamente 7 dígitos"""
        data = self.VALID_DATA.copy()
        data['phone'] = '3001234'
        form = ContactForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['phone'], '3001234')

    def test_phone_strips_non_digits(self):
        """HU-051 | ESCENARIO 2 | H | Teléfono válido con guiones, espacios, etc."""
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

        self.request = Mock()
        self.request.POST = {}

    @patch('django.contrib.auth.forms.authenticate')
    def test_staff_user_allowed(self, mock_auth):
        """HU-003 | ESCENARIO 1 | H | Usuario staff con permisos"""
        mock_auth.return_value = self.user_staff
        form = StaffLoginForm(
            request=self.request,
            data={'username': 'staff', 'password': 'pass1234'}
        )
        self.assertTrue(form.is_valid())

    @patch('django.contrib.auth.forms.authenticate')
    def test_delivery_user_allowed(self, mock_auth):
        """HU-003 | ESCENARIO 2 | H | Usuario delivery con permisos"""
        mock_auth.return_value = self.user_delivery
        form = StaffLoginForm(
            request=self.request,
            data={'username': 'delivery', 'password': 'pass1234'}
        )
        self.assertTrue(form.is_valid())

    @patch('django.contrib.auth.forms.authenticate')
    def test_normal_user_denied(self, mock_auth):
        """HU-003 | ESCENARIO 3 | E | Usuario sin permisos (ni staff ni delivery)"""
        mock_auth.return_value = self.user_normal
        form = StaffLoginForm(
            request=self.request,
            data={'username': 'normal', 'password': 'pass1234'}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('No tienes permisos', str(form.errors.get('__all__', [])))

    @patch('django.contrib.auth.forms.authenticate')
    def test_inactive_user_denied(self, mock_auth):
        """HU-001 | ESCENARIO 4 | E | Usuario inactivo"""
        mock_auth.return_value = self.user_inactive
        form = StaffLoginForm(
            request=self.request,
            data={'username': 'inactive', 'password': 'pass1234'}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('inactiva', str(form.errors.get('__all__', [])).lower())

    @patch('django.contrib.auth.forms.authenticate')
    def test_wrong_credentials(self, mock_auth):
        """HU-001 | ESCENARIO 3 | E | Credenciales incorrectas (authenticate retorna None)"""
        mock_auth.return_value = None
        form = StaffLoginForm(
            request=self.request,
            data={'username': 'staff', 'password': 'wrong'}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('usuario y contraseña', str(form.errors.get('__all__', [])).lower())


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
        """Retorna datos válidos usando URLs reales"""
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

    def test_create_valid_slide(self):
        """HU-053 | ESCENARIO 1 | H | Datos válidos → formulario válido y guarda"""
        data = self.get_valid_data()
        form = HeroConfigCreateForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Errores: {form.errors}")

        hero = form.save()
        self.assertEqual(hero.title_text, 'Hero de prueba')
        self.assertIn('bg-zicada-accent', hero.button_style)
        self.assertIn('hover:bg-red-700', hero.button_style)
        self.assertEqual(hero.sort_order, 0)

    def test_title_required(self):
        """HU-053 | ESCENARIO 2 | A | Título vacío → error"""
        data = self.get_valid_data()
        data['title_text'] = ''
        form = HeroConfigCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('title_text', form.errors)
        self.assertIn('requerido', str(form.errors['title_text']).lower())

    def test_sort_order_duplicate(self):
        """HU-053 | ESCENARIO 2 | A | sort_order duplicado → error"""
        _create_hero(sort_order=0)
        data = self.get_valid_data()
        data['sort_order'] = 0
        form = HeroConfigCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('sort_order', form.errors)
        self.assertIn('ya existe', str(form.errors['sort_order']).lower())

    def test_save_builds_button_style(self):
        """HU-053 | ESCENARIO 1 | H | save() construye button_style automáticamente"""
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
        """Retorna datos de actualización usando URLs reales"""
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

    def test_update_valid_slide(self):
        """HU-054 | ESCENARIO 1 | H | Actualización válida de todos los campos"""
        data = self.get_update_data()
        form = HeroConfigUpdateForm(data=data, instance=self.hero)
        self.assertTrue(form.is_valid(), msg=f"Errores: {form.errors}")

        hero = form.save()
        self.assertEqual(hero.title_text, 'Actualizado')
        self.assertEqual(hero.section_height, '90vh')
        self.assertEqual(hero.title_font_size, '3rem')
        self.assertEqual(hero.content_alignment, 'left')

    def test_parse_button_style_from_instance(self):
        """
        HU-054 | ESCENARIO 1 | H | Parsea el estilo del botón e inicializa los campos
        """
        form = HeroConfigUpdateForm(instance=self.hero)
        self.assertEqual(form.fields['button_bg_color'].initial, 'bg-zicada-accent')
        self.assertEqual(form.fields['button_hover_color'].initial, 'hover:bg-red-700')
        self.assertEqual(form.fields['button_text_color'].initial, 'text-white')
        self.assertEqual(form.fields['button_border_radius'].initial, 'rounded-lg')
        self.assertEqual(form.fields['button_size'].initial, 'px-8 py-3 text-lg')
        # El botón usa 'shadow' sin -lg en el hero creado
        self.assertEqual(form.fields['button_shadow'].initial, 'shadow')
        self.assertEqual(form.fields['button_width'].initial, 'inline-block')

    def test_save_updates_button_style(self):
        """HU-054 | ESCENARIO 1 | H | save() actualiza button_style según nuevos valores"""
        data = self.get_update_data()
        data['button_bg_color'] = 'bg-purple-600'
        data['button_hover_color'] = 'hover:bg-purple-700'

        form = HeroConfigUpdateForm(data=data, instance=self.hero)
        self.assertTrue(form.is_valid())
        hero = form.save()
        self.assertIn('bg-purple-600', hero.button_style)
        self.assertIn('hover:bg-purple-700', hero.button_style)

    def test_invalid_data(self):
        """HU-054 | ESCENARIO 2 | A | Datos inválidos (título vacío) → formulario inválido"""
        data = self.get_update_data()
        data['title_text'] = ''
        form = HeroConfigUpdateForm(data=data, instance=self.hero)
        self.assertFalse(form.is_valid())
        self.assertIn('title_text', form.errors)


# =============================================================================
# TESTS: HU-055 HeroConfigDeleteForm
# =============================================================================

class HeroConfigDeleteFormTest(TestCase):
    """HU-055: Archivar slide del hero (soft delete)"""

    def setUp(self):
        self.hero = _create_hero(title_text='Eliminar Slide')

    def test_correct_confirmation(self):
        """HU-055 | ESCENARIO 1 | H | Confirmación correcta → formulario válido"""
        form = HeroConfigDeleteForm(data={'confirm': 'Eliminar Slide'}, slide=self.hero)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['confirm'], 'eliminar slide')

    def test_wrong_confirmation(self):
        """HU-055 | ESCENARIO 2 | A | Confirmación incorrecta → error"""
        form = HeroConfigDeleteForm(data={'confirm': 'Otro Nombre'}, slide=self.hero)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)
        self.assertIn('no coincide', str(form.errors['confirm']).lower())

    def test_case_insensitive(self):
        """HU-055 | ESCENARIO 1 | H | Confirmación con mayúsculas/minúsculas mezcladas"""
        form = HeroConfigDeleteForm(data={'confirm': 'eliminar slide'}, slide=self.hero)
        self.assertTrue(form.is_valid())

    def test_no_slide_provided(self):
        """HU-055 | ESCENARIO 3 | E | Slide no especificado → error"""
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

    def test_correct_confirmation(self):
        """HU-056 | ESCENARIO 1 | H | Restauración válida con confirmación marcada y sin conflictos"""
        HeroConfig.objects.filter(is_active=True, sort_order=1).update(sort_order=999)
        form = HeroConfigRestoreForm(data={'confirm': True}, slide=self.hero)
        self.assertTrue(form.is_valid(), f"Errores: {form.errors}")

    def test_confirmation_not_checked(self):
        """HU-056 | ESCENARIO 3 | A | Confirmación no marcada → error"""
        form = HeroConfigRestoreForm(data={'confirm': False}, slide=self.hero)
        self.assertFalse(form.is_valid())
        self.assertIn('confirmar', str(form.errors.get('__all__', '')).lower())

    def test_sort_order_conflict(self):
        """HU-056 | ESCENARIO 3 | A | Conflicto de orden → error"""
        _create_hero(title_text='Activo', sort_order=1)
        form = HeroConfigRestoreForm(data={'confirm': True}, slide=self.hero)
        self.assertFalse(form.is_valid())
        self.assertIn('Ya existe un slide activo', str(form.errors.get('__all__', '')))

    def test_no_slide_provided(self):
        """HU-056 | ESCENARIO 4 | E | Slide no especificado → error"""
        form = HeroConfigRestoreForm(data={'confirm': True})
        self.assertFalse(form.is_valid())
        self.assertIn('Slide no especificado', str(form.errors.get('__all__', '')))