"""Supply-chain network topology using NetworkX.

Wraps a ``networkx.DiGraph`` to represent the directed connections
between supply-chain agents, with edge attributes like lead time.
"""

from __future__ import annotations

from typing import Any

import networkx as nx


class SupplyChainNetwork:
    """Directed graph representing the supply-chain topology.

    Nodes are supply-chain agents. Directed edges represent material
    flow from upstream to downstream, annotated with lead time and
    optional attributes (cost, capacity, etc.).

    Example::

        net = SupplyChainNetwork()
        net.add_node(supplier)
        net.add_node(warehouse)
        net.add_connection(supplier, warehouse, lead_time=3)
    """

    def __init__(self) -> None:
        """Create an empty supply-chain network."""
        self._graph: nx.DiGraph = nx.DiGraph()

    # ------------------------------------------------------------------
    # Node management
    # ------------------------------------------------------------------

    def add_node(self, agent: Any) -> None:
        """Add a supply-chain agent as a node.

        Args:
            agent: The agent to add. Must not already be in the network.

        Raises:
            ValueError: If *agent* is already a node.
        """
        if self._graph.has_node(agent):
            raise ValueError(f"Agent {agent} is already in the network.")
        self._graph.add_node(agent)

    def has_node(self, agent: Any) -> bool:
        """Return ``True`` if *agent* is in the network."""
        return self._graph.has_node(agent)

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def add_connection(
        self,
        source: Any,
        destination: Any,
        lead_time: int = 0,
        **attrs: Any,
    ) -> None:
        """Add a directed connection from *source* to *destination*.

        Args:
            source: Upstream agent.
            destination: Downstream agent.
            lead_time: Transit time in simulation steps. Must be >= 0.
            **attrs: Additional edge attributes (e.g. cost, capacity).

        Raises:
            ValueError: If source equals destination, either agent
                is not in the network, or the connection already exists.
        """
        if source is destination:
            raise ValueError("Cannot connect an agent to itself.")
        if not self._graph.has_node(source):
            raise ValueError(
                f"Source agent {source} is not in the network."
            )
        if not self._graph.has_node(destination):
            raise ValueError(
                f"Destination agent {destination} is not in the network."
            )
        if self._graph.has_edge(source, destination):
            raise ValueError(
                f"Connection from {source} to {destination} already exists."
            )
        if lead_time < 0:
            raise ValueError(
                f"Lead time must be >= 0, got {lead_time}."
            )
        self._graph.add_edge(
            source, destination, lead_time=lead_time, **attrs
        )

    def get_lead_time(self, source: Any, destination: Any) -> int:
        """Return the lead time for the edge from *source* to *destination*.

        Args:
            source: Upstream agent.
            destination: Downstream agent.

        Returns:
            Lead time in simulation steps.

        Raises:
            ValueError: If the connection does not exist.
        """
        if not self._graph.has_edge(source, destination):
            raise ValueError(
                f"No connection from {source} to {destination}."
            )
        return self._graph.edges[source, destination]["lead_time"]

    # ------------------------------------------------------------------
    # Neighbor queries
    # ------------------------------------------------------------------

    def get_upstream(self, agent: Any) -> list[Any]:
        """Return agents that supply to *agent* (predecessors).

        Args:
            agent: The downstream agent.

        Returns:
            List of upstream agents.
        """
        return list(self._graph.predecessors(agent))

    def get_downstream(self, agent: Any) -> list[Any]:
        """Return agents that *agent* supplies to (successors).

        Args:
            agent: The upstream agent.

        Returns:
            List of downstream agents.
        """
        return list(self._graph.successors(agent))

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    @property
    def nodes(self) -> list[Any]:
        """All agents in the network."""
        return list(self._graph.nodes)

    @property
    def edges(self) -> list[tuple[Any, Any, dict]]:
        """All connections as ``(source, dest, attrs)`` triples."""
        return list(self._graph.edges(data=True))

    @property
    def graph(self) -> nx.DiGraph:
        """The underlying NetworkX DiGraph (read-only access)."""
        return self._graph

    def __repr__(self) -> str:
        return (
            f"SupplyChainNetwork(nodes={len(self._graph.nodes)}, "
            f"edges={len(self._graph.edges)})"
        )
