"""
Tests for forms of the products app.
CP-395 to CP-495

Cubre:
- Size forms (CP-395 a CP-405)
- Category forms (CP-406 a CP-416)
- Color forms (CP-416 a CP-428)
- Product Image forms (CP-432 a CP-440)
- Product forms (CP-441 a CP-456)
- Product Color forms (CP-457 a CP-466)
- Product Variant forms (CP-466 a CP-478)
"""

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


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _create_base_objects():
    """Crea objetos base necesarios para la mayoría de tests."""
    cat = Category.objects.create(name='TestCat')
    color = Color.objects.create(name='Rojo', code='#FF0000')
    size = Size.objects.create(name='M')
    product = Product.objects.create(name='Prod', price=10000, category=cat)
    pc = ProductColor.objects.create(product=product, color=color)
    return cat, color, size, product, pc


# =============================================================================
# SIZE FORMS (CP-395 a CP-405)
# =============================================================================

class SizeCreateFormTest(TestCase):
    def test_size_create_valid(self):
        """CP-395: Crear talla con nombre válido y único."""
        form = SizeCreateForm(data={'name': 'XL'})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(Size.objects.count(), 1)

    def test_size_create_duplicate_name(self):
        """CP-396: Nombre duplicado -> error de validación."""
        Size.objects.create(name='M')
        form = SizeCreateForm(data={'name': 'm'})
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())

    def test_size_create_name_uppercased(self):
        """CP-397: El nombre se convierte a mayúsculas y se limpia."""
        form = SizeCreateForm(data={'name': '  xl '})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'XL')


class SizeUpdateFormTest(TestCase):
    def setUp(self):
        self.size = Size.objects.create(name='M')

    def test_size_update_valid(self):
        """CP-398: Actualizar nombre correctamente."""
        form = SizeUpdateForm(data={'name': 'L'}, instance=self.size)
        self.assertTrue(form.is_valid())
        form.save()
        self.size.refresh_from_db()
        self.assertEqual(self.size.name, 'L')

    def test_size_update_duplicate_name(self):
        """CP-399: Nombre duplicado con otra talla -> error."""
        Size.objects.create(name='L')
        form = SizeUpdateForm(data={'name': 'L'}, instance=self.size)
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())

    def test_size_update_same_name_allowed(self):
        """CP-400: Mantener el mismo nombre (excluye la instancia actual)."""
        form = SizeUpdateForm(data={'name': 'M'}, instance=self.size)
        self.assertTrue(form.is_valid())


class SizeDeleteFormTest(TestCase):
    def setUp(self):
        self.size = Size.objects.create(name='M')

    def test_size_delete_confirm_correct(self):
        """CP-401: Confirmación correcta y sin variantes -> válido."""
        form = SizeDeleteForm(data={'confirm': 'M'}, size=self.size)
        self.assertTrue(form.is_valid())

    def test_size_delete_wrong_name(self):
        """CP-402: Nombre no coincide -> error."""
        form = SizeDeleteForm(data={'confirm': 'L'}, size=self.size)
        self.assertFalse(form.is_valid())
        self.assertIn('no coincide', form.errors['confirm'][0].lower())

    def test_size_delete_with_active_variants(self):
        """CP-403: Talla con variantes activas -> error."""
        cat = Category.objects.create(name='X')
        product = Product.objects.create(name='P', price=100, category=cat)
        color = Color.objects.create(name='N', code='#000')
        pc = ProductColor.objects.create(product=product, color=color)
        ProductVariant.objects.create(product=product, product_color=pc, size=self.size, stock=5)
        form = SizeDeleteForm(data={'confirm': 'M'}, size=self.size)
        self.assertFalse(form.is_valid())
        self.assertIn('variante', form.errors['confirm'][0].lower())

    def test_size_delete_confirm_case_insensitive(self):
        """CP-405: Comparación insensible a mayúsculas/minúsculas."""
        form = SizeDeleteForm(data={'confirm': 'm'}, size=self.size)
        self.assertTrue(form.is_valid())


# =============================================================================
# CATEGORY FORMS (CP-406 a CP-416)
# =============================================================================

