"""Warehouse agent for supply-chain simulations.

The Warehouse sits between upstream suppliers/factories and downstream
retailers/customers. It receives shipments, stores inventory, fulfills
downstream orders, and places replenishment orders upstream using an
inventory policy.
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


class WarehouseAgent(SupplyChainAgent):
    """A warehouse that stores inventory and fulfills downstream orders.

    Attributes:
        policy: The inventory ordering policy.
        demand_this_step: Demand received this step.
        fulfilled_this_step: Demand fulfilled this step.
        total_demand: Cumulative demand received.
        total_fulfilled: Cumulative demand fulfilled.
        orders_placed: Count of replenishment orders placed.
    """

    agent_type: str = "warehouse"

    def __init__(
        self,
        model: SupplyChainModel,
        name: str,
        initial_inventory: int = 100,
        reorder_point: int = 50,
        order_quantity: int = 100,
        policy: InventoryPolicy | None = None,
    ) -> None:
        """Create a WarehouseAgent.

        Args:
            model: The Mesa model this agent belongs to.
            name: Human-readable name.
            initial_inventory: Starting inventory level.
            reorder_point: Threshold for reordering (used if no custom
                *policy* is provided).
            order_quantity: Quantity per replenishment order.
            policy: Custom inventory policy. If ``None``, a
                :class:`ReorderPointPolicy` is created from
                *reorder_point* and *order_quantity*.
        """
        super().__init__(model, name, initial_inventory)
        self.policy: InventoryPolicy = policy or ReorderPointPolicy(
            reorder_point=reorder_point,
            order_quantity=order_quantity,
        )
        self.demand_this_step: int = 0
        self.fulfilled_this_step: int = 0
        self.total_demand: int = 0
        self.total_fulfilled: int = 0
        self.orders_placed: int = 0

    def step(self) -> None:
        """Execute one simulation step.

        Step logic:
        1. Fulfill incoming orders from downstream agents.
        2. Apply inventory policy — place replenishment orders upstream.
        3. Record metrics.
        """
        # --- 1. Fulfill downstream demand ---
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

        # --- 2. Replenishment ---
        ordered_qty = 0
        if self.policy.should_order(self.inventory):
            ordered_qty = self.policy.order_quantity(self.inventory)
            upstream_agents = self.model.network.get_upstream(self)
            for supplier in upstream_agents:
                replenishment_order = Order(
                    source=self,
                    destination=supplier,
                    quantity=ordered_qty,
                    step_created=self.model.current_step,
                )
                supplier.incoming_orders.append(replenishment_order)
                self.outgoing_orders.append(replenishment_order)
                self.orders_placed += 1

        # --- 3. Metrics ---
        unfulfilled = self.demand_this_step - self.fulfilled_this_step
        service_level = (
            self.fulfilled_this_step / self.demand_this_step
            if self.demand_this_step > 0
            else 1.0
        )
        self.record_metrics(
            demand=self.demand_this_step,
            fulfilled=self.fulfilled_this_step,
            unfulfilled=unfulfilled,
            service_level=service_level,
            orders_placed=1 if ordered_qty > 0 else 0,
            order_quantity=ordered_qty,
        )
