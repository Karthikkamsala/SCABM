"""Customer agent for supply-chain simulations.

The Customer generates demand and places orders to the nearest
downstream-facing agent (retailer or warehouse).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from supplychain_abm.agents.base import SupplyChainAgent
from supplychain_abm.demand.demand import ConstantDemand, DemandGenerator
from supplychain_abm.orders.order import Order

if TYPE_CHECKING:
    from supplychain_abm.model.supply_chain_model import SupplyChainModel


class CustomerAgent(SupplyChainAgent):
    """A customer that generates demand and places orders.

    The customer uses a :class:`DemandGenerator` to determine how
    many units to request each step, then places orders to its
    upstream agent(s).

    Attributes:
        demand_generator: The strategy used to generate demand.
        demand_this_step: Demand generated this step.
        received_this_step: Units received (delivered) this step.
        total_demand: Cumulative demand generated.
        total_received: Cumulative units received.
    """

    agent_type: str = "customer"

    def __init__(
        self,
        model: SupplyChainModel,
        name: str,
        demand: int | DemandGenerator = 10,
    ) -> None:
        """Create a CustomerAgent.

        Args:
            model: The Mesa model this agent belongs to.
            name: Human-readable name.
            demand: Either a fixed demand quantity (int) or a
                :class:`DemandGenerator` instance.
        """
        # Customers don't hold inventory.
        super().__init__(model, name, initial_inventory=0)
        if isinstance(demand, int):
            self.demand_generator: DemandGenerator = ConstantDemand(demand)
        else:
            self.demand_generator = demand
        self.demand_this_step: int = 0
        self.received_this_step: int = 0
        self.total_demand: int = 0
        self.total_received: int = 0

    def step(self) -> None:
        """Generate demand and place orders to upstream agents.

        Step logic:
        1. Generate demand for this step.
        2. Place orders to upstream agents.
        3. Record metrics.
        """
        # --- 1. Generate demand ---
        self.demand_this_step = self.demand_generator.generate(
            self.model.current_step
        )
        self.total_demand += self.demand_this_step
        self.received_this_step = 0

        # --- 2. Place orders upstream ---
        upstream_agents = self.model.network.get_upstream(self)
        if upstream_agents and self.demand_this_step > 0:
            # For v0.1, split demand equally if multiple suppliers,
            # or send all to the single upstream agent.
            for agent in upstream_agents:
                order = Order(
                    source=self,
                    destination=agent,
                    quantity=self.demand_this_step,
                    step_created=self.model.current_step,
                )
                agent.incoming_orders.append(order)
                self.outgoing_orders.append(order)

        # --- 3. Metrics ---
        self.record_metrics(
            demand=self.demand_this_step,
            received=self.received_this_step,
        )
