"""Shared fixtures for tests."""

import pytest

from supplychain_abm.orders.order import reset_order_counter


@pytest.fixture(autouse=True)
def _reset_order_ids():
    """Reset the global order-ID counter before each test."""
    reset_order_counter()
