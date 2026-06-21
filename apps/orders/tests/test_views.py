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
    defaults = {'username': 'normal', 'password': 'pass1234', 'is_staff': False}
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

    # UT-239: HU-027 CA-001 - Lista de pedidos cargada exitosamente
    def test_list_returns_200(self):
        response = self.client.get(reverse(ORDERS_LIST))
        self.assertEqual(response.status_code, 200)

    # UT-240: HU-027 CA-005 - Usuario no autenticado redirige a login
    def test_list_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(ORDERS_LIST))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(ORDERS_LIST)}')

    # UT-241: HU-027 CA-005 - Usuario sin rol Administrador redirige a catálogo
    def test_list_requires_admin_role(self):
        normal_user = _create_normal_user(username='normal')
        self.client.force_login(normal_user)
        response = self.client.get(reverse(ORDERS_LIST))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    # UT-242: HU-027 CA-004 - Búsqueda por número de pedido
    def test_search_by_order_number(self):
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

    # UT-243: HU-028 CA-001 - Detalle cargado exitosamente
    def test_detail_returns_200(self):
        response = self.client.get(reverse(ORDERS_DETAIL, kwargs={'pk': self.order.pk}))
        self.assertEqual(response.status_code, 200)

    # UT-244: HU-028 CA-002 - Usuario no autenticado redirige a login
    def test_detail_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(ORDERS_DETAIL, kwargs={'pk': self.order.pk}))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(ORDERS_DETAIL, kwargs={"pk": self.order.pk})}')

    # UT-245: HU-028 CA-002 - Usuario sin rol Administrador redirige a catálogo
    def test_detail_requires_admin_role(self):
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

    # UT-246: HU-031 - Muestra formulario de creación
    def test_get_create_form(self):
        response = self.client.get(reverse(ORDERS_CREATE))
        self.assertEqual(response.status_code, 200)

    # UT-247: HU-031 CA-001 - Pedido manual creado exitosamente
    def test_create_valid_order(self):
        data = self.get_valid_data()
        response = self.client.post(reverse(ORDERS_CREATE), data=data)
        self.assertRedirects(response, reverse(ORDERS_LIST))
        self.assertTrue(Order.objects.filter(customer_name='Nuevo Cliente').exists())

    # UT-248: HU-031 CA-004 - Usuario no autenticado redirige a login
    def test_create_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(ORDERS_CREATE))
        self.assertRedirects(response, f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(ORDERS_CREATE)}')

    # UT-249: HU-031 CA-004 - Usuario sin rol Administrador redirige a catálogo
    def test_create_requires_admin_role(self):
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

    # UT-250: HU-031 - Muestra formulario de edición
    def test_get_update_form(self):
        response = self.client.get(reverse(ORDERS_EDIT, kwargs={'pk': self.order.pk}))
        self.assertEqual(response.status_code, 200)

    # UT-251: HU-031 CA-001 - Pedido actualizado exitosamente
    def test_update_valid_order(self):
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
        self.order = _create_order(is_paid=True)
        _create_order_item(self.order, self.variant, quantity=2)

    # UT-252: HU-029 CA-001 - Pedido confirmado exitosamente
    def test_confirm_valid_order(self):
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

    # UT-253: HU-030 CA-001 - Pedido cancelado exitosamente
    def test_cancel_valid_order(self):
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

    # UT-254: HU-029 CA-002 - Pedido marcado como en preparación
    def test_mark_preparing(self):
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

    # UT-255: HU-029 CA-002 - Pedido marcado como listo
    def test_mark_ready(self):
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

    # UT-256: HU-032 CA-001 - Repartidor asignado exitosamente
    def test_assign_delivery(self):
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

    # UT-257: HU-034 CA-001 - Pedido marcado como entregado
    def test_mark_delivered(self):
        response = self.client.post(reverse(ORDERS_MARK_DELIVERED, kwargs={'pk': self.order.pk}), {'confirm': True})
        self.assertRedirects(response, reverse(ORDERS_DETAIL, kwargs={'pk': self.order.pk}))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'entregado')
        self.assertTrue(self.order.is_paid)


# =============================================================================
# TESTS: HU-033 Delivery Dashboard
# =============================================================================

