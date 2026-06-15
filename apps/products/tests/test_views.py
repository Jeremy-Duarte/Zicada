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
from django.contrib.auth.models import Permission
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
    """Crea una imagen de prueba para tests."""
    return SimpleUploadedFile(
        "test_image.jpg",
        b"fake_image_content",
        content_type="image/jpeg"
    )


def _create_staff_user(**kwargs):
    """Crea un usuario staff."""
    defaults = {'username': 'staff', 'password': 'pass1234', 'is_staff': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    user = User(**defaults)
    user.set_password(password)
    user.is_staff = True
    user.save()
    user.save()
    return user


def _add_product_permissions(user):
    """Añade todos los permisos de products a un usuario."""
    content_type = ContentType.objects.get_for_model(Product)
    perms = Permission.objects.filter(content_type__app_label='products')
    user.user_permissions.add(*perms)
    user.refresh_from_db()
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
        # Crear usuario staff con todos los permisos de productos
        self.staff_user = _create_staff_user(username='staff', is_staff=True)
        self.staff_user = _add_product_permissions(self.staff_user)
        self.client.force_login(self.staff_user)

    def test_stock_dashboard_requires_staff(self):
        """CP-226 | Sin permisos de staff → redirección al login."""
        self.client.logout()
        response = self.client.get(reverse(PRODUCTS_STOCK_DASHBOARD))
        # ✅ El mixin redirige a CORE_STAFF_LOGIN
        self.assertRedirects(
            response, 
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(PRODUCTS_STOCK_DASHBOARD)}'
        )

    def test_stock_dashboard_returns_200(self):
        """CP-225 | Dashboard devuelve 200 para usuario staff."""
        response = self.client.get(reverse(PRODUCTS_STOCK_DASHBOARD))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_STOCK_DASHBOARD)

    def test_stock_dashboard_low_stock_variants(self):
        """CP-227 | Verifica que variantes con stock bajo aparecen en el dashboard."""
        category = _create_category()
        color = _create_color()
        size = _create_size()
        product = _create_product(name="Producto Low Stock", category=category)
        product_color = _create_product_color(product, color)
        
        low_stock_variant = ProductVariant.objects.create(
            product=product,
            product_color=product_color,
            size=size,
            stock=STOCK_LOW_THRESHOLD,
            is_active=True
        )
        
        response = self.client.get(reverse(PRODUCTS_STOCK_DASHBOARD))
        
        self.assertIsNotNone(response.context)
        self.assertIn('low_stock_variants', response.context)
        self.assertIn(low_stock_variant, response.context['low_stock_variants'])
        self.assertEqual(response.context['low_stock_count'], 1)

    def test_stock_dashboard_out_of_stock_variants(self):
        """CP-228 | Verifica que variantes agotadas aparecen en el dashboard."""
        category = _create_category()
        color = _create_color()
        size = _create_size()
        product = _create_product(name="Producto Out of Stock", category=category)
        product_color = _create_product_color(product, color)
        
        out_of_stock_variant = ProductVariant.objects.create(
            product=product,
            product_color=product_color,
            size=size,
            stock=0,
            is_active=True
        )
        
        response = self.client.get(reverse(PRODUCTS_STOCK_DASHBOARD))
        
        self.assertIsNotNone(response.context)
        self.assertIn('out_of_stock_variants', response.context)
        self.assertIn(out_of_stock_variant, response.context['out_of_stock_variants'])
        self.assertEqual(response.context['out_of_stock_variants_count'], 1)

    def test_stock_dashboard_out_of_stock_products(self):
        """CP-229 | Verifica que productos sin stock aparecen en el dashboard."""
        category = _create_category()
        product = _create_product(name="Sin Stock", category=category)
        
        response = self.client.get(reverse(PRODUCTS_STOCK_DASHBOARD))
        
        self.assertIsNotNone(response.context)
        self.assertIn('out_of_stock_products', response.context)
        self.assertIn(product, response.context['out_of_stock_products'])
        self.assertEqual(response.context['out_of_stock_products_count'], 1)


