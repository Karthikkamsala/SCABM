"""Tests for the Shipment class."""

import pytest

from supplychain_abm.shipments.shipment import Shipment, ShipmentStatus


class TestShipmentCreation:
    def test_basic_shipment(self):
        s = Shipment(origin="A", destination="B", quantity=100,
                     step_created=1, lead_time=3)
        assert s.quantity == 100
        assert s.lead_time == 3
        assert s.arrival_step == 4  # 1 + 3
        assert s.status == ShipmentStatus.IN_TRANSIT

    def test_zero_lead_time(self):
        s = Shipment(origin="A", destination="B", quantity=50,
                     step_created=5, lead_time=0)
        assert s.arrival_step == 5

    def test_negative_quantity_raises(self):
        with pytest.raises(ValueError, match="must be > 0"):
            Shipment(origin="A", destination="B", quantity=0,
                     step_created=1, lead_time=1)

    def test_negative_lead_time_raises(self):
        with pytest.raises(ValueError, match="must be >= 0"):
            Shipment(origin="A", destination="B", quantity=10,
                     step_created=1, lead_time=-1)


class TestShipmentArrival:
    def test_has_not_arrived_before_time(self):
        s = Shipment(origin="A", destination="B", quantity=10,
                     step_created=1, lead_time=3)
        assert s.has_arrived(2) is False
        assert s.has_arrived(3) is False

    def test_has_arrived_at_time(self):
        s = Shipment(origin="A", destination="B", quantity=10,
                     step_created=1, lead_time=3)
        assert s.has_arrived(4) is True

    def test_has_arrived_after_time(self):
        s = Shipment(origin="A", destination="B", quantity=10,
                     step_created=1, lead_time=3)
        assert s.has_arrived(10) is True

    def test_deliver(self):
        s = Shipment(origin="A", destination="B", quantity=10,
                     step_created=1, lead_time=3)
        s.deliver()
        assert s.is_delivered is True
        assert s.status == ShipmentStatus.DELIVERED
