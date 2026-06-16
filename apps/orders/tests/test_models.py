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
    defaults = {'username': 'testuser', 'password': 'pass1234'}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


def _create_delivery_user(**kwargs):
    defaults = {'username': 'delivery', 'password': 'pass1234', 'is_delivery': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


def _create_admin_user(**kwargs):
    defaults = {'username': 'admin', 'password': 'pass1234', 'is_staff': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


def _create_product_variant(stock=10):
    category = Category.objects.create(name='Test Category')
    size = Size.objects.create(name='M')
    color = Color.objects.create(name='Rojo', code='#FF0000')
    product = Product.objects.create(
        name='Test Product',
        price=Decimal('5.00'),
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
    unit_price = Decimal('5.00')
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
    """Pruebas del modelo Order"""

    def setUp(self):
        self.variant = _create_product_variant(stock=10)
        self.order = _create_order()

    # UT-188: HU-031 CA-001 - Creación de pedido con todos los campos
    def test_create_order_with_all_fields(self):
        self.assertEqual(self.order.customer_name, 'Juan Perez')
        self.assertEqual(self.order.customer_phone, '3001234567')
        self.assertEqual(self.order.customer_email, 'juan@test.com')
        self.assertEqual(self.order.shipping_address, 'Calle 123, Bogotá')
        self.assertEqual(self.order.subtotal, Decimal('10.00'))
        self.assertEqual(self.order.shipping_cost, Decimal('2.00'))
        self.assertEqual(self.order.total_amount, Decimal('12.00'))
        self.assertEqual(self.order.status, 'pendiente')
        self.assertFalse(self.order.is_paid)

    # UT-189: HU-027 - __str__ retorna número de pedido y nombre del cliente
    def test_order_str_returns_order_number_and_customer(self):
        expected = f"{self.order.order_number} - Juan Perez"
        self.assertEqual(str(self.order), expected)

    # UT-190: HU-024 CA-001 - Generación automática de número de pedido
    def test_order_number_auto_generation(self):
        self.assertIsNotNone(self.order.order_number)
        self.assertTrue(self.order.order_number.startswith('ZCD-'))
        self.assertEqual(len(self.order.order_number), 8)

    # UT-191: HU-024 CA-001 - Números de pedido secuenciales
    def test_order_number_sequential(self):
        order2 = _create_order(customer_name='Maria Gomez')
        self.assertNotEqual(self.order.order_number, order2.order_number)
        num1 = int(self.order.order_number.split('-')[1])
        num2 = int(order2.order_number.split('-')[1])
        self.assertEqual(num2, num1 + 1)

    # UT-192: HU-026 CA-001 - Token de seguimiento único generado automáticamente
    def test_tracking_token_auto_generation(self):
        self.assertIsNotNone(self.order.tracking_token)
        order2 = _create_order(customer_name='Maria Gomez')
        self.assertNotEqual(self.order.tracking_token, order2.tracking_token)

    # UT-193: HU-024 CA-001 - Cálculo automático del total
    def test_total_amount_auto_calculation_on_save(self):
        order = Order(
            customer_name='Test',
            customer_phone='123',
            shipping_address='Test',
            subtotal=Decimal('10.00'),
            shipping_cost=Decimal('2.00')
        )
        order.save()
        self.assertEqual(order.total_amount, Decimal('12.00'))

    # UT-194: HU-031 CA-001 - Actualización del total al modificar subtotal
    def test_total_amount_updates_when_subtotal_changes(self):
        self.order.subtotal = Decimal('15.00')
        self.order.save()
        self.assertEqual(self.order.total_amount, Decimal('17.00'))

    # UT-195: HU-024 CA-001 / HU-031 CA-001 - Subtotal no negativo
    def test_clean_validation_subtotal_negative(self):
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

    # UT-196: HU-024 CA-001 - Costo de envío no negativo
    def test_clean_validation_shipping_cost_negative(self):
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

    # UT-197: HU-034 CA-003 - Pedido entregado debe estar pagado
    def test_clean_validation_delivered_must_be_paid(self):
        order = Order.objects.create(
            customer_name='Test',
            customer_phone='123',
            shipping_address='Test',
            status='entregado',
            is_paid=True,
            subtotal=Decimal('10.00'),
            shipping_cost=Decimal('2.00'),
            total_amount=Decimal('12.00')
        )
        order.is_paid = False
        with self.assertRaises(ValidationError) as cm:
            order.full_clean()
        self.assertIn('is_paid', str(cm.exception))

    # UT-198: HU-024 CA-001 - Estado inicial pendiente
    def test_default_status_is_pending(self):
        self.assertEqual(self.order.status, 'pendiente')

    # UT-199: HU-024 CA-001 - is_paid inicial False
    def test_default_is_paid_false(self):
        self.assertFalse(self.order.is_paid)

    # UT-200: HU-029 CA-002 - Transiciones permitidas
    def test_can_transition_to_allowed_status(self):
        self.assertTrue(self.order.can_transition_to('confirmado'))
        self.assertTrue(self.order.can_transition_to('cancelado'))
        self.assertFalse(self.order.can_transition_to('entregado'))

    # UT-201: HU-029 CA-003 - Transición no permitida
    def test_can_transition_to_disallowed_status(self):
        self.assertFalse(self.order.can_transition_to('preparando'))

    # UT-202: HU-024 CA-001 / HU-029 CA-001 - Confirmar pedido exitoso
    def test_confirm_order_success(self):
        _create_order_item(self.order, self.variant, quantity=2)
        self.order.confirm()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmado')

    # UT-203: HU-013 CA-005 - Reduce stock automáticamente al confirmar
    def test_confirm_order_reduces_stock(self):
        initial_stock = self.variant.stock
        _create_order_item(self.order, self.variant, quantity=3)
        self.order.confirm()
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, initial_stock - 3)

    # UT-204: HU-024 CA-002 - Stock insuficiente al confirmar
    def test_confirm_order_insufficient_stock_raises_error(self):
        _create_order_item(self.order, self.variant, quantity=20)
        with self.assertRaises(ValidationError) as cm:
            self.order.confirm()
        self.assertIn('Stock insuficiente', str(cm.exception))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'pendiente')

    # UT-205: HU-029 CA-003 - No confirmar pedido en estado inválido
    def test_confirm_order_invalid_status(self):
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

    # UT-206: HU-030 CA-001 - Cancelación exitosa
    def test_cancel_order_success(self):
        _create_order_item(self.order, self.variant, quantity=2)
        self.order.confirm()
        self.order.cancel(reason='Cliente solicitó cancelación')
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelado')
        self.assertEqual(self.order.cancelled_reason, 'Cliente solicitó cancelación')

    # UT-207: HU-030 CA-001 - Cancelación libera stock
    def test_cancel_order_restores_stock(self):
        initial_stock = self.variant.stock
        _create_order_item(self.order, self.variant, quantity=3)
        self.order.confirm()
        self.variant.refresh_from_db()
        self.order.cancel(reason='Prueba')
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, initial_stock)

    # UT-208: HU-030 CA-003 - Cancelación requiere motivo
    def test_cancel_order_without_reason_raises_error(self):
        with self.assertRaises(ValidationError) as cm:
            self.order.cancel(reason='')
        self.assertIn('Debe indicar un motivo', str(cm.exception))

    # UT-209: HU-030 CA-002 - Pedido entregado no se cancela
    def test_cancel_delivered_order_raises_error(self):
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

    # UT-210: HU-030 CA-004 - Pedido ya cancelado no se cancela nuevamente
    def test_cancel_already_cancelled_order_raises_error(self):
        self.order.cancel(reason='Primera cancelación')
        self.assertEqual(self.order.status, 'cancelado')
        with self.assertRaises(ValidationError) as cm:
            self.order.cancel(reason='Segunda cancelación')
        self.assertIn('cancelado', str(cm.exception).lower())

    # UT-211: HU-029 CA-002 - Cambiar de preparando a listo
    def test_mark_as_ready_success(self):
        self.order.status = 'preparando'
        self.order.save()
        self.order.mark_as_ready()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'listo')

    # UT-212: HU-029 CA-003 - Marcar listo desde estado inválido
    def test_mark_as_ready_invalid_status(self):
        with self.assertRaises(ValidationError) as cm:
            self.order.mark_as_ready()
        self.assertIn('No se puede marcar como listo', str(cm.exception))

    # UT-213: HU-029 CA-002 - Cambiar de confirmado a preparando
    def test_mark_as_preparing_success(self):
        self.order.status = 'confirmado'
        self.order.save()
        self.order.mark_as_preparing()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'preparando')

    # UT-214: HU-032 CA-001 - Asignación de repartidor exitosa
    def test_assign_delivery_success(self):
        delivery_user = _create_delivery_user(username='delivery1')
        self.order.status = 'listo'
        self.order.save()
        self.order.assign_delivery(delivery_user)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'en_camino')
        self.assertEqual(self.order.assigned_delivery_user, delivery_user)

    # UT-215: HU-032 CA-003 - Asignar repartidor solo a pedidos listos
    def test_assign_delivery_not_ready_status(self):
        delivery_user = _create_delivery_user(username='delivery1')
        with self.assertRaises(ValidationError) as cm:
            self.order.assign_delivery(delivery_user)
        self.assertIn('Solo se puede asignar un repartidor a pedidos listos', str(cm.exception))

    # UT-216: HU-034 CA-001 - Marcar como entregado y pagado
    def test_mark_as_delivered_success(self):
        self.order.status = 'en_camino'
        self.order.save()
        self.order.mark_as_delivered()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'entregado')
        self.assertTrue(self.order.is_paid)

    # UT-217: HU-034 CA-003 - Pedido no está en camino
    def test_mark_as_delivered_not_en_camino_status(self):
        with self.assertRaises(ValidationError) as cm:
            self.order.mark_as_delivered()
        self.assertIn('Solo se puede entregar un pedido que está en camino', str(cm.exception))

    # UT-218: HU-027 - Orden por defecto -created_at
    def test_order_meta_ordering(self):
        older = _create_order(customer_name='Older')
        newer = _create_order(customer_name='Newer')
        qs = Order.objects.all()
        self.assertEqual(qs.first().customer_name, 'Newer')

    # UT-219: HU-027 - Verbose names correctos
    def test_order_verbose_names(self):
        self.assertEqual(Order._meta.verbose_name, 'Pedido')
        self.assertEqual(Order._meta.verbose_name_plural, 'Pedidos')

    # UT-220: HU-024 - Email opcional
    def test_customer_email_optional(self):
        order = _create_order(customer_email=None)
        self.assertIsNone(order.customer_email)

    # UT-221: HU-024 - Notas de entrega opcionales
    def test_delivery_notes_optional(self):
        order = _create_order(delivery_notes='Dejar con el portero')
        self.assertEqual(order.delivery_notes, 'Dejar con el portero')

    # UT-222: HU-024 - ID de sesión de pago opcional
    def test_payment_session_id_optional(self):
        self.assertIsNone(self.order.payment_session_id)