# =============================================================================
# TESTS: PRODUCT CATALOG VIEW (CP-233 a CP-245)
# =============================================================================

class ProductCatalogViewTest(TestCase):
    """HU-004: Consultar catálogo | HU-007: Filtrar productos"""

    def setUp(self):
        self.client = Client()
        self.category = _create_category(name="Electronics")
        self.product1 = _create_product(name="Laptop", price=1500.00, category=self.category)
        self.product2 = _create_product(name="Mouse", price=25.00, category=self.category)
        self.inactive_product = _create_product(
            name="Inactive", price=10.00, category=self.category, is_active=False
        )

    def test_catalog_loads_active_products(self):
        """CP-233 | HU-004 | ESCENARIO 1 | H | Catálogo cargado exitosamente con productos activos."""
        response = self.client.get(reverse(PRODUCTS_CATALOG))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_CATALOG)
        self.assertContains(response, "Laptop")
        self.assertContains(response, "Mouse")
        self.assertNotContains(response, "Inactive")

    def test_catalog_search_filter(self):
        """CP-234 | HU-007 | ESCENARIO 1 | H | Búsqueda por nombre filtra correctamente."""
        response = self.client.get(reverse(PRODUCTS_CATALOG), {QUERY_PARAM_SEARCH: 'Laptop'})
        self.assertContains(response, "Laptop")
        self.assertNotContains(response, "Mouse")

    def test_catalog_price_range_filter(self):
        """CP-235 | HU-007 | ESCENARIO 3 | H | Filtro por rango de precios."""
        response = self.client.get(reverse(PRODUCTS_CATALOG), {QUERY_PARAM_MIN_PRICE: '100', QUERY_PARAM_MAX_PRICE: '2000'})
        self.assertContains(response, "Laptop")
        self.assertNotContains(response, "Mouse")

    def test_catalog_category_filter(self):
        """CP-236 | HU-007 | ESCENARIO 2 | H | Filtro por categoría."""
        response = self.client.get(reverse(PRODUCTS_CATALOG), {QUERY_PARAM_CATEGORY: self.category.slug})
        self.assertContains(response, "Laptop")
        self.assertContains(response, "Mouse")

    def test_catalog_combined_filters(self):
        """CP-238 | HU-007 | ESCENARIO 4 | H | Filtros combinados (búsqueda + precio)."""
        response = self.client.get(
            reverse(PRODUCTS_CATALOG),
            {QUERY_PARAM_SEARCH: 'Laptop', QUERY_PARAM_MIN_PRICE: '1000'}
        )
        self.assertContains(response, "Laptop")
        self.assertNotContains(response, "Mouse")

    def test_catalog_ordering_price_asc(self):
        """CP-239 | HU-004 | ESCENARIO 3 | H | Orden ascendente por precio."""
        response = self.client.get(reverse(PRODUCTS_CATALOG), {QUERY_PARAM_ORDER_BY: 'price'})
        products = list(response.context['products'])
        self.assertEqual(products[0].price, 25.00)
        self.assertEqual(products[1].price, 1500.00)

    def test_catalog_ordering_price_desc(self):
        """CP-239 | HU-004 | ESCENARIO 3 | H | Orden descendente por precio."""
        response = self.client.get(reverse(PRODUCTS_CATALOG), {QUERY_PARAM_ORDER_BY: '-price'})
        products = list(response.context['products'])
        self.assertEqual(products[0].price, 1500.00)
        self.assertEqual(products[1].price, 25.00)

    def test_catalog_no_results_message(self):
        """CP-241 | HU-007 | ESCENARIO 5 | A | Sin resultados → template muestra mensaje."""
        response = self.client.get(reverse(PRODUCTS_CATALOG), {QUERY_PARAM_SEARCH: 'ProductoInexistenteXYZ'})
        self.assertEqual(len(response.context['products']), 0)
        self.assertContains(response, "No hay productos disponibles")

    def test_catalog_has_active_filters_flag(self):
        """CP-244 | HU-007 | ESCENARIO 6 | H | Indicador de filtros activos correcto."""
        response = self.client.get(reverse(PRODUCTS_CATALOG), {QUERY_PARAM_SEARCH: 'Laptop'})
        self.assertTrue(response.context['has_active_filters'])
        
        response = self.client.get(reverse(PRODUCTS_CATALOG))
        self.assertFalse(response.context['has_active_filters'])

    def test_catalog_returns_only_active_products(self):
        """CP-245 | HU-004 | ESCENARIO 2 | H | Productos inactivos no aparecen en catálogo."""
        response = self.client.get(reverse(PRODUCTS_CATALOG))
        self.assertEqual(len(response.context['products']), 2)
        self.assertNotIn(self.inactive_product, response.context['products'])


