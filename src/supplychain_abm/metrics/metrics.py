"""Metrics collection for supply-chain simulations.

The MetricsCollector aggregates per-step data from all agents and
provides summary statistics, DataFrames, and cost computations.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


class MetricsCollector:
    """Collects and aggregates simulation metrics from all agents.

    The collector stores per-step snapshots and provides methods
    to produce Pandas DataFrames and summary statistics.

    Attributes:
        holding_cost_per_unit: Cost per unit of inventory per step.
        stockout_cost_per_unit: Cost per unit of unmet demand.
    """

    def __init__(
        self,
        holding_cost_per_unit: float = 1.0,
        stockout_cost_per_unit: float = 10.0,
    ) -> None:
        """Create a MetricsCollector.

        Args:
            holding_cost_per_unit: Holding cost per unit per step.
            stockout_cost_per_unit: Penalty cost per unit of stockout.
        """
        self.holding_cost_per_unit = holding_cost_per_unit
        self.stockout_cost_per_unit = stockout_cost_per_unit
        self._records: list[dict[str, Any]] = []

    def record(self, data: dict[str, Any]) -> None:
        """Append a single metrics record.

        Args:
            data: A dictionary containing at least ``"step"`` and
                ``"agent"`` keys.
        """
        self._records.append(data)

    def collect_from_agents(self, agents: list[Any]) -> None:
        """Pull the latest metrics from each agent's history.

        This is called automatically by the model at each step.
        """
        for agent in agents:
            if hasattr(agent, "metrics_history") and agent.metrics_history:
                latest = agent.metrics_history[-1]
                self._records.append(latest)

    def to_dataframe(self) -> pd.DataFrame:
        """Return all collected metrics as a Pandas DataFrame."""
        if not self._records:
            return pd.DataFrame()
        return pd.DataFrame(self._records)

    def agent_dataframe(self, agent_name: str) -> pd.DataFrame:
        """Return metrics for a specific agent as a DataFrame.

        Args:
            agent_name: The ``name`` of the agent to filter by.
        """
        df = self.to_dataframe()
        if df.empty:
            return df
        return df[df["agent"] == agent_name].reset_index(drop=True)

    def summary(self) -> dict[str, Any]:
        """Compute aggregate summary statistics.

        Returns:
            A dictionary with keys such as ``avg_inventory``,
            ``total_demand``, ``total_fulfilled``,
            ``overall_service_level``, ``total_stockouts``,
            ``total_holding_cost``, and ``total_stockout_cost``.
        """
        df = self.to_dataframe()
        if df.empty:
            return {}

        result: dict[str, Any] = {}

        if "inventory" in df.columns:
            result["avg_inventory"] = df["inventory"].mean()
            result["max_inventory"] = df["inventory"].max()
            result["min_inventory"] = df["inventory"].min()
            result["total_holding_cost"] = (
                df["inventory"].sum() * self.holding_cost_per_unit
            )

        if "demand" in df.columns:
            result["total_demand"] = df["demand"].sum()

        if "fulfilled" in df.columns:
            result["total_fulfilled"] = df["fulfilled"].sum()

        if "demand" in df.columns and "fulfilled" in df.columns:
            total_demand = df["demand"].sum()
            total_fulfilled = df["fulfilled"].sum()
            result["overall_service_level"] = (
                total_fulfilled / total_demand
                if total_demand > 0
                else 1.0
            )

        if "unfulfilled" in df.columns:
            total_unfulfilled = df["unfulfilled"].sum()
            result["total_stockouts"] = total_unfulfilled
            result["total_stockout_cost"] = (
                total_unfulfilled * self.stockout_cost_per_unit
            )

        return result

    def __repr__(self) -> str:
        return f"MetricsCollector(records={len(self._records)})"
