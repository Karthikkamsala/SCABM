"""Inventory management for supply-chain agents.

Encapsulates inventory-related operations: receiving, removing,
and tracking stock levels and stockouts.
"""

from __future__ import annotations


class Inventory:
    """Tracks inventory levels for a supply-chain agent.

    Attributes:
        level: Current inventory level (units on hand).
        total_received: Cumulative units received.
        total_removed: Cumulative units removed (shipped/consumed).
        total_stockout_qty: Cumulative units of unmet demand.
        stockout_count: Number of times a removal was partially
            or fully unfulfilled due to insufficient inventory.
    """

    def __init__(self, initial_level: int = 0) -> None:
        """Create an Inventory tracker.

        Args:
            initial_level: Starting inventory level. Must be >= 0.

        Raises:
            ValueError: If *initial_level* is negative.
        """
        if initial_level < 0:
            raise ValueError(
                f"Initial inventory level must be >= 0, got {initial_level}."
            )
        self.level: int = initial_level
        self.total_received: int = 0
        self.total_removed: int = 0
        self.total_stockout_qty: int = 0
        self.stockout_count: int = 0

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def receive(self, quantity: int) -> None:
        """Add *quantity* units to inventory.

        Args:
            quantity: Number of units to add. Must be > 0.

        Raises:
            ValueError: If *quantity* is not positive.
        """
        if quantity <= 0:
            raise ValueError(
                f"Receive quantity must be > 0, got {quantity}."
            )
        self.level += quantity
        self.total_received += quantity

    def remove(self, quantity: int) -> int:
        """Remove up to *quantity* units from inventory.

        If insufficient inventory is available, removes whatever is
        on hand and records the shortfall as a stockout.

        Args:
            quantity: Number of units requested. Must be > 0.

        Returns:
            The number of units actually removed (may be less than
            *quantity* if inventory was insufficient).

        Raises:
            ValueError: If *quantity* is not positive.
        """
        if quantity <= 0:
            raise ValueError(
                f"Remove quantity must be > 0, got {quantity}."
            )
        fulfilled = min(quantity, self.level)
        shortfall = quantity - fulfilled
        self.level -= fulfilled
        self.total_removed += fulfilled
        if shortfall > 0:
            self.total_stockout_qty += shortfall
            self.stockout_count += 1
        return fulfilled

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def available(self) -> int:
        """Current units available (alias for *level*)."""
        return self.level

    @property
    def has_stock(self) -> bool:
        """``True`` if at least one unit is available."""
        return self.level > 0

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Inventory(level={self.level}, received={self.total_received}, "
            f"removed={self.total_removed}, stockouts={self.stockout_count})"
        )
