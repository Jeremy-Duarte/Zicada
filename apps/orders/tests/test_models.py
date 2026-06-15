"""
Tests unitarios para modelos de apps.orders.models

Cubre:
- HU-024: Confirmar pedido
- HU-025: Recibir confirmación de pedido
- HU-026: Consultar estado del pedido
- HU-027: Listar pedidos (admin)
- HU-028: Ver detalle de pedido (admin)
- HU-029: Cambiar estado de pedido
- HU-030: Cancelar pedido
- HU-031: Crear pedido manual (admin)
- HU-032: Asignar repartidor
- HU-033: Consultar pedidos del día (entregador)
- HU-034: Marcar pedido como pagado/entregado
- HU-035: Registrar incidencia

Casos de prueba: CP-xxx a CP-xxx
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.orders.models import Order, OrderItem
from apps.products.models import Product, Category, Size, Color, ProductColor, ProductVariant
from apps.users.models import User


# =============================================================================
# HELPERS
# =============================================================================

def _create_user(**kwargs):
    """Crea un usuario de prueba."""
    defaults = {'username': 'testuser', 'password': 'pass1234'}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


def _create_delivery_user(**kwargs):
    """Crea un usuario con rol de entregador."""
    defaults = {'username': 'delivery', 'password': 'pass1234', 'is_delivery': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


def _create_admin_user(**kwargs):
    """Crea un usuario administrador."""
    defaults = {'username': 'admin', 'password': 'pass1234', 'is_staff': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


def _create_product_variant(stock=10):
    """Crea una variante de producto para pruebas."""
    category = Category.objects.create(name='Test Category')
    size = Size.objects.create(name='M')
    color = Color.objects.create(name='Rojo', code='#FF0000')
    product = Product.objects.create(
        name='Test Product',
        price=Decimal('5.00'),  # Precio pequeño
        category=category
    )
    product_color = ProductColor.objects.create(
        product=product,
        color=color
    )
    return ProductVariant.objects.create(
        product=product,
        product_color=product_color,
        size=size,
        stock=stock
    )


def _create_order(**kwargs):
    """Crea un pedido de prueba con valores pequeños."""
    defaults = {
        'customer_name': 'Juan Perez',
        'customer_phone': '3001234567',
        'customer_email': 'juan@test.com',
        'shipping_address': 'Calle 123, Bogotá',
        'subtotal': Decimal('10.00'),
        'shipping_cost': Decimal('2.00'),
        'total_amount': Decimal('12.00'),
        'status': 'pendiente',
        'is_paid': False,
    }
    defaults.update(kwargs)
    return Order.objects.create(**defaults)


def _create_order_item(order, variant, quantity=2):
    """Crea un item de pedido con precio pequeño."""
    unit_price = Decimal('5.00')  # Precio pequeño
    return OrderItem.objects.create(
        order=order,
        variant=variant,
        product_name_snapshot=variant.product.name,
        size_snapshot=variant.size.name,
        quantity=quantity,
        unit_price=unit_price,
        stock_snapshot=variant.stock,
        subtotal=unit_price * quantity
    )


# =============================================================================
# TESTS: Order Model
# =============================================================================

class OrderModelTest(TestCase):
    """
    HU-024: Confirmar pedido
    HU-026: Consultar estado del pedido
    HU-027: Listar pedidos (admin)
    HU-028: Ver detalle de pedido (admin)
    HU-029: Cambiar estado de pedido
    HU-030: Cancelar pedido
    HU-031: Crear pedido manual (admin)
    HU-032: Asignar repartidor
    HU-034: Marcar pedido como pagado/entregado
    """

    def setUp(self):
        self.variant = _create_product_variant(stock=10)
        self.order = _create_order()

    def test_create_order_with_all_fields(self):
        """
        CP-xxx
        HU-031 | ESCENARIO 1 | H | Creación de pedido manual con todos los campos
        """
        # Usar valores pequeños del helper
        self.assertEqual(self.order.customer_name, 'Juan Perez')
        self.assertEqual(self.order.customer_phone, '3001234567')
        self.assertEqual(self.order.customer_email, 'juan@test.com')
        self.assertEqual(self.order.shipping_address, 'Calle 123, Bogotá')
        self.assertEqual(self.order.subtotal, Decimal('10.00'))
        self.assertEqual(self.order.shipping_cost, Decimal('2.00'))
        self.assertEqual(self.order.total_amount, Decimal('12.00'))
        self.assertEqual(self.order.status, 'pendiente')
        self.assertFalse(self.order.is_paid)

    def test_order_str_returns_order_number_and_customer(self):
        """
        CP-xxx
        HU-027 | H | __str__ retorna número de pedido y nombre del cliente
        """
        expected = f"{self.order.order_number} - Juan Perez"
        self.assertEqual(str(self.order), expected)

    def test_order_number_auto_generation(self):
        """
        CP-xxx
        HU-024 | ESCENARIO 1 | H | Generación automática de número de pedido
        """
        self.assertIsNotNone(self.order.order_number)
        self.assertTrue(self.order.order_number.startswith('ZCD-'))
        self.assertEqual(len(self.order.order_number), 8)

    def test_order_number_sequential(self):
        """
        CP-xxx
        HU-024 | ESCENARIO 1 | H | Números de pedido secuenciales
        """
        order2 = _create_order(customer_name='Maria Gomez')
        self.assertNotEqual(self.order.order_number, order2.order_number)
        num1 = int(self.order.order_number.split('-')[1])
        num2 = int(order2.order_number.split('-')[1])
        self.assertEqual(num2, num1 + 1)

    def test_tracking_token_auto_generation(self):
        """
        CP-xxx
        HU-026 | ESCENARIO 1 | H | Token de seguimiento único generado automáticamente
        """
        self.assertIsNotNone(self.order.tracking_token)
        order2 = _create_order(customer_name='Maria Gomez')
        self.assertNotEqual(self.order.tracking_token, order2.tracking_token)

    def test_total_amount_auto_calculation_on_save(self):
        """
        CP-xxx
        HU-024 | ESCENARIO 1 | H | Cálculo automático del total (subtotal + envío)
        """
        order = Order(
            customer_name='Test',
            customer_phone='123',
            shipping_address='Test',
            subtotal=Decimal('10.00'),
            shipping_cost=Decimal('2.00')
        )
        order.save()
        self.assertEqual(order.total_amount, Decimal('12.00'))

    def test_total_amount_updates_when_subtotal_changes(self):
        """
        CP-xxx
        HU-031 | ESCENARIO 1 | H | Actualización del total al modificar subtotal
        """
        self.order.subtotal = Decimal('15.00')
        self.order.save()
        self.assertEqual(self.order.total_amount, Decimal('17.00'))  # 15 + 2

    def test_clean_validation_subtotal_negative(self):
        """
        CP-xxx
        HU-024 | ESCENARIO 1 | H | Validación: subtotal no puede ser negativo
        HU-031 | ESCENARIO 1 | H | Validaciones para pedido manual
        """
        order = Order(
            customer_name='Test',
            customer_phone='123',
            shipping_address='Test',
            subtotal=Decimal('-10.00'),
            shipping_cost=Decimal('5.00')
        )
        with self.assertRaises(ValidationError) as cm:
            order.full_clean()
        self.assertIn('subtotal', str(cm.exception))

    def test_clean_validation_shipping_cost_negative(self):
        """
        CP-xxx
        HU-024 | ESCENARIO 1 | H | Validación: costo de envío no puede ser negativo
        """
        order = Order(
            customer_name='Test',
            customer_phone='123',
            shipping_address='Test',
            subtotal=Decimal('10.00'),
            shipping_cost=Decimal('-5.00')
        )
        with self.assertRaises(ValidationError) as cm:
            order.full_clean()
        self.assertIn('shipping_cost', str(cm.exception))

    def test_clean_validation_delivered_must_be_paid(self):
        """
        CP-xxx
        HU-034 | ESCENARIO 3 | E | Pedido entregado debe estar marcado como pagado
        """
        # Crear pedido directamente en la BD para evitar validaciones intermedias
        order = Order.objects.create(
            customer_name='Test',
            customer_phone='123',
            shipping_address='Test',
            status='entregado',
            is_paid=True,  # Debe estar pagado para pasar la validación
            subtotal=Decimal('10.00'),
            shipping_cost=Decimal('2.00'),
            total_amount=Decimal('12.00')
        )
        # Cambiar is_paid a False después de crear
        order.is_paid = False
        with self.assertRaises(ValidationError) as cm:
            order.full_clean()
        self.assertIn('is_paid', str(cm.exception))

    def test_default_status_is_pending(self):
        """
        CP-xxx
        HU-024 | ESCENARIO 1 | H | Estado inicial por defecto es 'pendiente'
        """
        self.assertEqual(self.order.status, 'pendiente')

    def test_default_is_paid_false(self):
        """
        CP-xxx
        HU-024 | ESCENARIO 1 | H | is_paid por defecto es False
        """
        self.assertFalse(self.order.is_paid)

    def test_can_transition_to_allowed_status(self):
        """
        CP-xxx
        HU-029 | ESCENARIO 2 | H | Verifica transiciones de estado permitidas
        """
        # pendiente → confirmado
        self.assertTrue(self.order.can_transition_to('confirmado'))
        # pendiente → cancelado
        self.assertTrue(self.order.can_transition_to('cancelado'))
        # pendiente → entregado (no permitido)
        self.assertFalse(self.order.can_transition_to('entregado'))

    def test_can_transition_to_disallowed_status(self):
        """
        CP-xxx
        HU-029 | ESCENARIO 3 | E | Transición no permitida → retorna False
        """
        # pendiente → preparando (no permitido directamente)
        self.assertFalse(self.order.can_transition_to('preparando'))

    def test_confirm_order_success(self):
        """
        CP-xxx
        HU-024 | ESCENARIO 1 | H | Confirmar pedido (pendiente → confirmado)
        HU-029 | ESCENARIO 1 | H | Cambio de estado exitoso
        """
        _create_order_item(self.order, self.variant, quantity=2)
        self.order.confirm()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmado')

    def test_confirm_order_reduces_stock(self):
        """
        CP-xxx
        HU-013 | ESCENARIO 5 | H | Reduce stock automáticamente al confirmar
        """
        initial_stock = self.variant.stock
        _create_order_item(self.order, self.variant, quantity=3)
        self.order.confirm()
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, initial_stock - 3)

    def test_confirm_order_insufficient_stock_raises_error(self):
        """
        CP-xxx
        HU-024 | ESCENARIO 2 | E | Stock insuficiente al confirmar
        """
        _create_order_item(self.order, self.variant, quantity=20)  # stock es 10
        with self.assertRaises(ValidationError) as cm:
            self.order.confirm()
        self.assertIn('Stock insuficiente', str(cm.exception))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'pendiente')

    def test_confirm_order_invalid_status(self):
        """
        CP-xxx
        HU-029 | ESCENARIO 3 | E | No se puede confirmar pedido en estado inválido
        """
        # Crear pedido directamente con estado entregado y pagado
        delivered_order = Order.objects.create(
            customer_name='Test',
            customer_phone='123',
            shipping_address='Test',
            status='entregado',
            is_paid=True,
            subtotal=Decimal('10.00'),
            shipping_cost=Decimal('2.00'),
            total_amount=Decimal('12.00')
        )
        with self.assertRaises(ValidationError) as cm:
            delivered_order.confirm()
        self.assertIn('No se puede confirmar', str(cm.exception))

    def test_cancel_order_success(self):
        """
        CP-xxx
        HU-030 | ESCENARIO 1 | H | Cancelación exitosa (libera stock)
        """
        _create_order_item(self.order, self.variant, quantity=2)
        self.order.confirm()
        self.order.cancel(reason='Cliente solicitó cancelación')
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelado')
        self.assertEqual(self.order.cancelled_reason, 'Cliente solicitó cancelación')

    def test_cancel_order_restores_stock(self):
        """
        CP-xxx
        HU-030 | ESCENARIO 1 | H | Cancelación libera stock
        """
        initial_stock = self.variant.stock
        _create_order_item(self.order, self.variant, quantity=3)
        self.order.confirm()
        self.variant.refresh_from_db()
        self.order.cancel(reason='Prueba')
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, initial_stock)

    def test_cancel_order_without_reason_raises_error(self):
        """
        CP-xxx
        HU-030 | ESCENARIO 3 | H | Cancelación requiere motivo
        """
        with self.assertRaises(ValidationError) as cm:
            self.order.cancel(reason='')
        self.assertIn('Debe indicar un motivo', str(cm.exception))

    def test_cancel_delivered_order_raises_error(self):
        """
        CP-xxx
        HU-030 | ESCENARIO 2 | E | Pedido ya entregado no se puede cancelar
        """
        # Crear pedido directamente con estado entregado y pagado
        delivered_order = Order.objects.create(
            customer_name='Test',
            customer_phone='123',
            shipping_address='Test',
            status='entregado',
            is_paid=True,
            subtotal=Decimal('10.00'),
            shipping_cost=Decimal('2.00'),
            total_amount=Decimal('12.00')
        )
        with self.assertRaises(ValidationError) as cm:
            delivered_order.cancel(reason='Prueba')
        self.assertIn('No se puede cancelar un pedido ya entregado', str(cm.exception))

    def test_cancel_already_cancelled_order_raises_error(self):
        """
        CP-xxx
        HU-030 | ESCENARIO 4 | E | Pedido ya cancelado
        """
        # Cancelar el pedido primero
        self.order.cancel(reason='Primera cancelación')
        self.assertEqual(self.order.status, 'cancelado')
        # Intentar cancelar nuevamente
        with self.assertRaises(ValidationError) as cm:
            self.order.cancel(reason='Segunda cancelación')
        self.assertIn('cancelado', str(cm.exception).lower())

    def test_mark_as_ready_success(self):
        """
        CP-xxx
        HU-029 | ESCENARIO 2 | H | Cambiar estado de preparando a listo
        """
        self.order.status = 'preparando'
        self.order.save()
        self.order.mark_as_ready()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'listo')

    def test_mark_as_ready_invalid_status(self):
        """
        CP-xxx
        HU-029 | ESCENARIO 3 | E | No se puede marcar como listo desde estado inválido
        """
        with self.assertRaises(ValidationError) as cm:
            self.order.mark_as_ready()
        self.assertIn('No se puede marcar como listo', str(cm.exception))

    def test_mark_as_preparing_success(self):
        """
        CP-xxx
        HU-029 | ESCENARIO 2 | H | Cambiar estado de confirmado a preparando
        """
        self.order.status = 'confirmado'
        self.order.save()
        self.order.mark_as_preparing()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'preparando')

    def test_assign_delivery_success(self):
        """
        CP-xxx
        HU-032 | ESCENARIO 1 | H | Asignación exitosa (cambia estado a en_camino)
        """
        delivery_user = _create_delivery_user(username='delivery1')
        self.order.status = 'listo'
        self.order.save()
        self.order.assign_delivery(delivery_user)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'en_camino')
        self.assertEqual(self.order.assigned_delivery_user, delivery_user)

    def test_assign_delivery_not_ready_status(self):
        """
        CP-xxx
        HU-032 | ESCENARIO 1 | H | Solo se puede asignar repartidor a pedidos listos
        """
        delivery_user = _create_delivery_user(username='delivery1')
        with self.assertRaises(ValidationError) as cm:
            self.order.assign_delivery(delivery_user)
        self.assertIn('Solo se puede asignar un repartidor a pedidos listos', str(cm.exception))

    def test_mark_as_delivered_success(self):
        """
        CP-xxx
        HU-034 | ESCENARIO 1 | H | Marcar como entregado y pagado
        """
        self.order.status = 'en_camino'
        self.order.save()
        self.order.mark_as_delivered()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'entregado')
        self.assertTrue(self.order.is_paid)

    def test_mark_as_delivered_not_en_camino_status(self):
        """
        CP-xxx
        HU-034 | ESCENARIO 3 | E | Pedido no está en camino
        """
        with self.assertRaises(ValidationError) as cm:
            self.order.mark_as_delivered()
        self.assertIn('Solo se puede entregar un pedido que está en camino', str(cm.exception))

    def test_order_meta_ordering(self):
        """
        CP-xxx
        HU-027 | H | Orden por defecto es -created_at (más reciente primero)
        """
        older = _create_order(customer_name='Older')
        newer = _create_order(customer_name='Newer')
        qs = Order.objects.all()
        self.assertEqual(qs.first().customer_name, 'Newer')

    def test_order_verbose_names(self):
        """
        CP-xxx
        HU-027 | H | Meta.verbose_name y verbose_name_plural correctos
        """
        self.assertEqual(Order._meta.verbose_name, 'Pedido')
        self.assertEqual(Order._meta.verbose_name_plural, 'Pedidos')

    def test_customer_email_optional(self):
        """
        CP-xxx
        HU-024 | H | Correo electrónico opcional
        """
        order = _create_order(customer_email=None)
        self.assertIsNone(order.customer_email)

    def test_delivery_notes_optional(self):
        """
        CP-xxx
        HU-024 | H | Notas de entrega opcionales
        """
        order = _create_order(delivery_notes='Dejar con el portero')
        self.assertEqual(order.delivery_notes, 'Dejar con el portero')

    def test_payment_session_id_optional(self):
        """
        CP-xxx
        HU-024 | H | ID de sesión de pago opcional
        """
        self.assertIsNone(self.order.payment_session_id)


# =============================================================================
# TESTS: OrderItem Model
# =============================================================================

class OrderItemModelTest(TestCase):
    """
    HU-024: Confirmar pedido (creación de items)
    HU-028: Ver detalle de pedido (admin)
    HU-031: Crear pedido manual (admin) - items asociados
    """

    def setUp(self):
        self.variant = _create_product_variant(stock=10)
        self.order = _create_order()
        self.order_item = _create_order_item(self.order, self.variant, quantity=2)

    def test_create_order_item_with_all_fields(self):
        """
        CP-xxx
        HU-024 | ESCENARIO 1 | H | Creación de item con todos los campos
        HU-031 | ESCENARIO 1 | H | Items asociados a pedido manual
        """
        self.assertEqual(self.order_item.order, self.order)
        self.assertEqual(self.order_item.variant, self.variant)
        self.assertEqual(self.order_item.product_name_snapshot, self.variant.product.name)
        self.assertEqual(self.order_item.size_snapshot, self.variant.size.name)
        self.assertEqual(self.order_item.quantity, 2)
        self.assertEqual(self.order_item.unit_price, Decimal('5.00'))
        self.assertEqual(self.order_item.stock_snapshot, self.variant.stock)
        self.assertEqual(self.order_item.subtotal, Decimal('10.00'))

    def test_order_item_str(self):
        """
        CP-xxx
        HU-028 | H | __str__ retorna número de pedido y producto
        """
        expected = f"{self.order.order_number} - Test Product x2"
        self.assertEqual(str(self.order_item), expected)

    def test_order_item_subtotal_auto_calculation(self):
        """
        CP-xxx
        HU-024 | ESCENARIO 1 | H | Cálculo automático del subtotal (precio * cantidad)
        """
        item = OrderItem(
            order=self.order,
            variant=self.variant,
            quantity=3,
            unit_price=Decimal('5.00')
        )
        item.save()
        self.assertEqual(item.subtotal, Decimal('15.00'))

    def test_order_item_snapshot_auto_population_from_variant(self):
        """
        CP-xxx
        HU-024 | ESCENARIO 1 | H | Snapshots automáticos desde la variante
        """
        # Crear nuevo item sin snapshots
        item = OrderItem(
            order=self.order,
            variant=self.variant,
            quantity=1
        )
        item.save()
        self.assertEqual(item.product_name_snapshot, self.variant.product.name)
        self.assertEqual(item.size_snapshot, self.variant.size.name)
        self.assertEqual(item.unit_price, self.variant.product.price)
        self.assertEqual(item.stock_snapshot, self.variant.stock)

    def test_order_item_manual_snapshot_override(self):
        """
        CP-xxx
        HU-031 | ESCENARIO 2 | H | Permite sobrescribir snapshots manualmente
        """
        item = OrderItem(
            order=self.order,
            variant=self.variant,
            product_name_snapshot='Nombre Personalizado',
            size_snapshot='XL',
            quantity=1,
            unit_price=Decimal('10.00')
        )
        item.save()
        self.assertEqual(item.product_name_snapshot, 'Nombre Personalizado')
        self.assertEqual(item.size_snapshot, 'XL')
        self.assertEqual(item.unit_price, Decimal('10.00'))

    def test_order_item_variant_nullable(self):
        """
        CP-xxx
        HU-031 | ESCENARIO 1 | H | Variante puede ser nula (para items manuales sin stock)
        """
        item = OrderItem(
            order=self.order,
            variant=None,
            product_name_snapshot='Producto Manual',
            size_snapshot='M',
            quantity=1,
            unit_price=Decimal('10.00')
        )
        item.save()
        self.assertIsNone(item.variant)
        self.assertEqual(item.product_name_snapshot, 'Producto Manual')

    def test_clean_quantity_zero_or_negative_raises_error(self):
        """
        CP-xxx
        HU-031 | ESCENARIO 2 | A | Validación: cantidad debe ser mayor a 0
        """
        item = OrderItem(
            order=self.order,
            variant=self.variant,
            quantity=0
        )
        with self.assertRaises(ValidationError) as cm:
            item.full_clean()
        self.assertIn('quantity', str(cm.exception).lower())

    def test_clean_unit_price_negative_raises_error(self):
        """
        CP-xxx
        HU-031 | ESCENARIO 2 | A | Validación: precio unitario no puede ser negativo
        """
        item = OrderItem(
            order=self.order,
            variant=self.variant,
            quantity=1,
            unit_price=Decimal('-10.00')
        )
        with self.assertRaises(ValidationError) as cm:
            item.full_clean()
        self.assertIn('unit_price', str(cm.exception).lower())

    def test_clean_stock_snapshot_negative_raises_error(self):
        """
        CP-xxx
        HU-031 | ESCENARIO 2 | A | Validación: stock snapshot no puede ser negativo
        """
        item = OrderItem(
            order=self.order,
            variant=self.variant,
            quantity=1,
            stock_snapshot=-5
        )
        with self.assertRaises(ValidationError) as cm:
            item.full_clean()
        self.assertIn('stock_snapshot', str(cm.exception).lower())

    def test_order_item_meta_ordering(self):
        """
        CP-xxx
        HU-028 | H | Orden por defecto por id
        """
        item2 = _create_order_item(self.order, self.variant, quantity=1)
        self.assertEqual(OrderItem.objects.first().id, self.order_item.id)

    def test_order_item_verbose_names(self):
        """
        CP-xxx
        HU-028 | H | Meta.verbose_name y verbose_name_plural correctos
        """
        self.assertEqual(OrderItem._meta.verbose_name, 'Item del pedido')
        self.assertEqual(OrderItem._meta.verbose_name_plural, 'Items del pedido')

    def test_order_item_cascade_delete(self):
        """
        CP-xxx
        HU-028 | H | Al eliminar pedido, se eliminan sus items (CASCADE)
        """
        self.order.delete()
        self.assertEqual(OrderItem.objects.count(), 0)


# =============================================================================
# TESTS: Order Status Progression (HU-035 incidencia)
# =============================================================================

class OrderStatusProgressionTest(TestCase):
    """Pruebas de progresión de estados y registro de incidencias."""

    def setUp(self):
        self.variant = _create_product_variant(stock=10)
        self.order = _create_order()

    def test_full_status_progression(self):
        """
        CP-xxx
        HU-029 | ESCENARIO 1 | H | Progresión completa de estados
        """
        # pendiente → confirmado
        _create_order_item(self.order, self.variant, quantity=2)
        self.order.confirm()
        self.assertEqual(self.order.status, 'confirmado')
        
        # confirmado → preparando
        self.order.mark_as_preparing()
        self.assertEqual(self.order.status, 'preparando')
        
        # preparando → listo
        self.order.mark_as_ready()
        self.assertEqual(self.order.status, 'listo')
        
        # listo → en_camino
        delivery_user = _create_delivery_user(username='delivery1')
        self.order.assign_delivery(delivery_user)
        self.assertEqual(self.order.status, 'en_camino')
        
        # en_camino → entregado
        self.order.mark_as_delivered()
        self.assertEqual(self.order.status, 'entregado')
        self.assertTrue(self.order.is_paid)

    def test_cancellation_at_different_stages(self):
        """
        CP-xxx
        HU-030 | ESCENARIO 1 | H | Cancelación permitida en múltiples estados
        HU-030 | ESCENARIO 3 | H | Cancelación con motivo (incidencia)
        """
        stages = ['pendiente', 'confirmado', 'preparando', 'listo', 'en_camino']
        
        for stage in stages:
            order = _create_order(status=stage)
            order.cancel(reason=f'Cancelado desde estado {stage}')
            self.assertEqual(order.status, 'cancelado')
            self.assertIn(f'Cancelado desde estado {stage}', order.cancelled_reason)

    def test_incidence_registration_on_cancellation(self):
        """
        CP-xxx
        HU-035 | ESCENARIO 1 | H | Registrar incidencia (motivo guardado en cancelled_reason)
        HU-035 | ESCENARIO 2 | H | Tipos de incidencia disponibles (campo libre)
        """
        self.order.cancel(reason='Producto dañado - incidencia registrada')
        self.assertEqual(self.order.cancelled_reason, 'Producto dañado - incidencia registrada')

    def test_cannot_cancel_delivered_order(self):
        """
        CP-xxx
        HU-035 | ESCENARIO 3 | E | No se puede registrar incidencia en pedido entregado
        """
        delivered_order = Order.objects.create(
            customer_name='Test',
            customer_phone='123',
            shipping_address='Test',
            status='entregado',
            is_paid=True,
            subtotal=Decimal('10.00'),
            shipping_cost=Decimal('2.00'),
            total_amount=Decimal('12.00')
        )
        with self.assertRaises(ValidationError) as cm:
            delivered_order.cancel(reason='Intento de incidencia post-entrega')
        self.assertIn('No se puede cancelar un pedido ya entregado', str(cm.exception))