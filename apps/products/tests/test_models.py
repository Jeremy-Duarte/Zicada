import json
from unittest.mock import patch, Mock, PropertyMock
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError, transaction

from apps.products.models import (
    Size, Category, Color, ProductImage, ProductColor,
    Product, ProductVariant, Collection
)
from apps.products.constants import STOCK_LOW_THRESHOLD


# =============================================================================
# TESTS: SIZE MODEL (HU-058 a HU-062)
# =============================================================================

class SizeModelTest(TestCase):
    """HU-058 a HU-062: Gestión de tallas"""

    def setUp(self):
        self.size = Size.objects.create(name='M', sort_order=2)
        self.size_xs = Size.objects.create(name='XS', sort_order=1)

    # UT-346: HU-058 CA-001 - __str__ retorna el nombre
    def test_size_str(self):
        self.assertEqual(str(self.size), 'M')

    # UT-347: HU-058 - Ordenado por sort_order
    def test_size_ordering(self):
        sizes = list(Size.objects.all())
        self.assertEqual(sizes, [self.size_xs, self.size])

    # UT-348: HU-058 CA-002 - Nombre único
    def test_size_unique_name(self):
        with self.assertRaises(IntegrityError):
            Size.objects.create(name='M')

    # UT-349: HU-058 - sort_order por defecto 0
    def test_size_default_sort_order_zero(self):
        s = Size.objects.create(name='XXL')
        self.assertEqual(s.sort_order, 0)


# =============================================================================
# TESTS: CATEGORY MODEL (HU-063 a HU-067)
# =============================================================================

class CategoryModelTest(TestCase):
    """HU-063 a HU-067: Gestión de categorías"""

    def setUp(self):
        self.cat = Category.objects.create(name='Camisetas', sort_order=1)

    # UT-350: HU-063 CA-001 - __str__ retorna el nombre
    def test_category_str(self):
        self.assertEqual(str(self.cat), 'Camisetas')

    # UT-351: HU-064 CA-001 - Slug se genera automáticamente
    def test_category_slug_auto_generated(self):
        self.assertEqual(self.cat.slug, 'camisetas')

    # UT-352: HU-065 CA-001 - Slug personalizado se mantiene
    def test_category_slug_custom(self):
        cat = Category.objects.create(name='Hoodies', slug='sudaderas')
        self.assertEqual(cat.slug, 'sudaderas')

    # UT-353: HU-063 - Ordenado por sort_order
    def test_category_ordering(self):
        c1 = Category.objects.create(name='Accesorios', sort_order=2)
        c2 = Category.objects.create(name='Zapatos', sort_order=0)
        cats = list(Category.objects.all())
        self.assertEqual(cats, [c2, self.cat, c1])

    # UT-354: HU-064 CA-002 - Nombre único
    def test_category_unique_name(self):
        with self.assertRaises(IntegrityError):
            Category.objects.create(name='Camisetas', slug='otro')


# =============================================================================
# TESTS: COLOR MODEL (HU-068 a HU-072)
# =============================================================================

class ColorModelTest(TestCase):
    """HU-068 a HU-072: Gestión de colores"""

    def setUp(self):
        self.color = Color.objects.create(name='Negro', code='#000000', sort_order=1)

    # UT-355: HU-068 CA-001 - __str__ retorna el nombre
    def test_color_str(self):
        self.assertEqual(str(self.color), 'Negro')

    # UT-356: HU-069 CA-002 - Código único
    def test_color_unique_code(self):
        with self.assertRaises(IntegrityError):
            Color.objects.create(name='Blanco', code='#000000')

    # UT-357: HU-068 - Ordenado por sort_order
    def test_color_ordering(self):
        c2 = Color.objects.create(name='Blanco', code='#FFFFFF', sort_order=0)
        colors = list(Color.objects.all())
        self.assertEqual(colors, [c2, self.color])

    # UT-358: HU-069 CA-001 - sort_order por defecto 0
    def test_color_default_sort_order(self):
        c = Color.objects.create(name='Rojo', code='#FF0000')
        self.assertEqual(c.sort_order, 0)


