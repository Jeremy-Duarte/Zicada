"""
Tests para modelos de la app products.
CP-321 a CP-395
"""
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
# TESTS: SIZE MODEL (CP-321 a CP-324)
# =============================================================================

class SizeModelTest(TestCase):
    def setUp(self):
        self.size = Size.objects.create(name='M', sort_order=2)
        self.size_xs = Size.objects.create(name='XS', sort_order=1)

    def test_size_str(self):
        """CP-321: __str__ retorna el nombre."""
        self.assertEqual(str(self.size), 'M')

    def test_size_ordering(self):
        """CP-322: Ordenado por sort_order."""
        sizes = list(Size.objects.all())
        self.assertEqual(sizes, [self.size_xs, self.size])

    def test_size_unique_name(self):
        """CP-323: Nombre único (violación de unicidad)."""
        with self.assertRaises(IntegrityError):
            Size.objects.create(name='M')

    def test_size_default_sort_order_zero(self):
        """CP-324: sort_order por defecto 0."""
        s = Size.objects.create(name='XXL')
        self.assertEqual(s.sort_order, 0)


# =============================================================================
# TESTS: CATEGORY MODEL (CP-325 a CP-329)
# =============================================================================

class CategoryModelTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Camisetas', sort_order=1)

    def test_category_str(self):
        """CP-325: __str__ retorna el nombre."""
        self.assertEqual(str(self.cat), 'Camisetas')

    def test_category_slug_auto_generated(self):
        """CP-326: Slug se genera automáticamente desde el nombre."""
        self.assertEqual(self.cat.slug, 'camisetas')

    def test_category_slug_custom(self):
        """CP-327: Slug personalizado se mantiene."""
        cat = Category.objects.create(name='Hoodies', slug='sudaderas')
        self.assertEqual(cat.slug, 'sudaderas')

    def test_category_ordering(self):
        """CP-328: Ordenado por sort_order."""
        c1 = Category.objects.create(name='Accesorios', sort_order=2)
        c2 = Category.objects.create(name='Zapatos', sort_order=0)
        cats = list(Category.objects.all())
        self.assertEqual(cats, [c2, self.cat, c1])

    def test_category_unique_name(self):
        """CP-329: Nombre único (violación)."""
        with self.assertRaises(IntegrityError):
            Category.objects.create(name='Camisetas', slug='otro')


# =============================================================================
# TESTS: COLOR MODEL (CP-330 a CP-333)
# =============================================================================

class ColorModelTest(TestCase):
    def setUp(self):
        self.color = Color.objects.create(name='Negro', code='#000000', sort_order=1)

    def test_color_str(self):
        """CP-330: __str__ retorna el nombre."""
        self.assertEqual(str(self.color), 'Negro')

    def test_color_unique_code(self):
        """CP-331: Código único."""
        with self.assertRaises(IntegrityError):
            Color.objects.create(name='Blanco', code='#000000')

    def test_color_ordering(self):
        """CP-332: Ordenado por sort_order."""
        c2 = Color.objects.create(name='Blanco', code='#FFFFFF', sort_order=0)
        colors = list(Color.objects.all())
        self.assertEqual(colors, [c2, self.color])

    def test_color_default_sort_order(self):
        """CP-333: sort_order por defecto 0."""
        c = Color.objects.create(name='Rojo', code='#FF0000')
        self.assertEqual(c.sort_order, 0)


# =============================================================================
# TESTS: PRODUCT IMAGE MODEL (CP-334 a CP-337)
# =============================================================================

class ProductImageModelTest(TestCase):
    @patch('apps.products.models.ProductImage.image', new_callable=PropertyMock)
    def test_product_image_str_with_alt(self, mock_image):
        """CP-334: __str__ retorna alt_text si existe."""
        img = ProductImage(alt_text='Foto frontal', id=1)
        self.assertEqual(str(img), 'Foto frontal')

    @patch('apps.products.models.ProductImage.image', new_callable=PropertyMock)
    def test_product_image_str_without_alt(self, mock_image):
        """CP-335: __str__ retorna 'Imagen {id}' si no hay alt_text."""
        img = ProductImage(alt_text='', id=5)
        self.assertEqual(str(img), 'Imagen 5')

    def test_product_image_ordering(self):
        """CP-336: Ordenado por id (por defecto)."""
        img1 = ProductImage.objects.create(alt_text='A')
        img2 = ProductImage.objects.create(alt_text='B')
        images = list(ProductImage.objects.all())
        self.assertEqual(images, [img1, img2])

    def test_product_image_default_alt_blank(self):
        """CP-337: alt_text blank=True."""
        img = ProductImage.objects.create()
        self.assertEqual(img.alt_text, '')


