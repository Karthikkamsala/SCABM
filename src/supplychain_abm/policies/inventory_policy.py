"""Inventory ordering policies for supply-chain agents.

Each policy implements a ``decide`` method that determines whether
to place a replenishment order and how many units to order.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from supplychain_abm.inventory.inventory import Inventory


class InventoryPolicy(ABC):
    """Abstract base class for inventory ordering policies."""

    @abstractmethod
    def should_order(self, inventory: Inventory) -> bool:
        """Return ``True`` if a replenishment order should be placed.

        Args:
            inventory: The agent's current inventory state.
        """

    @abstractmethod
    def order_quantity(self, inventory: Inventory) -> int:
        """Return the quantity to order.

        Only called when ``should_order`` returns ``True``.

        Args:
            inventory: The agent's current inventory state.
        """


class ReorderPointPolicy(InventoryPolicy):
    """Place an order when inventory drops below the reorder point.

    This is the classic (s, Q) policy:
    - **s** (reorder point): if ``inventory.level < s``, trigger an order.
    - **Q** (order quantity): the fixed quantity to order.

    Example::

        policy = ReorderPointPolicy(reorder_point=50, order_quantity=100)
    """

    def __init__(self, reorder_point: int, order_quantity: int) -> None:
        """Create a ReorderPointPolicy.

        Args:
            reorder_point: Threshold below which to reorder. Must be >= 0.
            order_quantity: Fixed quantity per order. Must be > 0.

        Raises:
            ValueError: On invalid parameters.
        """
        if reorder_point < 0:
            raise ValueError(
                f"Reorder point must be >= 0, got {reorder_point}."
            )
        if order_quantity <= 0:
            raise ValueError(
                f"Order quantity must be > 0, got {order_quantity}."
            )
        self.reorder_point = reorder_point
        self._order_quantity = order_quantity

    def should_order(self, inventory: Inventory) -> bool:
        """Return ``True`` if inventory is below the reorder point."""
        return inventory.level < self.reorder_point

    def order_quantity(self, inventory: Inventory) -> int:  # noqa: ARG002
        """Return the fixed order quantity."""
        return self._order_quantity

    def __repr__(self) -> str:
        return (
            f"ReorderPointPolicy(reorder_point={self.reorder_point}, "
            f"order_quantity={self._order_quantity})"
        )