# =============================================================================
# TESTS: PRODUCT IMAGE MODEL (HU-073 a HU-076)
# =============================================================================

class ProductImageModelTest(TestCase):
    """HU-073 a HU-076: Gestión de imágenes"""

    @patch('apps.products.models.ProductImage.image', new_callable=PropertyMock)
    def test_product_image_str_with_alt(self, mock_image):
        # UT-359: HU-073 CA-001 - __str__ retorna alt_text si existe
        img = ProductImage(alt_text='Foto frontal', id=1)
        self.assertEqual(str(img), 'Foto frontal')

    @patch('apps.products.models.ProductImage.image', new_callable=PropertyMock)
    def test_product_image_str_without_alt(self, mock_image):
        # UT-360: HU-073 - __str__ retorna 'Imagen {id}' si no hay alt_text
        img = ProductImage(alt_text='', id=5)
        self.assertEqual(str(img), 'Imagen 5')

    # UT-361: HU-073 - Ordenado por id por defecto
    def test_product_image_ordering(self):
        img1 = ProductImage.objects.create(alt_text='A')
        img2 = ProductImage.objects.create(alt_text='B')
        images = list(ProductImage.objects.all())
        self.assertEqual(images, [img1, img2])

    # UT-362: HU-074 - alt_text opcional
    def test_product_image_default_alt_blank(self):
        img = ProductImage.objects.create()
        self.assertEqual(img.alt_text, '')


# =============================================================================
# TESTS: PRODUCT COLOR MODEL (HU-013 parte)
# =============================================================================

class ProductColorModelTest(TestCase):
    """HU-013: Gestionar tallas y stock - colores por producto"""

    def setUp(self):
        self.size = Size.objects.create(name='M')
        self.category = Category.objects.create(name='Test')
        self.color = Color.objects.create(name='Rojo', code='#FF0000')
        self.product = Product.objects.create(
            name='Producto Test', price=10000,
            category=self.category, product_type='fabrica'
        )
        self.product_color = ProductColor.objects.create(
            product=self.product, color=self.color, sort_order=1
        )

    # UT-363: HU-013 - __str__ retorna 'producto - color'
    def test_product_color_str(self):
        self.assertEqual(str(self.product_color), 'Producto Test - Rojo')

    # UT-364: HU-013 - Mismo producto y color viola unique_together
    def test_product_color_unique_together(self):
        with self.assertRaises(IntegrityError):
            ProductColor.objects.create(product=self.product, color=self.color)

    # UT-365: HU-013 - Ordenado por sort_order
    def test_product_color_ordering(self):
        color2 = Color.objects.create(name='Azul', code='#0000FF')
        pc2 = ProductColor.objects.create(
            product=self.product, color=color2, sort_order=0
        )
        pcs = list(ProductColor.objects.all())
        self.assertEqual(pcs, [pc2, self.product_color])

    # UT-366: HU-013 - get_images retorna lista vacía sin imágenes
    def test_get_images_empty(self):
        self.assertEqual(self.product_color.get_images(), [])

    # UT-367: HU-013 - get_images pone featured_image primero
    def test_get_images_with_featured_first(self):
        img1 = ProductImage.objects.create(alt_text='Img1')
        img2 = ProductImage.objects.create(alt_text='Img2')
        self.product_color.images.add(img1, img2)
        self.product_color.featured_image = img2
        self.product_color.save()
        images = self.product_color.get_images()
        self.assertEqual(images, [img2, img1])

    # UT-368: HU-013 - get_images sin featured retorna todas en orden
    def test_get_images_no_featured(self):
        img1 = ProductImage.objects.create(alt_text='Img1')
        img2 = ProductImage.objects.create(alt_text='Img2')
        self.product_color.images.add(img1, img2)
        images = self.product_color.get_images()
        self.assertEqual(images, [img1, img2])


# =============================================================================
# TESTS: PRODUCT MODEL (HU-004 a HU-013)
# =============================================================================

