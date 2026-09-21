"""Integration tests for the SupplyChainModel.

These test full simulation runs to verify correct end-to-end behaviour.
"""

import pytest

from supplychain_abm import SupplyChainModel, RandomDemand
import numpy as np


class TestModelCreation:
    def test_empty_model(self):
        model = SupplyChainModel(seed=42)
        assert model.current_step == 0
        assert len(model.network.nodes) == 0

    def test_invalid_steps_raises(self):
        model = SupplyChainModel()
        with pytest.raises(ValueError, match="must be > 0"):
            model.run(0)


class TestBasicSupplyChain:
    """Supplier → Warehouse → Customer (30 days, constant demand=10)."""

    def setup_method(self):
        self.model = SupplyChainModel(seed=42)
        self.supplier = self.model.add_supplier("Supplier", inventory=1000)
        self.warehouse = self.model.add_warehouse(
            "Warehouse", inventory=100,
            reorder_point=50, order_quantity=100,
        )
        self.customer = self.model.add_customer("Customer", demand=10)
        self.model.connect(self.supplier, self.warehouse, lead_time=3)
        self.model.connect(self.warehouse, self.customer, lead_time=1)

    def test_runs_without_error(self):
        self.model.run(30)
        assert self.model.current_step == 30

    def test_results_not_empty(self):
        self.model.run(30)
        results = self.model.results()
        assert not results.empty
        assert "step" in results.columns
        assert "agent" in results.columns

    def test_no_stockouts_with_sufficient_supply(self):
        self.model.run(30)
        summary = self.model.summary()
        # 1000 units of supplier inventory, 100 starting warehouse
        # 30 * 10 = 300 demand, should be fully met
        assert summary["overall_service_level"] == 1.0
        assert summary["total_stockouts"] == 0.0

    def test_total_demand_correct(self):
        self.model.run(30)
        summary = self.model.summary()
        assert summary["total_demand"] == 300.0  # 30 * 10

    def test_supplier_inventory_decreases(self):
        self.model.run(30)
        # Supplier started with 1000, should have shipped some
        assert self.supplier.inventory.level < 1000

    def test_reproducibility(self):
        self.model.run(30)
        r1 = self.model.results()

        model2 = SupplyChainModel(seed=42)
        model2.add_supplier("Supplier", inventory=1000)
        model2.add_warehouse(
            "Warehouse", inventory=100,
            reorder_point=50, order_quantity=100,
        )
        model2.add_customer("Customer", demand=10)
        model2.connect(
            model2._suppliers[0], model2._warehouses[0], lead_time=3
        )
        model2.connect(
            model2._warehouses[0], model2._customers[0], lead_time=1
        )
        model2.run(30)
        r2 = model2.results()

        # Inventory columns should match exactly
        inv1 = r1[r1["agent"] == "Warehouse"]["inventory"].values
        inv2 = r2[r2["agent"] == "Warehouse"]["inventory"].values
        assert list(inv1) == list(inv2)


class TestSupplierDisruption:
    """Supplier disrupted from day 11–20."""

    def test_disruption_causes_stockouts(self):
        model = SupplyChainModel(seed=42)
        supplier = model.add_supplier("Supplier", inventory=1000)
        warehouse = model.add_warehouse(
            "Warehouse", inventory=50,
            reorder_point=30, order_quantity=50,
        )
        customer = model.add_customer("Customer", demand=10)
        model.connect(supplier, warehouse, lead_time=2)
        model.connect(warehouse, customer, lead_time=1)

        for day in range(1, 31):
            # Disrupt supplier on days 11-20
            if 11 <= day <= 20:
                supplier.active = False
            else:
                supplier.active = True
            model.step()

        # Warehouse started with only 50, demand=10/day
        # Without replenishment during disruption, stockouts expected
        summary = model.summary()
        assert summary["overall_service_level"] < 1.0


class TestMultiStageChain:
    """Supplier → Factory → Warehouse → Retailer → Customer."""

    def test_five_stage_runs(self):
        model = SupplyChainModel(seed=42)
        supplier = model.add_supplier("Supplier", inventory=5000)
        factory = model.add_factory(
            "Factory", inventory=500,
            production_capacity=50,
        )
        warehouse = model.add_warehouse(
            "Warehouse", inventory=200,
            reorder_point=100, order_quantity=200,
        )
        retailer = model.add_retailer(
            "Retailer", inventory=100,
            reorder_point=50, order_quantity=100,
        )
        customer = model.add_customer("Customer", demand=10)

        model.connect(supplier, factory, lead_time=3)
        model.connect(factory, warehouse, lead_time=2)
        model.connect(warehouse, retailer, lead_time=1)
        model.connect(retailer, customer, lead_time=1)

        model.run(30)
        assert model.current_step == 30
        results = model.results()
        assert not results.empty


class TestRandomDemand:
    def test_random_demand_simulation(self):
        model = SupplyChainModel(seed=42)
        model.add_supplier("Supplier", inventory=5000)
        model.add_warehouse(
            "Warehouse", inventory=200,
            reorder_point=100, order_quantity=200,
        )
        rng = np.random.default_rng(42)
        model.add_customer(
            "Customer",
            demand=RandomDemand(mean=10, std=3, rng=rng),
        )
        model.connect(model._suppliers[0], model._warehouses[0], lead_time=3)
        model.connect(model._warehouses[0], model._customers[0], lead_time=1)

        model.run(30)
        results = model.results()
        cust_df = results[results["agent"] == "Customer"]
        # Demand should vary (not all 10)
        demands = cust_df["demand"].values
        assert len(set(demands)) > 1
