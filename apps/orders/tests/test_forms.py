"""
Tests unitarios para formularios de apps.orders.forms

Cubre:
- HU-023: CheckoutOrderForm
- HU-031: OrderCreateForm
- HU-031 (parte): OrderUpdateForm
- HU-029: OrderConfirmForm
- HU-030/035: OrderCancelForm
- HU-029: OrderChangeStatusForm
- HU-032: OrderAssignDeliveryForm
- HU-034: OrderMarkAsDeliveredForm
- HU-024: OrderPaymentForm
- HU-031: OrderItemCreateForm
- HU-031: OrderItemUpdateForm
- HU-031: OrderItemDeleteForm

Casos de prueba: CP-xxx a CP-xxx
"""

from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.orders.forms import (
    CheckoutOrderForm,
    OrderCreateForm,
    OrderUpdateForm,
    OrderConfirmForm,
    OrderCancelForm,
    OrderChangeStatusForm,
    OrderAssignDeliveryForm,
    OrderMarkAsDeliveredForm,
    OrderPaymentForm,
    OrderItemCreateForm,
    OrderItemUpdateForm,
    OrderItemDeleteForm,
)
from apps.orders.models import Order, OrderItem
from apps.products.models import Product, Category, Size, Color, ProductColor, ProductVariant
from apps.users.models import User


# =============================================================================
# HELPERS
# =============================================================================

def _create_delivery_user(**kwargs):
    """Crea un usuario con rol de entregador."""
    defaults = {'username': 'delivery', 'password': 'pass1234', 'is_delivery': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


def _create_normal_user(**kwargs):
    """Crea un usuario normal."""
    defaults = {'username': 'normal', 'password': 'pass1234'}
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
    """Crea un pedido de prueba."""
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
    """Crea un item de pedido."""
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
# TESTS: HU-023 CheckoutOrderForm
# =============================================================================

class CheckoutOrderFormTest(TestCase):
    """HU-023: Completar formulario de envío"""

    def get_valid_data(self):
        return {
            'customer_name': 'María Gómez Rodríguez',
            'customer_phone': '3001234567',
            'customer_email': 'maria@test.com',
            'shipping_address': 'Calle 123 #45-67, Bogotá',
            'delivery_notes': 'Dejar con el portero',
        }

    def test_valid_form(self):
        form = CheckoutOrderForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid(), msg=f"Errores: {form.errors}")

    def test_required_fields(self):
        form = CheckoutOrderForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('customer_name', form.errors)
        self.assertIn('customer_phone', form.errors)
        self.assertIn('shipping_address', form.errors)

    def test_invalid_phone_format(self):
        data = self.get_valid_data()
        data['customer_phone'] = '12345'
        form = CheckoutOrderForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('customer_phone', form.errors)

    def test_invalid_phone_too_long(self):
        data = self.get_valid_data()
        data['customer_phone'] = '1' * 20
        form = CheckoutOrderForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('customer_phone', form.errors)

    def test_phone_with_spaces_and_dashes_normalized(self):
        data = self.get_valid_data()
        data['customer_phone'] = '+57 (300) 123-4567'
        form = CheckoutOrderForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['customer_phone'], '573001234567')

    def test_email_optional(self):
        data = self.get_valid_data()
        data['customer_email'] = ''
        form = CheckoutOrderForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['customer_email'], '')

    def test_invalid_email(self):
        data = self.get_valid_data()
        data['customer_email'] = 'invalid-email'
        form = CheckoutOrderForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('customer_email', form.errors)

    def test_name_min_length(self):
        data = self.get_valid_data()
        data['customer_name'] = 'Jo'
        form = CheckoutOrderForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('customer_name', form.errors)

    def test_address_min_length(self):
        data = self.get_valid_data()
        data['shipping_address'] = 'Cll'
        form = CheckoutOrderForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('shipping_address', form.errors)

    def test_delivery_notes_optional(self):
        data = self.get_valid_data()
        data['delivery_notes'] = ''
        form = CheckoutOrderForm(data=data)
        self.assertTrue(form.is_valid())


# =============================================================================
# TESTS: HU-031 OrderCreateForm
# =============================================================================

