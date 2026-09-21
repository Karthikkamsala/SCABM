#!/usr/bin/env python3
"""Demand Increase — What happens when customer demand jumps?

Customer demand starts at 10 units/day, then jumps to 20 units/day
on day 16. Observe how inventory depletes faster and whether the
reorder policy can keep up.

Run:
    python examples/demand_increase.py
"""

from supplychain_abm import SupplyChainModel
from supplychain_abm.demand.demand import DemandGenerator


class StepDemand(DemandGenerator):
    """Demand that steps up at a given point in time.

    Before ``change_step``, demand is ``base_demand``.
    From ``change_step`` onwards, demand is ``new_demand``.
    """

    def __init__(
        self, base_demand: int, new_demand: int, change_step: int
    ) -> None:
        self.base_demand = base_demand
        self.new_demand = new_demand
        self.change_step = change_step

    def generate(self, step: int) -> int:
        if step >= self.change_step:
            return self.new_demand
        return self.base_demand


def main() -> None:
    model = SupplyChainModel(seed=42)

    supplier = model.add_supplier(name="Supplier", inventory=2000)
    warehouse = model.add_warehouse(
        name="Warehouse",
        inventory=100,
        reorder_point=50,
        order_quantity=100,
    )

    demand_gen = StepDemand(base_demand=10, new_demand=20, change_step=16)
    customer = model.add_customer(name="Customer", demand=demand_gen)

    model.connect(supplier, warehouse, lead_time=3)
    model.connect(warehouse, customer, lead_time=1)

    model.run(steps=40)

    print("=" * 60)
    print("DEMAND INCREASE — 40-Day Simulation")
    print("  Demand: 10/day (days 1–15) → 20/day (days 16–40)")
    print("=" * 60)

    summary = model.summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    print("\n--- Warehouse Details ---")
    results = model.results()
    wh = results[results["agent"] == "Warehouse"][
        ["step", "inventory", "demand", "fulfilled", "unfulfilled", "service_level"]
    ]
    print(wh.to_string(index=False))

    model.plot_inventory()
    model.plot_demand()
    model.plot_service_level()


if __name__ == "__main__":
    main()
