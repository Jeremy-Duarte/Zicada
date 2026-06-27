# Aqui se almacenaran los fixtures para pruebas unitarias (los fixtures representan los prerequisitos repetitivos para cada prueba)
import pytest
from decimal import Decimal
from apps.products.models import Product, ProductVariant, ProductColor, Color, Size

@pytest.fixture
def base_product(db, ifactory):
    return ifactory.create(
        Product,
        name='Test Product',
        price=Decimal('10000.00'),
        is_active=True
    )

@pytest.fixture
def product_whit_price(db, ifactory):
    def _create_product(precio=Decimal('10000.00')):
        return ifactory.create(
            Product,
            name=f'Procucto {precio}',
            price=precio,
            is_active=True
        )
    return _create_product

@pytest.fixture
def product_whit_stock(db, ifactory):
    def _create_product(stock=10, price=Decimal('10000.00')):
        product = ifactory.create(
            Product,
            name='Product whit Stock',
            is_active=True,
            price=price
        )
        product_color = ifactory.create(
            ProductColor,
            product=product,
            color=ifactory.create(Color)
        )
        variant = ifactory.create(
            ProductVariant,
            product=product,
            product_color=product_color,
            size=ifactory.create(Size),
            stock=stock
        )
        return product, variant
    return _create_product