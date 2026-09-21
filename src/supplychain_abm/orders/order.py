"""Order representation for supply-chain transactions.

An order captures a request from one agent to another for a quantity
of product, and tracks its lifecycle from creation to delivery.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class OrderStatus(Enum):
    """Lifecycle states of an order."""

    CREATED = "created"
    ACCEPTED = "accepted"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    REJECTED = "rejected"


# Module-level counter for deterministic, auto-incrementing IDs.
_next_order_id: int = 0


def _generate_order_id() -> int:
    """Return a unique order ID and increment the counter."""
    global _next_order_id
    order_id = _next_order_id
    _next_order_id += 1
    return order_id


def reset_order_counter() -> None:
    """Reset the global order-ID counter (useful for tests)."""
    global _next_order_id
    _next_order_id = 0


class Order:
    """A supply-chain order from one agent to another.

    Attributes:
        order_id: Unique identifier for this order.
        source: The agent placing the order.
        destination: The agent that should fulfill the order.
        product: Product identifier (default ``"default"``).
        quantity: Number of units requested.
        step_created: Simulation step when the order was created.
        status: Current lifecycle state.
    """

    def __init__(
        self,
        source: Any,
        destination: Any,
        quantity: int,
        step_created: int,
        product: str = "default",
    ) -> None:
        """Create an Order.

        Args:
            source: Agent placing the order.
            destination: Agent to fulfill the order.
            quantity: Units requested. Must be > 0.
            step_created: Simulation step of creation.
            product: Product identifier.

        Raises:
            ValueError: If *quantity* is not positive.
        """
        if quantity <= 0:
            raise ValueError(
                f"Order quantity must be > 0, got {quantity}."
            )
        self.order_id: int = _generate_order_id()
        self.source = source
        self.destination = destination
        self.product: str = product
        self.quantity: int = quantity
        self.step_created: int = step_created
        self.status: OrderStatus = OrderStatus.CREATED

    # ------------------------------------------------------------------
    # Lifecycle transitions
    # ------------------------------------------------------------------

    def accept(self) -> None:
        """Mark the order as accepted."""
        self.status = OrderStatus.ACCEPTED

    def ship(self) -> None:
        """Mark the order as shipped."""
        self.status = OrderStatus.SHIPPED

    def deliver(self) -> None:
        """Mark the order as delivered."""
        self.status = OrderStatus.DELIVERED

    def reject(self) -> None:
        """Mark the order as rejected."""
        self.status = OrderStatus.REJECTED

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Order(id={self.order_id}, src={self.source}, "
            f"dst={self.destination}, qty={self.quantity}, "
            f"status={self.status.value})"
        )
