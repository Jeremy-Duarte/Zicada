import pytest

class TestOrderModel:
    # UT - 005
    def test_check_flow_of_state_machine():
        pass

    # UT - 006
    def test_flow_breaks_when_states_are_not_followed():
        pass

    # UT - 007
    def test_shipping_cost_is_calculated():
        pass

    # UT - 008
    def test_whitout_shipping_cost():
        pass

    # UT - 009
    def test_prevents_double_purchase_of_last_item():
        pass

class TestOrderItemModel:
    # UT - 010
    def test_stock_reduces_at_confirming_order():
        pass

    # UT - 011
    def test_product_snapshots_are_saved():
        pass

class TestCartModel:
    # UT - 012
    def test_product_added():
        pass

    # UT - 013
    def test_product_deleted():
        pass

    # UT - 014
    def test_fails_at_adding_product_not_available():
        pass

    # UT - 015
    def test_total_is_calculated():
        pass

    # UT - 016
    def test_product_is_converted_in_order_item():
        pass