#!/usr/bin/env python3
"""Inventory Policy Comparison — Compare different reorder points.

Runs three simulations with different reorder points (30, 50, 80)
to observe how the policy affects inventory levels, stockouts,
and service level.

Run:
    python examples/inventory_policy.py
"""

import matplotlib.pyplot as plt

from supplychain_abm import SupplyChainModel


def run_scenario(reorder_point: int, order_quantity: int = 100) -> dict:
    """Run a 60-day simulation with the given reorder point."""
    model = SupplyChainModel(seed=42)
    model.add_supplier(name="Supplier", inventory=5000)
    model.add_warehouse(
        name="Warehouse",
        inventory=100,
        reorder_point=reorder_point,
        order_quantity=order_quantity,
    )
    model.add_customer(name="Customer", demand=10)
    model.connect(model._suppliers[0], model._warehouses[0], lead_time=3)
    model.connect(model._warehouses[0], model._customers[0], lead_time=1)

    model.run(steps=60)

    results = model.results()
    summary = model.summary()

    wh_data = results[results["agent"] == "Warehouse"]
    return {
        "reorder_point": reorder_point,
        "steps": wh_data["step"].values,
        "inventory": wh_data["inventory"].values,
        "service_level": summary.get("overall_service_level", 0),
        "total_stockouts": summary.get("total_stockouts", 0),
        "avg_inventory": summary.get("avg_inventory", 0),
    }


def main() -> None:
    scenarios = [
        run_scenario(reorder_point=30),
        run_scenario(reorder_point=50),
        run_scenario(reorder_point=80),
    ]

    print("=" * 60)
    print("INVENTORY POLICY COMPARISON — 60-Day Simulation")
    print("=" * 60)

    for s in scenarios:
        print(f"\n  Reorder Point = {s['reorder_point']}:")
        print(f"    Service Level:   {s['service_level']:.2%}")
        print(f"    Total Stockouts: {s['total_stockouts']}")
        print(f"    Avg Inventory:   {s['avg_inventory']:.1f}")

    # Plot comparison
    fig, ax = plt.subplots(figsize=(10, 5))
    for s in scenarios:
        ax.plot(
            s["steps"], s["inventory"],
            label=f"ROP={s['reorder_point']}",
        )
    ax.set_xlabel("Day")
    ax.set_ylabel("Warehouse Inventory (units)")
    ax.set_title("Inventory Policy Comparison — Reorder Point Effect")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
