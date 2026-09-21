"""Tests for inventory policies."""

import pytest

from supplychain_abm.inventory.inventory import Inventory
from supplychain_abm.policies.inventory_policy import ReorderPointPolicy


class TestReorderPointPolicy:
    def test_should_order_below_rop(self):
        policy = ReorderPointPolicy(reorder_point=50, order_quantity=100)
        inv = Inventory(initial_level=30)
        assert policy.should_order(inv) is True

    def test_should_not_order_above_rop(self):
        policy = ReorderPointPolicy(reorder_point=50, order_quantity=100)
        inv = Inventory(initial_level=60)
        assert policy.should_order(inv) is False

    def test_should_order_at_rop(self):
        policy = ReorderPointPolicy(reorder_point=50, order_quantity=100)
        inv = Inventory(initial_level=50)
        # At ROP, inventory is NOT below ROP, so no order
        assert policy.should_order(inv) is False

    def test_order_quantity_returns_fixed(self):
        policy = ReorderPointPolicy(reorder_point=50, order_quantity=100)
        inv = Inventory(initial_level=30)
        assert policy.order_quantity(inv) == 100

    def test_negative_rop_raises(self):
        with pytest.raises(ValueError, match="must be >= 0"):
            ReorderPointPolicy(reorder_point=-1, order_quantity=100)

    def test_zero_order_quantity_raises(self):
        with pytest.raises(ValueError, match="must be > 0"):
            ReorderPointPolicy(reorder_point=50, order_quantity=0)

    def test_repr(self):
        policy = ReorderPointPolicy(reorder_point=50, order_quantity=100)
        assert "ReorderPointPolicy" in repr(policy)