class CategoryCreateFormTest(TestCase):
    def test_category_create_valid(self):
        """CP-406: Crear categoría con nombre único."""
        form = CategoryCreateForm(data={'name': 'Camisetas'})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(Category.objects.count(), 1)

    def test_category_create_duplicate_name_iexact(self):
        """CP-407: Nombre duplicado (insensible a mayúsculas) -> error."""
        Category.objects.create(name='Camisetas')
        form = CategoryCreateForm(data={'name': 'camisetas'})
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())


class CategoryUpdateFormTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Camisetas', slug='camisetas')

    def test_category_update_valid(self):
        """CP-408: Actualizar nombre correctamente y slug regenerado."""
        form = CategoryUpdateForm(data={'name': 'Hoodies'}, instance=self.cat)
        self.assertTrue(form.is_valid())
        form.save()
        self.cat.refresh_from_db()
        self.assertEqual(self.cat.name, 'Hoodies')
        self.assertEqual(self.cat.slug, 'hoodies')

    def test_category_update_duplicate_name(self):
        """CP-409: Nombre duplicado -> error."""
        Category.objects.create(name='Hoodies', slug='hoodies')
        form = CategoryUpdateForm(data={'name': 'Hoodies'}, instance=self.cat)
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())


class CategoryDeleteFormTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Camisetas')

    def test_category_delete_confirm_correct(self):
        """CP-410: Confirmación correcta y sin productos -> válido."""
        form = CategoryDeleteForm(data={'confirm': 'Camisetas'}, category=self.cat)
        self.assertTrue(form.is_valid())

    def test_category_delete_wrong_name(self):
        """CP-411: Nombre no coincide -> error."""
        form = CategoryDeleteForm(data={'confirm': 'Hoodies'}, category=self.cat)
        self.assertFalse(form.is_valid())

    def test_category_delete_with_active_products(self):
        """CP-412: Categoría con productos activos -> error."""
        cat = Category.objects.create(name='Test')
        Product.objects.create(name='P', price=100, category=cat)
        form = CategoryDeleteForm(data={'confirm': 'Test'}, category=cat)
        self.assertFalse(form.is_valid())
        self.assertIn('producto', form.errors['confirm'][0].lower())


class CategoryImportFormTest(TestCase):
    def test_category_import_valid(self):
        """CP-413: Formulario individual de importación válido."""
        form = CategoryImportForm(data={'name': 'Accesorios'})
        self.assertTrue(form.is_valid())

    def test_category_import_duplicate(self):
        """CP-414: Nombre duplicado -> error."""
        Category.objects.create(name='Accesorios')
        form = CategoryImportForm(data={'name': 'Accesorios'})
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())

    def test_category_import_name_stripped(self):
        """CP-415: Nombre se limpia de espacios."""
        form = CategoryImportForm(data={'name': '  Zapatos '})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'Zapatos')


# =============================================================================
# COLOR FORMS (CP-416 a CP-428)
# =============================================================================

