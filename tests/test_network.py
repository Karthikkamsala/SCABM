"""Tests for the SupplyChainNetwork."""

import pytest

from supplychain_abm.network.network import SupplyChainNetwork


class TestNetworkNodes:
    def test_add_node(self):
        net = SupplyChainNetwork()
        net.add_node("A")
        assert net.has_node("A") is True

    def test_duplicate_node_raises(self):
        net = SupplyChainNetwork()
        net.add_node("A")
        with pytest.raises(ValueError, match="already in the network"):
            net.add_node("A")


class TestNetworkConnections:
    def test_add_connection(self):
        net = SupplyChainNetwork()
        net.add_node("A")
        net.add_node("B")
        net.add_connection("A", "B", lead_time=3)
        assert net.get_lead_time("A", "B") == 3

    def test_self_connection_raises(self):
        net = SupplyChainNetwork()
        net.add_node("A")
        with pytest.raises(ValueError, match="Cannot connect an agent to itself"):
            net.add_connection("A", "A")

    def test_missing_source_raises(self):
        net = SupplyChainNetwork()
        net.add_node("B")
        with pytest.raises(ValueError, match="not in the network"):
            net.add_connection("A", "B")

    def test_duplicate_connection_raises(self):
        net = SupplyChainNetwork()
        net.add_node("A")
        net.add_node("B")
        net.add_connection("A", "B", lead_time=1)
        with pytest.raises(ValueError, match="already exists"):
            net.add_connection("A", "B", lead_time=2)

    def test_negative_lead_time_raises(self):
        net = SupplyChainNetwork()
        net.add_node("A")
        net.add_node("B")
        with pytest.raises(ValueError, match="must be >= 0"):
            net.add_connection("A", "B", lead_time=-1)


class TestNetworkQueries:
    def test_upstream_downstream(self):
        net = SupplyChainNetwork()
        net.add_node("S")
        net.add_node("W")
        net.add_node("C")
        net.add_connection("S", "W", lead_time=3)
        net.add_connection("W", "C", lead_time=1)
        assert net.get_upstream("W") == ["S"]
        assert net.get_downstream("W") == ["C"]
        assert net.get_upstream("S") == []
        assert net.get_downstream("C") == []

    def test_missing_lead_time_raises(self):
        net = SupplyChainNetwork()
        net.add_node("A")
        net.add_node("B")
        with pytest.raises(ValueError, match="No connection"):
            net.get_lead_time("A", "B")

    def test_nodes_and_edges(self):
        net = SupplyChainNetwork()
        net.add_node("A")
        net.add_node("B")
        net.add_connection("A", "B", lead_time=2)
        assert len(net.nodes) == 2
        assert len(net.edges) == 1
