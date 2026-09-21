"""Tests for the Order class."""

import pytest

from supplychain_abm.orders.order import Order, OrderStatus


class TestOrderCreation:
    def test_basic_order(self):
        order = Order(source="A", destination="B", quantity=50, step_created=1)
        assert order.quantity == 50
        assert order.source == "A"
        assert order.destination == "B"
        assert order.step_created == 1
        assert order.status == OrderStatus.CREATED
        assert order.product == "default"

    def test_order_ids_auto_increment(self):
        o1 = Order(source="A", destination="B", quantity=10, step_created=1)
        o2 = Order(source="A", destination="B", quantity=20, step_created=2)
        assert o2.order_id == o1.order_id + 1

    def test_zero_quantity_raises(self):
        with pytest.raises(ValueError, match="must be > 0"):
            Order(source="A", destination="B", quantity=0, step_created=1)

    def test_negative_quantity_raises(self):
        with pytest.raises(ValueError, match="must be > 0"):
            Order(source="A", destination="B", quantity=-5, step_created=1)


class TestOrderLifecycle:
    def test_accept(self):
        order = Order(source="A", destination="B", quantity=10, step_created=1)
        order.accept()
        assert order.status == OrderStatus.ACCEPTED

    def test_ship(self):
        order = Order(source="A", destination="B", quantity=10, step_created=1)
        order.accept()
        order.ship()
        assert order.status == OrderStatus.SHIPPED

    def test_deliver(self):
        order = Order(source="A", destination="B", quantity=10, step_created=1)
        order.deliver()
        assert order.status == OrderStatus.DELIVERED

    def test_reject(self):
        order = Order(source="A", destination="B", quantity=10, step_created=1)
        order.reject()
        assert order.status == OrderStatus.REJECTED


class TestOrderRepr:
    def test_repr(self):
        order = Order(source="A", destination="B", quantity=10, step_created=1)
        assert "Order" in repr(order)
        assert "qty=10" in repr(order)
