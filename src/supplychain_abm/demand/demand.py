"""Demand generators for supply-chain simulations.

Each generator implements a ``generate`` method that returns the
demand quantity for the current simulation step.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod

import numpy as np


class DemandGenerator(ABC):
    """Abstract base class for demand generators."""

    @abstractmethod
    def generate(self, step: int) -> int:
        """Return the demand quantity for the given simulation step.

        Args:
            step: Current simulation step (0-indexed).

        Returns:
            Non-negative integer demand.
        """


class ConstantDemand(DemandGenerator):
    """Generates the same demand every step.

    Example::

        demand = ConstantDemand(quantity=10)
        demand.generate(step=0)  # 10
        demand.generate(step=5)  # 10
    """

    def __init__(self, quantity: int) -> None:
        """Create a ConstantDemand generator.

        Args:
            quantity: Fixed demand per step. Must be > 0.

        Raises:
            ValueError: If *quantity* is not positive.
        """
        if quantity <= 0:
            raise ValueError(
                f"Demand quantity must be > 0, got {quantity}."
            )
        self.quantity = quantity

    def generate(self, step: int) -> int:  # noqa: ARG002
        """Return the fixed demand quantity."""
        return self.quantity

    def __repr__(self) -> str:
        return f"ConstantDemand(quantity={self.quantity})"


class RandomDemand(DemandGenerator):
    """Generates demand from a normal distribution, clamped to >= 0.

    Example::

        demand = RandomDemand(mean=10, std=3)
        demand.generate(step=0)  # e.g. 12
    """

    def __init__(
        self,
        mean: float,
        std: float,
        rng: np.random.Generator | None = None,
    ) -> None:
        """Create a RandomDemand generator.

        Args:
            mean: Mean of the normal distribution. Must be >= 0.
            std: Standard deviation. Must be >= 0.
            rng: NumPy random generator for reproducibility.
                 If ``None``, a default generator is created.

        Raises:
            ValueError: If *mean* or *std* is negative.
        """
        if mean < 0:
            raise ValueError(f"Mean must be >= 0, got {mean}.")
        if std < 0:
            raise ValueError(f"Std must be >= 0, got {std}.")
        self.mean = mean
        self.std = std
        self.rng = rng if rng is not None else np.random.default_rng()

    def generate(self, step: int) -> int:  # noqa: ARG002
        """Return a random demand drawn from N(mean, std), clamped >= 0."""
        value = self.rng.normal(self.mean, self.std)
        return max(0, round(value))

    def __repr__(self) -> str:
        return f"RandomDemand(mean={self.mean}, std={self.std})"


class SeasonalDemand(DemandGenerator):
    """Generates demand with a sinusoidal seasonal pattern.

    The demand at step *t* is::

        demand = base + amplitude * sin(2π * t / period)

    clamped to >= 0.

    Example::

        demand = SeasonalDemand(base=10, amplitude=5, period=30)
        demand.generate(step=7)  # varies with the sine curve
    """

    def __init__(
        self,
        base: float,
        amplitude: float,
        period: float,
        rng: np.random.Generator | None = None,
        noise_std: float = 0.0,
    ) -> None:
        """Create a SeasonalDemand generator.

        Args:
            base: Baseline demand level. Must be >= 0.
            amplitude: Peak deviation from base. Must be >= 0.
            period: Length of one seasonal cycle (in steps). Must be > 0.
            rng: NumPy random generator for noise.
            noise_std: Standard deviation of additive Gaussian noise.
                Defaults to 0 (no noise).

        Raises:
            ValueError: On invalid parameters.
        """
        if base < 0:
            raise ValueError(f"Base must be >= 0, got {base}.")
        if amplitude < 0:
            raise ValueError(f"Amplitude must be >= 0, got {amplitude}.")
        if period <= 0:
            raise ValueError(f"Period must be > 0, got {period}.")
        self.base = base
        self.amplitude = amplitude
        self.period = period
        self.noise_std = noise_std
        self.rng = rng if rng is not None else np.random.default_rng()

    def generate(self, step: int) -> int:
        """Return seasonal demand for the given step."""
        seasonal = self.base + self.amplitude * math.sin(
            2 * math.pi * step / self.period
        )
        if self.noise_std > 0:
            seasonal += self.rng.normal(0, self.noise_std)
        return max(0, round(seasonal))

    def __repr__(self) -> str:
        return (
            f"SeasonalDemand(base={self.base}, amplitude={self.amplitude}, "
            f"period={self.period})"
        )