class ProductModelTest(TestCase):
    """HU-004 a HU-013: Gestión de productos"""

    def setUp(self):
        self.category = Category.objects.create(name='Test')
        self.color = Color.objects.create(name='Rojo', code='#FF0000')
        self.size = Size.objects.create(name='M')
        self.product = Product.objects.create(
            name='Camiseta Roja', price=25000,
            category=self.category, product_type='fabrica'
        )
        self.product_color = ProductColor.objects.create(
            product=self.product, color=self.color
        )
        self.variant1 = ProductVariant.objects.create(
            product=self.product, product_color=self.product_color,
            size=self.size, stock=10
        )

    # UT-369: HU-006 CA-001 - __str__ retorna el nombre
    def test_product_str(self):
        self.assertEqual(str(self.product), 'Camiseta Roja')

    # UT-370: HU-009 CA-001 - Slug se genera automáticamente
    def test_product_slug_auto_generated(self):
        self.assertEqual(self.product.slug, 'camiseta-roja')

    # UT-371: HU-011 CA-001 - Slug personalizado se mantiene
    def test_product_slug_custom(self):
        p = Product.objects.create(
            name='Producto', price=10000, category=self.category,
            slug='mi-producto'
        )
        self.assertEqual(p.slug, 'mi-producto')

    # UT-372: HU-010 CA-002 - clean lanza error si price <= 0
    def test_product_clean_price_positive(self):
        p = Product(name='Test', price=Decimal('0'), category=self.category)
        with self.assertRaises(ValidationError):
            p.clean()

    # UT-373: HU-010 CA-002 - clean lanza error si price negativo
    def test_product_clean_price_positive_negative(self):
        p = Product(name='Test', price=Decimal('-100'), category=self.category)
        with self.assertRaises(ValidationError):
            p.clean()

    # UT-374: HU-013 CA-005 - total_stock suma stock de variantes activas
    def test_total_stock(self):
        self.assertEqual(self.product.total_stock(), 10)

    # UT-375: HU-013 - Variantes inactivas no se suman
    def test_total_stock_inactive_excluded(self):
        self.variant1.is_active = False
        self.variant1.save()
        self.assertEqual(self.product.total_stock(), 0)

    # UT-376: HU-007 CA-001 - stock_by_size_color retorna dict
    def test_stock_by_size_color(self):
        result = self.product.stock_by_size_color()
        expected = {'M-Rojo': 10}
        self.assertEqual(result, expected)

    # UT-377: HU-008 CA-001 - available_variants retorna variantes con stock > 0
    def test_available_variants(self):
        av = self.product.available_variants()
        self.assertEqual(av.count(), 1)
        self.assertEqual(av.first(), self.variant1)

    # UT-378: HU-008 CA-002 - Variante con stock 0 no está en available
    def test_available_variants_excludes_zero(self):
        self.variant1.stock = 0
        self.variant1.save()
        av = self.product.available_variants()
        self.assertNotIn(self.variant1, av)

    # UT-379: HU-004 CA-001 - is_available True si hay variante con stock
    def test_is_available_true(self):
        self.assertTrue(self.product.is_available())

    # UT-380: HU-004 CA-003 - is_available False si todas variantes sin stock
    def test_is_available_false(self):
        self.variant1.stock = 0
        self.variant1.save()
        self.assertFalse(self.product.is_available())

    # UT-381: HU-006 - get_featured_image usa prefetched si disponible
    @patch('apps.products.models.Product.product_colors')
    def test_get_featured_image_prefetched(self, mock_pc):
        mock_pc.all.return_value = []
        self.product._prefetched_objects_cache = {'product_colors': []}
        self.assertIsNone(self.product.get_featured_image())

    # UT-382: HU-006 - get_featured_image sin prefetch consulta BD
    def test_get_featured_image_from_db(self):
        self.assertIsNone(self.product.get_featured_image())

    # UT-383: HU-006 CA-001 - get_featured_image retorna primera imagen disponible
    def test_get_featured_image_with_image(self):
        img = ProductImage.objects.create(alt_text='Imagen')
        self.product_color.images.add(img)
        self.product_color.featured_image = img
        self.product_color.save()
        product = Product.objects.get(pk=self.product.pk)
        self.assertEqual(product.get_featured_image(), img)


# =============================================================================
# TESTS: PRODUCT VARIANT MANAGER (HU-013 parte)
# =============================================================================

