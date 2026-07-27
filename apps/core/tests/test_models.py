import pytest
from apps.products.models import Product

@pytest.mark.django_db
class TestActiveManager:
    # UT - 001
    def test_returns_active_objects(self, product_with_state):
        product_active = product_with_state(True)
        product_inactive = product_with_state(False)
        result = Product.objects.all()

        assert product_active in result
        assert product_inactive not in result
        assert result.count() == 1
    # UT - 002
    def test_returns_filtered_objects(self, product_with_state):
        product_active = product_with_state(True)
        product_inactive = product_with_state(False)
        result = Product.all_objects.all()

        assert product_active in result
        assert product_inactive in result
        assert result.count() == 2

@pytest.mark.django_db
class TestBaseAuditModel:
    # UT - 003
    def test_models_can_be_softdeleted(self, base_product):
        product = base_product
        product.soft_delete()

        assert product.is_active == False
        assert product.deleted_at is not None

    #UT - 004
    def test_softdeleted_models_can_be_restored(self, base_product):
        product = base_product
        product.soft_delete()
        product.restore()

        assert product.is_active == True
        assert product.deleted_at is None