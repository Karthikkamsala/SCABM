"""Shipment representation for physical goods movement.

A shipment tracks the transit of goods from one supply-chain agent
to another, including lead time and arrival logic.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class ShipmentStatus(Enum):
    """Lifecycle states of a shipment."""

    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


class Shipment:
    """A physical shipment of goods between supply-chain agents.

    Attributes:
        origin: The agent sending the shipment.
        destination: The agent receiving the shipment.
        quantity: Number of units being shipped.
        step_created: Simulation step when the shipment was created.
        lead_time: Number of simulation steps until arrival.
        arrival_step: The simulation step when the shipment will arrive.
        status: Current lifecycle state.
    """

    def __init__(
        self,
        origin: Any,
        destination: Any,
        quantity: int,
        step_created: int,
        lead_time: int,
    ) -> None:
        """Create a Shipment.

        Args:
            origin: Agent sending the shipment.
            destination: Agent receiving the shipment.
            quantity: Units being shipped. Must be > 0.
            step_created: Simulation step of creation.
            lead_time: Steps until delivery. Must be >= 0.

        Raises:
            ValueError: If *quantity* is not positive or
                *lead_time* is negative.
        """
        if quantity <= 0:
            raise ValueError(
                f"Shipment quantity must be > 0, got {quantity}."
            )
        if lead_time < 0:
            raise ValueError(
                f"Lead time must be >= 0, got {lead_time}."
            )
        self.origin = origin
        self.destination = destination
        self.quantity: int = quantity
        self.step_created: int = step_created
        self.lead_time: int = lead_time
        self.arrival_step: int = step_created + lead_time
        self.status: ShipmentStatus = ShipmentStatus.IN_TRANSIT

    def has_arrived(self, current_step: int) -> bool:
        """Check whether the shipment has arrived by *current_step*.

        Args:
            current_step: The current simulation step.

        Returns:
            ``True`` if the shipment should be delivered.
        """
        return current_step >= self.arrival_step

    def deliver(self) -> None:
        """Mark the shipment as delivered."""
        self.status = ShipmentStatus.DELIVERED

    @property
    def is_delivered(self) -> bool:
        """``True`` if the shipment has been delivered."""
        return self.status == ShipmentStatus.DELIVERED

    def __repr__(self) -> str:
        return (
            f"Shipment(origin={self.origin}, dest={self.destination}, "
            f"qty={self.quantity}, arrives={self.arrival_step}, "
            f"status={self.status.value})"
        )
