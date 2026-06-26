# Aqui se almacenaran los fixtures para pruebas unitarias (los fixtures representan los prerequisitos repetitivos para cada prueba)
import pytest
from decimal import Decimal

@pytest.fixture
def base_product(db, ifactory):
    return ifactory.products.product.create(
        name='Test Product',
        price=Decimal('10000.00'),
        is_active=True
    )

@pytest.fixture
def product_whit_price(db, ifactory):
    def _create_product(precio=Decimal('10000.00')):
        return ifactory.products.product.create(
            name=f'Procucto {precio}',
            price=precio,
            is_active=True
        )
    return _create_product

@pytest.fixture
def product_whit_stock(db, ifactory):
    def _create_product(stock=10):
        product = ifactory.products.product.create(
            name='Product whit Stock',
            is_active=True
        )
        variant = ifactory.products.productvariant.create(
            product=product,
            stock=stock
        )
        return product, variant
    return _create_product