# =============================================================================
# TESTS: OrderItem Model
# =============================================================================

class OrderItemModelTest(TestCase):
    """Pruebas del modelo OrderItem"""

    def setUp(self):
        self.variant = _create_product_variant(stock=10)
        self.order = _create_order()
        self.order_item = _create_order_item(self.order, self.variant, quantity=2)

    # UT-223: HU-024 CA-001 / HU-031 CA-001 - Creación de item
    def test_create_order_item_with_all_fields(self):
        self.assertEqual(self.order_item.order, self.order)
        self.assertEqual(self.order_item.variant, self.variant)
        self.assertEqual(self.order_item.product_name_snapshot, self.variant.product.name)
        self.assertEqual(self.order_item.size_snapshot, self.variant.size.name)
        self.assertEqual(self.order_item.quantity, 2)
        self.assertEqual(self.order_item.unit_price, Decimal('5.00'))
        self.assertEqual(self.order_item.stock_snapshot, self.variant.stock)
        self.assertEqual(self.order_item.subtotal, Decimal('10.00'))

    # UT-224: HU-028 - __str__ retorna número y producto
    def test_order_item_str(self):
        expected = f"{self.order.order_number} - Test Product x2"
        self.assertEqual(str(self.order_item), expected)

    # UT-225: HU-024 CA-001 - Cálculo automático del subtotal
    def test_order_item_subtotal_auto_calculation(self):
        item = OrderItem(
            order=self.order,
            variant=self.variant,
            quantity=3,
            unit_price=Decimal('5.00')
        )
        item.save()
        self.assertEqual(item.subtotal, Decimal('15.00'))

    # UT-226: HU-024 CA-001 - Snapshots automáticos desde variante
    def test_order_item_snapshot_auto_population_from_variant(self):
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

    # UT-227: HU-031 CA-002 - Sobrescribir snapshots manualmente
    def test_order_item_manual_snapshot_override(self):
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

    # UT-228: HU-031 CA-001 - Variante puede ser nula
    def test_order_item_variant_nullable(self):
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

    # UT-229: HU-031 CA-002 - Cantidad mayor a 0
    def test_clean_quantity_zero_or_negative_raises_error(self):
        item = OrderItem(
            order=self.order,
            variant=self.variant,
            quantity=0
        )
        with self.assertRaises(ValidationError) as cm:
            item.full_clean()
        self.assertIn('quantity', str(cm.exception).lower())

    # UT-230: HU-031 CA-002 - Precio unitario no negativo
    def test_clean_unit_price_negative_raises_error(self):
        item = OrderItem(
            order=self.order,
            variant=self.variant,
            quantity=1,
            unit_price=Decimal('-10.00')
        )
        with self.assertRaises(ValidationError) as cm:
            item.full_clean()
        self.assertIn('unit_price', str(cm.exception).lower())

    # UT-231: HU-031 CA-002 - Stock snapshot no negativo
    def test_clean_stock_snapshot_negative_raises_error(self):
        item = OrderItem(
            order=self.order,
            variant=self.variant,
            quantity=1,
            stock_snapshot=-5
        )
        with self.assertRaises(ValidationError) as cm:
            item.full_clean()
        self.assertIn('stock_snapshot', str(cm.exception).lower())

    # UT-232: HU-028 - Orden por defecto por id
    def test_order_item_meta_ordering(self):
        item2 = _create_order_item(self.order, self.variant, quantity=1)
        self.assertEqual(OrderItem.objects.first().id, self.order_item.id)

    # UT-233: HU-028 - Verbose names correctos
    def test_order_item_verbose_names(self):
        self.assertEqual(OrderItem._meta.verbose_name, 'Item del pedido')
        self.assertEqual(OrderItem._meta.verbose_name_plural, 'Items del pedido')

    # UT-234: HU-028 - CASCADE al eliminar pedido
    def test_order_item_cascade_delete(self):
        self.order.delete()
        self.assertEqual(OrderItem.objects.count(), 0)