class OrderCreateFormTest(TestCase):
    """HU-031: Crear pedido manual (admin)"""

    def get_valid_data(self):
        return {
            'customer_name': 'Juan Perez',
            'customer_phone': '3001234567',
            'customer_email': 'juan@test.com',
            'shipping_address': 'Calle 123, Bogotá',
            'delivery_notes': '',
            'shipping_cost': Decimal('2.00'),
            'is_paid': False,
        }

    def test_valid_form(self):
        form = OrderCreateForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid(), msg=f"Errores: {form.errors}")

    def test_phone_normalization(self):
        data = self.get_valid_data()
        data['customer_phone'] = '+57 (300) 123-4567'
        form = OrderCreateForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['customer_phone'], '573001234567')

    def test_phone_too_short(self):
        data = self.get_valid_data()
        data['customer_phone'] = '12345'
        form = OrderCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('customer_phone', form.errors)

    def test_phone_too_long(self):
        data = self.get_valid_data()
        data['customer_phone'] = '1' * 20
        form = OrderCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('customer_phone', form.errors)

    def test_shipping_cost_negative(self):
        data = self.get_valid_data()
        data['shipping_cost'] = Decimal('-5.00')
        form = OrderCreateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('shipping_cost', form.errors)

    def test_shipping_cost_zero(self):
        data = self.get_valid_data()
        data['shipping_cost'] = Decimal('0.00')
        form = OrderCreateForm(data=data)
        self.assertTrue(form.is_valid())

    def test_email_optional(self):
        data = self.get_valid_data()
        data['customer_email'] = ''
        form = OrderCreateForm(data=data)
        self.assertTrue(form.is_valid())


# =============================================================================
# TESTS: HU-031 (PARTE) OrderUpdateForm
# =============================================================================

class OrderUpdateFormTest(TestCase):
    """HU-031 (parte): Editar pedido manual (admin)"""

    def setUp(self):
        self.variant = _create_product_variant(stock=10)
        self.order = _create_order()
        _create_order_item(self.order, self.variant, quantity=2)

    def get_valid_data(self):
        return {
            'customer_name': 'Juan Actualizado',
            'customer_phone': '3111234567',
            'customer_email': 'juan_updated@test.com',
            'shipping_address': 'Calle Actualizada 123',
            'delivery_notes': 'Nota actualizada',
            'shipping_cost': Decimal('3.00'),
            'is_paid': False,
            'status': 'pendiente',
            'assigned_delivery_user': None,
        }

    def test_valid_form(self):
        form = OrderUpdateForm(data=self.get_valid_data(), instance=self.order)
        self.assertTrue(form.is_valid(), msg=f"Errores: {form.errors}")

    def test_negative_shipping_cost(self):
        data = self.get_valid_data()
        data['shipping_cost'] = Decimal('-5.00')
        form = OrderUpdateForm(data=data, instance=self.order)
        self.assertFalse(form.is_valid())
        self.assertIn('shipping_cost', form.errors)

    def test_free_shipping_when_subtotal_high(self):
        from apps.orders.constants import FREE_SHIPPING_THRESHOLD
        self.order.subtotal = Decimal(str(FREE_SHIPPING_THRESHOLD))
        self.order.save()
        
        data = self.get_valid_data()
        data['shipping_cost'] = Decimal('5.00')
        form = OrderUpdateForm(data=data, instance=self.order)
        self.assertFalse(form.is_valid())
        self.assertIn('shipping_cost', form.errors)

    def test_invalid_status_transition(self):
        self.order.status = 'pendiente'
        self.order.save()
        
        data = self.get_valid_data()
        data['status'] = 'entregado'
        data['is_paid'] = True
        form = OrderUpdateForm(data=data, instance=self.order)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)

    def test_cannot_unpaid_delivered_order(self):
        self.order.is_paid = True
        self.order.save()
        
        form = OrderUpdateForm(instance=self.order)
        self.assertTrue(form.fields['is_paid'].disabled)
        
        data = self.get_valid_data()
        data['is_paid'] = False
        form = OrderUpdateForm(data=data, instance=self.order)
        self.assertTrue(form.is_valid())
        form.save()
        self.order.refresh_from_db()
        self.assertTrue(self.order.is_paid)

    def test_delivered_order_must_be_paid(self):
        data = self.get_valid_data()
        data['status'] = 'entregado'
        data['is_paid'] = False
        form = OrderUpdateForm(data=data, instance=self.order)
        self.assertFalse(form.is_valid())
        # El error puede estar en status (transición inválida) o en is_paid
        self.assertTrue(
            'status' in form.errors or 'is_paid' in form.errors,
            f"Expected error in 'status' or 'is_paid', got: {form.errors}"
        )


