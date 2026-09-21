"""Supply-chain simulation model built on Mesa.

:class:`SupplyChainModel` is the central orchestrator. It provides
factory methods to create agents, connect them in a network, run the
simulation, and collect/visualize results.
"""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import mesa
import numpy as np
import pandas as pd

from supplychain_abm.agents.customer import CustomerAgent
from supplychain_abm.agents.factory import FactoryAgent
from supplychain_abm.agents.retailer import RetailerAgent
from supplychain_abm.agents.supplier import SupplierAgent
from supplychain_abm.agents.warehouse import WarehouseAgent
from supplychain_abm.demand.demand import DemandGenerator
from supplychain_abm.metrics.metrics import MetricsCollector
from supplychain_abm.network.network import SupplyChainNetwork
from supplychain_abm.policies.inventory_policy import InventoryPolicy
from supplychain_abm.shipments.shipment import Shipment


class SupplyChainModel(mesa.Model):
    """Agent-based supply-chain simulation model.

    Provides a high-level API to build a supply chain, run simulations,
    and analyze results.

    Example::

        model = SupplyChainModel(seed=42)
        s = model.add_supplier("Supplier", inventory=1000)
        w = model.add_warehouse("Warehouse", inventory=100,
                                reorder_point=50, order_quantity=100)
        c = model.add_customer("Customer", demand=10)
        model.connect(s, w, lead_time=3)
        model.connect(w, c, lead_time=1)
        model.run(steps=30)
        print(model.results())

    Simulation step order:
        1. Customers generate demand and place orders.
        2. Retailers/Warehouses fulfill demand and reorder.
        3. Factories produce and fulfill orders.
        4. Suppliers process orders and create shipments.
        5. Advance in-transit shipments; deliver arrivals.
        6. Record metrics.
    """

    def __init__(
        self,
        seed: int | None = None,
        holding_cost: float = 1.0,
        stockout_cost: float = 10.0,
    ) -> None:
        """Create a SupplyChainModel.

        Args:
            seed: Random seed for reproducibility.
            holding_cost: Holding cost per unit per step.
            stockout_cost: Penalty cost per unit of stockout.
        """
        self._rng: np.random.Generator = np.random.default_rng(seed)
        super().__init__(rng=self._rng)
        self.network: SupplyChainNetwork = SupplyChainNetwork()
        self.metrics_collector: MetricsCollector = MetricsCollector(
            holding_cost_per_unit=holding_cost,
            stockout_cost_per_unit=stockout_cost,
        )
        self.shipments_in_transit: list[Shipment] = []
        self.current_step: int = 0

        # Agent registries (by type) — NOT shadowing model.agents
        self._suppliers: list[SupplierAgent] = []
        self._factories: list[FactoryAgent] = []
        self._warehouses: list[WarehouseAgent] = []
        self._retailers: list[RetailerAgent] = []
        self._customers: list[CustomerAgent] = []

    # ------------------------------------------------------------------
    # Factory methods for adding agents
    # ------------------------------------------------------------------

    def add_supplier(
        self,
        name: str,
        inventory: int = 1000,
    ) -> SupplierAgent:
        """Add a Supplier agent to the model.

        Args:
            name: Human-readable name.
            inventory: Starting inventory.

        Returns:
            The created :class:`SupplierAgent`.
        """
        agent = SupplierAgent(model=self, name=name, initial_inventory=inventory)
        self.network.add_node(agent)
        self._suppliers.append(agent)
        return agent

    def add_factory(
        self,
        name: str,
        inventory: int = 200,
        production_capacity: int = 100,
        reorder_point: int = 100,
        order_quantity: int = 200,
        policy: InventoryPolicy | None = None,
    ) -> FactoryAgent:
        """Add a Factory agent to the model.

        Args:
            name: Human-readable name.
            inventory: Starting finished-goods inventory.
            production_capacity: Max units produced per step.
            reorder_point: Threshold for ordering raw materials.
            order_quantity: Quantity per raw-material order.
            policy: Custom inventory policy.

        Returns:
            The created :class:`FactoryAgent`.
        """
        agent = FactoryAgent(
            model=self,
            name=name,
            initial_inventory=inventory,
            production_capacity=production_capacity,
            reorder_point=reorder_point,
            order_quantity=order_quantity,
            policy=policy,
        )
        self.network.add_node(agent)
        self._factories.append(agent)
        return agent

    def add_warehouse(
        self,
        name: str,
        inventory: int = 100,
        reorder_point: int = 50,
        order_quantity: int = 100,
        policy: InventoryPolicy | None = None,
    ) -> WarehouseAgent:
        """Add a Warehouse agent to the model.

        Args:
            name: Human-readable name.
            inventory: Starting inventory.
            reorder_point: Threshold for reordering.
            order_quantity: Quantity per replenishment order.
            policy: Custom inventory policy.

        Returns:
            The created :class:`WarehouseAgent`.
        """
        agent = WarehouseAgent(
            model=self,
            name=name,
            initial_inventory=inventory,
            reorder_point=reorder_point,
            order_quantity=order_quantity,
            policy=policy,
        )
        self.network.add_node(agent)
        self._warehouses.append(agent)
        return agent

    def add_retailer(
        self,
        name: str,
        inventory: int = 100,
        reorder_point: int = 50,
        order_quantity: int = 100,
        policy: InventoryPolicy | None = None,
    ) -> RetailerAgent:
        """Add a Retailer agent to the model.

        Args:
            name: Human-readable name.
            inventory: Starting inventory.
            reorder_point: Threshold for reordering.
            order_quantity: Quantity per replenishment order.
            policy: Custom inventory policy.

        Returns:
            The created :class:`RetailerAgent`.
        """
        agent = RetailerAgent(
            model=self,
            name=name,
            initial_inventory=inventory,
            reorder_point=reorder_point,
            order_quantity=order_quantity,
            policy=policy,
        )
        self.network.add_node(agent)
        self._retailers.append(agent)
        return agent

    def add_customer(
        self,
        name: str,
        demand: int | DemandGenerator = 10,
    ) -> CustomerAgent:
        """Add a Customer agent to the model.

        Args:
            name: Human-readable name.
            demand: Fixed demand quantity (int) or a
                :class:`DemandGenerator` instance.

        Returns:
            The created :class:`CustomerAgent`.
        """
        agent = CustomerAgent(model=self, name=name, demand=demand)
        self.network.add_node(agent)
        self._customers.append(agent)
        return agent

    # ------------------------------------------------------------------
    # Network connections
    # ------------------------------------------------------------------

    def connect(
        self,
        source: Any,
        destination: Any,
        lead_time: int = 0,
        **attrs: Any,
    ) -> None:
        """Connect two agents in the supply-chain network.

        Material flows from *source* (upstream) to *destination*
        (downstream). Orders flow in the reverse direction.

        Args:
            source: Upstream agent.
            destination: Downstream agent.
            lead_time: Transit time in simulation steps.
            **attrs: Additional edge attributes.
        """
        self.network.add_connection(
            source, destination, lead_time=lead_time, **attrs
        )

    # ------------------------------------------------------------------
    # Simulation execution
    # ------------------------------------------------------------------

    def step(self) -> None:
        """Execute one simulation step.

        Step order:
        1. Customers generate demand → place orders.
        2. Retailers fulfill demand → reorder upstream.
        3. Warehouses fulfill demand → reorder upstream.
        4. Factories produce → fulfill → reorder.
        5. Suppliers process orders → create shipments.
        6. Advance shipments → deliver arrivals.
        7. Collect metrics.
        """
        self.current_step += 1

        # 1. Customers generate demand
        for customer in self._customers:
            customer.step()

        # 2. Retailers fulfill and reorder
        for retailer in self._retailers:
            retailer.step()

        # 3. Warehouses fulfill and reorder
        for warehouse in self._warehouses:
            warehouse.step()

        # 4. Factories produce and fulfill
        for factory in self._factories:
            factory.step()

        # 5. Suppliers process orders
        for supplier in self._suppliers:
            supplier.step()

        # 6. Advance shipments and deliver
        self._process_shipments()

    def _process_shipments(self) -> None:
        """Advance in-transit shipments and deliver arrivals."""
        still_in_transit: list[Shipment] = []
        for shipment in self.shipments_in_transit:
            if shipment.has_arrived(self.current_step):
                shipment.deliver()
                dest = shipment.destination
                if hasattr(dest, "inventory"):
                    dest.inventory.receive(shipment.quantity)
                # Update customer received count
                if hasattr(dest, "received_this_step"):
                    dest.received_this_step += shipment.quantity
                if hasattr(dest, "total_received"):
                    dest.total_received += shipment.quantity
            else:
                still_in_transit.append(shipment)
        self.shipments_in_transit = still_in_transit

    def run(self, steps: int) -> None:
        """Run the simulation for a given number of steps.

        Args:
            steps: Number of simulation steps (days) to run.
                Must be > 0.

        Raises:
            ValueError: If *steps* is not positive.
        """
        if steps <= 0:
            raise ValueError(f"Steps must be > 0, got {steps}.")
        for _ in range(steps):
            self.step()

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    def results(self) -> pd.DataFrame:
        """Return simulation results as a Pandas DataFrame.

        Each row is one agent's metrics for one step.
        """
        all_records: list[dict[str, Any]] = []
        all_agents = (
            self._suppliers
            + self._factories
            + self._warehouses
            + self._retailers
            + self._customers
        )
        for agent in all_agents:
            all_records.extend(agent.metrics_history)
        if not all_records:
            return pd.DataFrame()
        return pd.DataFrame(all_records)

    def summary(self) -> dict[str, Any]:
        """Return aggregate summary statistics.

        Returns:
            Dictionary with overall metrics such as service level,
            total demand, total stockouts, inventory costs, etc.
        """
        df = self.results()
        if df.empty:
            return {}

        summary: dict[str, Any] = {}

        # Filter to agents that handle demand (warehouses + retailers)
        demand_agents = df[df["agent"].isin(
            [a.name for a in self._warehouses + self._retailers]
        )]

        if "demand" in demand_agents.columns:
            total_demand = demand_agents["demand"].sum()
            summary["total_demand"] = total_demand

        if "fulfilled" in demand_agents.columns:
            total_fulfilled = demand_agents["fulfilled"].sum()
            summary["total_fulfilled"] = total_fulfilled

        if "demand" in demand_agents.columns and "fulfilled" in demand_agents.columns:
            td = demand_agents["demand"].sum()
            tf = demand_agents["fulfilled"].sum()
            summary["overall_service_level"] = tf / td if td > 0 else 1.0

        if "unfulfilled" in demand_agents.columns:
            summary["total_stockouts"] = demand_agents["unfulfilled"].sum()

        if "inventory" in df.columns:
            # Average across all inventory-holding agents
            inv_agents = df[df["agent"].isin(
                [a.name for a in self._suppliers + self._factories
                 + self._warehouses + self._retailers]
            )]
            summary["avg_inventory"] = inv_agents["inventory"].mean()

        return summary

    # ------------------------------------------------------------------
    # Visualization
    # ------------------------------------------------------------------

    def plot_inventory(self, agents: list[str] | None = None) -> None:
        """Plot inventory levels over time.

        Args:
            agents: List of agent names to include. If ``None``,
                plots all inventory-holding agents.
        """
        df = self.results()
        if df.empty:
            print("No results to plot.")
            return

        inv_names = [
            a.name for a in (
                self._suppliers + self._factories
                + self._warehouses + self._retailers
            )
        ]
        if agents:
            inv_names = [n for n in inv_names if n in agents]

        fig, ax = plt.subplots(figsize=(10, 5))
        for name in inv_names:
            agent_df = df[df["agent"] == name]
            if not agent_df.empty and "inventory" in agent_df.columns:
                ax.plot(agent_df["step"], agent_df["inventory"], label=name)

        ax.set_xlabel("Day")
        ax.set_ylabel("Inventory (units)")
        ax.set_title("Inventory Levels Over Time")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def plot_demand(self) -> None:
        """Plot customer demand over time."""
        df = self.results()
        if df.empty:
            return

        fig, ax = plt.subplots(figsize=(10, 5))
        for customer in self._customers:
            cdf = df[df["agent"] == customer.name]
            if not cdf.empty and "demand" in cdf.columns:
                ax.plot(cdf["step"], cdf["demand"], label=customer.name)

        ax.set_xlabel("Day")
        ax.set_ylabel("Demand (units)")
        ax.set_title("Customer Demand Over Time")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def plot_orders(self) -> None:
        """Plot order quantities placed by warehouses/retailers."""
        df = self.results()
        if df.empty:
            return

        fig, ax = plt.subplots(figsize=(10, 5))
        for agent in self._warehouses + self._retailers:
            adf = df[df["agent"] == agent.name]
            if not adf.empty and "order_quantity" in adf.columns:
                ax.plot(
                    adf["step"], adf["order_quantity"],
                    label=f"{agent.name} orders", marker="o", markersize=3,
                )

        ax.set_xlabel("Day")
        ax.set_ylabel("Order Quantity (units)")
        ax.set_title("Replenishment Orders Over Time")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def plot_service_level(self) -> None:
        """Plot service level over time for warehouses/retailers."""
        df = self.results()
        if df.empty:
            return

        fig, ax = plt.subplots(figsize=(10, 5))
        for agent in self._warehouses + self._retailers:
            adf = df[df["agent"] == agent.name]
            if not adf.empty and "service_level" in adf.columns:
                ax.plot(
                    adf["step"], adf["service_level"],
                    label=agent.name,
                )

        ax.set_xlabel("Day")
        ax.set_ylabel("Service Level")
        ax.set_title("Service Level Over Time")
        ax.set_ylim(-0.05, 1.05)
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def plot_bullwhip(self) -> None:
        """Plot order variability across supply-chain stages.

        Shows the bullwhip effect by plotting demand/order quantities
        at each stage from Customer → Retailer → Warehouse → Factory
        → Supplier.
        """
        df = self.results()
        if df.empty:
            return

        fig, ax = plt.subplots(figsize=(10, 5))

        # Customer demand
        for c in self._customers:
            cdf = df[df["agent"] == c.name]
            if not cdf.empty and "demand" in cdf.columns:
                ax.plot(cdf["step"], cdf["demand"], label=f"{c.name} demand")

        # Orders at each stage
        for agent in self._retailers + self._warehouses:
            adf = df[df["agent"] == agent.name]
            if not adf.empty and "order_quantity" in adf.columns:
                ax.plot(
                    adf["step"], adf["order_quantity"],
                    label=f"{agent.name} orders",
                )

        ax.set_xlabel("Day")
        ax.set_ylabel("Quantity (units)")
        ax.set_title("Bullwhip Effect — Demand vs Orders")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"SupplyChainModel(step={self.current_step}, "
            f"agents={len(self.network.nodes)})"
        )