class ProductVariantManagerTest(TestCase):
    """HU-013: Gestionar tallas y stock - queries de variantes"""

    def setUp(self):
        self.category = Category.objects.create(name='Test')
        self.color = Color.objects.create(name='Rojo', code='#FF0000')
        self.size_m = Size.objects.create(name='M')
        self.size_l = Size.objects.create(name='L')
        self.size_s = Size.objects.create(name='S')
        self.product = Product.objects.create(
            name='Producto', price=10000, category=self.category
        )
        self.pc = ProductColor.objects.create(product=self.product, color=self.color)
        self.v1 = ProductVariant.objects.create(
            product=self.product, product_color=self.pc, size=self.size_m, stock=5
        )
        self.v2 = ProductVariant.objects.create(
            product=self.product, product_color=self.pc, size=self.size_l, stock=0
        )
        self.v3 = ProductVariant.objects.create(
            product=self.product, product_color=self.pc, size=self.size_s, stock=2
        )

    # UT-384: HU-008 CA-001 - available retorna variantes activas con stock > 0
    def test_available(self):
        qs = ProductVariant.objects.available()
        self.assertIn(self.v1, qs)
        self.assertIn(self.v3, qs)
        self.assertNotIn(self.v2, qs)

    # UT-385: HU-008 CA-002 - in_stock retorna variantes con stock > 0
    def test_in_stock(self):
        qs = ProductVariant.objects.in_stock()
        self.assertIn(self.v1, qs)
        self.assertIn(self.v3, qs)
        self.assertNotIn(self.v2, qs)

    # UT-386: HU-008 CA-002 - out_of_stock retorna variantes activas con stock = 0
    def test_out_of_stock(self):
        qs = ProductVariant.objects.out_of_stock()
        self.assertIn(self.v2, qs)

    # UT-387: HU-013 - low_stock retorna variantes con stock entre 1 y threshold
    def test_low_stock_default_threshold(self):
        qs = ProductVariant.objects.low_stock()
        self.assertIn(self.v1, qs)
        self.assertIn(self.v3, qs)
        self.assertNotIn(self.v2, qs)

    # UT-388: HU-013 - low_stock con threshold personalizado
    def test_low_stock_custom_threshold(self):
        qs = ProductVariant.objects.low_stock(threshold=3)
        self.assertNotIn(self.v1, qs)
        self.assertIn(self.v3, qs)

    # UT-389: HU-009 CA-001 - for_product filtra por producto
    def test_for_product(self):
        qs = ProductVariant.objects.for_product(self.product)
        self.assertIn(self.v1, qs)
        self.assertEqual(qs.count(), 3)

    # UT-390: HU-007 CA-001 - by_size_color filtra por size_id
    def test_by_size_color(self):
        qs = ProductVariant.objects.by_size_color(
            size_id=self.size_m.id, color_id=self.color.id
        )
        self.assertIn(self.v1, qs)
        self.assertEqual(qs.count(), 1)

    # UT-391: HU-007 CA-001 - by_size_color con ambos filtros
    def test_by_size_color_both(self):
        qs = ProductVariant.objects.by_size_color(
            size_id=self.size_m.id, color_id=self.color.id
        )
        self.assertIn(self.v1, qs)


# =============================================================================
# TESTS: PRODUCT VARIANT MODEL (HU-013 parte)
# =============================================================================

