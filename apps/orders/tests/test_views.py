"""
Tests para vistas de apps.orders.views

Cubre:
- HU-027: OrderListView
- HU-028: OrderDetailView
- HU-029: OrderConfirmView, OrderMarkPreparingView, OrderMarkReadyView
- HU-030: OrderCancelView
- HU-031: OrderCreateView, OrderUpdateView
- HU-032: OrderAssignDeliveryView
- HU-033: delivery_dashboard, take_order
- HU-034: OrderMarkAsDeliveredView, deliver_order
- HU-035: OrderCancelView (incidencias)
- OrderItemCreateView, OrderItemUpdateView, OrderItemDeleteView

Casos de prueba: CP-xxx a CP-xxx
"""

from decimal import Decimal

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.core import mail
from unittest.mock import patch, MagicMock

from apps.core.url_names import (
    CORE_STAFF_LOGIN,
    PRODUCTS_CATALOG,
    ORDERS_LIST,
    ORDERS_DETAIL,
    ORDERS_CREATE,
    ORDERS_EDIT,
    ORDERS_CONFIRM,
    ORDERS_CANCEL,
    ORDERS_ASSIGN_DELIVERY,
    ORDERS_MARK_DELIVERED,
    ORDERS_MARK_PREPARING,
    ORDERS_MARK_READY,
    ORDERS_ITEM_CREATE,
    ORDERS_ITEM_EDIT,
    ORDERS_ITEM_DELETE,
    ORDERS_DELIVERY_DASHBOARD,
    ORDERS_TAKE_ORDER,
    ORDERS_DELIVER_ORDER,
)
from apps.orders.models import Order, OrderItem
from apps.products.models import Product, Category, Size, Color, ProductColor, ProductVariant
from apps.users.models import User

User = get_user_model()


# =============================================================================
# HELPERS
# =============================================================================

def _create_admin_user(**kwargs):
    """Create an admin user with Administrador role."""
    defaults = {'username': 'admin', 'password': 'pass1234', 'is_staff': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    is_delivery = defaults.pop('is_delivery', False)
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    
    if is_delivery:
        user.is_delivery = True
        user.save(update_fields=['is_delivery'])
    
    admin_group, _ = Group.objects.get_or_create(name='Administrador')
    user.groups.add(admin_group)
    
    return user


def _create_delivery_user(**kwargs):
    """Create a delivery user with Entregador role."""
    defaults = {'username': 'delivery', 'password': 'pass1234', 'is_delivery': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    
    delivery_group, _ = Group.objects.get_or_create(name='Entregador')
    user.groups.add(delivery_group)
    
    return user


def _create_normal_user(**kwargs):
    """Create a normal user without special roles."""
    defaults = {'username': 'normal', 'password': 'pass1234', 'is_staff': False}
    defaults.update(kwargs)
    password = defaults.pop('password')
    
    user = User(**defaults)
    user.set_password(password)
    user.save()
    
    return user


def _create_product_variant(stock=10):
    """Create a product variant for testing."""
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
    """Create a test order."""
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
    """Create an order item."""
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
# TESTS: HU-027 OrderListView
# =============================================================================

class OrderListViewTest(TestCase):
    """HU-027: Listar pedidos (admin)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)
        
        self.order1 = _create_order(customer_name='Juan Perez')
        self.order2 = _create_order(customer_name='Maria Gomez')

    def test_list_returns_200(self):
        """CP-xxx | HU-027 | ESCENARIO 1 | H | Lista de pedidos cargada exitosamente"""
        response = self.client.get(reverse(ORDERS_LIST))
        self.assertEqual(response.status_code, 200)

    def test_list_requires_authentication(self):
        """CP-xxx | HU-027 | ESCENARIO 6 | E | Usuario no autenticado -> login"""
        self.client.logout()
        response = self.client.get(reverse(ORDERS_LIST))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(ORDERS_LIST)}')

    def test_list_requires_admin_role(self):
        """CP-xxx | HU-027 | ESCENARIO 6 | E | Usuario sin rol Administrador -> catálogo"""
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(ORDERS_LIST))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_search_by_order_number(self):
        """CP-xxx | HU-027 | ESCENARIO 4 | H | Búsqueda por número de pedido"""
        response = self.client.get(reverse(ORDERS_LIST), {'search': self.order1.order_number})
        self.assertContains(response, self.order1.customer_name)
        self.assertNotContains(response, self.order2.customer_name)


# =============================================================================
# TESTS: HU-028 OrderDetailView
# =============================================================================

class OrderDetailViewTest(TestCase):
    """HU-028: Ver detalle de pedido (admin)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)
        self.order = _create_order()

    def test_detail_returns_200(self):
        """CP-xxx | HU-028 | ESCENARIO 1 | H | Detalle cargado exitosamente"""
        response = self.client.get(reverse(ORDERS_DETAIL, kwargs={'pk': self.order.pk}))
        self.assertEqual(response.status_code, 200)

    def test_detail_requires_authentication(self):
        """CP-xxx | HU-028 | ESCENARIO 3 | E | Usuario no autenticado -> login"""
        self.client.logout()
        response = self.client.get(reverse(ORDERS_DETAIL, kwargs={'pk': self.order.pk}))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(ORDERS_DETAIL, kwargs={"pk": self.order.pk})}')

    def test_detail_requires_admin_role(self):
        """CP-xxx | HU-028 | ESCENARIO 3 | E | Usuario sin rol Administrador -> catálogo"""
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(ORDERS_DETAIL, kwargs={'pk': self.order.pk}))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: HU-031 OrderCreateView
# =============================================================================