# =============================================================================
# TESTS: HU-029 OrderConfirmForm
# =============================================================================

class OrderConfirmFormTest(TestCase):
    """HU-029: Confirmar pedido"""

    def setUp(self):
        self.variant = _create_product_variant(stock=10)
        self.order = _create_order()
        _create_order_item(self.order, self.variant, quantity=2)

    def test_valid_confirmation(self):
        form = OrderConfirmForm(data={'confirm': True}, order=self.order)
        self.assertTrue(form.is_valid())

    def test_no_items_error(self):
        order = _create_order()
        form = OrderConfirmForm(data={'confirm': True}, order=order)
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors.get('__all__', ''))
        self.assertIn('No se puede confirmar un pedido sin items', error_msg)

    def test_wrong_status_error(self):
        self.order.status = 'confirmado'
        self.order.save()
        form = OrderConfirmForm(data={'confirm': True}, order=self.order)
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors.get('__all__', ''))
        self.assertIn('Solo se pueden confirmar pedidos en estado', error_msg)
        self.assertIn('Confirmado', error_msg)

    def test_insufficient_stock_error(self):
        item = self.order.items.first()
        item.quantity = 20
        item.save()
        form = OrderConfirmForm(data={'confirm': True}, order=self.order)
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors.get('__all__', ''))
        self.assertIn('Stock insuficiente', error_msg)

    def test_confirm_not_checked_error(self):
        form = OrderConfirmForm(data={'confirm': False}, order=self.order)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)

    def test_no_order_specified(self):
        form = OrderConfirmForm(data={'confirm': True})
        self.assertFalse(form.is_valid())
        self.assertIn('Pedido no especificado', str(form.errors.get('__all__', '')))


# =============================================================================
# TESTS: HU-030/035 OrderCancelForm
# =============================================================================

class OrderCancelFormTest(TestCase):
    """HU-030: Cancelar pedido / HU-035: Registrar incidencia"""

    def setUp(self):
        self.order = _create_order()

    def get_valid_data(self):
        return {
            'reason': 'Cliente solicitó cancelación - motivo válido',
            'confirm': True,
        }

    def test_valid_cancellation(self):
        form = OrderCancelForm(data=self.get_valid_data(), order=self.order)
        self.assertTrue(form.is_valid())

    def test_reason_too_short(self):
        data = self.get_valid_data()
        data['reason'] = 'Corto'
        form = OrderCancelForm(data=data, order=self.order)
        self.assertFalse(form.is_valid())
        self.assertIn('reason', form.errors)

    def test_empty_reason(self):
        data = self.get_valid_data()
        data['reason'] = ''
        form = OrderCancelForm(data=data, order=self.order)
        self.assertFalse(form.is_valid())
        self.assertIn('reason', form.errors)

    def test_delivered_order_cannot_be_cancelled(self):
        self.order.status = 'entregado'
        self.order.is_paid = True
        self.order.save()
        form = OrderCancelForm(data=self.get_valid_data(), order=self.order)
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors.get('__all__', ''))
        self.assertIn('No se puede cancelar un pedido ya entregado', error_msg)

    def test_already_cancelled_order_cannot_be_cancelled(self):
        self.order.status = 'cancelado'
        self.order.save()
        form = OrderCancelForm(data=self.get_valid_data(), order=self.order)
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors.get('__all__', ''))
        self.assertIn('Este pedido ya está cancelado.', error_msg)

    def test_confirm_not_checked(self):
        data = self.get_valid_data()
        data['confirm'] = False
        form = OrderCancelForm(data=data, order=self.order)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)

    def test_no_order_specified(self):
        form = OrderCancelForm(data=self.get_valid_data())
        self.assertFalse(form.is_valid())
        self.assertIn('Pedido no especificado', str(form.errors.get('__all__', '')))


