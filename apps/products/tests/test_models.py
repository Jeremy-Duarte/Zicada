import pytest
from django.core.exceptions import ValidationError
from apps.orders.models import Order, OrderItem
from decimal import Decimal

@pytest.mark.django_db
class TestProductModel:
    # UT - 017
    def test_prevents_deleting_product_whit_existing_orders(self, order_factory, order_item_factory, product_whit_stock):
        product, variant = product_whit_stock(stock=1, price=Decimal('10000.00'))
        order = order_factory()
        order_item = order_item_factory(order=order, variant=variant)

        with pytest.raises(ValidationError):
            product.delete()

        with pytest.raises(ValidationError):
            product.soft_delete()