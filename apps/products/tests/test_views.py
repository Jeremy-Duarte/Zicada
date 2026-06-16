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
# HELPERS
# =============================================================================

def _create_test_image():
    return SimpleUploadedFile(
        "test_image.jpg",
        b"fake_image_content",
        content_type="image/jpeg"
    )


def _create_admin_user(**kwargs):
    from django.contrib.auth.models import Group as AuthGroup
    
    defaults = {'username': 'admin', 'password': 'pass1234', 'is_staff': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    
    admin_group, _ = AuthGroup.objects.get_or_create(name='Administrador')
    user.groups.add(admin_group)
    
    return user


def _create_delivery_user(**kwargs):
    from django.contrib.auth.models import Group as AuthGroup
    
    defaults = {'username': 'delivery', 'password': 'pass1234', 'is_delivery': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    
    delivery_group, _ = AuthGroup.objects.get_or_create(name='Entregador')
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


def _create_staff_user(**kwargs):
    defaults = {'username': 'staff', 'password': 'pass1234', 'is_staff': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    
    admin_group, _ = AuthGroup.objects.get_or_create(name='Administrador')
    user.groups.add(admin_group)
    
    return user


def _create_category(name="Test Category", sort_order=0):
    return Category.objects.create(name=name, sort_order=sort_order)


def _create_size(name="M", sort_order=0):
    return Size.objects.create(name=name, sort_order=sort_order)


def _create_color(name="Rojo", code="#FF0000", sort_order=0):
    return Color.objects.create(name=name, code=code, sort_order=sort_order)


def _create_product(name="Test Product", price=100.00, category=None, product_type='fabrica', is_active=True):
    if category is None:
        category = _create_category()
    return Product.objects.create(
        name=name, price=price, category=category,
        product_type=product_type, is_active=is_active
    )


def _create_product_color(product, color, featured_image=None, sort_order=0, is_active=True):
    return ProductColor.objects.create(
        product=product, color=color, featured_image=featured_image,
        sort_order=sort_order, is_active=is_active
    ) 


def _create_variant(product_color, size, stock=10, is_active=True):
    product = product_color.product
    return ProductVariant.objects.create(
        product=product,
        product_color=product_color,
        size=size,
        stock=stock,
        is_active=is_active
    )


def _create_collection(name="Test Collection", status=STATUS_DRAFT, is_active=True):
    return Collection.objects.create(name=name, status=status, is_active=is_active)


def _add_product_to_collection(product, collection):
    collection.products.add(product)
    collection.save()


def _create_product_with_variants():
    category = _create_category()
    size = _create_size()
    color = _create_color()
    product = _create_product(name="Producto Test", category=category)
    product_color = _create_product_color(product, color)
    variant = _create_variant(product_color, size, stock=10)
    return product, product_color, variant


# =============================================================================
# TESTS: HU-044 Stock Dashboard
# =============================================================================

class StockDashboardTest(TestCase):
    """HU-044: Stock Dashboard"""

    def setUp(self):
        self.client = Client()
        self.admin_user = _create_admin_user(username='admin', is_staff=True)
        self.client.force_login(self.admin_user)

    # UT-420: HU-044 - Sin autenticación redirige a login con next
    def test_stock_dashboard_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(PRODUCTS_STOCK_DASHBOARD))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse(CORE_STAFF_LOGIN), response.url)
        self.assertIn(f'next={reverse(PRODUCTS_STOCK_DASHBOARD)}', response.url)

    # UT-421: HU-044 - Usuario con rol Entregador redirige a login
    def test_stock_dashboard_requires_admin_role(self):
        delivery_user = _create_delivery_user(username='delivery')
        self.client.force_login(delivery_user)
        response = self.client.get(reverse(PRODUCTS_STOCK_DASHBOARD))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(CORE_STAFF_LOGIN))

    # UT-422: HU-044 CA-001 - Dashboard devuelve 200 para usuario administrador
    def test_stock_dashboard_returns_200(self):
        response = self.client.get(reverse(PRODUCTS_STOCK_DASHBOARD))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_STOCK_DASHBOARD)