# =============================================================================
# TESTS: HU-029 OrderChangeStatusForm
# =============================================================================

class OrderChangeStatusFormTest(TestCase):
    """HU-029: Cambiar estado de pedido"""

    def setUp(self):
        self.order = _create_order()

    def test_valid_transition_pending_to_confirmado(self):
        form = OrderChangeStatusForm(data={'new_status': 'confirmado'}, order=self.order)
        self.assertTrue(form.is_valid())

    def test_valid_transition_confirmado_to_preparando(self):
        self.order.status = 'confirmado'
        self.order.save()
        form = OrderChangeStatusForm(data={'new_status': 'preparando'}, order=self.order)
        self.assertTrue(form.is_valid())

    def test_invalid_transition(self):
        form = OrderChangeStatusForm(data={'new_status': 'entregado'}, order=self.order)
        self.assertFalse(form.is_valid())
        self.assertIn('new_status', form.errors)

    def test_notes_optional(self):
        form = OrderChangeStatusForm(
            data={'new_status': 'confirmado', 'notes': 'Nota de prueba'},
            order=self.order
        )
        self.assertTrue(form.is_valid())

    def test_no_order_specified(self):
        form = OrderChangeStatusForm(data={'new_status': 'confirmado'})
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors.get('__all__', ''))
        self.assertIn('Pedido no especificado.', error_msg)


# =============================================================================
# TESTS: HU-032 OrderAssignDeliveryForm
# =============================================================================

class OrderAssignDeliveryFormTest(TestCase):
    """HU-032: Asignar repartidor"""

    def setUp(self):
        self.delivery_user = _create_delivery_user(username='delivery1')
        self.order = _create_order(status='listo')

    def test_valid_assignment(self):
        form = OrderAssignDeliveryForm(
            data={'delivery_user': self.delivery_user.id, 'confirm': True},
            order=self.order
        )
        self.assertTrue(form.is_valid())

    def test_no_delivery_user_selected(self):
        form = OrderAssignDeliveryForm(
            data={'confirm': True},
            order=self.order
        )
        self.assertFalse(form.is_valid())
        self.assertIn('delivery_user', form.errors)

    def test_confirm_not_checked(self):
        form = OrderAssignDeliveryForm(
            data={'delivery_user': self.delivery_user.id, 'confirm': False},
            order=self.order
        )
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)

    def test_wrong_status_for_assignment(self):
        self.order.status = 'pendiente'
        self.order.save()
        form = OrderAssignDeliveryForm(
            data={'delivery_user': self.delivery_user.id, 'confirm': True},
            order=self.order
        )
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors.get('__all__', ''))
        self.assertIn('Solo se puede asignar repartidor a pedidos en estado', error_msg)
        self.assertIn('Pendiente', error_msg)

    def test_no_order_specified(self):
        form = OrderAssignDeliveryForm(
            data={'delivery_user': self.delivery_user.id, 'confirm': True}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('Pedido no especificado', str(form.errors.get('__all__', '')))


# =============================================================================
# TESTS: HU-034 OrderMarkAsDeliveredForm
# =============================================================================

class OrderMarkAsDeliveredFormTest(TestCase):
    """HU-034: Marcar pedido como pagado/entregado"""

    def setUp(self):
        self.delivery_user = _create_delivery_user(username='delivery1')
        self.order = _create_order(status='en_camino', assigned_delivery_user=self.delivery_user)

    def test_valid_delivery(self):
        form = OrderMarkAsDeliveredForm(data={'confirm': True}, order=self.order)
        self.assertTrue(form.is_valid())

    def test_delivery_evidence_optional(self):
        form = OrderMarkAsDeliveredForm(
            data={'confirm': True, 'delivery_evidence': 'Recibido por Juan'},
            order=self.order
        )
        self.assertTrue(form.is_valid())

    def test_confirm_not_checked(self):
        form = OrderMarkAsDeliveredForm(data={'confirm': False}, order=self.order)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)

    def test_wrong_status_for_delivery(self):
        self.order.status = 'pendiente'
        self.order.save()
        form = OrderMarkAsDeliveredForm(data={'confirm': True}, order=self.order)
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors.get('__all__', ''))
        self.assertIn('Solo se puede entregar pedidos que están', error_msg)
        self.assertIn('Pendiente', error_msg)

    def test_no_delivery_assigned(self):
        self.order.assigned_delivery_user = None
        self.order.save()
        form = OrderMarkAsDeliveredForm(data={'confirm': True}, order=self.order)
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors.get('__all__', ''))
        self.assertIn('repartidor', error_msg.lower())

    def test_no_order_specified(self):
        form = OrderMarkAsDeliveredForm(data={'confirm': True})
        self.assertFalse(form.is_valid())
        self.assertIn('Pedido no especificado', str(form.errors.get('__all__', '')))