# =============================================================================
# TESTS: PRODUCT COLOR MODEL (CP-338 a CP-343)
# =============================================================================

class ProductColorModelTest(TestCase):
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

    def test_product_color_str(self):
        """CP-338: __str__ retorna 'producto - color'."""
        self.assertEqual(str(self.product_color), 'Producto Test - Rojo')

    def test_product_color_unique_together(self):
        """CP-339: Mismo producto y color → violación unique_together."""
        with self.assertRaises(IntegrityError):
            ProductColor.objects.create(product=self.product, color=self.color)

    def test_product_color_ordering(self):
        """CP-340: Ordenado por sort_order."""
        color2 = Color.objects.create(name='Azul', code='#0000FF')
        pc2 = ProductColor.objects.create(
            product=self.product, color=color2, sort_order=0
        )
        pcs = list(ProductColor.objects.all())
        self.assertEqual(pcs, [pc2, self.product_color])

    def test_get_images_empty(self):
        """CP-341: get_images retorna lista vacía si no hay imágenes."""
        self.assertEqual(self.product_color.get_images(), [])

    def test_get_images_with_featured_first(self):
        """CP-342: get_images pone featured_image primero."""
        img1 = ProductImage.objects.create(alt_text='Img1')
        img2 = ProductImage.objects.create(alt_text='Img2')
        self.product_color.images.add(img1, img2)
        self.product_color.featured_image = img2
        self.product_color.save()
        images = self.product_color.get_images()
        self.assertEqual(images, [img2, img1])

    def test_get_images_no_featured(self):
        """CP-343: get_images sin featured_image retorna todas en orden."""
        img1 = ProductImage.objects.create(alt_text='Img1')
        img2 = ProductImage.objects.create(alt_text='Img2')
        self.product_color.images.add(img1, img2)
        images = self.product_color.get_images()
        self.assertEqual(images, [img1, img2])


# =============================================================================
# TESTS: PRODUCT MODEL (CP-344 a CP-358)
# =============================================================================