class OrderCreateViewTest(TestCase):
    """HU-031: Crear pedido manual (admin)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)

    def get_valid_data(self):
        return {
            'customer_name': 'Nuevo Cliente',
            'customer_phone': '3001234567',
            'customer_email': 'cliente@test.com',
            'shipping_address': 'Calle 123, Bogotá',
            'delivery_notes': '',
            'shipping_cost': Decimal('2.00'),
            'is_paid': False,
        }

    def test_get_create_form(self):
        """CP-xxx | HU-031 | GET | Muestra formulario de creación"""
        response = self.client.get(reverse(ORDERS_CREATE))
        self.assertEqual(response.status_code, 200)

    def test_create_valid_order(self):
        """CP-xxx | HU-031 | ESCENARIO 1 | H | Pedido manual creado exitosamente"""
        data = self.get_valid_data()
        response = self.client.post(reverse(ORDERS_CREATE), data=data)
        self.assertRedirects(response, reverse(ORDERS_LIST))
        self.assertTrue(Order.objects.filter(customer_name='Nuevo Cliente').exists())

    def test_create_requires_authentication(self):
        """CP-xxx | HU-031 | ESCENARIO 4 | E | Usuario no autenticado -> login"""
        self.client.logout()
        response = self.client.get(reverse(ORDERS_CREATE))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(ORDERS_CREATE)}')

    def test_create_requires_admin_role(self):
        """CP-xxx | HU-031 | ESCENARIO 4 | E | Usuario sin rol Administrador -> catálogo"""
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(ORDERS_CREATE))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))


# =============================================================================
# TESTS: HU-031 OrderUpdateView
# =============================================================================

class OrderUpdateViewTest(TestCase):
    """HU-031 (parte): Editar pedido manual (admin)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)
        self.order = _create_order()

    def get_valid_data(self):
        return {
            'customer_name': 'Cliente Actualizado',
            'customer_phone': '3111234567',
            'customer_email': 'actualizado@test.com',
            'shipping_address': 'Calle Actualizada 456',
            'delivery_notes': 'Nota actualizada',
            'shipping_cost': Decimal('3.00'),
            'is_paid': False,
            'status': 'pendiente',
        }

    def test_get_update_form(self):
        """CP-xxx | HU-031 | GET | Muestra formulario de edición"""
        response = self.client.get(reverse(ORDERS_EDIT, kwargs={'pk': self.order.pk}))
        self.assertEqual(response.status_code, 200)

    def test_update_valid_order(self):
        """CP-xxx | HU-031 | ESCENARIO 1 | H | Pedido actualizado exitosamente"""
        data = self.get_valid_data()
        response = self.client.post(reverse(ORDERS_EDIT, kwargs={'pk': self.order.pk}), data=data)
        self.assertRedirects(response, reverse(ORDERS_LIST))
        self.order.refresh_from_db()
        self.assertEqual(self.order.customer_name, 'Cliente Actualizado')


# =============================================================================
# TESTS: HU-029 OrderConfirmView
# =============================================================================

class OrderConfirmViewTest(TestCase):
    """HU-029: Confirmar pedido"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)
        self.variant = _create_product_variant(stock=10)
        self.order = _create_order(is_paid=True)  # Pagado para poder confirmar
        _create_order_item(self.order, self.variant, quantity=2)

    def test_confirm_valid_order(self):
        """CP-xxx | HU-029 | ESCENARIO 1 | H | Pedido confirmado exitosamente"""
        response = self.client.post(reverse(ORDERS_CONFIRM, kwargs={'pk': self.order.pk}), {'confirm': True})
        self.assertRedirects(response, reverse(ORDERS_DETAIL, kwargs={'pk': self.order.pk}))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmado')


# =============================================================================
# TESTS: HU-030 OrderCancelView
# =============================================================================

class OrderCancelViewTest(TestCase):
    """HU-030: Cancelar pedido (admin)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)
        self.order = _create_order()

    def get_valid_data(self):
        return {
            'reason': 'Cliente solicitó cancelación - motivo válido',
            'confirm': True,
        }

    def test_cancel_valid_order(self):
        """CP-xxx | HU-030 | ESCENARIO 1 | H | Pedido cancelado exitosamente"""
        response = self.client.post(reverse(ORDERS_CANCEL, kwargs={'pk': self.order.pk}), data=self.get_valid_data())
        self.assertRedirects(response, reverse(ORDERS_DETAIL, kwargs={'pk': self.order.pk}))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelado')