# =============================================================================
# TESTS: HU-024 OrderPaymentForm
# =============================================================================

class OrderPaymentFormTest(TestCase):
    """HU-024 (parte): Generar link de pago"""

    def setUp(self):
        self.order = _create_order(status='pendiente', is_paid=False)

    def test_valid_payment_email(self):
        form = OrderPaymentForm(data={'send_email': True, 'send_whatsapp': False}, order=self.order)
        self.assertTrue(form.is_valid())

    def test_valid_payment_whatsapp(self):
        form = OrderPaymentForm(data={'send_email': False, 'send_whatsapp': True}, order=self.order)
        self.assertTrue(form.is_valid())

    def test_valid_payment_both(self):
        form = OrderPaymentForm(data={'send_email': True, 'send_whatsapp': True}, order=self.order)
        self.assertTrue(form.is_valid())

    def test_no_payment_method_selected(self):
        form = OrderPaymentForm(data={'send_email': False, 'send_whatsapp': False}, order=self.order)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_wrong_status_for_payment(self):
        self.order.status = 'confirmado'
        self.order.save()
        form = OrderPaymentForm(data={'send_email': True, 'send_whatsapp': False}, order=self.order)
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors.get('__all__', ''))
        self.assertIn('pendiente', error_msg.lower())

    def test_order_already_paid(self):
        self.order.is_paid = True
        self.order.save()
        form = OrderPaymentForm(data={'send_email': True, 'send_whatsapp': False}, order=self.order)
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors.get('__all__', ''))
        self.assertIn('pagado', error_msg.lower())

    def test_no_email_for_notification(self):
        self.order.customer_email = None
        self.order.save()
        form = OrderPaymentForm(data={'send_email': True, 'send_whatsapp': False}, order=self.order)
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors.get('__all__', ''))
        self.assertIn('email', error_msg.lower())

    def test_notes_optional(self):
        form = OrderPaymentForm(
            data={'send_email': True, 'send_whatsapp': False, 'notify_notes': 'Nota para el cliente'},
            order=self.order
        )
        self.assertTrue(form.is_valid())

    def test_no_order_specified(self):
        form = OrderPaymentForm(data={'send_email': True, 'send_whatsapp': False})
        self.assertFalse(form.is_valid())
        self.assertIn('Pedido no especificado', str(form.errors.get('__all__', '')))


# =============================================================================
# TESTS: HU-031 OrderItemCreateForm
# =============================================================================

