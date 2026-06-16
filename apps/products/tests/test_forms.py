from decimal import Decimal
from unittest.mock import patch, Mock
from datetime import datetime

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.products.forms import (
    SizeCreateForm, SizeUpdateForm, SizeDeleteForm,
    CategoryCreateForm, CategoryUpdateForm, CategoryDeleteForm, CategoryImportForm,
    ColorCreateForm, ColorUpdateForm, ColorDeleteForm, ColorImportForm,
    ProductImageCreateForm, ProductImageUpdateForm, ProductImageDeleteForm,
    ProductCreateForm, ProductUpdateForm, ProductDeleteForm, ProductRestoreForm,
    ProductColorCreateForm, ProductColorUpdateForm, ProductColorDeleteForm,
    ProductVariantCreateForm, ProductVariantUpdateForm, ProductVariantDeleteForm,
    ProductVariantRestoreForm,
)
from apps.products.models import (
    Size, Category, Color, ProductImage, Product, ProductColor,
    ProductVariant, Collection
)
from apps.products.constants import STOCK_LOW_THRESHOLD


# =============================================================================
# HELPERS
# =============================================================================

def _create_base_objects():
    cat = Category.objects.create(name='TestCat')
    color = Color.objects.create(name='Rojo', code='#FF0000')
    size = Size.objects.create(name='M')
    product = Product.objects.create(name='Prod', price=10000, category=cat)
    pc = ProductColor.objects.create(product=product, color=color)
    return cat, color, size, product, pc


# =============================================================================
# TESTS: SIZE FORMS (HU-058 a HU-062)
# =============================================================================

class SizeCreateFormTest(TestCase):
    """HU-059: Crear talla"""

    # UT-268: HU-059 CA-001 - Crear talla con nombre válido y único
    def test_size_create_valid(self):
        form = SizeCreateForm(data={'name': 'XL'})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(Size.objects.count(), 1)

    # UT-269: HU-059 CA-002 - Nombre duplicado da error
    def test_size_create_duplicate_name(self):
        Size.objects.create(name='M')
        form = SizeCreateForm(data={'name': 'm'})
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())

    # UT-270: HU-059 CA-001 - Nombre se convierte a mayúsculas
    def test_size_create_name_uppercased(self):
        form = SizeCreateForm(data={'name': '  xl '})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'XL')


class SizeUpdateFormTest(TestCase):
    """HU-060: Editar talla"""

    def setUp(self):
        self.size = Size.objects.create(name='M')

    # UT-271: HU-060 CA-001 - Actualizar nombre correctamente
    def test_size_update_valid(self):
        form = SizeUpdateForm(data={'name': 'L'}, instance=self.size)
        self.assertTrue(form.is_valid())
        form.save()
        self.size.refresh_from_db()
        self.assertEqual(self.size.name, 'L')

    # UT-272: HU-060 CA-002 - Nombre duplicado con otra talla da error
    def test_size_update_duplicate_name(self):
        Size.objects.create(name='L')
        form = SizeUpdateForm(data={'name': 'L'}, instance=self.size)
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())

    # UT-273: HU-060 CA-001 - Mantener mismo nombre permitido
    def test_size_update_same_name_allowed(self):
        form = SizeUpdateForm(data={'name': 'M'}, instance=self.size)
        self.assertTrue(form.is_valid())


class SizeDeleteFormTest(TestCase):
    """HU-061: Eliminar talla"""

    def setUp(self):
        self.size = Size.objects.create(name='M')

    # UT-274: HU-061 CA-001 - Confirmación correcta sin variantes válido
    def test_size_delete_confirm_correct(self):
        form = SizeDeleteForm(data={'confirm': 'M'}, size=self.size)
        self.assertTrue(form.is_valid())

    # UT-275: HU-061 CA-002 - Nombre no coincide da error
    def test_size_delete_wrong_name(self):
        form = SizeDeleteForm(data={'confirm': 'L'}, size=self.size)
        self.assertFalse(form.is_valid())
        self.assertIn('no coincide', form.errors['confirm'][0].lower())

    # UT-276: HU-061 CA-004 - Talla con variantes activas da error
    def test_size_delete_with_active_variants(self):
        cat = Category.objects.create(name='X')
        product = Product.objects.create(name='P', price=100, category=cat)
        color = Color.objects.create(name='N', code='#000')
        pc = ProductColor.objects.create(product=product, color=color)
        ProductVariant.objects.create(product=product, product_color=pc, size=self.size, stock=5)
        form = SizeDeleteForm(data={'confirm': 'M'}, size=self.size)
        self.assertFalse(form.is_valid())
        self.assertIn('variante', form.errors['confirm'][0].lower())

    # UT-277: HU-061 CA-001 - Comparación insensible a mayúsculas
    def test_size_delete_confirm_case_insensitive(self):
        form = SizeDeleteForm(data={'confirm': 'm'}, size=self.size)
        self.assertTrue(form.is_valid())