class ProductModelTest(TestCase):
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

    def test_product_str(self):
        """CP-344: __str__ retorna el nombre."""
        self.assertEqual(str(self.product), 'Camiseta Roja')

    def test_product_slug_auto_generated(self):
        """CP-345: Slug se genera automáticamente."""
        self.assertEqual(self.product.slug, 'camiseta-roja')

    def test_product_slug_custom(self):
        """CP-346: Slug personalizado se mantiene."""
        p = Product.objects.create(
            name='Producto', price=10000, category=self.category,
            slug='mi-producto'
        )
        self.assertEqual(p.slug, 'mi-producto')

    def test_product_clean_price_positive(self):
        """CP-347: clean lanza ValidationError si price <= 0."""
        p = Product(name='Test', price=Decimal('0'), category=self.category)
        with self.assertRaises(ValidationError):
            p.clean()

    def test_product_clean_price_positive_negative(self):
        """CP-348: clean lanza ValidationError si price negativo."""
        p = Product(name='Test', price=Decimal('-100'), category=self.category)
        with self.assertRaises(ValidationError):
            p.clean()

    def test_total_stock(self):
        """CP-349: total_stock suma stock de variantes activas."""
        self.assertEqual(self.product.total_stock(), 10)

    def test_total_stock_inactive_excluded(self):
        """CP-350: Variantes inactivas no se suman."""
        self.variant1.is_active = False
        self.variant1.save()
        self.assertEqual(self.product.total_stock(), 0)

    def test_stock_by_size_color(self):
        """CP-351: stock_by_size_color retorna dict con tallas y colores."""
        result = self.product.stock_by_size_color()
        expected = {'M-Rojo': 10}
        self.assertEqual(result, expected)

    def test_available_variants(self):
        """CP-352: available_variants retorna variantes con stock > 0."""
        av = self.product.available_variants()
        self.assertEqual(av.count(), 1)
        self.assertEqual(av.first(), self.variant1)

    def test_available_variants_excludes_zero(self):
        """CP-353: Variante con stock 0 no está en available."""
        self.variant1.stock = 0
        self.variant1.save()
        av = self.product.available_variants()
        self.assertNotIn(self.variant1, av)

    def test_is_available_true(self):
        """CP-354: is_available True si hay variante con stock."""
        self.assertTrue(self.product.is_available())

    def test_is_available_false(self):
        """CP-355: is_available False si todas las variantes sin stock o inactivas."""
        self.variant1.stock = 0
        self.variant1.save()
        self.assertFalse(self.product.is_available())

    @patch('apps.products.models.Product.product_colors')
    def test_get_featured_image_prefetched(self, mock_pc):
        """CP-356: get_featured_image usa prefetched si disponible."""
        mock_pc.all.return_value = []
        self.product._prefetched_objects_cache = {'product_colors': []}
        self.assertIsNone(self.product.get_featured_image())

    def test_get_featured_image_from_db(self):
        """CP-357: get_featured_image sin prefetch consulta BD."""
        self.assertIsNone(self.product.get_featured_image())

    def test_get_featured_image_with_image(self):
        """CP-358: get_featured_image retorna la primera imagen disponible."""
        img = ProductImage.objects.create(alt_text='Imagen')
        self.product_color.images.add(img)
        self.product_color.featured_image = img
        self.product_color.save()
        product = Product.objects.get(pk=self.product.pk)
        self.assertEqual(product.get_featured_image(), img)


# =============================================================================
# TESTS: PRODUCT VARIANT MANAGER (CP-359 a CP-366)
# =============================================================================

class ProductVariantManagerTest(TestCase):
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

    def test_available(self):
        """CP-359: available retorna variantes activas con stock > 0."""
        qs = ProductVariant.objects.available()
        self.assertIn(self.v1, qs)
        self.assertIn(self.v3, qs)
        self.assertNotIn(self.v2, qs)

    def test_in_stock(self):
        """CP-360: in_stock retorna variantes con stock > 0."""
        qs = ProductVariant.objects.in_stock()
        self.assertIn(self.v1, qs)
        self.assertIn(self.v3, qs)
        self.assertNotIn(self.v2, qs)

    def test_out_of_stock(self):
        """CP-361: out_of_stock retorna variantes activas con stock = 0."""
        qs = ProductVariant.objects.out_of_stock()
        self.assertIn(self.v2, qs)

    def test_low_stock_default_threshold(self):
        """CP-362: low_stock retorna variantes con stock entre 1 y threshold."""
        qs = ProductVariant.objects.low_stock()
        # Como STOCK_LOW_THRESHOLD = 10, stock=5 y 2 son bajos
        self.assertIn(self.v1, qs, f"v1 (stock=5) debería estar en low_stock")
        self.assertIn(self.v3, qs, f"v3 (stock=2) debería estar en low_stock")
        self.assertNotIn(self.v2, qs)

    def test_low_stock_custom_threshold(self):
        """CP-363: low_stock con threshold personalizado."""
        qs = ProductVariant.objects.low_stock(threshold=3)
        self.assertNotIn(self.v1, qs)  # stock=5 > 3
        self.assertIn(self.v3, qs)      # stock=2 <= 3

    def test_for_product(self):
        """CP-364: for_product filtra por producto."""
        qs = ProductVariant.objects.for_product(self.product)
        self.assertIn(self.v1, qs)
        self.assertEqual(qs.count(), 3)

    def test_by_size_color(self):
        """CP-365: by_size_color filtra por size_id."""
        qs = ProductVariant.objects.by_size_color(
            size_id=self.size_m.id, color_id=self.color.id
        )
        self.assertIn(self.v1, qs)
        self.assertEqual(qs.count(), 1)

    def test_by_size_color_both(self):
        """CP-366: by_size_color con ambos filtros (size_id y color_id)."""
        qs = ProductVariant.objects.by_size_color(
            size_id=self.size_m.id, color_id=self.color.id
        )
        self.assertIn(self.v1, qs)