class DeliveryDashboardTest(TestCase):
    """HU-033: Consultar pedidos del día (entregador)"""

    def setUp(self):
        self.client = Client()
        self.delivery_user = _create_delivery_user(username='delivery1')
        self.client.force_login(self.delivery_user)
        self.staff_user = _create_admin_user(username='staff1')
        self.order_ready = _create_order(status='listo')
        self.order_assigned = _create_order(status='en_camino', assigned_delivery_user=self.delivery_user)

    # UT-258: HU-033 - Usuario entregador sin is_staff redirigido
    def test_dashboard_requires_staff_access(self):
        response = self.client.get(reverse(ORDERS_DELIVERY_DASHBOARD))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    # UT-259: HU-033 - Usuario staff puede acceder
    def test_dashboard_accessible_by_staff(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse(ORDERS_DELIVERY_DASHBOARD))
        self.assertEqual(response.status_code, 200)

    # UT-260: HU-033 CA-001 - Dashboard carga para usuarios staff
    def test_dashboard_returns_200_for_staff(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse(ORDERS_DELIVERY_DASHBOARD))
        self.assertEqual(response.status_code, 200)

    # UT-261: HU-033 CA-001 - Dashboard muestra pedidos listos para staff
    def test_dashboard_shows_ready_orders_for_staff(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse(ORDERS_DELIVERY_DASHBOARD))
        self.assertIn('pedidos_listos', response.context)
        self.assertIn(self.order_ready, response.context['pedidos_listos'])

    # UT-262: HU-033 - Usuario no autenticado redirige a login
    def test_dashboard_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(ORDERS_DELIVERY_DASHBOARD))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)


# =============================================================================
# TESTS: take_order (HU-033 parte)
# =============================================================================

class TakeOrderViewTest(TestCase):
    """HU-033 (parte): Asignar pedido a repartidor"""

    def setUp(self):
        self.client = Client()
        self.delivery_staff_user = _create_admin_user(
            username='delivery_staff', 
            is_delivery=True
        )
        self.client.force_login(self.delivery_staff_user)
        self.order = _create_order(status='listo')

    # UT-263: HU-033 CA-001 - Repartidor (staff) toma pedido exitosamente
    def test_take_order_success(self):
        response = self.client.post(reverse(ORDERS_TAKE_ORDER, kwargs={'order_id': self.order.pk}))
        self.assertRedirects(response, reverse(ORDERS_DELIVERY_DASHBOARD))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'en_camino')
        self.assertEqual(self.order.assigned_delivery_user, self.delivery_staff_user)

    # UT-264: HU-033 - Pedido no está listo muestra error
    def test_take_order_not_ready(self):
        self.order.status = 'pendiente'
        self.order.save()
        response = self.client.post(reverse(ORDERS_TAKE_ORDER, kwargs={'order_id': self.order.pk}))
        self.assertRedirects(response, reverse(ORDERS_DELIVERY_DASHBOARD))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'pendiente')

    # UT-265: HU-033 - Usuario no autenticado redirige a login
    def test_take_order_requires_authentication(self):
        self.client.logout()
        response = self.client.post(reverse(ORDERS_TAKE_ORDER, kwargs={'order_id': self.order.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)


# =============================================================================
# TESTS: deliver_order (HU-034 parte entregador)
# =============================================================================

class DeliverOrderViewTest(TestCase):
    """HU-034: Marcar pedido como pagado (entregador)"""

    def setUp(self):
        self.client = Client()
        self.delivery_staff_user = _create_admin_user(
            username='delivery_staff',
            is_delivery=True
        )
        self.client.force_login(self.delivery_staff_user)
        self.order = _create_order(status='en_camino', assigned_delivery_user=self.delivery_staff_user)

    # UT-266: HU-034 CA-001 - Pedido entregado exitosamente
    def test_deliver_order_success(self):
        response = self.client.post(reverse(ORDERS_DELIVER_ORDER, kwargs={'order_id': self.order.pk}))
        self.assertRedirects(response, reverse(ORDERS_DELIVERY_DASHBOARD))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'entregado')
        self.assertTrue(self.order.is_paid)

    # UT-267: HU-034 - Usuario no autenticado redirige a login
    def test_deliver_order_requires_authentication(self):
        self.client.logout()
        response = self.client.post(reverse(ORDERS_DELIVER_ORDER, kwargs={'order_id': self.order.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)