class ProductVariantModelTest(TestCase):
    """HU-013: Gestionar tallas y stock - modelo de variante"""

    def setUp(self):
        self.category = Category.objects.create(name='Test')
        self.color = Color.objects.create(name='Rojo', code='#FF0000')
        self.size = Size.objects.create(name='M')
        self.product = Product.objects.create(
            name='Producto', price=10000, category=self.category
        )
        self.pc = ProductColor.objects.create(product=self.product, color=self.color)
        self.variant = ProductVariant.objects.create(
            product=self.product, product_color=self.pc, size=self.size, stock=10
        )

    # UT-392: HU-013 - __str__ retorna 'producto - color - talla'
    def test_variant_str(self):
        self.assertEqual(str(self.variant), 'Producto - Rojo - M')

    # UT-393: HU-013 - property color retorna objeto Color
    def test_variant_color_property(self):
        self.assertEqual(self.variant.color, self.color)

    # UT-394: HU-013 - property color_name retorna nombre
    def test_variant_color_name(self):
        self.assertEqual(self.variant.color_name, 'Rojo')

    # UT-395: HU-013 - property color_code retorna código
    def test_variant_color_code(self):
        self.assertEqual(self.variant.color_code, '#FF0000')

    # UT-396: HU-006 CA-001 - images property llama a get_images
    def test_variant_images_property(self):
        img = ProductImage.objects.create(alt_text='Test')
        self.pc.images.add(img)
        self.assertIn(img, self.variant.images)

    # UT-397: HU-006 CA-001 - featured_image property retorna el featured
    def test_variant_featured_image(self):
        img = ProductImage.objects.create(alt_text='Feat')
        self.pc.featured_image = img
        self.pc.save()
        variant = ProductVariant.objects.get(pk=self.variant.pk)
        self.assertEqual(variant.featured_image, img)

    # UT-398: HU-008 CA-001 - stock_status 'available' cuando stock > threshold
    def test_stock_status_available(self):
        self.variant.stock = STOCK_LOW_THRESHOLD + 1
        self.assertEqual(self.variant.stock_status, 'available')

    # UT-399: HU-008 CA-001 - stock_status 'low_stock' cuando 0 < stock <= threshold
    def test_stock_status_low_stock(self):
        self.variant.stock = STOCK_LOW_THRESHOLD
        self.assertEqual(self.variant.stock_status, 'low_stock')

    # UT-400: HU-008 CA-002 - stock_status 'out_of_stock' cuando stock = 0
    def test_stock_status_out_of_stock(self):
        self.variant.stock = 0
        self.assertEqual(self.variant.stock_status, 'out_of_stock')

    # UT-401: HU-013 - stock_status 'discontinued' si is_active=False
    def test_stock_status_discontinued(self):
        self.variant.is_active = False
        self.assertEqual(self.variant.stock_status, 'discontinued')

    # UT-402: HU-008 CA-001 - is_available True si activo y stock > 0
    def test_is_available_true(self):
        self.assertTrue(self.variant.is_available)

    # UT-403: HU-008 CA-002 - is_available False si inactivo
    def test_is_available_false_inactive(self):
        self.variant.is_active = False
        self.assertFalse(self.variant.is_available)

    # UT-404: HU-008 CA-002 - is_available False si stock = 0
    def test_is_available_false_zero_stock(self):
        self.variant.stock = 0
        self.assertFalse(self.variant.is_available)

    # UT-405: HU-008 CA-001 - get_stock_display muestra cantidad
    def test_get_stock_display_available(self):
        self.variant.stock = STOCK_LOW_THRESHOLD + 1
        self.assertEqual(self.variant.get_stock_display(), f'{STOCK_LOW_THRESHOLD + 1} disponibles')

    # UT-406: HU-008 CA-001 - get_stock_display muestra advertencia low stock
    def test_get_stock_display_low_stock(self):
        self.variant.stock = STOCK_LOW_THRESHOLD
        self.assertEqual(self.variant.get_stock_display(), f'¡Últimas {STOCK_LOW_THRESHOLD} unidades!')

    # UT-407: HU-008 CA-002 - get_stock_display 'Agotado'
    def test_get_stock_display_out_of_stock(self):
        self.variant.stock = 0
        self.assertEqual(self.variant.get_stock_display(), 'Agotado')

    # UT-408: HU-013 - get_stock_display 'No disponible' si inactivo
    def test_get_stock_display_discontinued(self):
        self.variant.is_active = False
        self.assertEqual(self.variant.get_stock_display(), 'No disponible')


# =============================================================================
# TESTS: PRODUCT VARIANT CLEAN & SAVE
# =============================================================================