class OrderItemCreateFormTest(TestCase):
    """HU-031 (parte): Agregar producto a pedido manual"""

    def setUp(self):
        self.variant = _create_product_variant(stock=10)
        self.order = _create_order()

    def test_valid_item_creation(self):
        form = OrderItemCreateForm(
            data={'variant': self.variant.id, 'quantity': 2},
            order=self.order
        )
        self.assertTrue(form.is_valid())

    def test_quantity_zero(self):
        form = OrderItemCreateForm(
            data={'variant': self.variant.id, 'quantity': 0},
            order=self.order
        )
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    def test_quantity_exceeds_max(self):
        from apps.orders.constants import MAX_QUANTITY_PER_ITEM
        form = OrderItemCreateForm(
            data={'variant': self.variant.id, 'quantity': MAX_QUANTITY_PER_ITEM + 1},
            order=self.order
        )
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    def test_quantity_exceeds_stock(self):
        form = OrderItemCreateForm(
            data={'variant': self.variant.id, 'quantity': 20},
            order=self.order
        )
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    def test_duplicate_product_in_order(self):
        _create_order_item(self.order, self.variant, quantity=1)
        form = OrderItemCreateForm(
            data={'variant': self.variant.id, 'quantity': 2},
            order=self.order
        )
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors.get('__all__', ''))
        self.assertIn('ya existe', error_msg.lower())

    def test_wrong_order_status(self):
        self.order.status = 'entregado'
        self.order.is_paid = True
        self.order.save()
        form = OrderItemCreateForm(
            data={'variant': self.variant.id, 'quantity': 2},
            order=self.order
        )
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors.get('__all__', ''))
        self.assertIn('pendientes o confirmados', error_msg.lower())

    def test_no_order_specified(self):
        form = OrderItemCreateForm(data={'variant': self.variant.id, 'quantity': 2})
        self.assertFalse(form.is_valid())
        self.assertIn('Pedido no especificado', str(form.errors.get('__all__', '')))


# =============================================================================
# TESTS: HU-031 OrderItemUpdateForm
# =============================================================================

class OrderItemUpdateFormTest(TestCase):
    """HU-031 (parte): Modificar cantidad de producto"""

    def setUp(self):
        self.variant = _create_product_variant(stock=10)
        self.order = _create_order()
        self.order_item = _create_order_item(self.order, self.variant, quantity=2)

    def test_valid_quantity_update(self):
        form = OrderItemUpdateForm(data={'quantity': 3}, instance=self.order_item)
        self.assertTrue(form.is_valid())

    def test_quantity_zero(self):
        form = OrderItemUpdateForm(data={'quantity': 0}, instance=self.order_item)
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    def test_quantity_exceeds_max(self):
        from apps.orders.constants import MAX_QUANTITY_PER_ITEM
        form = OrderItemUpdateForm(
            data={'quantity': MAX_QUANTITY_PER_ITEM + 1},
            instance=self.order_item
        )
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    def test_increase_quantity_exceeds_stock(self):
        form = OrderItemUpdateForm(data={'quantity': 15}, instance=self.order_item)
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    def test_decrease_quantity_valid(self):
        form = OrderItemUpdateForm(data={'quantity': 1}, instance=self.order_item)
        self.assertTrue(form.is_valid())

    def test_wrong_order_status(self):
        self.order.status = 'entregado'
        self.order.is_paid = True
        self.order.save()
        form = OrderItemUpdateForm(data={'quantity': 3}, instance=self.order_item)
        self.assertFalse(form.is_valid())
        error_msg = str(form.errors.get('__all__', ''))
        self.assertIn('modificar', error_msg.lower())


# =============================================================================
# TESTS: HU-031 OrderItemDeleteForm
# =============================================================================

class OrderItemDeleteFormTest(TestCase):
    """HU-031 (parte): Eliminar producto de pedido"""

    def setUp(self):
        self.variant = _create_product_variant(stock=10)
        self.order = _create_order()
        self.order_item = _create_order_item(self.order, self.variant, quantity=2)

    def test_valid_deletion(self):
        form = OrderItemDeleteForm(data={'confirm': 'ELIMINAR'}, order_item=self.order_item)
        self.assertTrue(form.is_valid())

    def test_wrong_confirmation(self):
        form = OrderItemDeleteForm(data={'confirm': 'BORRAR'}, order_item=self.order_item)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)

    def test_case_insensitive_confirmation(self):
        form = OrderItemDeleteForm(data={'confirm': 'eliminar'}, order_item=self.order_item)
        self.assertTrue(form.is_valid())

    def test_wrong_order_status(self):
        self.order.status = 'entregado'
        self.order.is_paid = True
        self.order.save()
        form = OrderItemDeleteForm(data={'confirm': 'ELIMINAR'}, order_item=self.order_item)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)
        self.assertIn('Solo se pueden modificar items de pedidos pendientes o confirmados', str(form.errors['confirm']))

    def test_no_order_item_specified(self):
        form = OrderItemDeleteForm(data={'confirm': 'ELIMINAR'})
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)
        self.assertIn('Pedido no especificado.', str(form.errors['confirm']))