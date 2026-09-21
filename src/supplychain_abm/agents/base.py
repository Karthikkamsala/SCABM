"""Base class for all supply-chain agents.

Provides shared infrastructure (name, inventory, order queues, metrics
recording) on top of Mesa's ``Agent``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import mesa

from supplychain_abm.inventory.inventory import Inventory

if TYPE_CHECKING:
    from supplychain_abm.model.supply_chain_model import SupplyChainModel


class SupplyChainAgent(mesa.Agent):
    """Abstract base agent for all supply-chain entities.

    Subclasses must implement :meth:`step`.

    Attributes:
        name: Human-readable name for this agent.
        inventory: The agent's inventory tracker (may be unused by
            agents like Customer that don't hold inventory).
        incoming_orders: Orders received from downstream agents
            that need to be fulfilled this step.
        outgoing_orders: Orders this agent has placed upstream
            that are pending.
        metrics_history: Per-step metrics recorded during the
            simulation.
    """

    agent_type: str = "base"

    def __init__(
        self,
        model: SupplyChainModel,
        name: str,
        initial_inventory: int = 0,
    ) -> None:
        """Create a SupplyChainAgent.

        Args:
            model: The Mesa model this agent belongs to.
            name: Human-readable name.
            initial_inventory: Starting inventory level.
        """
        super().__init__(model)
        self.name: str = name
        self.inventory: Inventory = Inventory(initial_inventory)
        self.incoming_orders: list[Any] = []
        self.outgoing_orders: list[Any] = []
        self.metrics_history: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # To be overridden
    # ------------------------------------------------------------------

    def step(self) -> None:
        """Execute one simulation step. Must be overridden."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement step()."
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def record_metrics(self, **extra: Any) -> None:
        """Snapshot the agent's current state into metrics_history.

        Automatically records inventory level and step number.
        Additional key-value pairs can be passed via *extra*.
        """
        record: dict[str, Any] = {
            "step": self.model.current_step,
            "agent": self.name,
            "inventory": self.inventory.level,
        }
        record.update(extra)
        self.metrics_history.append(record)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