# =============================================================================
# TESTS: PUBLIC COLLECTION LIST (CP-246 a CP-260)
# =============================================================================

class CollectionListViewPublicTest(TestCase):
    """HU-005: Consultar colecciones (público)"""

    def setUp(self):
        self.client = Client()
        self.category = _create_category()
        self.product = _create_product(name="Producto Test", category=self.category)
        self.active_collection = _create_collection(name="Verano 2024", status=STATUS_DRAFT)
        _add_product_to_collection(self.product, self.active_collection)
        self.active_collection.status = STATUS_PUBLISHED
        self.active_collection.start_date = timezone.now() - timedelta(days=1)
        self.active_collection.end_date = timezone.now() + timedelta(days=30)
        self.active_collection.save()
        self.draft_collection = _create_collection(name="Invierno 2024", status=STATUS_DRAFT, is_active=True)
        self.draft_collection.start_date = timezone.now() + timedelta(days=7)
        self.draft_collection.end_date = timezone.now() + timedelta(days=37)
        self.draft_collection.save()
        
        self.archived_collection = _create_collection(name="Otoño 2023", status=STATUS_ARCHIVED)

    def test_collection_list_loads_active(self):
        """CP-246 | HU-005 | ESCENARIO 1 | H | Listado de colecciones activas cargado."""
        response = self.client.get(reverse(PRODUCTS_COLLECTIONS_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_COLLECTIONS_LIST_PUBLIC)
        self.assertContains(response, "Verano 2024")
        self.assertNotContains(response, "Invierno 2024")
        self.assertNotContains(response, "Otoño 2023")

    def test_collection_status_filter_upcoming(self):
        """CP-249 | HU-005 | ESCENARIO 2 | A | Filtro por estado 'borrador' (próximas)."""
        response = self.client.get(
            reverse(PRODUCTS_COLLECTIONS_LIST), 
            {QUERY_PARAM_DATE_FILTER: DATE_FILTER_UPCOMING}
        )
        self.assertContains(response, "Invierno 2024")

    def test_collection_no_results_message(self):
        """CP-257 | HU-005 | ESCENARIO 4 | A | Sin colecciones activas → mensaje."""
        Collection.objects.all().delete()
        response = self.client.get(reverse(PRODUCTS_COLLECTIONS_LIST))
        self.assertEqual(len(response.context['collections']), 0)


# =============================================================================
# TESTS: COLLECTION DETAIL (CP-261 a CP-273)
# =============================================================================

class CollectionDetailViewTest(TestCase):
    """HU-005: Consultar detalle de colección | HU-006: Ver productos de una colección"""

    def setUp(self):
        self.client = Client()
        self.category = _create_category()
        self.product1 = _create_product(name="Producto 1", category=self.category)
        self.product2 = _create_product(name="Producto 2", category=self.category)
        
        # Crear colección como borrador primero
        self.collection = _create_collection(name="Colección Test", status=STATUS_DRAFT)
        # Asignar productos
        _add_product_to_collection(self.product1, self.collection)
        _add_product_to_collection(self.product2, self.collection)
        # Cambiar a publicada después de tener productos
        self.collection.status = STATUS_PUBLISHED
        self.collection.start_date = timezone.now() - timedelta(days=1)
        self.collection.end_date = timezone.now() + timedelta(days=30)
        self.collection.save()

    def test_collection_detail_loads(self):
        """CP-261 | HU-005 | ESCENARIO 1 | H | Detalle de colección pública accesible."""
        response = self.client.get(reverse(PRODUCTS_COLLECTION_DETAIL, kwargs={'slug': self.collection.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_COLLECTION_DETAIL)

    def test_collection_detail_not_found(self):
        """CP-262 | HU-005 | ESCENARIO 4 | E | Colección no existe → 404."""
        response = self.client.get(reverse(PRODUCTS_COLLECTION_DETAIL, kwargs={'slug': 'no-existe'}))
        self.assertEqual(response.status_code, 404)

    def test_collection_detail_upcoming_not_accessible(self):
        """CP-263 | HU-005 | ESCENARIO 2 | A | Colección con status borrador no accesible."""
        draft = _create_collection(name="Borrador", status=STATUS_DRAFT)
        response = self.client.get(reverse(PRODUCTS_COLLECTION_DETAIL, kwargs={'slug': draft.slug}))
        self.assertEqual(response.status_code, 404)

    def test_collection_detail_expired_not_accessible(self):
        """CP-264 | HU-005 | ESCENARIO 3 | A | Colección archivada no accesible."""
        archived = _create_collection(name="Archivada", status=STATUS_ARCHIVED)
        response = self.client.get(reverse(PRODUCTS_COLLECTION_DETAIL, kwargs={'slug': archived.slug}))
        self.assertEqual(response.status_code, 404)

    def test_collection_detail_products_filtered(self):
        """CP-265 | HU-006 | ESCENARIO 1 | H | Productos de la colección filtrados correctamente."""
        response = self.client.get(reverse(PRODUCTS_COLLECTION_DETAIL, kwargs={'slug': self.collection.slug}))
        self.assertEqual(len(response.context['products']), 2)

    def test_collection_detail_custom_css_sanitized(self):
        """CP-266 | HU-006 | ESCENARIO 2 | H | CSS personalizado sanitizado."""
        self.collection.custom_css = "body { color: red; }"
        self.collection.save()
        response = self.client.get(reverse(PRODUCTS_COLLECTION_DETAIL, kwargs={'slug': self.collection.slug}))
        self.assertIn('safe_custom_css', response.context)
        self.assertIn('body { color: red; }', response.context['safe_custom_css'])

    def test_collection_detail_css_with_javascript_removed(self):
        """CP-267 | HU-006 | ESCENARIO 2 | H | CSS malicioso (javascript:) es eliminado."""
        self.collection.custom_css = "body { color: red; } javascript:alert('xss')"
        self.collection.save()
        response = self.client.get(reverse(PRODUCTS_COLLECTION_DETAIL, kwargs={'slug': self.collection.slug}))
        self.assertNotIn('javascript:', response.context['safe_custom_css'])

    def test_collection_detail_css_truncated_over_5000(self):
        """CP-268 | HU-006 | ESCENARIO 2 | H | CSS truncado a 5000 caracteres."""
        self.collection.custom_css = "a" * 6000
        self.collection.save()
        response = self.client.get(reverse(PRODUCTS_COLLECTION_DETAIL, kwargs={'slug': self.collection.slug}))
        self.assertEqual(len(response.context['safe_custom_css']), 5000)

    def test_collection_detail_search_filter(self):
        """CP-269 | HU-006 | ESCENARIO 1 | H | Búsqueda dentro de productos de la colección."""
        response = self.client.get(
            reverse(PRODUCTS_COLLECTION_DETAIL, kwargs={'slug': self.collection.slug}),
            {QUERY_PARAM_SEARCH: 'Producto 1'}
        )
        self.assertEqual(len(response.context['products']), 1)


# =============================================================================
# TESTS: PRODUCT DETAIL (CP-274 a CP-285)
# =============================================================================

class ProductDetailViewTest(TestCase):
    """HU-006: Consultar detalle de producto | HU-008: Consultar disponibilidad de talla"""

    def setUp(self):
        self.client = Client()
        self.category = _create_category()
        self.size = _create_size()
        self.color = _create_color()
        self.product = _create_product(name="Producto Test", category=self.category)
        self.product_color = _create_product_color(self.product, self.color)
        self.variant = _create_variant(self.product_color, self.size, stock=10)

    def test_product_detail_200(self):
        """CP-274 | HU-006 | ESCENARIO 1 | H | Producto activo muestra detalle."""
        response = self.client.get(reverse(PRODUCTS_DETAIL, kwargs={'slug': self.product.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_PRODUCT_DETAIL)

    def test_product_detail_404_inactive(self):
        """CP-275 | HU-006 | ESCENARIO 4 | E | Producto inactivo → 404."""
        self.product.is_active = False
        self.product.save()
        response = self.client.get(reverse(PRODUCTS_DETAIL, kwargs={'slug': self.product.slug}))
        self.assertEqual(response.status_code, 404)

    def test_product_detail_404_not_found(self):
        """CP-276 | HU-006 | ESCENARIO 4 | E | Producto no existe → 404."""
        response = self.client.get(reverse(PRODUCTS_DETAIL, kwargs={'slug': 'no-existe'}))
        self.assertEqual(response.status_code, 404)

    def test_product_detail_variants_context(self):
        """CP-278 | HU-008 | ESCENARIO 1,3 | H/A | Variantes disponibles (colores y tallas)."""
        response = self.client.get(reverse(PRODUCTS_DETAIL, kwargs={'slug': self.product.slug}))
        self.assertEqual(len(response.context['variants']), 1)
        self.assertEqual(response.context['unique_colors'][0]['name'], self.color.name)
        self.assertEqual(response.context['unique_sizes'][0]['name'], self.size.name)

    def test_product_detail_variant_out_of_stock(self):
        """CP-279 | HU-008 | ESCENARIO 2 | A | Talla agotada muestra stock_display='out_of_stock'."""
        self.variant.stock = 0
        self.variant.save()
        response = self.client.get(reverse(PRODUCTS_DETAIL, kwargs={'slug': self.product.slug}))
        self.assertIn('out_of_stock', response.context['variants_json'])


# =============================================================================
# TESTS: SIZE CRUD (CP-286 a CP-296)
# =============================================================================

class SizeListViewTest(TestCase):
    """HU-058: Listar tallas"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)

    def test_size_list_200(self):
        """CP-286 | HU-058 | ESCENARIO 1 | H | Lista de tallas cargada exitosamente."""
        response = self.client.get(reverse(PRODUCTS_SIZE_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_SIZE_LIST)

    def test_size_list_requires_authentication(self):
        """CP-287 | HU-058 | ESCENARIO 2 | E | Usuario no autenticado → login."""
        self.client.logout()
        response = self.client.get(reverse(PRODUCTS_SIZE_LIST))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(PRODUCTS_SIZE_LIST)}')


class SizeCreateViewTest(TestCase):
    """HU-059: Crear talla"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)

    def test_size_create_success(self):
        """CP-290 | HU-059 | ESCENARIO 1 | H | Talla creada exitosamente."""
        data = {'name': 'XL', 'sort_order': 5}
        response = self.client.post(reverse(PRODUCTS_SIZE_CREATE), data=data)
        self.assertRedirects(response, reverse(PRODUCTS_SIZE_LIST))
        self.assertTrue(Size.objects.filter(name='XL').exists())

    def test_size_create_duplicate_name(self):
        """CP-291 | HU-059 | ESCENARIO 2 | A | Crear talla con nombre duplicado → error."""
        _create_size(name='XL')
        data = {'name': 'XL', 'sort_order': 5}
        response = self.client.post(reverse(PRODUCTS_SIZE_CREATE), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('name', response.context['form'].errors)


class SizeUpdateViewTest(TestCase):
    """HU-060: Editar talla"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)
        self.size = _create_size(name="M")

    def test_size_update_success(self):
        """CP-293 | HU-060 | ESCENARIO 1 | H | Talla actualizada exitosamente."""
        data = {'name': 'G', 'sort_order': 10}
        response = self.client.post(reverse(PRODUCTS_SIZE_EDIT, kwargs={'pk': self.size.pk}), data=data)
        self.assertRedirects(response, reverse(PRODUCTS_SIZE_LIST))
        self.size.refresh_from_db()
        self.assertEqual(self.size.name, 'G')


class SizeDeleteViewTest(TestCase):
    """HU-061: Eliminar talla"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)
        self.size = _create_size(name="S")

    def test_size_delete_success(self):
        """CP-296 | HU-061 | ESCENARIO 1 | H | Talla eliminada exitosamente."""
        response = self.client.post(reverse(PRODUCTS_SIZE_DELETE, kwargs={'pk': self.size.pk}), {'confirm': 'S'})
        self.assertRedirects(response, reverse(PRODUCTS_SIZE_LIST))
        self.assertFalse(Size.objects.filter(pk=self.size.pk).exists())


# =============================================================================
# TESTS: CATEGORY CRUD (CP-297 a CP-307)
# =============================================================================

class CategoryListViewTest(TestCase):
    """HU-063: Listar categorías"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)

    def test_category_list_200(self):
        """CP-297 | HU-063 | ESCENARIO 1 | H | Lista de categorías cargada exitosamente."""
        response = self.client.get(reverse(PRODUCTS_CATEGORY_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_CATEGORY_LIST)


class CategoryCreateViewTest(TestCase):
    """HU-064: Crear categoría"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)

    def test_category_create_success(self):
        """CP-298 | HU-064 | ESCENARIO 1 | H | Categoría creada exitosamente."""
        data = {'name': 'Nueva Cat', 'sort_order': 1}
        response = self.client.post(reverse(PRODUCTS_CATEGORY_CREATE), data=data)
        self.assertRedirects(response, reverse(PRODUCTS_CATEGORY_LIST))
        self.assertTrue(Category.objects.filter(name='Nueva Cat').exists())


# =============================================================================
# TESTS: COLOR CRUD (CP-308 a CP-318)
# =============================================================================

class ColorListViewTest(TestCase):
    """HU-068: Listar colores"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)

    def test_color_list_200(self):
        """CP-308 | HU-068 | ESCENARIO 1 | H | Lista de colores cargada exitosamente."""
        response = self.client.get(reverse(PRODUCTS_COLOR_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_COLOR_LIST)


class ColorCreateViewTest(TestCase):
    """HU-069: Crear color"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)

    def test_color_create_success(self):
        """CP-309 | HU-069 | ESCENARIO 1 | H | Color creado exitosamente."""
        data = {'name': 'Verde', 'code': '#00FF00', 'sort_order': 1}
        response = self.client.post(reverse(PRODUCTS_COLOR_CREATE), data=data)
        self.assertRedirects(response, reverse(PRODUCTS_COLOR_LIST))
        self.assertTrue(Color.objects.filter(name='Verde').exists())


# =============================================================================
# TESTS: PRODUCT CRUD (CP-329 a CP-345)
# =============================================================================

class ProductListViewTest(TestCase):
    """HU-009: Listar productos (admin)"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)
        self.category = _create_category()
        self.product = _create_product(category=self.category)

    def test_product_list_200(self):
        """CP-329 | HU-009 | ESCENARIO 1 | H | Lista de productos cargada exitosamente."""
        response = self.client.get(reverse(PRODUCTS_LIST))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_PRODUCT_LIST)


class ProductCreateViewTest(TestCase):
    """HU-010: Crear producto"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)
        self.category = _create_category()

    def test_product_create_success(self):
        """CP-330 | HU-010 | ESCENARIO 1 | H | Producto creado exitosamente."""
        data = {
            'name': 'Nuevo Producto',
            'price': '99.99',
            'category': self.category.id,
            'product_type': 'fabrica',
        }
        response = self.client.post(reverse(PRODUCTS_CREATE), data=data)
        product = Product.objects.first()
        self.assertRedirects(response, reverse(PRODUCTS_EDIT, kwargs={'pk': product.pk}))
        self.assertTrue(Product.objects.filter(name='Nuevo Producto').exists())

    def test_product_create_duplicate_name(self):
        """CP-331 | HU-010 | ESCENARIO 2 | A | Crear producto con nombre duplicado → error."""
        existing = _create_product(name='Existente', category=self.category)
        data = {
            'name': 'Existente',
            'price': '99.99',
            'category': self.category.id,
            'product_type': 'fabrica',
        }
        response = self.client.post(reverse(PRODUCTS_CREATE), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('name', response.context['form'].errors)


class ProductUpdateViewTest(TestCase):
    """HU-011: Editar producto"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)
        self.category = _create_category()
        self.product = _create_product(name="Original", category=self.category)

    def test_product_update_success(self):
        """CP-332 | HU-011 | ESCENARIO 1 | H | Producto actualizado exitosamente."""
        data = {
            'name': 'Actualizado',
            'price': '199.99',
            'category': self.category.id,
            'product_type': 'fabrica',
        }
        response = self.client.post(reverse(PRODUCTS_EDIT, kwargs={'pk': self.product.pk}), data=data)
        self.assertRedirects(response, reverse(PRODUCTS_LIST))
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Actualizado')
        self.assertEqual(float(self.product.price), 199.99)


class ProductDeleteViewTest(TestCase):
    """HU-012: Eliminar producto (soft delete)"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)
        self.category = _create_category()
        self.product = _create_product(name="Eliminar", category=self.category)

    def test_product_delete_success(self):
        """CP-333 | HU-012 | ESCENARIO 1 | H | Producto archivado (soft delete)."""
        response = self.client.post(
            reverse(PRODUCTS_DELETE, kwargs={'pk': self.product.pk}), 
            {'confirm': self.product.name}
        )
        self.assertRedirects(response, reverse(PRODUCTS_LIST))
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)
        self.assertIsNotNone(self.product.deleted_at)


class ProductRestoreViewTest(TestCase):
    """HU-012 | ESCENARIO 4 | H | Restaurar producto desde papelera"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)
        self.category = _create_category()
        self.product = _create_product(name="Restaurar", category=self.category, is_active=False)

    def test_product_restore_success(self):
        """CP-334 | HU-012 | ESCENARIO 4 | H | Producto restaurado exitosamente."""
        response = self.client.post(reverse(PRODUCTS_RESTORE, kwargs={'pk': self.product.pk}), {'confirm': True})
        self.assertRedirects(response, reverse(PRODUCTS_LIST))
        self.product.refresh_from_db()
        self.assertTrue(self.product.is_active)
        self.assertIsNone(self.product.deleted_at)


# =============================================================================
# TESTS: COLLECTION CRUD (CP-371 a CP-395)
# =============================================================================

class CollectionListViewAdminTest(TestCase):
    """HU-014: Listar colecciones (admin) con acciones masivas"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)
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
        self.assertRedirects(response, reverse(PRODUCTS_COLLECTION_LIST))
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
        self.assertRedirects(response, reverse(PRODUCTS_COLLECTION_LIST))
        mock_call_command.assert_called_once_with('publish_collections')
        
        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any('publicadas' in str(m.message).lower() for m in messages_list))

    def test_bulk_action_invalid_action(self):
        """CP-371e | HU-014 | A | Acción masiva inválida muestra error."""
        response = self.client.post(
            reverse(PRODUCTS_COLLECTION_LIST), 
            {'bulk_action': 'invalid_action'}
        )
        self.assertRedirects(response, reverse(PRODUCTS_COLLECTION_LIST))
        
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
        self.assertRedirects(response, reverse(PRODUCTS_COLLECTION_LIST))
        
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
        self.assertRedirects(response, reverse(PRODUCTS_COLLECTION_LIST))
        
        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any('no se seleccionó' in str(m.message).lower() for m in messages_list))

    def test_collection_list_requires_authentication(self):
        """CP-371h | HU-014 | ESCENARIO 4 | E | Usuario no autenticado → login."""
        self.client.logout()
        response = self.client.get(reverse(PRODUCTS_COLLECTION_LIST))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(PRODUCTS_COLLECTION_LIST)}')

    def test_collection_list_requires_permission(self):
        """CP-371i | HU-014 | ESCENARIO 4 | E | Usuario sin permiso → catálogo."""
        normal_user = _create_staff_user(username='normal', is_staff=False)
        self.client.force_login(normal_user)
        response = self.client.get(reverse(PRODUCTS_COLLECTION_LIST))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))


class CollectionCreateViewTest(TestCase):
    """HU-015: Crear colección"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)

    def test_collection_create_success(self):
        """CP-372 | HU-015 | ESCENARIO 1 | H | Colección creada exitosamente."""
        data = {
            'name': 'Nueva Colección',
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
        }
        response = self.client.post(reverse(PRODUCTS_COLLECTION_CREATE), data=data)
        collection = Collection.objects.first()
        self.assertRedirects(response, reverse(PRODUCTS_COLLECTION_EDIT, kwargs={'pk': collection.pk}))
        self.assertTrue(Collection.objects.filter(name='Nueva Colección').exists())


class CollectionUpdateViewTest(TestCase):
    """HU-016: Editar colección | HU-018: Asignar productos a colección"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)
        self.collection = _create_collection(name="Original", status=STATUS_DRAFT)

    def test_collection_update_success(self):
        """CP-373 | HU-016 | ESCENARIO 1 | H | Colección actualizada exitosamente."""
        data = {
            'name': 'Actualizada',
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
        }
        response = self.client.post(reverse(PRODUCTS_COLLECTION_EDIT, kwargs={'pk': self.collection.pk}), data=data)
        self.assertRedirects(response, reverse(PRODUCTS_COLLECTION_LIST))
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.name, 'Actualizada')


