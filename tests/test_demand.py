"""Tests for demand generators."""

import numpy as np
import pytest

from supplychain_abm.demand.demand import (
    ConstantDemand,
    RandomDemand,
    SeasonalDemand,
)


class TestConstantDemand:
    def test_always_returns_same(self):
        d = ConstantDemand(quantity=10)
        assert d.generate(0) == 10
        assert d.generate(5) == 10
        assert d.generate(100) == 10

    def test_zero_quantity_raises(self):
        with pytest.raises(ValueError, match="must be > 0"):
            ConstantDemand(quantity=0)

    def test_repr(self):
        d = ConstantDemand(quantity=10)
        assert "ConstantDemand" in repr(d)


class TestRandomDemand:
    def test_produces_non_negative(self):
        rng = np.random.default_rng(42)
        d = RandomDemand(mean=5, std=3, rng=rng)
        for step in range(100):
            assert d.generate(step) >= 0

    def test_reproducible_with_seed(self):
        d1 = RandomDemand(mean=10, std=2, rng=np.random.default_rng(42))
        d2 = RandomDemand(mean=10, std=2, rng=np.random.default_rng(42))
        for step in range(20):
            assert d1.generate(step) == d2.generate(step)

    def test_negative_mean_raises(self):
        with pytest.raises(ValueError, match="Mean must be >= 0"):
            RandomDemand(mean=-1, std=1)


class TestSeasonalDemand:
    def test_produces_non_negative(self):
        d = SeasonalDemand(base=10, amplitude=5, period=30)
        for step in range(60):
            assert d.generate(step) >= 0

    def test_varies_over_period(self):
        d = SeasonalDemand(base=10, amplitude=5, period=30)
        values = [d.generate(step) for step in range(30)]
        # Should have variation, not all the same
        assert len(set(values)) > 1

    def test_invalid_period_raises(self):
        with pytest.raises(ValueError, match="Period must be > 0"):
            SeasonalDemand(base=10, amplitude=5, period=0)