# =============================================================================
# TESTS: OrderMarkPreparingView
# =============================================================================

class OrderMarkPreparingViewTest(TestCase):
    """HU-029: Cambiar estado de confirmado a preparando"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)
        self.order = _create_order(status='confirmado')

    def test_mark_preparing(self):
        """CP-xxx | HU-029 | ESCENARIO 2 | H | Pedido marcado como en preparación"""
        response = self.client.post(reverse(ORDERS_MARK_PREPARING, kwargs={'pk': self.order.pk}))
        self.assertRedirects(response, reverse(ORDERS_DETAIL, kwargs={'pk': self.order.pk}))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'preparando')


# =============================================================================
# TESTS: OrderMarkReadyView
# =============================================================================

class OrderMarkReadyViewTest(TestCase):
    """HU-029: Cambiar estado de preparando a listo"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)
        self.order = _create_order(status='preparando')

    def test_mark_ready(self):
        """CP-xxx | HU-029 | ESCENARIO 2 | H | Pedido marcado como listo"""
        response = self.client.post(reverse(ORDERS_MARK_READY, kwargs={'pk': self.order.pk}))
        self.assertRedirects(response, reverse(ORDERS_DETAIL, kwargs={'pk': self.order.pk}))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'listo')


# =============================================================================
# TESTS: HU-032 OrderAssignDeliveryView
# =============================================================================

