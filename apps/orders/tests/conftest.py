import pytest
from apps.orders.models import Order, OrderItem
from decimal import Decimal

@pytest.fixture
def base_order(db, order_factory, order_item_factory, product_with_stock):
    product, variant = product_with_stock(1, Decimal('10000.00'))
    order = order_factory(
        status='pendiente',
        order_number='ZC-TEST',
        customer_name='John Doe',
        customer_phone='3000000000',
        shipping_address="John Doe's House"
    )
    order_item = order_item_factory(
        order=order,
        variant=variant,
        quantity=1,
        price=Decimal('10000.00')
    )
    return product, variant, order, order_item

@pytest.fixture
def cart_request():
    class FakeSession(dict):
        def __init__(self):
            super().__init__()
            self.modified = False
            self.session_key = 'test_session_key'

    class FakeRequest:
        def __init__(self):
            self.session = FakeSession()

    return FakeRequest()
