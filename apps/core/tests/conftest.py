import pytest
from decimal import Decimal
from apps.products.models import Product

@pytest.fixture
def product_with_state(db, ifactory):
    def _create_product(status):
        return ifactory.create(
            Product,
            price=Decimal('1'),
            is_active=status
        )
    return _create_product