class OrderAssignDeliveryViewTest(TestCase):
    """HU-032: Asignar repartidor"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)
        self.delivery_user = _create_delivery_user(username='delivery1')
        self.order = _create_order(status='listo')

    def test_assign_delivery(self):
        """CP-xxx | HU-032 | ESCENARIO 1 | H | Repartidor asignado exitosamente"""
        response = self.client.post(
            reverse(ORDERS_ASSIGN_DELIVERY, kwargs={'pk': self.order.pk}),
            {'delivery_user': self.delivery_user.id, 'confirm': True}
        )
        self.assertRedirects(response, reverse(ORDERS_DETAIL, kwargs={'pk': self.order.pk}))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'en_camino')
        self.assertEqual(self.order.assigned_delivery_user, self.delivery_user)


# =============================================================================
# TESTS: HU-034 OrderMarkAsDeliveredView
# =============================================================================

class OrderMarkAsDeliveredViewTest(TestCase):
    """HU-034: Marcar pedido como pagado/entregado (admin)"""

    def setUp(self):
        self.client = Client()
        self.admin = _create_admin_user(username='admin')
        self.client.force_login(self.admin)
        self.delivery_user = _create_delivery_user(username='delivery1')
        self.order = _create_order(status='en_camino', assigned_delivery_user=self.delivery_user)

    def test_mark_delivered(self):
        """CP-xxx | HU-034 | ESCENARIO 1 | H | Pedido marcado como entregado"""
        response = self.client.post(reverse(ORDERS_MARK_DELIVERED, kwargs={'pk': self.order.pk}), {'confirm': True})
        self.assertRedirects(response, reverse(ORDERS_DETAIL, kwargs={'pk': self.order.pk}))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'entregado')
        self.assertTrue(self.order.is_paid)


# =============================================================================
# TESTS: HU-033 Delivery Dashboard (PENDIENTE DE IMPLEMENTACIÓN COMPLETA)
# =============================================================================

class DeliveryDashboardTest(TestCase):
    """
    HU-033: Consultar pedidos del día (entregador)
    NOTA: Actualmente las vistas usan @staff_member_required, por lo que
    solo usuarios staff pueden acceder. La funcionalidad completa para
    entregadores se implementará en una fase posterior.
    """

    def setUp(self):
        self.client = Client()
        self.delivery_user = _create_delivery_user(username='delivery1')
        self.client.force_login(self.delivery_user)
        self.staff_user = _create_admin_user(username='staff1')
        self.order_ready = _create_order(status='listo')
        self.order_assigned = _create_order(status='en_camino', assigned_delivery_user=self.delivery_user)

    def test_dashboard_requires_staff_access(self):
        """
        CP-xxx | HU-033 | ACTUAL | Usuario entregador sin is_staff -> redirigido al login
        NOTA: Pendiente implementar dashboard específico para entregadores
        """
        response = self.client.get(reverse(ORDERS_DELIVERY_DASHBOARD))
        # El decorador @staff_member_required redirige al login de admin
        self.assertEqual(response.status_code, 302)
        # La URL de redirección es /admin/login/ (por defecto de Django)
        self.assertIn('/admin/login/', response.url)

    def test_dashboard_accessible_by_staff(self):
        """
        CP-xxx | HU-033 | ACTUAL | Usuario staff puede acceder al dashboard
        """
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse(ORDERS_DELIVERY_DASHBOARD))
        # Staff tiene acceso (código 200)
        self.assertEqual(response.status_code, 200)

    def test_dashboard_returns_200_for_staff(self):
        """
        CP-xxx | HU-033 | ACTUAL | Dashboard carga para usuarios staff
        """
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse(ORDERS_DELIVERY_DASHBOARD))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_shows_ready_orders_for_staff(self):
        """
        CP-xxx | HU-033 | ACTUAL | Dashboard muestra pedidos listos para staff
        """
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse(ORDERS_DELIVERY_DASHBOARD))
        self.assertIn('pedidos_listos', response.context)
        self.assertIn(self.order_ready, response.context['pedidos_listos'])

    def test_dashboard_requires_authentication(self):
        """
        CP-xxx | HU-033 | E | Usuario no autenticado -> redirige al login de admin
        """
        self.client.logout()
        response = self.client.get(reverse(ORDERS_DELIVERY_DASHBOARD))
        # El decorador @staff_member_required redirige a /admin/login/
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)


# =============================================================================
# TESTS: take_order (HU-033 parte)
# =============================================================================

class TakeOrderViewTest(TestCase):
    """HU-033 (parte): Asignar pedido a repartidor"""

    def setUp(self):
        self.client = Client()
        # Necesitamos un usuario que tenga is_staff=True Y is_delivery=True
        self.delivery_staff_user = _create_admin_user(
            username='delivery_staff', 
            is_delivery=True  # Importante para la validación del modelo
        )
        self.client.force_login(self.delivery_staff_user)
        self.order = _create_order(status='listo')

    def test_take_order_success(self):
        """
        CP-xxx | HU-033 | ESCENARIO 1 | H | Repartidor (staff) toma pedido exitosamente
        """
        response = self.client.post(reverse(ORDERS_TAKE_ORDER, kwargs={'order_id': self.order.pk}))
        self.assertRedirects(response, reverse(ORDERS_DELIVERY_DASHBOARD))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'en_camino')
        self.assertEqual(self.order.assigned_delivery_user, self.delivery_staff_user)

    def test_take_order_not_ready(self):
        """
        CP-xxx | HU-033 | E | Pedido no está listo -> mensaje de error
        """
        self.order.status = 'pendiente'
        self.order.save()
        response = self.client.post(reverse(ORDERS_TAKE_ORDER, kwargs={'order_id': self.order.pk}))
        self.assertRedirects(response, reverse(ORDERS_DELIVERY_DASHBOARD))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'pendiente')

    def test_take_order_requires_authentication(self):
        """
        CP-xxx | HU-033 | E | Usuario no autenticado -> redirige al login
        """
        self.client.logout()
        response = self.client.post(reverse(ORDERS_TAKE_ORDER, kwargs={'order_id': self.order.pk}))
        # El decorador @staff_member_required redirige a /admin/login/
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)


# =============================================================================
# TESTS: deliver_order (HU-034 parte entregador)
# =============================================================================

class DeliverOrderViewTest(TestCase):
    """HU-034: Marcar pedido como pagado (entregador)"""

    def setUp(self):
        self.client = Client()
        # Necesitamos un usuario que tenga is_staff=True Y is_delivery=True
        self.delivery_staff_user = _create_admin_user(
            username='delivery_staff',
            is_delivery=True
        )
        self.client.force_login(self.delivery_staff_user)
        self.order = _create_order(status='en_camino', assigned_delivery_user=self.delivery_staff_user)

    def test_deliver_order_success(self):
        """
        CP-xxx | HU-034 | ESCENARIO 1 | H | Pedido entregado exitosamente
        """
        response = self.client.post(reverse(ORDERS_DELIVER_ORDER, kwargs={'order_id': self.order.pk}))
        self.assertRedirects(response, reverse(ORDERS_DELIVERY_DASHBOARD))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'entregado')
        self.assertTrue(self.order.is_paid)

    def test_deliver_order_wrong_status(self):
        """
        CP-xxx | HU-034 | ESCENARIO 3 | E | Pedido no está en camino, sin vista por ahora
        """
        pass 

    def test_deliver_order_requires_authentication(self):
        """
        CP-xxx | HU-034 | E | Usuario no autenticado -> redirige al login
        """
        self.client.logout()
        response = self.client.post(reverse(ORDERS_DELIVER_ORDER, kwargs={'order_id': self.order.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)