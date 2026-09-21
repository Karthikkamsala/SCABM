#!/usr/bin/env python3
"""Basic Supply Chain — Supplier → Warehouse → Customer.

This is the simplest possible supply-chain simulation.
A customer demands 10 units/day, a warehouse fulfills from inventory
and reorders from a supplier when stock drops below the reorder point.

Run:
    python examples/basic_supply_chain.py
"""

from supplychain_abm import SupplyChainModel


def main() -> None:
    # Create the simulation model with a fixed seed for reproducibility
    model = SupplyChainModel(seed=42)

    # Add agents
    supplier = model.add_supplier(name="Supplier", inventory=1000)
    warehouse = model.add_warehouse(
        name="Warehouse",
        inventory=100,
        reorder_point=50,
        order_quantity=100,
    )
    customer = model.add_customer(name="Customer", demand=10)

    # Connect the supply chain
    #   Supplier → Warehouse (3-day lead time)
    #   Warehouse → Customer (1-day lead time)
    model.connect(supplier, warehouse, lead_time=3)
    model.connect(warehouse, customer, lead_time=1)

    # Run for 30 days
    model.run(steps=30)

    # Print results
    print("=" * 60)
    print("BASIC SUPPLY CHAIN — 30-Day Simulation")
    print("=" * 60)

    summary = model.summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    print("\n--- Warehouse Inventory Over Time ---")
    results = model.results()
    wh_data = results[results["agent"] == "Warehouse"][
        ["step", "inventory", "demand", "fulfilled", "service_level"]
    ]
    print(wh_data.to_string(index=False))

    # Visualize
    model.plot_inventory()


if __name__ == "__main__":
    main()
