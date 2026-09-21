#!/usr/bin/env python3
"""Bullwhip Effect — Order variance amplification across supply-chain stages.

Demonstrates how small demand variability at the customer level creates
progressively larger order variability as we move upstream through the
supply chain.

Uses a 4-stage chain: Supplier → Warehouse → Retailer → Customer
with slightly random demand.

Run:
    python examples/bullwhip_effect.py
"""

import matplotlib.pyplot as plt
import numpy as np

from supplychain_abm import SupplyChainModel, RandomDemand


def main() -> None:
    model = SupplyChainModel(seed=42)

    rng = np.random.default_rng(42)

    supplier = model.add_supplier(name="Supplier", inventory=10000)
    warehouse = model.add_warehouse(
        name="Warehouse",
        inventory=200,
        reorder_point=100,
        order_quantity=200,
    )
    retailer = model.add_retailer(
        name="Retailer",
        inventory=100,
        reorder_point=50,
        order_quantity=100,
    )
    customer = model.add_customer(
        name="Customer",
        demand=RandomDemand(mean=10, std=3, rng=rng),
    )

    model.connect(supplier, warehouse, lead_time=3)
    model.connect(warehouse, retailer, lead_time=2)
    model.connect(retailer, customer, lead_time=1)

    model.run(steps=60)

    results = model.results()

    print("=" * 60)
    print("BULLWHIP EFFECT — 60-Day Simulation")
    print("=" * 60)

    # Compute order variance at each stage
    customer_df = results[results["agent"] == "Customer"]
    retailer_df = results[results["agent"] == "Retailer"]
    warehouse_df = results[results["agent"] == "Warehouse"]

    customer_demand = customer_df["demand"].values
    retailer_orders = retailer_df["order_quantity"].values if "order_quantity" in retailer_df.columns else np.zeros(0)
    warehouse_orders = warehouse_df["order_quantity"].values if "order_quantity" in warehouse_df.columns else np.zeros(0)

    print(f"\n  Customer demand std:   {np.std(customer_demand):.2f}")
    if len(retailer_orders) > 0:
        print(f"  Retailer order std:    {np.std(retailer_orders):.2f}")
    if len(warehouse_orders) > 0:
        print(f"  Warehouse order std:   {np.std(warehouse_orders):.2f}")

    # Plot
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        customer_df["step"].values, customer_demand,
        label="Customer Demand", alpha=0.8,
    )
    if "order_quantity" in retailer_df.columns:
        ax.plot(
            retailer_df["step"].values, retailer_orders,
            label="Retailer Orders", alpha=0.8,
        )
    if "order_quantity" in warehouse_df.columns:
        ax.plot(
            warehouse_df["step"].values, warehouse_orders,
            label="Warehouse Orders", alpha=0.8,
        )

    ax.set_xlabel("Day")
    ax.set_ylabel("Quantity (units)")
    ax.set_title("Bullwhip Effect — Demand vs Orders Across Stages")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

    # Summary
    summary = model.summary()
    print("\n  --- Overall Summary ---")
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"    {key}: {value:.2f}")
        else:
            print(f"    {key}: {value}")


if __name__ == "__main__":
    main()