# =============================================================================
# TESTS: HU-058 a HU-062 Size CRUD
# =============================================================================

class SizeListViewTest(TestCase):
    """HU-058: Listar tallas"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)

    # UT-423: HU-058 CA-001 - Lista de tallas cargada exitosamente
    def test_size_list_200(self):
        response = self.client.get(reverse(PRODUCTS_SIZE_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_SIZE_LIST)

    # UT-424: HU-058 CA-002 - Usuario no autenticado redirige a login con next
    def test_size_list_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(PRODUCTS_SIZE_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse(CORE_STAFF_LOGIN), response.url)
        self.assertIn(f'next={reverse(PRODUCTS_SIZE_LIST)}', response.url)

    # UT-425: HU-058 CA-002 - Usuario con rol Entregador redirige a login
    def test_size_list_requires_admin_role(self):
        delivery_user = _create_delivery_user(username='delivery')
        self.client.force_login(delivery_user)
        response = self.client.get(reverse(PRODUCTS_SIZE_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(CORE_STAFF_LOGIN))

    # UT-426: HU-058 CA-002 - Usuario normal sin roles redirige a catálogo
    def test_size_list_requires_admin_role_normal_user(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(PRODUCTS_SIZE_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: HU-063 a HU-067 Category CRUD
# =============================================================================

class CategoryListViewTest(TestCase):
    """HU-063: Listar categorías"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)

    # UT-427: HU-063 CA-001 - Lista de categorías cargada exitosamente
    def test_category_list_200(self):
        response = self.client.get(reverse(PRODUCTS_CATEGORY_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_CATEGORY_LIST)

    # UT-428: HU-063 CA-002 - Usuario normal sin roles redirige a catálogo
    def test_category_list_requires_admin_role_normal_user(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(PRODUCTS_CATEGORY_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: HU-068 a HU-072 Color CRUD
# =============================================================================

class ColorListViewTest(TestCase):
    """HU-068: Listar colores"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)

    # UT-429: HU-068 CA-001 - Lista de colores cargada exitosamente
    def test_color_list_200(self):
        response = self.client.get(reverse(PRODUCTS_COLOR_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_COLOR_LIST)

    # UT-430: HU-068 CA-002 - Usuario normal sin roles redirige a catálogo
    def test_color_list_requires_admin_role_normal_user(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(PRODUCTS_COLOR_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: HU-009 a HU-013 Product CRUD
# =============================================================================

class ProductPermissionsTest(TestCase):
    """Pruebas de permisos para vistas de products"""

    def setUp(self):
        self.client = Client()
        self.normal_user = _create_normal_user(username='normal', is_staff=False)
        self.client.force_login(self.normal_user)
        self.category = _create_category()

    # UT-431: HU-009 CA-005 - Usuario normal sin roles redirige a catálogo
    def test_product_list_requires_admin_role(self):
        response = self.client.get(reverse(PRODUCTS_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_CATALOG))

    # UT-432: HU-009 CA-005 - Usuario con rol Entregador redirige a login
    def test_product_list_delivery_role_redirects_to_login(self):
        delivery_user = _create_delivery_user(username='delivery')
        self.client.force_login(delivery_user)
        response = self.client.get(reverse(PRODUCTS_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(CORE_STAFF_LOGIN))

    # UT-433: HU-010 CA-004 - Usuario normal sin roles redirige a catálogo
    def test_product_create_requires_admin_role(self):
        response = self.client.get(reverse(PRODUCTS_CREATE))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: HU-014 a HU-018 Collection CRUD
# =============================================================================

class CollectionListViewAdminTest(TestCase):
    """HU-014: Listar colecciones (admin)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)
        self.collection = _create_collection(name="Admin Collection", status=STATUS_DRAFT)

    # UT-434: HU-014 CA-001 - Lista de colecciones (admin) cargada exitosamente
    def test_collection_list_200(self):
        response = self.client.get(reverse(PRODUCTS_COLLECTION_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_COLLECTIONS_LIST)

    # UT-435: HU-014 - El contexto incluye bulk_actions
    def test_collection_list_context_has_bulk_actions(self):
        response = self.client.get(reverse(PRODUCTS_COLLECTION_LIST))
        self.assertIn('bulk_actions', response.context)
        self.assertEqual(len(response.context['bulk_actions']), 2)
        
        action_names = [action['name'] for action in response.context['bulk_actions']]
        self.assertIn('archive_expired', action_names)
        self.assertIn('publish_scheduled', action_names)

    # UT-436: HU-014 - Acción masiva 'Archivar expiradas' ejecuta comando
    @patch('apps.products.views.call_command')
    def test_bulk_action_archive_expired(self, mock_call_command):
        response = self.client.post(
            reverse(PRODUCTS_COLLECTION_LIST), 
            {'bulk_action': 'archive_expired'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_COLLECTION_LIST))
        mock_call_command.assert_called_once_with('archive_collections')
        
        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any('archivadas' in str(m.message).lower() for m in messages_list))

    # UT-437: HU-014 - Acción masiva 'Publicar programadas' ejecuta comando
    @patch('apps.products.views.call_command')
    def test_bulk_action_publish_scheduled(self, mock_call_command):
        response = self.client.post(
            reverse(PRODUCTS_COLLECTION_LIST), 
            {'bulk_action': 'publish_scheduled'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_COLLECTION_LIST))
        mock_call_command.assert_called_once_with('publish_collections')
        
        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any('publicadas' in str(m.message).lower() for m in messages_list))

    # UT-438: HU-014 - Acción masiva inválida muestra error
    def test_bulk_action_invalid_action(self):
        response = self.client.post(
            reverse(PRODUCTS_COLLECTION_LIST), 
            {'bulk_action': 'invalid_action'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_COLLECTION_LIST))
        
        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any('no válida' in str(m.message).lower() for m in messages_list))

    # UT-439: HU-014 - Acción masiva 'Archivar seleccionadas' funciona
    def test_bulk_action_archive_selected(self):
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

    # UT-440: HU-014 - Acción masiva sin selección muestra advertencia
    def test_bulk_action_archive_selected_no_ids(self):
        response = self.client.post(
            reverse(PRODUCTS_COLLECTION_LIST), 
            {'bulk_action': 'archive_selected', 'selected_ids': []}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(PRODUCTS_COLLECTION_LIST))
        
        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any('no se seleccionó' in str(m.message).lower() for m in messages_list))

    # UT-441: HU-014 CA-004 - Usuario no autenticado redirige a login
    def test_collection_list_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(PRODUCTS_COLLECTION_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse(CORE_STAFF_LOGIN), response.url)
        self.assertIn(f'next={reverse(PRODUCTS_COLLECTION_LIST)}', response.url)

    # UT-442: HU-014 CA-004 - Usuario con rol Entregador redirige a login
    def test_collection_list_requires_admin_role(self):
        delivery_user = _create_delivery_user(username='delivery')
        self.client.force_login(delivery_user)
        response = self.client.get(reverse(PRODUCTS_COLLECTION_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(CORE_STAFF_LOGIN))

    # UT-443: HU-014 CA-004 - Usuario normal sin roles redirige a catálogo
    def test_collection_list_requires_admin_role_normal_user(self):
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

    # UT-444: HU-015 CA-001 - Colección creada exitosamente
    def test_collection_create_success(self):
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
    """HU-016: Editar colección | HU-018: Asignar productos"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)
        self.collection = _create_collection(name="Original", status=STATUS_DRAFT)

    # UT-445: HU-016 CA-001 - Colección actualizada exitosamente
    def test_collection_update_success(self):
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
    """HU-015 CA-004: Estilos visuales personalizados"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)
        self.collection = _create_collection(name="Style Collection", status=STATUS_DRAFT)

    # UT-446: HU-015 CA-004 - Estilos de colección actualizados
    def test_collection_style_update(self):
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