# =============================================================================
# TESTS: PRODUCT VARIANT MODEL (CP-367 a CP-383)
# =============================================================================

class ProductVariantModelTest(TestCase):
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

    def test_variant_str(self):
        """CP-367: __str__ retorna 'producto - color - talla'."""
        self.assertEqual(str(self.variant), 'Producto - Rojo - M')

    def test_variant_color_property(self):
        """CP-368: property color retorna el objeto Color."""
        self.assertEqual(self.variant.color, self.color)

    def test_variant_color_name(self):
        """CP-369: property color_name retorna nombre."""
        self.assertEqual(self.variant.color_name, 'Rojo')

    def test_variant_color_code(self):
        """CP-370: property color_code retorna código."""
        self.assertEqual(self.variant.color_code, '#FF0000')

    def test_variant_images_property(self):
        """CP-371: images property llama a get_images de ProductColor."""
        img = ProductImage.objects.create(alt_text='Test')
        self.pc.images.add(img)
        self.assertIn(img, self.variant.images)

    def test_variant_featured_image(self):
        """CP-372: featured_image property retorna el featured de ProductColor."""
        img = ProductImage.objects.create(alt_text='Feat')
        self.pc.featured_image = img
        self.pc.save()
        variant = ProductVariant.objects.get(pk=self.variant.pk)
        self.assertEqual(variant.featured_image, img)

    def test_stock_status_available(self):
        """CP-373: stock_status 'available' cuando stock > threshold."""
        self.variant.stock = STOCK_LOW_THRESHOLD + 1
        self.assertEqual(self.variant.stock_status, 'available')

    def test_stock_status_low_stock(self):
        """CP-374: stock_status 'low_stock' cuando 0 < stock <= threshold."""
        self.variant.stock = STOCK_LOW_THRESHOLD
        self.assertEqual(self.variant.stock_status, 'low_stock')

    def test_stock_status_out_of_stock(self):
        """CP-375: stock_status 'out_of_stock' cuando stock = 0."""
        self.variant.stock = 0
        self.assertEqual(self.variant.stock_status, 'out_of_stock')

    def test_stock_status_discontinued(self):
        """CP-376: stock_status 'discontinued' si is_active=False."""
        self.variant.is_active = False
        self.assertEqual(self.variant.stock_status, 'discontinued')

    def test_is_available_true(self):
        """CP-377: is_available True si activo y stock > 0."""
        self.assertTrue(self.variant.is_available)

    def test_is_available_false_inactive(self):
        """CP-378: is_available False si inactivo."""
        self.variant.is_active = False
        self.assertFalse(self.variant.is_available)

    def test_is_available_false_zero_stock(self):
        """CP-379: is_available False si stock = 0."""
        self.variant.stock = 0
        self.assertFalse(self.variant.is_available)

    def test_get_stock_display_available(self):
        """CP-380: get_stock_display muestra cantidad (solo si stock > threshold)."""
        self.variant.stock = STOCK_LOW_THRESHOLD + 1
        self.assertEqual(self.variant.get_stock_display(), f'{STOCK_LOW_THRESHOLD + 1} disponibles')

    def test_get_stock_display_low_stock(self):
        """CP-381: get_stock_display muestra advertencia."""
        self.variant.stock = STOCK_LOW_THRESHOLD
        self.assertEqual(self.variant.get_stock_display(), f'¡Últimas {STOCK_LOW_THRESHOLD} unidades!')

    def test_get_stock_display_out_of_stock(self):
        """CP-382: get_stock_display 'Agotado'."""
        self.variant.stock = 0
        self.assertEqual(self.variant.get_stock_display(), 'Agotado')

    def test_get_stock_display_discontinued(self):
        """CP-383: get_stock_display 'No disponible' si inactivo."""
        self.variant.is_active = False
        self.assertEqual(self.variant.get_stock_display(), 'No disponible')


# =============================================================================
# TESTS: PRODUCT VARIANT CLEAN & SAVE (CP-384 a CP-388)
# =============================================================================

class ProductVariantCleanTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test')
        self.color = Color.objects.create(name='Rojo', code='#FF0000')
        self.size = Size.objects.create(name='M')
        self.product1 = Product.objects.create(name='Prod1', price=10000, category=self.category)
        self.product2 = Product.objects.create(name='Prod2', price=20000, category=self.category)
        self.pc1 = ProductColor.objects.create(product=self.product1, color=self.color)
        self.pc2 = ProductColor.objects.create(product=self.product2, color=self.color)

    def test_clean_negative_stock(self):
        """CP-384: stock negativo lanza ValidationError."""
        v = ProductVariant(
            product=self.product1, product_color=self.pc1,
            size=self.size, stock=-1
        )
        with self.assertRaises(ValidationError):
            v.clean()

    def test_clean_valid(self):
        """CP-386: Variante válida no lanza error."""
        v = ProductVariant(
            product=self.product1, product_color=self.pc1,
            size=self.size, stock=5
        )
        try:
            v.clean()
        except ValidationError:
            self.fail('clean() lanzó ValidationError innecesariamente')

    def test_save_generates_sku(self):
        """CP-387: save() genera SKU automáticamente."""
        v = ProductVariant(
            product=self.product1, product_color=self.pc1,
            size=self.size, stock=5
        )
        v.save()
        self.assertIsNotNone(v.sku)
        self.assertIn('ZCD', v.sku)

    def test_save_sku_already_set(self):
        """CP-388: Si SKU ya existe, no se sobrescribe."""
        v = ProductVariant(
            product=self.product1, product_color=self.pc1,
            size=self.size, stock=5, sku='CUSTOM-SKU'
        )
        v.save()
        self.assertEqual(v.sku, 'CUSTOM-SKU')


# =============================================================================
# TESTS: COLLECTION MODEL (CP-389 a CP-395)
# =============================================================================

class CollectionModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test')
        self.product = Product.objects.create(
            name='Producto', price=10000, category=self.category
        )
        self.collection = Collection.objects.create(
            name='Colección Otoño', description='Descripción',
            status='borrador'
        )

    def test_collection_str(self):
        """CP-389: __str__ retorna el nombre."""
        self.assertEqual(str(self.collection), 'Colección Otoño')

    def test_collection_slug_auto(self):
        """CP-390: Slug se genera automáticamente."""
        self.assertEqual(self.collection.slug, 'coleccion-otono')

    def test_collection_get_style_config_individual(self):
        """CP-391: get_style_config usa campos individuales si están configurados."""
        collection = Collection.objects.create(
            name='Test', primary_color='#123456'
        )
        config = collection.get_style_config()
        self.assertEqual(config['colors']['primary'], '#123456')

    def test_collection_get_style_config_legacy(self):
        """CP-392: get_style_config usa style_config legacy si no hay individuales."""
        collection = Collection.objects.create(
            name='Test', style_config={'colors': {'primary': '#abc'}}
        )
        config = collection.get_style_config()
        self.assertEqual(config['colors']['primary'], '#abc')

    def test_collection_clean_dates_invalid(self):
        """CP-393: Fecha fin anterior a inicio → ValidationError."""
        c = Collection(
            name='Test',
            start_date=timezone.now(),
            end_date=timezone.now() - timedelta(days=1)
        )
        with self.assertRaises(ValidationError):
            c.clean()

    def test_collection_clean_published_without_products(self):
        """CP-394: Colección publicada sin productos → ValidationError (solo si tiene pk)."""
        # Para un objeto nuevo, no se valida (no tiene pk)
        c = Collection(name='Test', status='publicada')
        # No debe lanzar ValidationError porque aún no tiene pk
        try:
            c.clean()
        except ValidationError:
            self.fail('clean() lanzó ValidationError para objeto nuevo')
        
        # Para un objeto guardado, sí debe lanzar
        c.save()
        with self.assertRaises(ValidationError):
            c.clean()

    def test_collection_update_products_type(self):
        """CP-395: update_products_type actualiza tipo de productos asociados."""
        self.collection.products.add(self.product)
        self.collection.status = 'publicada'
        self.collection.save()
        self.collection.update_products_type()
        self.product.refresh_from_db()
        self.assertEqual(self.product.product_type, 'coleccion_limitada')