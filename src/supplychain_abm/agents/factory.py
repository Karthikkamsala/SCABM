"""Factory agent for supply-chain simulations.

The Factory receives raw materials from upstream suppliers, produces
finished goods (with a simple capacity model), and ships them to
downstream warehouses/retailers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from supplychain_abm.agents.base import SupplyChainAgent
from supplychain_abm.orders.order import Order
from supplychain_abm.policies.inventory_policy import (
    InventoryPolicy,
    ReorderPointPolicy,
)
from supplychain_abm.shipments.shipment import Shipment

if TYPE_CHECKING:
    from supplychain_abm.model.supply_chain_model import SupplyChainModel


class FactoryAgent(SupplyChainAgent):
    """A production facility with simple capacity-based manufacturing.

    The factory produces up to ``production_capacity`` units per step,
    using raw materials from inventory to create finished goods.

    Attributes:
        production_capacity: Max units produced per step.
        policy: Inventory ordering policy for raw materials.
        produced_this_step: Units produced this step.
        total_produced: Cumulative units produced.
        demand_this_step: Demand received from downstream.
        fulfilled_this_step: Demand fulfilled this step.
        total_demand: Cumulative demand received.
        total_fulfilled: Cumulative demand fulfilled.
        orders_placed: Count of replenishment orders placed.
    """

    agent_type: str = "factory"

    def __init__(
        self,
        model: SupplyChainModel,
        name: str,
        initial_inventory: int = 200,
        production_capacity: int = 100,
        reorder_point: int = 100,
        order_quantity: int = 200,
        policy: InventoryPolicy | None = None,
    ) -> None:
        """Create a FactoryAgent.

        Args:
            model: The Mesa model this agent belongs to.
            name: Human-readable name.
            initial_inventory: Starting finished-goods inventory.
            production_capacity: Max units produced per step.
            reorder_point: Threshold for ordering raw materials.
            order_quantity: Quantity per raw-material order.
            policy: Custom inventory policy. Falls back to
                :class:`ReorderPointPolicy`.
        """
        super().__init__(model, name, initial_inventory)
        if production_capacity <= 0:
            raise ValueError(
                f"Production capacity must be > 0, got {production_capacity}."
            )
        self.production_capacity: int = production_capacity
        self.policy: InventoryPolicy = policy or ReorderPointPolicy(
            reorder_point=reorder_point,
            order_quantity=order_quantity,
        )
        self.produced_this_step: int = 0
        self.total_produced: int = 0
        self.demand_this_step: int = 0
        self.fulfilled_this_step: int = 0
        self.total_demand: int = 0
        self.total_fulfilled: int = 0
        self.orders_placed: int = 0

    def step(self) -> None:
        """Execute one simulation step.

        Step logic:
        1. Produce finished goods (up to capacity, capped by
           pending demand so production isn't wastefully infinite).
        2. Fulfill incoming downstream orders.
        3. Order raw materials if needed.
        4. Record metrics.
        """
        # --- 1. Production ---
        # Produce up to capacity each step (simplified: unlimited raw
        # materials for v0.1, production is capped by capacity only).
        self.produced_this_step = self.production_capacity
        self.inventory.receive(self.produced_this_step)
        self.total_produced += self.produced_this_step

        # --- 2. Fulfill downstream orders ---
        self.demand_this_step = 0
        self.fulfilled_this_step = 0

        for order in self.incoming_orders:
            self.demand_this_step += order.quantity
            shipped = self.inventory.remove(order.quantity)
            self.fulfilled_this_step += shipped
            if shipped > 0:
                order.accept()
                order.ship()
                lead_time = self.model.network.get_lead_time(
                    self, order.source
                )
                shipment = Shipment(
                    origin=self,
                    destination=order.source,
                    quantity=shipped,
                    step_created=self.model.current_step,
                    lead_time=lead_time,
                )
                self.model.shipments_in_transit.append(shipment)
            if shipped < order.quantity:
                order.reject()

        self.total_demand += self.demand_this_step
        self.total_fulfilled += self.fulfilled_this_step
        self.incoming_orders.clear()

        # --- 3. Raw material ordering ---
        ordered_qty = 0
        if self.policy.should_order(self.inventory):
            ordered_qty = self.policy.order_quantity(self.inventory)
            upstream_agents = self.model.network.get_upstream(self)
            for supplier in upstream_agents:
                raw_order = Order(
                    source=self,
                    destination=supplier,
                    quantity=ordered_qty,
                    step_created=self.model.current_step,
                )
                supplier.incoming_orders.append(raw_order)
                self.outgoing_orders.append(raw_order)
                self.orders_placed += 1

        # --- 4. Metrics ---
        unfulfilled = self.demand_this_step - self.fulfilled_this_step
        service_level = (
            self.fulfilled_this_step / self.demand_this_step
            if self.demand_this_step > 0
            else 1.0
        )
        self.record_metrics(
            produced=self.produced_this_step,
            demand=self.demand_this_step,
            fulfilled=self.fulfilled_this_step,
            unfulfilled=unfulfilled,
            service_level=service_level,
            orders_placed=1 if ordered_qty > 0 else 0,
            order_quantity=ordered_qty,
        )
