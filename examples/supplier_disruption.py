#!/usr/bin/env python3
"""Supplier Disruption — What happens when a supplier goes offline?

The supplier operates normally for days 1–20, goes offline for
days 21–30 (simulating a disruption), and resumes on day 31.

We observe how inventory depletes, stockouts occur, and the system
recovers after the disruption ends.

Run:
    python examples/supplier_disruption.py
"""

from supplychain_abm import SupplyChainModel


def main() -> None:
    model = SupplyChainModel(seed=42)

    supplier = model.add_supplier(name="Supplier", inventory=1000)
    warehouse = model.add_warehouse(
        name="Warehouse",
        inventory=80,
        reorder_point=40,
        order_quantity=80,
    )
    customer = model.add_customer(name="Customer", demand=10)

    model.connect(supplier, warehouse, lead_time=3)
    model.connect(warehouse, customer, lead_time=1)

    # Run with disruption
    disruption_start = 21
    disruption_end = 30
    total_days = 50

    for day in range(1, total_days + 1):
        # Toggle supplier availability
        if disruption_start <= day <= disruption_end:
            supplier.active = False
        else:
            supplier.active = True
        model.step()

    print("=" * 60)
    print("SUPPLIER DISRUPTION — 50-Day Simulation")
    print(f"  Disruption period: Day {disruption_start}–{disruption_end}")
    print("=" * 60)

    summary = model.summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    print("\n--- Warehouse Inventory & Service Level ---")
    results = model.results()
    wh_data = results[results["agent"] == "Warehouse"][
        ["step", "inventory", "demand", "fulfilled", "unfulfilled", "service_level"]
    ]
    print(wh_data.to_string(index=False))

    # Visualize
    model.plot_inventory()
    model.plot_service_level()


if __name__ == "__main__":
    main()
