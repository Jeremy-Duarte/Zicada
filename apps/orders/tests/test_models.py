import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from apps.orders.models import Order, OrderItem
from apps.orders.cart import Cart

@pytest.mark.django_db
class TestOrderModel:
    # UT - 005
    def test_check_flow_of_state_machine(self, base_order):
        product, variant, order, order_item = base_order
        order.confirm()
        order.mark_as_preparing()
        order.mark_as_ready()

        assert order.status == 'listo'

    # UT - 006
    def test_flow_breaks_when_states_are_not_followed(self, base_order):
        product, variant, order, order_item = base_order
        with pytest.raises(ValidationError):
            order.mark_as_ready()
        assert order.status == 'pendiente'

        with pytest.raises(ValidationError):
            order.mark_as_preparing()
        assert order.status == 'pendiente'
        
        order.confirm()
        assert order.status == 'confirmado'

    # UT - 007
    def test_shipping_cost_is_calculated(self, order_factory, order_item_factory, product_whit_stock):
        product, variant = product_whit_stock(stock=1, price=Decimal('100000.00'))
        order = order_factory()
        order_item = order_item_factory(order=order, variant=variant, price=Decimal('100000.00'))
        order.refresh_from_db()
        assert order.shipping_cost == Decimal('10000.00')
        assert order.total_amount == Decimal('110000.00')

    # UT - 008
    def test_whitout_shipping_cost(self, order_factory, order_item_factory, product_whit_stock):
        product, variant = product_whit_stock(stock=1, price=Decimal('160000.00'))
        order = order_factory()
        order_item = order_item_factory(order=order, variant=variant, price=Decimal('160000.00'))
        order.refresh_from_db()
        assert order.shipping_cost == Decimal('0.00')
        assert order.total_amount == Decimal('160000.00')

    # UT - 009
    def test_prevents_double_purchase_of_last_item(self, order_factory, order_item_factory, product_whit_stock):
        product, variant = product_whit_stock(stock=1, price=Decimal('10000.00'))
        
        order1 = order_factory()
        order_item1 = order_item_factory(order=order1, variant=variant)
        
        order2 = order_factory()
        order_item2 = order_item_factory(order=order2, variant=variant)
        
        order1.confirm()
        assert order1.status == 'confirmado'
        
        variant.refresh_from_db()
        assert variant.stock == 0
        
        with pytest.raises(ValidationError):
            order2.confirm()

@pytest.mark.django_db
class TestOrderItemModel:
    # UT - 010
    def test_stock_reduces_at_confirming_order(self, order_factory, order_item_factory, product_whit_stock):
        product, variant = product_whit_stock(stock=5, price=Decimal('10000.00'))
        order = order_factory()
        order_item = order_item_factory(order=order, variant=variant, quantity=2)
        
        variant.refresh_from_db()
        assert variant.stock == 5
        
        order.confirm()
        
        variant.refresh_from_db()
        assert variant.stock == 3

    # UT - 011
    def test_product_snapshots_are_saved(self, order_factory, product_whit_stock):
        product, variant = product_whit_stock(stock=3, price=Decimal('15000.00'))
        order = order_factory()
        
        order_item = OrderItem.objects.create(
            order=order,
            variant=variant,
            quantity=1
        )
        
        assert order_item.product_name_snapshot == product.name
        assert order_item.size_snapshot == variant.size.name
        assert order_item.unit_price == product.price
        assert order_item.stock_snapshot == 3

@pytest.mark.django_db
class TestCartModel:
    # UT - 012
    def test_product_added(self, cart_request, product_whit_stock):
        product, variant = product_whit_stock(stock=1, price=Decimal('10000.00'))
        cart = Cart(cart_request)
        
        cart.add(variant_id=variant.id, quantity=1)
        
        assert not cart.is_empty()
        assert cart.get_total_items() == 1
        assert cart.get_item(variant.id) is not None
        assert cart.get_item(variant.id)['product_name'] == product.name

    # UT - 013
    def test_product_deleted(self, cart_request, product_whit_stock):
        product, variant = product_whit_stock(stock=1, price=Decimal('10000.00'))
        cart = Cart(cart_request)
        
        cart.add(variant_id=variant.id, quantity=1)
        assert not cart.is_empty()
        
        cart.remove(variant_id=variant.id)
        
        assert cart.is_empty()
        assert cart.get_item(variant.id) is None

    # UT - 014
    def test_fails_at_adding_product_not_available(self, cart_request, product_whit_stock):
        product, variant = product_whit_stock(stock=1, price=Decimal('10000.00'))
        cart = Cart(cart_request)
        
        cart.add(variant_id=variant.id, quantity=1)
        
        with pytest.raises(ValidationError):
            cart.add(variant_id=variant.id, quantity=1)

    # UT - 015
    def test_total_is_calculated(self, cart_request, product_whit_stock):
        product, variant = product_whit_stock(stock=2, price=Decimal('90000.00'))
        cart = Cart(cart_request)
        
        cart.add(variant_id=variant.id, quantity=1)
        
        assert cart.get_subtotal() == Decimal('90000.00')
        assert cart.get_shipping_cost() == Decimal('10000.00')
        assert cart.get_total() == Decimal('100000.00')

    # UT - 016
    def test_product_is_converted_in_order_item(self, order_factory, cart_request, product_whit_stock):
        product, variant = product_whit_stock(stock=2, price=Decimal('90000.00'))
        cart = Cart(cart_request)
        
        cart.add(variant_id=variant.id, quantity=1)
        
        order = order_factory()
        
        order_items = cart.to_order_items(order)
        
        assert len(order_items) == 1
        order_item = order_items[0]
        assert order_item.order == order
        assert order_item.variant == variant
        assert order_item.quantity == 1
        assert order_item.unit_price == Decimal('90000.00')
        assert order_item.product_name_snapshot == product.name
        
        assert cart.is_empty()