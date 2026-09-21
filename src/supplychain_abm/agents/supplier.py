"""Supplier agent for supply-chain simulations.

The Supplier is the most upstream agent. It holds inventory (or has
unlimited capacity) and fulfills orders from downstream agents by
creating shipments.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from supplychain_abm.agents.base import SupplyChainAgent
from supplychain_abm.orders.order import Order
from supplychain_abm.shipments.shipment import Shipment

if TYPE_CHECKING:
    from supplychain_abm.model.supply_chain_model import SupplyChainModel


class SupplierAgent(SupplyChainAgent):
    """An upstream supplier that fulfills orders from its inventory.

    The supplier can be **disrupted** — when ``active`` is ``False``,
    it will not fulfill any orders (simulating a disruption event).

    Attributes:
        active: Whether the supplier is currently operational.
        orders_fulfilled: Count of orders fulfilled.
        units_shipped: Total units shipped across all orders.
    """

    agent_type: str = "supplier"

    def __init__(
        self,
        model: SupplyChainModel,
        name: str,
        initial_inventory: int = 1000,
    ) -> None:
        """Create a SupplierAgent.

        Args:
            model: The Mesa model this agent belongs to.
            name: Human-readable name.
            initial_inventory: Starting inventory (units on hand).
        """
        super().__init__(model, name, initial_inventory)
        self.active: bool = True
        self.orders_fulfilled: int = 0
        self.units_shipped: int = 0

    def step(self) -> None:
        """Process incoming orders and create shipments.

        Simulation step logic:
        1. If disrupted (``active=False``), skip all fulfillment.
        2. For each incoming order, ship as many units as available.
        3. Create a :class:`Shipment` for each fulfilled order.
        4. Record metrics.
        """
        fulfilled_qty = 0
        orders_this_step = 0

        for order in self.incoming_orders:
            if not self.active:
                order.reject()
                continue

            shipped = self.inventory.remove(order.quantity)
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
                fulfilled_qty += shipped
                orders_this_step += 1
                self.orders_fulfilled += 1
                self.units_shipped += shipped
            else:
                order.reject()

        self.incoming_orders.clear()

        self.record_metrics(
            fulfilled=fulfilled_qty,
            orders_processed=orders_this_step,
            active=self.active,
        )
