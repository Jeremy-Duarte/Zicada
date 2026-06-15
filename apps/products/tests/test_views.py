"""
Tests para vistas de la app products.
CP-225 a CP-320

Cubre:
- Stock Dashboard (CP-225 a CP-232)
- Product Catalog (CP-233 a CP-245)
- Public Collection List (CP-246 a CP-260)
- Collection Detail (CP-261 a CP-273)
- Product Detail (CP-274 a CP-285)
- Size CRUD (CP-286 a CP-296)
- Category CRUD (CP-297 a CP-307)
- Color CRUD (CP-308 a CP-318)
- Product Image CRUD (CP-319 a CP-328)
- Product CRUD (CP-329 a CP-345)
- Product Color CRUD (CP-346 a CP-355)
- Product Variant CRUD (CP-356 a CP-370)
- Collection CRUD (CP-371 a CP-395)
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group as AuthGroup
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

from apps.core.url_names import (
    PRODUCTS_CATALOG,
    PRODUCTS_STOCK_DASHBOARD,
    PRODUCTS_SIZE_LIST,
    PRODUCTS_SIZE_CREATE,
    PRODUCTS_SIZE_EDIT,
    PRODUCTS_SIZE_DELETE,
    PRODUCTS_SIZE_IMPORT,
    PRODUCTS_SIZE_TEMPLATE,
    PRODUCTS_CATEGORY_LIST,
    PRODUCTS_CATEGORY_CREATE,
    PRODUCTS_CATEGORY_EDIT,
    PRODUCTS_CATEGORY_DELETE,
    PRODUCTS_CATEGORY_IMPORT,
    PRODUCTS_CATEGORY_TEMPLATE,
    PRODUCTS_COLOR_LIST,
    PRODUCTS_COLOR_CREATE,
    PRODUCTS_COLOR_EDIT,
    PRODUCTS_COLOR_DELETE,
    PRODUCTS_COLOR_IMPORT,
    PRODUCTS_COLOR_TEMPLATE,
    PRODUCTS_IMAGE_LIST,
    PRODUCTS_IMAGE_CREATE,
    PRODUCTS_IMAGE_EDIT,
    PRODUCTS_IMAGE_DELETE,
    PRODUCTS_LIST,
    PRODUCTS_CREATE,
    PRODUCTS_EDIT,
    PRODUCTS_DELETE,
    PRODUCTS_RESTORE,
    PRODUCTS_TRASHCAN,
    PRODUCTS_COLLECTION_LIST,
    PRODUCTS_COLLECTION_CREATE,
    PRODUCTS_COLLECTION_EDIT,
    PRODUCTS_COLLECTION_DELETE,
    PRODUCTS_COLLECTION_RESTORE,
    PRODUCTS_COLLECTION_TRASHCAN,
    PRODUCTS_COLLECTION_STYLE,
    PRODUCTS_COLLECTIONS_LIST,
    PRODUCTS_COLLECTION_DETAIL,
    PRODUCTS_DETAIL,
    CORE_STAFF_LOGIN,
)

from apps.products.constants import (
    STOCK_LOW_THRESHOLD,
    STATUS_PUBLISHED,
    STATUS_DRAFT,
    STATUS_ARCHIVED,
    MSG_SIZE_CREATED,
    MSG_SIZE_UPDATED,
    MSG_SIZE_DELETED,
    MSG_CATEGORY_CREATED,
    MSG_CATEGORY_UPDATED,
    MSG_CATEGORY_DELETED,
    MSG_COLOR_CREATED,
    MSG_COLOR_UPDATED,
    MSG_COLOR_DELETED,
    MSG_PRODUCT_IMAGE_UPLOADED,
    MSG_PRODUCT_IMAGE_UPDATED,
    MSG_PRODUCT_IMAGE_DELETED,
    MSG_PRODUCT_CREATED,
    MSG_PRODUCT_UPDATED,
    MSG_PRODUCT_DELETED,
    MSG_PRODUCT_RESTORED,
    MSG_VARIANT_CREATED,
    MSG_VARIANT_UPDATED,
    MSG_VARIANT_DELETED,
    MSG_VARIANT_RESTORED,
    MSG_COLLECTION_CREATED,
    MSG_COLLECTION_UPDATED,
    MSG_COLLECTION_DELETED,
    MSG_COLLECTION_RESTORED,
    MSG_COLLECTION_STYLE_UPDATED,
    TEMPLATE_CATALOG,
    TEMPLATE_COLLECTIONS_LIST_PUBLIC,
    TEMPLATE_COLLECTION_DETAIL,
    TEMPLATE_PRODUCT_DETAIL,
    TEMPLATE_SIZE_LIST,
    TEMPLATE_SIZE_FORM,
    TEMPLATE_SIZE_CONFIRM_DELETE,
    TEMPLATE_CATEGORY_LIST,
    TEMPLATE_CATEGORY_FORM,
    TEMPLATE_CATEGORY_CONFIRM_DELETE,
    TEMPLATE_COLOR_LIST,
    TEMPLATE_COLOR_FORM,
    TEMPLATE_COLOR_CONFIRM_DELETE,
    TEMPLATE_PRODUCTIMAGE_LIST,
    TEMPLATE_PRODUCTIMAGE_FORM,
    TEMPLATE_PRODUCTIMAGE_CONFIRM_DELETE,
    TEMPLATE_PRODUCT_LIST,
    TEMPLATE_PRODUCT_FORM,
    TEMPLATE_PRODUCT_CONFIRM_DELETE,
    TEMPLATE_PRODUCT_RESTORE,
    TEMPLATE_PRODUCT_TRASHCAN,
    TEMPLATE_COLLECTIONS_LIST,
    TEMPLATE_COLLECTION_FORM,
    TEMPLATE_COLLECTION_CONFIRM_DELETE,
    TEMPLATE_COLLECTION_RESTORE,
    TEMPLATE_COLLECTION_TRASHCAN,
    TEMPLATE_COLLECTION_STYLE_FORM,
    TEMPLATE_STOCK_DASHBOARD,
    QUERY_PARAM_SEARCH,
    QUERY_PARAM_MIN_PRICE,
    QUERY_PARAM_MAX_PRICE,
    QUERY_PARAM_CATEGORY,
    QUERY_PARAM_ORDER_BY,
    QUERY_PARAM_DATE_FILTER,
    DATE_FILTER_UPCOMING,
)

from apps.products.models import (
    Size, Category, Color, Product, ProductImage,
    ProductColor, ProductVariant, Collection
)

User = get_user_model()


# =============================================================================
# HELPERS - MODIFICADOS PARA USAR ROLES
# =============================================================================

def _create_test_image():
    """Crea una imagen de prueba para tests."""
    return SimpleUploadedFile(
        "test_image.jpg",
        b"fake_image_content",
        content_type="image/jpeg"
    )


def _create_admin_user(**kwargs):
    """Crea un usuario con rol Administrador."""
    from django.contrib.auth.models import Group as AuthGroup
    
    defaults = {'username': 'admin', 'password': 'pass1234', 'is_staff': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    
    # Assign Administrador role
    admin_group, _ = AuthGroup.objects.get_or_create(name='Administrador')
    user.groups.add(admin_group)
    
    return user


def _create_delivery_user(**kwargs):
    """Crea un usuario con rol Entregador."""
    from django.contrib.auth.models import Group as AuthGroup
    
    defaults = {'username': 'delivery', 'password': 'pass1234', 'is_delivery': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    
    # Assign Entregador role
    delivery_group, _ = AuthGroup.objects.get_or_create(name='Entregador')
    user.groups.add(delivery_group)
    
    return user


def _create_normal_user(**kwargs):
    """Crea un usuario sin roles especiales."""
    defaults = {'username': 'normal', 'password': 'pass1234', 'is_staff': False}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    
    return user


def _create_staff_user(**kwargs):
    """Crea un usuario staff con rol Administrador (para compatibilidad)."""
    defaults = {'username': 'staff', 'password': 'pass1234', 'is_staff': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    
    # Assign Administrador role
    admin_group, _ = AuthGroup.objects.get_or_create(name='Administrador')
    user.groups.add(admin_group)
    
    return user


def _create_category(name="Test Category", sort_order=0):
    """HU-063 | ESCENARIO 1 | H | Crea categoría para pruebas."""
    return Category.objects.create(name=name, sort_order=sort_order)


def _create_size(name="M", sort_order=0):
    """HU-058 | ESCENARIO 1 | H | Crea talla para pruebas."""
    return Size.objects.create(name=name, sort_order=sort_order)


def _create_color(name="Rojo", code="#FF0000", sort_order=0):
    """HU-068 | ESCENARIO 1 | H | Crea color para pruebas."""
    return Color.objects.create(name=name, code=code, sort_order=sort_order)


def _create_product(name="Test Product", price=100.00, category=None, product_type='fabrica', is_active=True):
    """HU-010 | ESCENARIO 1 | H | Crea producto para pruebas (slug se genera automáticamente)."""
    if category is None:
        category = _create_category()
    return Product.objects.create(
        name=name, price=price, category=category,
        product_type=product_type, is_active=is_active
    )


def _create_product_color(product, color, featured_image=None, sort_order=0, is_active=True):
    """HU-013 | ESCENARIO 1 | H | Asigna color a producto para pruebas."""
    return ProductColor.objects.create(
        product=product, color=color, featured_image=featured_image,
        sort_order=sort_order, is_active=is_active
    ) 


def _create_variant(product_color, size, stock=10, is_active=True):
    """HU-013 | ESCENARIO 1 | H | Crea variante (talla+stock) para pruebas."""
    product = product_color.product
    return ProductVariant.objects.create(
        product=product,
        product_color=product_color,
        size=size,
        stock=stock,
        is_active=is_active
    )


def _create_collection(name="Test Collection", status=STATUS_DRAFT, is_active=True):
    """HU-015 | ESCENARIO 1 | H | Crea colección para pruebas (slug se genera automáticamente)."""
    return Collection.objects.create(name=name, status=status, is_active=is_active)


def _add_product_to_collection(product, collection):
    """HU-018 | ESCENARIO 1 | H | Asigna producto a colección."""
    collection.products.add(product)
    collection.save()


def _create_product_with_variants():
    """Crea un producto completo con color y variante para pruebas de detalle."""
    category = _create_category()
    size = _create_size()
    color = _create_color()
    product = _create_product(name="Producto Test", category=category)
    product_color = _create_product_color(product, color)
    variant = _create_variant(product_color, size, stock=10)
    return product, product_color, variant


# =============================================================================
# TESTS: STOCK DASHBOARD (CP-225 a CP-232)
# =============================================================================

class StockDashboardTest(TestCase):
    """Pruebas para el dashboard de stock."""

    def setUp(self):
        self.client = Client()
        # Usar usuario con rol Administrador
        self.admin_user = _create_admin_user(username='admin', is_staff=True)
        self.client.force_login(self.admin_user)

    def test_stock_dashboard_requires_authentication(self):
        """CP-226 | Sin autenticación → redirección al login con next."""
        self.client.logout()
        response = self.client.get(reverse(PRODUCTS_STOCK_DASHBOARD))
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse(CORE_STAFF_LOGIN),
            response.url
        )
        self.assertIn(
            f'next={reverse(PRODUCTS_STOCK_DASHBOARD)}',
            response.url
        )

    def test_stock_dashboard_requires_admin_role(self):
        """CP-226b | Usuario con rol Entregador → redirección a login staff (sin next)."""
        delivery_user = _create_delivery_user(username='delivery')
        self.client.force_login(delivery_user)
        response = self.client.get(reverse(PRODUCTS_STOCK_DASHBOARD))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(CORE_STAFF_LOGIN))

    def test_stock_dashboard_returns_200(self):
        """CP-225 | Dashboard devuelve 200 para usuario administrador."""
        response = self.client.get(reverse(PRODUCTS_STOCK_DASHBOARD))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_STOCK_DASHBOARD)

    # ... resto de pruebas igual ...


# =============================================================================
# TESTS: SIZE CRUD (CP-286 a CP-296)
# =============================================================================

class SizeListViewTest(TestCase):
    """HU-058: Listar tallas"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)

    def test_size_list_200(self):
        """CP-286 | HU-058 | ESCENARIO 1 | H | Lista de tallas cargada exitosamente."""
        response = self.client.get(reverse(PRODUCTS_SIZE_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_SIZE_LIST)

    def test_size_list_requires_authentication(self):
        """CP-287 | HU-058 | ESCENARIO 2 | E | Usuario no autenticado → login con next."""
        self.client.logout()
        response = self.client.get(reverse(PRODUCTS_SIZE_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse(CORE_STAFF_LOGIN),
            response.url
        )
        self.assertIn(
            f'next={reverse(PRODUCTS_SIZE_LIST)}',
            response.url
        )

    def test_size_list_requires_admin_role(self):
        """CP-287b | HU-058 | ESCENARIO 2 | E | Usuario con rol Entregador → login staff (sin next)."""
        delivery_user = _create_delivery_user(username='delivery')
        self.client.force_login(delivery_user)
        response = self.client.get(reverse(PRODUCTS_SIZE_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(CORE_STAFF_LOGIN))

    def test_size_list_requires_admin_role_normal_user(self):
        """CP-287c | HU-058 | ESCENARIO 2 | E | Usuario normal sin roles → catálogo."""
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(PRODUCTS_SIZE_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: COLLECTION CRUD (CP-371 a CP-395)
# =============================================================================

class CollectionListViewAdminTest(TestCase):
    """HU-014: Listar colecciones (admin) con acciones masivas"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)
        self.collection = _create_collection(name="Admin Collection", status=STATUS_DRAFT)

    def test_collection_list_200(self):
        """CP-371 | HU-014 | ESCENARIO 1 | H | Lista de colecciones (admin) cargada exitosamente."""
        response = self.client.get(reverse(PRODUCTS_COLLECTION_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_COLLECTIONS_LIST)

    def test_collection_list_context_has_bulk_actions(self):
        """CP-371b | HU-014 | H | El contexto incluye bulk_actions."""
        response = self.client.get(reverse(PRODUCTS_COLLECTION_LIST))
        self.assertIn('bulk_actions', response.context)
        self.assertEqual(len(response.context['bulk_actions']), 2)
        
        action_names = [action['name'] for action in response.context['bulk_actions']]
        self.assertIn('archive_expired', action_names)
        self.assertIn('publish_scheduled', action_names)

    @patch('apps.products.views.call_command')
    def test_bulk_action_archive_expired(self, mock_call_command):
        """CP-371c | HU-014 | H | Acción masiva 'Archivar expiradas' ejecuta comando."""
        response = self.client.post(
            reverse(PRODUCTS_COLLECTION_LIST), 
            {'bulk_action': 'archive_expired'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_COLLECTION_LIST))
        mock_call_command.assert_called_once_with('archive_collections')
        
        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any('archivadas' in str(m.message).lower() for m in messages_list))

    @patch('apps.products.views.call_command')
    def test_bulk_action_publish_scheduled(self, mock_call_command):
        """CP-371d | HU-014 | H | Acción masiva 'Publicar programadas' ejecuta comando."""
        response = self.client.post(
            reverse(PRODUCTS_COLLECTION_LIST), 
            {'bulk_action': 'publish_scheduled'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_COLLECTION_LIST))
        mock_call_command.assert_called_once_with('publish_collections')
        
        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any('publicadas' in str(m.message).lower() for m in messages_list))

    def test_bulk_action_invalid_action(self):
        """CP-371e | HU-014 | A | Acción masiva inválida muestra error."""
        response = self.client.post(
            reverse(PRODUCTS_COLLECTION_LIST), 
            {'bulk_action': 'invalid_action'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_COLLECTION_LIST))
        
        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any('no válida' in str(m.message).lower() for m in messages_list))

    def test_bulk_action_archive_selected(self):
        """CP-371f | HU-014 | H | Acción masiva 'Archivar seleccionadas'."""
        category = _create_category()
        product = _create_product(category=category)
        collection_to_archive = _create_collection(name="Para Archivar", status=STATUS_PUBLISHED)
        _add_product_to_collection(product, collection_to_archive)
        
        response = self.client.post(
            reverse(PRODUCTS_COLLECTION_LIST), 
            {
                'bulk_action': 'archive_selected',
                'selected_ids': [collection_to_archive.pk]
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_COLLECTION_LIST))
        
        collection_to_archive.refresh_from_db()
        self.assertEqual(collection_to_archive.status, 'archivada')
        
        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any('archivada' in str(m.message).lower() for m in messages_list))

    def test_bulk_action_archive_selected_no_ids(self):
        """CP-371g | HU-014 | A | Acción masiva sin selección muestra advertencia."""
        response = self.client.post(
            reverse(PRODUCTS_COLLECTION_LIST), 
            {'bulk_action': 'archive_selected', 'selected_ids': []}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_COLLECTION_LIST))
        
        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any('no se seleccionó' in str(m.message).lower() for m in messages_list))

    def test_collection_list_requires_authentication(self):
        """CP-371h | HU-014 | ESCENARIO 4 | E | Usuario no autenticado → login con next."""
        self.client.logout()
        response = self.client.get(reverse(PRODUCTS_COLLECTION_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse(CORE_STAFF_LOGIN),
            response.url
        )
        self.assertIn(
            f'next={reverse(PRODUCTS_COLLECTION_LIST)}',
            response.url
        )

    def test_collection_list_requires_admin_role(self):
        """CP-371i | HU-014 | ESCENARIO 4 | E | Usuario con rol Entregador → login staff (sin next)."""
        delivery_user = _create_delivery_user(username='delivery')
        self.client.force_login(delivery_user)
        response = self.client.get(reverse(PRODUCTS_COLLECTION_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(CORE_STAFF_LOGIN))

    def test_collection_list_requires_admin_role_normal_user(self):
        """CP-371j | HU-014 | ESCENARIO 4 | E | Usuario normal sin roles → catálogo."""
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(PRODUCTS_COLLECTION_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_CATALOG))


class CollectionCreateViewTest(TestCase):
    """HU-015: Crear colección"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)

    def test_collection_create_success(self):
        """CP-372 | HU-015 | ESCENARIO 1 | H | Colección creada exitosamente."""
        data = {
            'name': 'Nueva Colección',
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
        }
        response = self.client.post(reverse(PRODUCTS_COLLECTION_CREATE), data=data)
        collection = Collection.objects.first()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, 
            reverse(PRODUCTS_COLLECTION_EDIT, kwargs={'pk': collection.pk})
        )
        self.assertTrue(Collection.objects.filter(name='Nueva Colección').exists())


class CollectionUpdateViewTest(TestCase):
    """HU-016: Editar colección | HU-018: Asignar productos a colección"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)
        self.collection = _create_collection(name="Original", status=STATUS_DRAFT)

    def test_collection_update_success(self):
        """CP-373 | HU-016 | ESCENARIO 1 | H | Colección actualizada exitosamente."""
        data = {
            'name': 'Actualizada',
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
        }
        response = self.client.post(reverse(PRODUCTS_COLLECTION_EDIT, kwargs={'pk': self.collection.pk}), data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_COLLECTION_LIST))
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.name, 'Actualizada')


class CollectionStyleViewTest(TestCase):
    """HU-015 | ESCENARIO 4 | H | Estilos visuales personalizados"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)
        self.collection = _create_collection(name="Style Collection", status=STATUS_DRAFT)

    def test_collection_style_update(self):
        """CP-394 | HU-015 | ESCENARIO 4 | H | Estilos de colección actualizados."""
        data = {
            'primary_color': '#FF0000',
            'secondary_color': '#00FF00',
            'background_color': '#FFFFFF',
            'text_color': '#000000',
        }
        response = self.client.post(reverse(PRODUCTS_COLLECTION_STYLE, kwargs={'pk': self.collection.pk}), data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_COLLECTION_LIST))
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.primary_color, '#FF0000')
        self.assertEqual(self.collection.secondary_color, '#00FF00')


# =============================================================================
# TESTS: PERMISSIONS (Vistas protegidas)
# =============================================================================

class ProductPermissionsTest(TestCase):
    """Pruebas de permisos para vistas de products usando roles."""

    def setUp(self):
        self.client = Client()
        self.normal_user = _create_normal_user(username='normal', is_staff=False)
        self.client.force_login(self.normal_user)
        self.category = _create_category()

    def test_product_list_requires_admin_role(self):
        """CP-329 | HU-009 | ESCENARIO 5 | E | Usuario normal sin rol → catálogo."""
        response = self.client.get(reverse(PRODUCTS_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_CATALOG))

    def test_product_list_delivery_role_redirects_to_login(self):
        """CP-329b | HU-009 | ESCENARIO 5 | E | Usuario con rol Entregador → login staff (sin next)."""
        delivery_user = _create_delivery_user(username='delivery')
        self.client.force_login(delivery_user)
        response = self.client.get(reverse(PRODUCTS_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(CORE_STAFF_LOGIN))

    def test_product_create_requires_admin_role(self):
        """CP-330 | HU-010 | ESCENARIO 4 | E | Usuario normal sin rol → catálogo."""
        response = self.client.get(reverse(PRODUCTS_CREATE))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_CATALOG))

    def test_size_list_requires_admin_role(self):
        """CP-286 | HU-058 | ESCENARIO 2 | E | Usuario normal sin rol → catálogo."""
        response = self.client.get(reverse(PRODUCTS_SIZE_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_CATALOG))

    def test_category_list_requires_admin_role(self):
        """CP-297 | HU-063 | ESCENARIO 2 | E | Usuario normal sin rol → catálogo."""
        response = self.client.get(reverse(PRODUCTS_CATEGORY_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_CATALOG))

    def test_color_list_requires_admin_role(self):
        """CP-308 | HU-068 | ESCENARIO 2 | E | Usuario normal sin rol → catálogo."""
        response = self.client.get(reverse(PRODUCTS_COLOR_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_CATALOG))

    def test_collection_list_requires_admin_role(self):
        """CP-371 | HU-014 | ESCENARIO 4 | E | Usuario normal sin rol → catálogo."""
        response = self.client.get(reverse(PRODUCTS_COLLECTION_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_CATALOG))

    def test_collection_list_delivery_role_redirects_to_login(self):
        """CP-371b | HU-014 | ESCENARIO 4 | E | Usuario con rol Entregador → login staff (sin next)."""
        delivery_user = _create_delivery_user(username='delivery')
        self.client.force_login(delivery_user)
        response = self.client.get(reverse(PRODUCTS_COLLECTION_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(CORE_STAFF_LOGIN))