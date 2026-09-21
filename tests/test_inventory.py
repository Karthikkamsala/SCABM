"""Tests for the Inventory class."""

import pytest

from supplychain_abm.inventory.inventory import Inventory


class TestInventoryCreation:
    def test_default_inventory(self):
        inv = Inventory()
        assert inv.level == 0
        assert inv.available == 0
        assert inv.total_received == 0
        assert inv.total_removed == 0

    def test_initial_inventory(self):
        inv = Inventory(initial_level=100)
        assert inv.level == 100
        assert inv.has_stock is True

    def test_negative_initial_raises(self):
        with pytest.raises(ValueError, match="must be >= 0"):
            Inventory(initial_level=-1)


class TestInventoryReceive:
    def test_receive_increases_level(self):
        inv = Inventory(initial_level=50)
        inv.receive(100)
        assert inv.level == 150
        assert inv.total_received == 100

    def test_receive_zero_raises(self):
        inv = Inventory()
        with pytest.raises(ValueError, match="must be > 0"):
            inv.receive(0)

    def test_receive_negative_raises(self):
        inv = Inventory()
        with pytest.raises(ValueError, match="must be > 0"):
            inv.receive(-10)


class TestInventoryRemove:
    def test_remove_decreases_level(self):
        inv = Inventory(initial_level=100)
        removed = inv.remove(20)
        assert removed == 20
        assert inv.level == 80
        assert inv.total_removed == 20

    def test_remove_more_than_available(self):
        inv = Inventory(initial_level=30)
        removed = inv.remove(50)
        assert removed == 30
        assert inv.level == 0
        assert inv.stockout_count == 1
        assert inv.total_stockout_qty == 20

    def test_remove_exact_amount(self):
        inv = Inventory(initial_level=50)
        removed = inv.remove(50)
        assert removed == 50
        assert inv.level == 0
        assert inv.stockout_count == 0

    def test_remove_zero_raises(self):
        inv = Inventory(initial_level=100)
        with pytest.raises(ValueError, match="must be > 0"):
            inv.remove(0)

    def test_remove_from_empty_inventory(self):
        inv = Inventory(initial_level=0)
        removed = inv.remove(10)
        assert removed == 0
        assert inv.stockout_count == 1
        assert inv.total_stockout_qty == 10


class TestInventoryRepr:
    def test_repr(self):
        inv = Inventory(initial_level=50)
        assert "Inventory" in repr(inv)
        assert "level=50" in repr(inv)