class ProductVariantCleanTest(TestCase):
    """HU-013: Validaciones de variante"""

    def setUp(self):
        self.category = Category.objects.create(name='Test')
        self.color = Color.objects.create(name='Rojo', code='#FF0000')
        self.size = Size.objects.create(name='M')
        self.product1 = Product.objects.create(name='Prod1', price=10000, category=self.category)
        self.product2 = Product.objects.create(name='Prod2', price=20000, category=self.category)
        self.pc1 = ProductColor.objects.create(product=self.product1, color=self.color)
        self.pc2 = ProductColor.objects.create(product=self.product2, color=self.color)

    # UT-409: HU-013 - stock negativo lanza ValidationError
    def test_clean_negative_stock(self):
        v = ProductVariant(
            product=self.product1, product_color=self.pc1,
            size=self.size, stock=-1
        )
        with self.assertRaises(ValidationError):
            v.clean()

    # UT-410: HU-013 CA-001 - Variante válida no lanza error
    def test_clean_valid(self):
        v = ProductVariant(
            product=self.product1, product_color=self.pc1,
            size=self.size, stock=5
        )
        try:
            v.clean()
        except ValidationError:
            self.fail('clean() lanzó ValidationError innecesariamente')

    # UT-411: HU-013 - save genera SKU automáticamente
    def test_save_generates_sku(self):
        v = ProductVariant(
            product=self.product1, product_color=self.pc1,
            size=self.size, stock=5
        )
        v.save()
        self.assertIsNotNone(v.sku)
        self.assertIn('ZCD', v.sku)

    # UT-412: HU-013 - Si SKU ya existe no se sobrescribe
    def test_save_sku_already_set(self):
        v = ProductVariant(
            product=self.product1, product_color=self.pc1,
            size=self.size, stock=5, sku='CUSTOM-SKU'
        )
        v.save()
        self.assertEqual(v.sku, 'CUSTOM-SKU')


# =============================================================================
# TESTS: COLLECTION MODEL (HU-014 a HU-018)
# =============================================================================

class CollectionModelTest(TestCase):
    """HU-014 a HU-018: Gestión de colecciones"""

    def setUp(self):
        self.category = Category.objects.create(name='Test')
        self.product = Product.objects.create(
            name='Producto', price=10000, category=self.category
        )
        self.collection = Collection.objects.create(
            name='Colección Otoño', description='Descripción',
            status='borrador'
        )

    # UT-413: HU-014 CA-001 - __str__ retorna el nombre
    def test_collection_str(self):
        self.assertEqual(str(self.collection), 'Colección Otoño')

    # UT-414: HU-015 CA-001 - Slug se genera automáticamente
    def test_collection_slug_auto(self):
        self.assertEqual(self.collection.slug, 'coleccion-otono')

    # UT-415: HU-015 CA-004 - get_style_config usa campos individuales
    def test_collection_get_style_config_individual(self):
        collection = Collection.objects.create(
            name='Test', primary_color='#123456'
        )
        config = collection.get_style_config()
        self.assertEqual(config['colors']['primary'], '#123456')

    # UT-416: HU-015 - get_style_config usa style_config legacy
    def test_collection_get_style_config_legacy(self):
        collection = Collection.objects.create(
            name='Test', style_config={'colors': {'primary': '#abc'}}
        )
        config = collection.get_style_config()
        self.assertEqual(config['colors']['primary'], '#abc')

    # UT-417: HU-015 CA-002 - Fecha fin anterior a inicio da error
    def test_collection_clean_dates_invalid(self):
        c = Collection(
            name='Test',
            start_date=timezone.now(),
            end_date=timezone.now() - timedelta(days=1)
        )
        with self.assertRaises(ValidationError):
            c.clean()

    # UT-418: HU-015 CA-002 - Colección publicada sin productos da error
    def test_collection_clean_published_without_products(self):
        c = Collection(name='Test', status='publicada')
        try:
            c.clean()
        except ValidationError:
            self.fail('clean() lanzó ValidationError para objeto nuevo')
        
        c.save()
        with self.assertRaises(ValidationError):
            c.clean()

    # UT-419: HU-018 CA-001 - update_products_type actualiza tipo de productos
    def test_collection_update_products_type(self):
        self.collection.products.add(self.product)
        self.collection.status = 'publicada'
        self.collection.save()
        self.collection.update_products_type()
        self.product.refresh_from_db()
        self.assertEqual(self.product.product_type, 'coleccion_limitada')