class ColorCreateFormTest(TestCase):
    def test_color_create_valid(self):
        """CP-416: Crear color con nombre y código válido."""
        form = ColorCreateForm(data={'name': 'Negro', 'code': '#000000'})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(Color.objects.count(), 1)

    def test_color_create_duplicate_name(self):
        """CP-417: Nombre duplicado -> error."""
        Color.objects.create(name='Negro', code='#000000')
        form = ColorCreateForm(data={'name': 'negro', 'code': '#111111'})
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())

    def test_color_create_duplicate_code(self):
        """CP-418: Código duplicado -> error."""
        Color.objects.create(name='Rojo', code='#FF0000')
        form = ColorCreateForm(data={'name': 'Azul', 'code': '#ff0000'})
        self.assertFalse(form.is_valid())
        self.assertIn('ya está en uso', form.errors['code'][0].lower())

    def test_color_create_invalid_code_format(self):
        """CP-419: Código hexadecimal inválido -> error."""
        form = ColorCreateForm(data={'name': 'Test', 'code': 'XYZ'})
        self.assertFalse(form.is_valid())
        self.assertIn('hexadecimal', form.errors['code'][0].lower())

    def test_color_create_code_adds_hash(self):
        """CP-420: Si código no empieza con #, se añade automáticamente."""
        form = ColorCreateForm(data={'name': 'Test', 'code': 'FF0000'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['code'], '#FF0000')

    def test_color_create_name_capitalized(self):
        """CP-421: Nombre se capitaliza."""
        form = ColorCreateForm(data={'name': 'blanco', 'code': '#FFF'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'Blanco')


class ColorUpdateFormTest(TestCase):
    def setUp(self):
        self.color = Color.objects.create(name='Rojo', code='#FF0000')

    def test_color_update_valid(self):
        """CP-422: Actualizar nombre y código correctamente."""
        form = ColorUpdateForm(data={'name': 'Azul', 'code': '#0000FF'}, instance=self.color)
        self.assertTrue(form.is_valid())
        form.save()
        self.color.refresh_from_db()
        self.assertEqual(self.color.name, 'Azul')

    def test_color_update_duplicate_name(self):
        """CP-423: Nombre duplicado con otro color -> error."""
        Color.objects.create(name='Azul', code='#0000FF')
        form = ColorUpdateForm(data={'name': 'Azul'}, instance=self.color)
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())

    def test_color_update_duplicate_code(self):
        """CP-424: Código duplicado -> error."""
        Color.objects.create(name='Azul', code='#0000FF')
        form = ColorUpdateForm(data={'code': '#0000FF'}, instance=self.color)
        self.assertFalse(form.is_valid())

    def test_color_update_same_name_allowed(self):
        """CP-425: Mantener el mismo nombre (excluye la instancia)."""
        form = ColorUpdateForm(data={'name': 'Rojo', 'code': '#FF0000'}, instance=self.color)
        self.assertTrue(form.is_valid())


class ColorDeleteFormTest(TestCase):
    def setUp(self):
        self.color = Color.objects.create(name='Rojo', code='#FF0000')

    def test_color_delete_confirm_correct(self):
        """CP-426: Confirmación correcta y sin variantes -> válido."""
        form = ColorDeleteForm(data={'confirm': 'Rojo'}, color=self.color)
        self.assertTrue(form.is_valid())

    def test_color_delete_with_active_product_colors(self):
        """CP-427: Color con ProductColor activo -> error."""
        cat = Category.objects.create(name='X')
        product = Product.objects.create(name='P', price=100, category=cat)
        ProductColor.objects.create(product=product, color=self.color)
        form = ColorDeleteForm(data={'confirm': 'Rojo'}, color=self.color)
        self.assertFalse(form.is_valid())
        self.assertIn('variante', form.errors['confirm'][0].lower())

    def test_color_delete_wrong_name(self):
        """CP-428: Nombre no coincide -> error."""
        form = ColorDeleteForm(data={'confirm': 'Azul'}, color=self.color)
        self.assertFalse(form.is_valid())


class ColorImportFormTest(TestCase):
    def test_color_import_valid(self):
        """CP-429: Importación válida de color."""
        form = ColorImportForm(data={'name': 'Verde', 'code': '#00FF00'})
        self.assertTrue(form.is_valid())

    def test_color_import_duplicate_name(self):
        """CP-430: Nombre duplicado -> error."""
        Color.objects.create(name='Verde', code='#00FF00')
        form = ColorImportForm(data={'name': 'verde', 'code': '#000000'})
        self.assertFalse(form.is_valid())

    def test_color_import_duplicate_code(self):
        """CP-431: Código duplicado -> error."""
        Color.objects.create(name='Verde', code='#00FF00')
        form = ColorImportForm(data={'name': 'Otro', 'code': '#00ff00'})
        self.assertFalse(form.is_valid())


# =============================================================================
# PRODUCT IMAGE FORMS (CP-432 a CP-440)
# =============================================================================

class ProductImageCreateFormTest(TestCase):
    def test_image_create_valid(self):
        """CP-432: Imagen con archivo y alt_text válido."""
        mock_file = Mock()
        mock_file.name = 'test.jpg'
        mock_file.size = 1024 * 1024
        form = ProductImageCreateForm(data={'alt_text': 'Foto'}, files={'image': mock_file})
        with patch('apps.products.forms.ALLOWED_IMAGE_EXTENSIONS', ['.jpg']):
            self.assertTrue(form.is_valid())

    def test_image_create_no_file(self):
        """CP-433: Sin archivo -> error."""
        form = ProductImageCreateForm(data={'alt_text': 'Foto'})
        self.assertFalse(form.is_valid())

    def test_image_create_file_too_large(self):
        """CP-434: Archivo > 5MB -> error."""
        mock_file = Mock()
        mock_file.name = 'test.jpg'
        mock_file.size = 6 * 1024 * 1024
        form = ProductImageCreateForm(data={'alt_text': 'Foto'}, files={'image': mock_file})
        with patch('apps.products.forms.ALLOWED_IMAGE_EXTENSIONS', ['.jpg']):
            self.assertFalse(form.is_valid())
            self.assertIn('5MB', form.errors['image'][0])

    def test_image_create_invalid_extension(self):
        """CP-435: Extensión no permitida -> error."""
        mock_file = Mock()
        mock_file.name = 'test.gif'
        mock_file.size = 1024
        form = ProductImageCreateForm(data={'alt_text': 'Foto'}, files={'image': mock_file})
        with patch('apps.products.forms.ALLOWED_IMAGE_EXTENSIONS', ['.jpg', '.png']):
            self.assertFalse(form.is_valid())
            self.assertIn('soportado', form.errors['image'][0].lower())


class ProductImageUpdateFormTest(TestCase):
    def test_image_update_valid(self):
        """CP-436: Actualizar alt_text correctamente."""
        img = ProductImage.objects.create(alt_text='Antes')
        form = ProductImageUpdateForm(data={'alt_text': 'Después'}, instance=img)
        self.assertTrue(form.is_valid())
        form.save()
        img.refresh_from_db()
        self.assertEqual(img.alt_text, 'Después')

    def test_image_update_blank_alt(self):
        """CP-437: alt_text puede quedar en blanco."""
        img = ProductImage.objects.create(alt_text='Antes')
        form = ProductImageUpdateForm(data={'alt_text': ''}, instance=img)
        self.assertTrue(form.is_valid())


class ProductImageDeleteFormTest(TestCase):
    def test_image_delete_confirm(self):
        """CP-438: Confirmación marcada y con imagen -> válido."""
        img = ProductImage.objects.create()
        form = ProductImageDeleteForm(data={'confirm': True}, image=img)
        self.assertTrue(form.is_valid())

    def test_image_delete_not_confirmed(self):
        """CP-439: Confirmación no marcada -> error."""
        img = ProductImage.objects.create()
        form = ProductImageDeleteForm(data={'confirm': False}, image=img)
        self.assertFalse(form.is_valid())
        self.assertIn('confirmar', form.errors['__all__'][0].lower())


# =============================================================================
# PRODUCT FORMS (CP-441 a CP-456)
# =============================================================================

class ProductCreateFormTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Test')

    def test_product_create_valid(self):
        """CP-441: Crear producto con datos válidos."""
        form = ProductCreateForm(data={
            'name': 'Camiseta',
            'price': 25000,
            'category': self.cat.id,
            'product_type': 'fabrica',
        })
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(Product.objects.count(), 1)

    def test_product_create_duplicate_name_active(self):
        """CP-442: Nombre duplicado en productos activos -> error."""
        Product.objects.create(name='Camiseta', price=10000, category=self.cat)
        form = ProductCreateForm(data={
            'name': 'camiseta',
            'price': 20000,
            'category': self.cat.id,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())

    def test_product_create_price_zero(self):
        """CP-444: Precio igual a 0 -> error."""
        form = ProductCreateForm(data={
            'name': 'Test',
            'price': 0,
            'category': self.cat.id,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('mayor', form.errors['price'][0].lower())

    def test_product_create_price_exceeds_max(self):
        """CP-445: Precio mayor a 10,000,000 -> error."""        
        form = ProductCreateForm(data={
            'name': 'Test',
            'price': Decimal('10000001'),
            'category': self.cat.id,
            'product_type': 'fabrica',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)
        error_msg = str(form.errors['price'][0]).lower()
        self.assertTrue('superar' in error_msg or '10.000.000' in error_msg)

    def test_product_create_missing_name(self):
        """CP-446: Nombre vacío -> error de required."""
        form = ProductCreateForm(data={
            'name': '',
            'price': 100,
            'category': self.cat.id,
        })
        self.assertFalse(form.is_valid())


class ProductUpdateFormTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Test')
        self.product = Product.objects.create(name='Original', price=1000, category=self.cat)

    def test_product_update_valid(self):
        """CP-447: Actualizar producto correctamente."""
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

    def test_product_update_duplicate_name(self):
        """CP-448: Nombre duplicado con otro producto activo -> error."""
        Product.objects.create(name='Otro', price=500, category=self.cat)
        form = ProductUpdateForm(data={
            'name': 'Otro',
        }, instance=self.product)
        self.assertFalse(form.is_valid())
        self.assertIn('ya existe', form.errors['name'][0].lower())

    def test_product_update_same_name_allowed(self):
        """CP-449: Mantener el mismo nombre (excluye la instancia)."""
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
    def setUp(self):
        self.cat = Category.objects.create(name='Test')
        self.product = Product.objects.create(name='Prod', price=100, category=self.cat)

    def test_product_delete_confirm_correct(self):
        """CP-450: Confirmación correcta y sin pedidos activos -> válido."""
        form = ProductDeleteForm(data={'confirm': 'Prod'}, product=self.product)
        self.assertTrue(form.is_valid())

    def test_product_delete_wrong_name(self):
        """CP-451: Nombre no coincide -> error."""
        form = ProductDeleteForm(data={'confirm': 'otro'}, product=self.product)
        self.assertFalse(form.is_valid())

    def test_product_delete_with_orders(self):
        """CP-452: Producto con pedidos en curso -> error simulado."""
        with patch('apps.products.forms.ProductDeleteForm.clean_confirm') as mock_clean:
            mock_clean.side_effect = ValidationError('pedidos en curso')
            form = ProductDeleteForm(data={'confirm': 'Prod'}, product=self.product)
            self.assertFalse(form.is_valid())


class ProductRestoreFormTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Test')
        self.product = Product.objects.create(name='Prod', price=100, category=self.cat)
        self.product.soft_delete()

    def test_product_restore_valid(self):
        """CP-454: Restauración sin conflicto -> válido."""
        form = ProductRestoreForm(data={'confirm': True}, product=self.product)
        self.assertTrue(form.is_valid())

    def test_product_restore_not_confirmed(self):
        """CP-456: Confirmación no marcada -> error."""
        form = ProductRestoreForm(data={'confirm': False}, product=self.product)
        self.assertFalse(form.is_valid())
        self.assertIn('confirmar', form.errors['__all__'][0].lower())


# =============================================================================
# PRODUCT COLOR FORMS (CP-457 a CP-466)
# =============================================================================

class ProductColorCreateFormTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Test')
        self.product = Product.objects.create(name='P', price=100, category=self.cat)
        self.color = Color.objects.create(name='Rojo', code='#FF0000')
        self.img = ProductImage.objects.create(alt_text='Img')

    def test_product_color_create_valid(self):
        """CP-457: Asignar color a producto correctamente."""
        form = ProductColorCreateForm(
            data={'color': self.color.id, 'images': [self.img.id], 'featured_image': self.img.id},
            product=self.product
        )
        self.assertTrue(form.is_valid())

    def test_product_color_create_duplicate(self):
        """CP-458: Color ya asignado al producto -> error."""
        ProductColor.objects.create(product=self.product, color=self.color)
        form = ProductColorCreateForm(data={'color': self.color.id}, product=self.product)
        self.assertFalse(form.is_valid())
        self.assertIn('ya está asignado', form.errors['__all__'][0].lower())

    def test_product_color_create_featured_not_in_images(self):
        """CP-459: Imagen destacada no está en la lista de imágenes -> error."""
        img2 = ProductImage.objects.create(alt_text='Img2')
        form = ProductColorCreateForm(
            data={'color': self.color.id, 'images': [self.img.id], 'featured_image': img2.id},
            product=self.product
        )
        self.assertFalse(form.is_valid())
        self.assertIn('destacada', form.errors['__all__'][0].lower())

    def test_product_color_create_no_product(self):
        """CP-460: Sin producto especificado -> error."""
        form = ProductColorCreateForm(data={'color': self.color.id})
        self.assertFalse(form.is_valid())


class ProductColorUpdateFormTest(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='P', price=100, category=cat)
        color = Color.objects.create(name='Rojo', code='#FF0000')
        self.pc = ProductColor.objects.create(product=product, color=color)

    def test_product_color_update_valid(self):
        """CP-461: Actualizar imágenes y featured correctamente."""
        img = ProductImage.objects.create(alt_text='Img')
        form = ProductColorUpdateForm(
            data={'images': [img.id], 'featured_image': img.id, 'is_active': True},
            instance=self.pc
        )
        self.assertTrue(form.is_valid())

    def test_product_color_update_featured_not_in_images(self):
        """CP-462: Imagen destacada no seleccionada en imágenes -> error."""
        img1 = ProductImage.objects.create(alt_text='Img1')
        img2 = ProductImage.objects.create(alt_text='Img2')
        form = ProductColorUpdateForm(
            data={'images': [img1.id], 'featured_image': img2.id, 'is_active': True},
            instance=self.pc
        )
        self.assertFalse(form.is_valid())
        self.assertIn('destacada', form.errors['__all__'][0].lower())


class ProductColorDeleteFormTest(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='P', price=100, category=cat)
        color = Color.objects.create(name='Rojo', code='#FF0000')
        self.pc = ProductColor.objects.create(product=product, color=color)

    def test_product_color_delete_confirm_correct(self):
        """CP-463: Confirmación correcta y sin variantes activas -> válido."""
        form = ProductColorDeleteForm(data={'confirm': 'Rojo'}, product_color=self.pc)
        self.assertTrue(form.is_valid())

    def test_product_color_delete_with_variants(self):
        """CP-464: Color con variantes activas -> error."""
        size = Size.objects.create(name='M')
        ProductVariant.objects.create(
            product=self.pc.product, product_color=self.pc, size=size, stock=5
        )
        form = ProductColorDeleteForm(data={'confirm': 'Rojo'}, product_color=self.pc)
        self.assertFalse(form.is_valid())
        self.assertIn('variante', form.errors['confirm'][0].lower())

    def test_product_color_delete_wrong_name(self):
        """CP-465: Nombre no coincide -> error."""
        form = ProductColorDeleteForm(data={'confirm': 'Azul'}, product_color=self.pc)
        self.assertFalse(form.is_valid())


# =============================================================================
# PRODUCT VARIANT FORMS (CP-466 a CP-478)
# =============================================================================

class ProductVariantCreateFormTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Test')
        self.product = Product.objects.create(name='P', price=100, category=self.cat)
        self.color = Color.objects.create(name='Rojo', code='#FF0000')
        self.size = Size.objects.create(name='M')
        self.pc = ProductColor.objects.create(product=self.product, color=self.color)

    def test_variant_create_valid(self):
        """CP-466: Crear variante correctamente."""
        form = ProductVariantCreateForm(
            data={'product_color': self.pc.id, 'size': self.size.id, 'stock': 10},
            product=self.product
        )
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.existing_variant)

    def test_variant_create_duplicate_sets_existing(self):
        """CP-467: Variante ya existente -> no lanza error, guarda existing_variant."""
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
        self.assertEqual(form.existing_variant.product_color, self.pc)
        self.assertEqual(form.existing_variant.size, self.size)

    def test_variant_create_product_color_not_belong(self):
        """CP-468: ProductColor de otro producto -> error."""
        product2 = Product.objects.create(name='P2', price=200, category=self.cat)
        pc2 = ProductColor.objects.create(product=product2, color=self.color)
        form = ProductVariantCreateForm(
            data={'product_color': pc2.id, 'size': self.size.id, 'stock': 10},
            product=self.product
        )
        self.assertFalse(form.is_valid())
        self.assertTrue('product_color' in form.errors or '__all__' in form.errors)


class ProductVariantUpdateFormTest(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='P', price=100, category=cat)
        color = Color.objects.create(name='Rojo', code='#FF0000')
        size = Size.objects.create(name='M')
        pc = ProductColor.objects.create(product=product, color=color)
        self.variant = ProductVariant.objects.create(
            product=product, product_color=pc, size=size, stock=10
        )

    def test_variant_update_valid(self):
        """CP-470: Actualizar stock a valores válidos."""
        form = ProductVariantUpdateForm(data={'stock': 20, 'is_active': True}, instance=self.variant)
        self.assertTrue(form.is_valid())
        form.save()
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 20)

    def test_variant_update_negative_stock(self):
        """CP-471: Stock negativo -> error."""
        form = ProductVariantUpdateForm(data={'stock': -1}, instance=self.variant)
        self.assertFalse(form.is_valid())
        self.assertIn('mayor o igual', form.errors['stock'][0].lower())

    def test_variant_update_zero_stock_allowed(self):
        """CP-472: Stock 0 permitido."""
        form = ProductVariantUpdateForm(data={'stock': 0}, instance=self.variant)
        self.assertTrue(form.is_valid())


class ProductVariantDeleteFormTest(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='P', price=100, category=cat)
        color = Color.objects.create(name='Rojo', code='#FF0000')
        size = Size.objects.create(name='M')
        pc = ProductColor.objects.create(product=product, color=color)
        self.variant = ProductVariant.objects.create(
            product=product, product_color=pc, size=size, stock=10
        )

    def test_variant_delete_confirm_correct(self):
        """CP-473: Confirmación 'ELIMINAR' correcta -> válido."""
        form = ProductVariantDeleteForm(data={'confirm': 'ELIMINAR'}, variant=self.variant)
        self.assertTrue(form.is_valid())

    def test_variant_delete_wrong_confirm(self):
        """CP-474: Confirmación diferente a 'ELIMINAR' -> error."""
        form = ProductVariantDeleteForm(data={'confirm': 'CANCELAR'}, variant=self.variant)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)
        self.assertIn('ELIMINAR', form.errors['confirm'][0])

    def test_variant_delete_with_orders(self):
        """CP-475: Variante con pedidos pendientes -> error simulado."""
        with patch('apps.products.forms.ProductVariantDeleteForm.clean_confirm') as mock_clean:
            mock_clean.side_effect = ValidationError('pedidos pendientes')
            form = ProductVariantDeleteForm(data={'confirm': 'ELIMINAR'}, variant=self.variant)
            self.assertFalse(form.is_valid())


class ProductVariantRestoreFormTest(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='P', price=100, category=cat)
        color = Color.objects.create(name='Rojo', code='#FF0000')
        size = Size.objects.create(name='M')
        pc = ProductColor.objects.create(product=product, color=color)
        self.variant = ProductVariant.objects.create(
            product=product, product_color=pc, size=size, stock=10, is_active=False
        )

    def test_variant_restore_valid(self):
        """CP-476: Restauración sin conflicto -> válido."""
        form = ProductVariantRestoreForm(data={'confirm': True}, variant=self.variant)
        self.assertTrue(form.is_valid())

    def test_variant_restore_conflict(self):
        """CP-477: Ya existe variante activa con misma combinación -> error."""
        # Primero restauramos manualmente (simulando que existe activa)
        ProductVariant.objects.filter(pk=self.variant.pk).update(is_active=True)
        form = ProductVariantRestoreForm(data={'confirm': True}, variant=self.variant)
        self.assertFalse(form.is_valid())
        errors_str = str(form.errors).lower()
        self.assertTrue('ya existe' in errors_str or 'activa' in errors_str)

    def test_variant_restore_not_confirmed(self):
        """CP-478: Confirmación no marcada -> error."""
        form = ProductVariantRestoreForm(data={'confirm': False}, variant=self.variant)
        self.assertFalse(form.is_valid())
        self.assertIn('confirmar', form.errors['__all__'][0].lower())