# =============================================================================
# TESTS: Order Status Progression
# =============================================================================

class OrderStatusProgressionTest(TestCase):
    """Pruebas de progresión de estados y registro de incidencias"""

    def setUp(self):
        self.variant = _create_product_variant(stock=10)
        self.order = _create_order()

    # UT-235: HU-029 CA-001 - Progresión completa de estados
    def test_full_status_progression(self):
        _create_order_item(self.order, self.variant, quantity=2)
        self.order.confirm()
        self.assertEqual(self.order.status, 'confirmado')
        
        self.order.mark_as_preparing()
        self.assertEqual(self.order.status, 'preparando')
        
        self.order.mark_as_ready()
        self.assertEqual(self.order.status, 'listo')
        
        delivery_user = _create_delivery_user(username='delivery1')
        self.order.assign_delivery(delivery_user)
        self.assertEqual(self.order.status, 'en_camino')
        
        self.order.mark_as_delivered()
        self.assertEqual(self.order.status, 'entregado')
        self.assertTrue(self.order.is_paid)

    # UT-236: HU-030 CA-001 - Cancelación en múltiples estados
    def test_cancellation_at_different_stages(self):
        stages = ['pendiente', 'confirmado', 'preparando', 'listo', 'en_camino']
        
        for stage in stages:
            order = _create_order(status=stage)
            order.cancel(reason=f'Cancelado desde estado {stage}')
            self.assertEqual(order.status, 'cancelado')
            self.assertIn(f'Cancelado desde estado {stage}', order.cancelled_reason)

    # UT-237: HU-035 CA-001 - Registrar incidencia en cancelled_reason
    def test_incidence_registration_on_cancellation(self):
        self.order.cancel(reason='Producto dañado - incidencia registrada')
        self.assertEqual(self.order.cancelled_reason, 'Producto dañado - incidencia registrada')

    # UT-238: HU-035 CA-003 - No registrar incidencia en pedido entregado
    def test_cannot_cancel_delivered_order(self):
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