class CollectionStyleViewTest(TestCase):
    """HU-015 | ESCENARIO 4 | H | Estilos visuales personalizados"""

    def setUp(self):
        self.client = Client()
        self.staff = _create_staff_user()
        self.staff = _add_product_permissions(self.staff)
        self.client.force_login(self.staff)
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
        self.assertRedirects(response, reverse(PRODUCTS_COLLECTION_LIST))
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.primary_color, '#FF0000')
        self.assertEqual(self.collection.secondary_color, '#00FF00')


# =============================================================================
# TESTS: PERMISSIONS (Vistas protegidas)
# =============================================================================

class ProductPermissionsTest(TestCase):
    """Pruebas de permisos para vistas de products."""

    def setUp(self):
        self.client = Client()
        self.normal_user = _create_staff_user(username='normal', is_staff=False)
        self.client.force_login(self.normal_user)
        self.category = _create_category()

    def test_product_list_requires_permission(self):
        """CP-329 | HU-009 | ESCENARIO 5 | E | Usuario sin permiso products.view_product → catálogo."""
        response = self.client.get(reverse(PRODUCTS_LIST))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_product_create_requires_permission(self):
        """CP-330 | HU-010 | ESCENARIO 4 | E | Usuario sin permiso products.add_product → catálogo."""
        response = self.client.get(reverse(PRODUCTS_CREATE))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_size_list_requires_permission(self):
        """CP-286 | HU-058 | ESCENARIO 2 | E | Usuario sin permiso products.view_size → catálogo."""
        response = self.client.get(reverse(PRODUCTS_SIZE_LIST))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_category_list_requires_permission(self):
        """CP-297 | HU-063 | ESCENARIO 2 | E | Usuario sin permiso products.view_category → catálogo."""
        response = self.client.get(reverse(PRODUCTS_CATEGORY_LIST))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_color_list_requires_permission(self):
        """CP-308 | HU-068 | ESCENARIO 2 | E | Usuario sin permiso products.view_color → catálogo."""
        response = self.client.get(reverse(PRODUCTS_COLOR_LIST))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_collection_list_requires_permission(self):
        """CP-371 | HU-014 | ESCENARIO 4 | E | Usuario sin permiso products.view_collection → catálogo."""
        response = self.client.get(reverse(PRODUCTS_COLLECTION_LIST))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))