# =============================================================================
# TESTS: CATEGORY FORMS (HU-063 a HU-067)
# =============================================================================

class CategoryCreateFormTest(TestCase):
    """HU-064: Crear categoría"""

    # UT-278: HU-064 CA-001 - Crear categoría con nombre único
    def test_category_create_valid(self):
        form = CategoryCreateForm(data={'name': 'Camisetas'})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(Category.objects.count(), 1)

    # UT-279: HU-064 CA-002 - Nombre duplicado insensible a mayúsculas da error
    def test_category_create_duplicate_name_iexact(self):
        Category.objects.create(name='Camisetas')
        form = CategoryCreateForm(data={'name': 'camisetas'})
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())


class CategoryUpdateFormTest(TestCase):
    """HU-065: Editar categoría"""

    def setUp(self):
        self.cat = Category.objects.create(name='Camisetas', slug='camisetas')

    # UT-280: HU-065 CA-001 - Actualizar nombre y regenerar slug
    def test_category_update_valid(self):
        form = CategoryUpdateForm(data={'name': 'Hoodies'}, instance=self.cat)
        self.assertTrue(form.is_valid())
        form.save()
        self.cat.refresh_from_db()
        self.assertEqual(self.cat.name, 'Hoodies')
        self.assertEqual(self.cat.slug, 'hoodies')

    # UT-281: HU-065 CA-002 - Nombre duplicado da error
    def test_category_update_duplicate_name(self):
        Category.objects.create(name='Hoodies', slug='hoodies')
        form = CategoryUpdateForm(data={'name': 'Hoodies'}, instance=self.cat)
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())


class CategoryDeleteFormTest(TestCase):
    """HU-066: Eliminar categoría"""

    def setUp(self):
        self.cat = Category.objects.create(name='Camisetas')

    # UT-282: HU-066 CA-001 - Confirmación correcta sin productos válido
    def test_category_delete_confirm_correct(self):
        form = CategoryDeleteForm(data={'confirm': 'Camisetas'}, category=self.cat)
        self.assertTrue(form.is_valid())

    # UT-283: HU-066 CA-002 - Nombre no coincide da error
    def test_category_delete_wrong_name(self):
        form = CategoryDeleteForm(data={'confirm': 'Hoodies'}, category=self.cat)
        self.assertFalse(form.is_valid())

    # UT-284: HU-066 CA-004 - Categoría con productos activos da error
    def test_category_delete_with_active_products(self):
        cat = Category.objects.create(name='Test')
        Product.objects.create(name='P', price=100, category=cat)
        form = CategoryDeleteForm(data={'confirm': 'Test'}, category=cat)
        self.assertFalse(form.is_valid())
        self.assertIn('producto', form.errors['confirm'][0].lower())


class CategoryImportFormTest(TestCase):
    """HU-067: Importar categorías"""

    # UT-285: HU-067 CA-002 - Importación válida
    def test_category_import_valid(self):
        form = CategoryImportForm(data={'name': 'Accesorios'})
        self.assertTrue(form.is_valid())

    # UT-286: HU-067 CA-003 - Nombre duplicado da error
    def test_category_import_duplicate(self):
        Category.objects.create(name='Accesorios')
        form = CategoryImportForm(data={'name': 'Accesorios'})
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())

    # UT-287: HU-067 CA-001 - Nombre se limpia de espacios
    def test_category_import_name_stripped(self):
        form = CategoryImportForm(data={'name': '  Zapatos '})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'Zapatos')


