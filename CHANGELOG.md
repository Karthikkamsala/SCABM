# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-09-21

### Added

- Initial release of `supplychain-abm`.
- Core agent types: Supplier, Factory, Warehouse, Retailer, Customer.
- Inventory management with stockout tracking.
- Order lifecycle (Created → Accepted → Shipped → Delivered).
- Shipment tracking with configurable lead times.
- Demand generators: Constant, Random, Seasonal.
- Inventory policy: Reorder Point Policy.
- Supply-chain network using NetworkX directed graph.
- Metrics collection: inventory, service level, stockouts, orders, costs.
- Matplotlib visualizations: inventory, demand, orders, service level, bullwhip.
- Reproducible simulations via random seed support.
- Example scripts: basic supply chain, supplier disruption, demand increase, inventory policy comparison, bullwhip effect.
- Comprehensive test suite using pytest.
