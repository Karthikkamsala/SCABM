"""supplychain-abm: Agent-based simulation of supply chains.

A virtual laboratory for experimenting with supply-chain decisions,
disruptions, and policies.

Quick start::

    from supplychain_abm import SupplyChainModel

    model = SupplyChainModel(seed=42)
    supplier = model.add_supplier("Supplier", inventory=1000)
    warehouse = model.add_warehouse("Warehouse", inventory=100,
                                    reorder_point=50, order_quantity=100)
    customer = model.add_customer("Customer", demand=10)
    model.connect(supplier, warehouse, lead_time=3)
    model.connect(warehouse, customer, lead_time=1)
    model.run(steps=30)
    print(model.results())
"""

from supplychain_abm.model.supply_chain_model import SupplyChainModel

# Agents
from supplychain_abm.agents.supplier import SupplierAgent
from supplychain_abm.agents.factory import FactoryAgent
from supplychain_abm.agents.warehouse import WarehouseAgent
from supplychain_abm.agents.retailer import RetailerAgent
from supplychain_abm.agents.customer import CustomerAgent

# Core data objects
from supplychain_abm.inventory.inventory import Inventory
from supplychain_abm.orders.order import Order, OrderStatus
from supplychain_abm.shipments.shipment import Shipment, ShipmentStatus

# Demand
from supplychain_abm.demand.demand import (
    ConstantDemand,
    DemandGenerator,
    RandomDemand,
    SeasonalDemand,
)

# Policies
from supplychain_abm.policies.inventory_policy import (
    InventoryPolicy,
    ReorderPointPolicy,
)

# Network
from supplychain_abm.network.network import SupplyChainNetwork

# Metrics
from supplychain_abm.metrics.metrics import MetricsCollector

__version__ = "0.1.0"

__all__ = [
    # Model
    "SupplyChainModel",
    # Agents
    "SupplierAgent",
    "FactoryAgent",
    "WarehouseAgent",
    "RetailerAgent",
    "CustomerAgent",
    # Data objects
    "Inventory",
    "Order",
    "OrderStatus",
    "Shipment",
    "ShipmentStatus",
    # Demand
    "DemandGenerator",
    "ConstantDemand",
    "RandomDemand",
    "SeasonalDemand",
    # Policies
    "InventoryPolicy",
    "ReorderPointPolicy",
    # Network
    "SupplyChainNetwork",
    # Metrics
    "MetricsCollector",
]