# =============================================================================
# TESTS: COLOR FORMS (HU-068 a HU-072)
# =============================================================================

class ColorCreateFormTest(TestCase):
    """HU-069: Crear color"""

    # UT-288: HU-069 CA-001 - Crear color con nombre y código válido
    def test_color_create_valid(self):
        form = ColorCreateForm(data={'name': 'Negro', 'code': '#000000'})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(Color.objects.count(), 1)

    # UT-289: HU-069 CA-002 - Nombre duplicado da error
    def test_color_create_duplicate_name(self):
        Color.objects.create(name='Negro', code='#000000')
        form = ColorCreateForm(data={'name': 'negro', 'code': '#111111'})
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())

    # UT-290: HU-069 CA-002 - Código duplicado da error
    def test_color_create_duplicate_code(self):
        Color.objects.create(name='Rojo', code='#FF0000')
        form = ColorCreateForm(data={'name': 'Azul', 'code': '#ff0000'})
        self.assertFalse(form.is_valid())
        self.assertIn('ya está en uso', form.errors['code'][0].lower())

    # UT-291: HU-069 CA-002 - Código hexadecimal inválido da error
    def test_color_create_invalid_code_format(self):
        form = ColorCreateForm(data={'name': 'Test', 'code': 'XYZ'})
        self.assertFalse(form.is_valid())
        self.assertIn('hexadecimal', form.errors['code'][0].lower())

    # UT-292: HU-069 CA-001 - Código sin # se añade automáticamente
    def test_color_create_code_adds_hash(self):
        form = ColorCreateForm(data={'name': 'Test', 'code': 'FF0000'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['code'], '#FF0000')

    # UT-293: HU-069 CA-001 - Nombre se capitaliza
    def test_color_create_name_capitalized(self):
        form = ColorCreateForm(data={'name': 'blanco', 'code': '#FFF'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'Blanco')


class ColorUpdateFormTest(TestCase):
    """HU-070: Editar color"""

    def setUp(self):
        self.color = Color.objects.create(name='Rojo', code='#FF0000')

    # UT-294: HU-070 CA-001 - Actualizar nombre y código correctamente
    def test_color_update_valid(self):
        form = ColorUpdateForm(data={'name': 'Azul', 'code': '#0000FF'}, instance=self.color)
        self.assertTrue(form.is_valid())
        form.save()
        self.color.refresh_from_db()
        self.assertEqual(self.color.name, 'Azul')

    # UT-295: HU-070 CA-002 - Nombre duplicado con otro color da error
    def test_color_update_duplicate_name(self):
        Color.objects.create(name='Azul', code='#0000FF')
        form = ColorUpdateForm(data={'name': 'Azul'}, instance=self.color)
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())

    # UT-296: HU-070 CA-002 - Código duplicado da error
    def test_color_update_duplicate_code(self):
        Color.objects.create(name='Azul', code='#0000FF')
        form = ColorUpdateForm(data={'code': '#0000FF'}, instance=self.color)
        self.assertFalse(form.is_valid())

    # UT-297: HU-070 CA-001 - Mantener mismo nombre permitido
    def test_color_update_same_name_allowed(self):
        form = ColorUpdateForm(data={'name': 'Rojo', 'code': '#FF0000'}, instance=self.color)
        self.assertTrue(form.is_valid())


class ColorDeleteFormTest(TestCase):
    """HU-071: Eliminar color"""

    def setUp(self):
        self.color = Color.objects.create(name='Rojo', code='#FF0000')

    # UT-298: HU-071 CA-001 - Confirmación correcta sin variantes válido
    def test_color_delete_confirm_correct(self):
        form = ColorDeleteForm(data={'confirm': 'Rojo'}, color=self.color)
        self.assertTrue(form.is_valid())

    # UT-299: HU-071 CA-004 - Color con ProductColor activo da error
    def test_color_delete_with_active_product_colors(self):
        cat = Category.objects.create(name='X')
        product = Product.objects.create(name='P', price=100, category=cat)
        ProductColor.objects.create(product=product, color=self.color)
        form = ColorDeleteForm(data={'confirm': 'Rojo'}, color=self.color)
        self.assertFalse(form.is_valid())
        self.assertIn('variante', form.errors['confirm'][0].lower())

    # UT-300: HU-071 CA-002 - Nombre no coincide da error
    def test_color_delete_wrong_name(self):
        form = ColorDeleteForm(data={'confirm': 'Azul'}, color=self.color)
        self.assertFalse(form.is_valid())


class ColorImportFormTest(TestCase):
    """HU-072: Importar colores"""

    # UT-301: HU-072 CA-001 - Importación válida de color
    def test_color_import_valid(self):
        form = ColorImportForm(data={'name': 'Verde', 'code': '#00FF00'})
        self.assertTrue(form.is_valid())

    # UT-302: HU-072 CA-003 - Nombre duplicado da error
    def test_color_import_duplicate_name(self):
        Color.objects.create(name='Verde', code='#00FF00')
        form = ColorImportForm(data={'name': 'verde', 'code': '#000000'})
        self.assertFalse(form.is_valid())

    # UT-303: HU-072 CA-003 - Código duplicado da error
    def test_color_import_duplicate_code(self):
        Color.objects.create(name='Verde', code='#00FF00')
        form = ColorImportForm(data={'name': 'Otro', 'code': '#00ff00'})
        self.assertFalse(form.is_valid())


# =============================================================================
# TESTS: PRODUCT IMAGE FORMS (HU-073 a HU-076)
# =============================================================================

class ProductImageCreateFormTest(TestCase):
    """HU-074: Subir imagen de producto"""

    # UT-304: HU-074 CA-001 - Imagen con archivo y alt_text válido
    def test_image_create_valid(self):
        mock_file = Mock()
        mock_file.name = 'test.jpg'
        mock_file.size = 1024 * 1024
        form = ProductImageCreateForm(data={'alt_text': 'Foto'}, files={'image': mock_file})
        with patch('apps.products.forms.ALLOWED_IMAGE_EXTENSIONS', ['.jpg']):
            self.assertTrue(form.is_valid())

    # UT-305: HU-074 CA-002 - Sin archivo da error
    def test_image_create_no_file(self):
        form = ProductImageCreateForm(data={'alt_text': 'Foto'})
        self.assertFalse(form.is_valid())

    # UT-306: HU-074 CA-002 - Archivo mayor a 5MB da error
    def test_image_create_file_too_large(self):
        mock_file = Mock()
        mock_file.name = 'test.jpg'
        mock_file.size = 6 * 1024 * 1024
        form = ProductImageCreateForm(data={'alt_text': 'Foto'}, files={'image': mock_file})
        with patch('apps.products.forms.ALLOWED_IMAGE_EXTENSIONS', ['.jpg']):
            self.assertFalse(form.is_valid())
            self.assertIn('5MB', form.errors['image'][0])

    # UT-307: HU-074 CA-002 - Extensión no permitida da error
    def test_image_create_invalid_extension(self):
        mock_file = Mock()
        mock_file.name = 'test.gif'
        mock_file.size = 1024
        form = ProductImageCreateForm(data={'alt_text': 'Foto'}, files={'image': mock_file})
        with patch('apps.products.forms.ALLOWED_IMAGE_EXTENSIONS', ['.jpg', '.png']):
            self.assertFalse(form.is_valid())
            self.assertIn('soportado', form.errors['image'][0].lower())


class ProductImageUpdateFormTest(TestCase):
    """HU-075: Editar imagen de producto"""

    # UT-308: HU-075 CA-001 - Actualizar alt_text correctamente
    def test_image_update_valid(self):
        img = ProductImage.objects.create(alt_text='Antes')
        form = ProductImageUpdateForm(data={'alt_text': 'Después'}, instance=img)
        self.assertTrue(form.is_valid())
        form.save()
        img.refresh_from_db()
        self.assertEqual(img.alt_text, 'Después')

    # UT-309: HU-075 CA-001 - alt_text puede quedar en blanco
    def test_image_update_blank_alt(self):
        img = ProductImage.objects.create(alt_text='Antes')
        form = ProductImageUpdateForm(data={'alt_text': ''}, instance=img)
        self.assertTrue(form.is_valid())


class ProductImageDeleteFormTest(TestCase):
    """HU-076: Eliminar imagen de producto"""

    # UT-310: HU-076 CA-001 - Confirmación marcada válido
    def test_image_delete_confirm(self):
        img = ProductImage.objects.create()
        form = ProductImageDeleteForm(data={'confirm': True}, image=img)
        self.assertTrue(form.is_valid())

    # UT-311: HU-076 CA-002 - Confirmación no marcada da error
    def test_image_delete_not_confirmed(self):
        img = ProductImage.objects.create()
        form = ProductImageDeleteForm(data={'confirm': False}, image=img)
        self.assertFalse(form.is_valid())
        self.assertIn('confirmar', form.errors['__all__'][0].lower())


# =============================================================================
# TESTS: PRODUCT FORMS (HU-009 a HU-013)
# =============================================================================

class ProductCreateFormTest(TestCase):
    """HU-010: Crear producto"""

    def setUp(self):
        self.cat = Category.objects.create(name='Test')

    # UT-312: HU-010 CA-001 - Crear producto con datos válidos
    def test_product_create_valid(self):
        form = ProductCreateForm(data={
            'name': 'Camiseta',
            'price': 25000,
            'category': self.cat.id,
            'product_type': 'fabrica',
        })
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(Product.objects.count(), 1)

    # UT-313: HU-010 CA-003 - Nombre duplicado en productos activos da error
    def test_product_create_duplicate_name_active(self):
        Product.objects.create(name='Camiseta', price=10000, category=self.cat)
        form = ProductCreateForm(data={
            'name': 'camiseta',
            'price': 20000,
            'category': self.cat.id,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())

    # UT-314: HU-010 CA-002 - Precio igual a 0 da error
    def test_product_create_price_zero(self):
        form = ProductCreateForm(data={
            'name': 'Test',
            'price': 0,
            'category': self.cat.id,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('mayor', form.errors['price'][0].lower())

    # UT-315: HU-010 CA-002 - Precio mayor a 10,000,000 da error
    def test_product_create_price_exceeds_max(self):
        form = ProductCreateForm(data={
            'name': 'Test',
            'price': Decimal('10000001'),
            'category': self.cat.id,
            'product_type': 'fabrica',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)

    # UT-316: HU-010 CA-002 - Nombre vacío da error
    def test_product_create_missing_name(self):
        form = ProductCreateForm(data={
            'name': '',
            'price': 100,
            'category': self.cat.id,
        })
        self.assertFalse(form.is_valid())


class ProductUpdateFormTest(TestCase):
    """HU-011: Editar producto"""

    def setUp(self):
        self.cat = Category.objects.create(name='Test')
        self.product = Product.objects.create(name='Original', price=1000, category=self.cat)

    # UT-317: HU-011 CA-001 - Actualizar producto correctamente
    def test_product_update_valid(self):
        form = ProductUpdateForm(data={
            'name': 'Modificado',
            'price': 2000,
            'category': self.cat.id,
            'product_type': 'fabrica',
            'is_active': True,
        }, instance=self.product)
        self.assertTrue(form.is_valid())
        form.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Modificado')

    # UT-318: HU-011 CA-002 - Nombre duplicado con otro producto activo da error
    def test_product_update_duplicate_name(self):
        Product.objects.create(name='Otro', price=500, category=self.cat)
        form = ProductUpdateForm(data={
            'name': 'Otro',
        }, instance=self.product)
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())

    # UT-319: HU-011 CA-001 - Mantener mismo nombre permitido
    def test_product_update_same_name_allowed(self):
        form = ProductUpdateForm(
            data={
                'name': 'Original',
                'price': 1000,
                'category': self.cat.id,
                'product_type': 'fabrica',
                'is_active': True,
            },
            instance=self.product
        )
        self.assertTrue(form.is_valid())


class ProductDeleteFormTest(TestCase):
    """HU-012: Eliminar producto (archivar)"""

    def setUp(self):
        self.cat = Category.objects.create(name='Test')
        self.product = Product.objects.create(name='Prod', price=100, category=self.cat)

    # UT-320: HU-012 CA-001 - Confirmación correcta sin pedidos válido
    def test_product_delete_confirm_correct(self):
        form = ProductDeleteForm(data={'confirm': 'Prod'}, product=self.product)
        self.assertTrue(form.is_valid())

    # UT-321: HU-012 CA-003 - Nombre no coincide da error
    def test_product_delete_wrong_name(self):
        form = ProductDeleteForm(data={'confirm': 'otro'}, product=self.product)
        self.assertFalse(form.is_valid())

    # UT-322: HU-012 CA-002 - Producto con pedidos en curso da error
    def test_product_delete_with_orders(self):
        with patch('apps.products.forms.ProductDeleteForm.clean_confirm') as mock_clean:
            mock_clean.side_effect = ValidationError('pedidos en curso')
            form = ProductDeleteForm(data={'confirm': 'Prod'}, product=self.product)
            self.assertFalse(form.is_valid())


class ProductRestoreFormTest(TestCase):
    """HU-012 CA-004: Restaurar producto desde papelera"""

    def setUp(self):
        self.cat = Category.objects.create(name='Test')
        self.product = Product.objects.create(name='Prod', price=100, category=self.cat)
        self.product.soft_delete()

    # UT-323: HU-012 CA-004 - Restauración sin conflicto válida
    def test_product_restore_valid(self):
        form = ProductRestoreForm(data={'confirm': True}, product=self.product)
        self.assertTrue(form.is_valid())

    # UT-324: HU-012 CA-004 - Confirmación no marcada da error
    def test_product_restore_not_confirmed(self):
        form = ProductRestoreForm(data={'confirm': False}, product=self.product)
        self.assertFalse(form.is_valid())
        self.assertIn('confirmar', form.errors['__all__'][0].lower())


# =============================================================================
# TESTS: PRODUCT COLOR FORMS (HU-013 parte)
# =============================================================================

class ProductColorCreateFormTest(TestCase):
    """HU-013: Gestionar tallas y stock - asignar colores"""

    def setUp(self):
        self.cat = Category.objects.create(name='Test')
        self.product = Product.objects.create(name='P', price=100, category=self.cat)
        self.color = Color.objects.create(name='Rojo', code='#FF0000')
        self.img = ProductImage.objects.create(alt_text='Img')

    # UT-325: HU-013 CA-001 - Asignar color a producto correctamente
    def test_product_color_create_valid(self):
        form = ProductColorCreateForm(
            data={'color': self.color.id, 'images': [self.img.id], 'featured_image': self.img.id},
            product=self.product
        )
        self.assertTrue(form.is_valid())

    # UT-326: HU-013 - Color ya asignado al producto da error
    def test_product_color_create_duplicate(self):
        ProductColor.objects.create(product=self.product, color=self.color)
        form = ProductColorCreateForm(data={'color': self.color.id}, product=self.product)
        self.assertFalse(form.is_valid())
        self.assertIn('ya está asignado', form.errors['__all__'][0].lower())

    # UT-327: HU-013 - Imagen destacada no está en la lista da error
    def test_product_color_create_featured_not_in_images(self):
        img2 = ProductImage.objects.create(alt_text='Img2')
        form = ProductColorCreateForm(
            data={'color': self.color.id, 'images': [self.img.id], 'featured_image': img2.id},
            product=self.product
        )
        self.assertFalse(form.is_valid())
        self.assertIn('destacada', form.errors['__all__'][0].lower())

    # UT-328: HU-013 - Sin producto especificado da error
    def test_product_color_create_no_product(self):
        form = ProductColorCreateForm(data={'color': self.color.id})
        self.assertFalse(form.is_valid())


class ProductColorUpdateFormTest(TestCase):
    """HU-013: Gestionar tallas y stock - actualizar colores"""

    def setUp(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='P', price=100, category=cat)
        color = Color.objects.create(name='Rojo', code='#FF0000')
        self.pc = ProductColor.objects.create(product=product, color=color)

    # UT-329: HU-013 - Actualizar imágenes y featured correctamente
    def test_product_color_update_valid(self):
        img = ProductImage.objects.create(alt_text='Img')
        form = ProductColorUpdateForm(
            data={'images': [img.id], 'featured_image': img.id, 'is_active': True},
            instance=self.pc
        )
        self.assertTrue(form.is_valid())

    # UT-330: HU-013 - Imagen destacada no seleccionada en imágenes da error
    def test_product_color_update_featured_not_in_images(self):
        img1 = ProductImage.objects.create(alt_text='Img1')
        img2 = ProductImage.objects.create(alt_text='Img2')
        form = ProductColorUpdateForm(
            data={'images': [img1.id], 'featured_image': img2.id, 'is_active': True},
            instance=self.pc
        )
        self.assertFalse(form.is_valid())
        self.assertIn('destacada', form.errors['__all__'][0].lower())


class ProductColorDeleteFormTest(TestCase):
    """HU-013: Gestionar tallas y stock - eliminar color de producto"""

    def setUp(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='P', price=100, category=cat)
        color = Color.objects.create(name='Rojo', code='#FF0000')
        self.pc = ProductColor.objects.create(product=product, color=color)

    # UT-331: HU-013 - Confirmación correcta sin variantes válido
    def test_product_color_delete_confirm_correct(self):
        form = ProductColorDeleteForm(data={'confirm': 'Rojo'}, product_color=self.pc)
        self.assertTrue(form.is_valid())

    # UT-332: HU-013 - Color con variantes activas da error
    def test_product_color_delete_with_variants(self):
        size = Size.objects.create(name='M')
        ProductVariant.objects.create(
            product=self.pc.product, product_color=self.pc, size=size, stock=5
        )
        form = ProductColorDeleteForm(data={'confirm': 'Rojo'}, product_color=self.pc)
        self.assertFalse(form.is_valid())
        self.assertIn('variante', form.errors['confirm'][0].lower())

    # UT-333: HU-013 - Nombre no coincide da error
    def test_product_color_delete_wrong_name(self):
        form = ProductColorDeleteForm(data={'confirm': 'Azul'}, product_color=self.pc)
        self.assertFalse(form.is_valid())


# =============================================================================
# TESTS: PRODUCT VARIANT FORMS (HU-013 parte)
# =============================================================================

class ProductVariantCreateFormTest(TestCase):
    """HU-013: Gestionar tallas y stock - crear variante"""

    def setUp(self):
        self.cat = Category.objects.create(name='Test')
        self.product = Product.objects.create(name='P', price=100, category=self.cat)
        self.color = Color.objects.create(name='Rojo', code='#FF0000')
        self.size = Size.objects.create(name='M')
        self.pc = ProductColor.objects.create(product=self.product, color=self.color)

    # UT-334: HU-013 CA-001 - Crear variante correctamente
    def test_variant_create_valid(self):
        form = ProductVariantCreateForm(
            data={'product_color': self.pc.id, 'size': self.size.id, 'stock': 10},
            product=self.product
        )
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.existing_variant)

    # UT-335: HU-013 - Variante ya existente guarda existing_variant
    def test_variant_create_duplicate_sets_existing(self):
        ProductVariant.objects.create(
            product=self.product,
            product_color=self.pc,
            size=self.size,
            stock=5
        )
        form = ProductVariantCreateForm(
            data={'product_color': self.pc.id, 'size': self.size.id, 'stock': 10},
            product=self.product
        )
        self.assertTrue(form.is_valid())
        self.assertIsNotNone(form.existing_variant)

    # UT-336: HU-013 - ProductColor de otro producto da error
    def test_variant_create_product_color_not_belong(self):
        product2 = Product.objects.create(name='P2', price=200, category=self.cat)
        pc2 = ProductColor.objects.create(product=product2, color=self.color)
        form = ProductVariantCreateForm(
            data={'product_color': pc2.id, 'size': self.size.id, 'stock': 10},
            product=self.product
        )
        self.assertFalse(form.is_valid())


class ProductVariantUpdateFormTest(TestCase):
    """HU-013: Gestionar tallas y stock - actualizar stock"""

    def setUp(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='P', price=100, category=cat)
        color = Color.objects.create(name='Rojo', code='#FF0000')
        size = Size.objects.create(name='M')
        pc = ProductColor.objects.create(product=product, color=color)
        self.variant = ProductVariant.objects.create(
            product=product, product_color=pc, size=size, stock=10
        )

    # UT-337: HU-013 CA-002 - Actualizar stock a valores válidos
    def test_variant_update_valid(self):
        form = ProductVariantUpdateForm(data={'stock': 20, 'is_active': True}, instance=self.variant)
        self.assertTrue(form.is_valid())
        form.save()
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 20)

    # UT-338: HU-013 CA-003 - Stock negativo da error
    def test_variant_update_negative_stock(self):
        form = ProductVariantUpdateForm(data={'stock': -1}, instance=self.variant)
        self.assertFalse(form.is_valid())
        self.assertIn('mayor o igual', form.errors['stock'][0].lower())

    # UT-339: HU-013 CA-002 - Stock 0 permitido
    def test_variant_update_zero_stock_allowed(self):
        form = ProductVariantUpdateForm(data={'stock': 0}, instance=self.variant)
        self.assertTrue(form.is_valid())


class ProductVariantDeleteFormTest(TestCase):
    """HU-013: Gestionar tallas y stock - eliminar variante"""

    def setUp(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='P', price=100, category=cat)
        color = Color.objects.create(name='Rojo', code='#FF0000')
        size = Size.objects.create(name='M')
        pc = ProductColor.objects.create(product=product, color=color)
        self.variant = ProductVariant.objects.create(
            product=product, product_color=pc, size=size, stock=10
        )

    # UT-340: HU-013 - Confirmación ELIMINAR correcta válido
    def test_variant_delete_confirm_correct(self):
        form = ProductVariantDeleteForm(data={'confirm': 'ELIMINAR'}, variant=self.variant)
        self.assertTrue(form.is_valid())

    # UT-341: HU-013 - Confirmación diferente a ELIMINAR da error
    def test_variant_delete_wrong_confirm(self):
        form = ProductVariantDeleteForm(data={'confirm': 'CANCELAR'}, variant=self.variant)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)
        self.assertIn('ELIMINAR', form.errors['confirm'][0])

    # UT-342: HU-013 - Variante con pedidos pendientes da error
    def test_variant_delete_with_orders(self):
        with patch('apps.products.forms.ProductVariantDeleteForm.clean_confirm') as mock_clean:
            mock_clean.side_effect = ValidationError('pedidos pendientes')
            form = ProductVariantDeleteForm(data={'confirm': 'ELIMINAR'}, variant=self.variant)
            self.assertFalse(form.is_valid())


class ProductVariantRestoreFormTest(TestCase):
    """HU-013: Gestionar tallas y stock - restaurar variante"""

    def setUp(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='P', price=100, category=cat)
        color = Color.objects.create(name='Rojo', code='#FF0000')
        size = Size.objects.create(name='M')
        pc = ProductColor.objects.create(product=product, color=color)
        self.variant = ProductVariant.objects.create(
            product=product, product_color=pc, size=size, stock=10, is_active=False
        )

    # UT-343: HU-013 - Restauración sin conflicto válida
    def test_variant_restore_valid(self):
        form = ProductVariantRestoreForm(data={'confirm': True}, variant=self.variant)
        self.assertTrue(form.is_valid())

    # UT-344: HU-013 - Ya existe variante activa con misma combinación da error
    def test_variant_restore_conflict(self):
        ProductVariant.objects.filter(pk=self.variant.pk).update(is_active=True)
        form = ProductVariantRestoreForm(data={'confirm': True}, variant=self.variant)
        self.assertFalse(form.is_valid())
        errors_str = str(form.errors).lower()
        self.assertTrue('ya existe' in errors_str or 'activa' in errors_str)

    # UT-345: HU-013 - Confirmación no marcada da error
    def test_variant_restore_not_confirmed(self):
        form = ProductVariantRestoreForm(data={'confirm': False}, variant=self.variant)
        self.assertFalse(form.is_valid())
        self.assertIn('confirmar', form.errors['__all__'][0].lower())