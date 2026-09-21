"""Tests for supply-chain agents."""

from supplychain_abm import SupplyChainModel


class TestSupplierAgent:
    def test_creation(self):
        model = SupplyChainModel(seed=42)
        s = model.add_supplier("TestSupplier", inventory=500)
        assert s.name == "TestSupplier"
        assert s.inventory.level == 500
        assert s.active is True
        assert s.agent_type == "supplier"

    def test_disruption_flag(self):
        model = SupplyChainModel(seed=42)
        s = model.add_supplier("S", inventory=500)
        s.active = False
        assert s.active is False


class TestWarehouseAgent:
    def test_creation(self):
        model = SupplyChainModel(seed=42)
        w = model.add_warehouse(
            "TestWarehouse", inventory=100,
            reorder_point=50, order_quantity=100,
        )
        assert w.name == "TestWarehouse"
        assert w.inventory.level == 100
        assert w.agent_type == "warehouse"


class TestRetailerAgent:
    def test_creation(self):
        model = SupplyChainModel(seed=42)
        r = model.add_retailer(
            "TestRetailer", inventory=80,
            reorder_point=40, order_quantity=80,
        )
        assert r.name == "TestRetailer"
        assert r.inventory.level == 80
        assert r.agent_type == "retailer"


class TestFactoryAgent:
    def test_creation(self):
        model = SupplyChainModel(seed=42)
        f = model.add_factory(
            "TestFactory", inventory=200,
            production_capacity=100,
        )
        assert f.name == "TestFactory"
        assert f.production_capacity == 100
        assert f.agent_type == "factory"


class TestCustomerAgent:
    def test_creation_with_int_demand(self):
        model = SupplyChainModel(seed=42)
        c = model.add_customer("TestCustomer", demand=15)
        assert c.name == "TestCustomer"
        assert c.demand_generator.quantity == 15
        assert c.agent_type == "customer"

    def test_creation_with_generator(self):
        from supplychain_abm import RandomDemand
        import numpy as np

        model = SupplyChainModel(seed=42)
        gen = RandomDemand(mean=10, std=3, rng=np.random.default_rng(42))
        c = model.add_customer("TestCustomer", demand=gen)
        assert c.demand_generator is gen
