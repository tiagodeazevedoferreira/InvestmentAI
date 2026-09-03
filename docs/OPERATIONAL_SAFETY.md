# Operational safety: kill switch and reconciliation

This layer hardens the operational controls that must exist before any demo-broker integration. It is PAPER/research infrastructure only.

## Kill switch

`OperationalKillSwitch` is an independent, fail-closed stop state. It records:

- active/inactive state;
- mandatory activation reason;
- activation timestamp;
- operator identity.

Activation blocks operations through `require_clear()`. Reset requires an explicit operator. The service does not submit, cancel or modify orders.

A future broker adapter must consume the kill-switch state at its authorization boundary rather than treating a model signal as permission to trade.

## Reconciliation

`OperationalReconciler` compares an internal account snapshot with an external execution snapshot. It is broker-neutral and read-only.

The current contract checks:

- cash within an explicit absolute tolerance;
- exact position quantities by normalized symbol;
- exact open-order identifier sets;
- execution identifier sets in both directions;
- evidence freshness and rejection of future timestamps.

Any mismatch or stale evidence produces `blocked`; only a complete, fresh match produces `healthy`.

Missing external evidence must therefore not be interpreted as healthy. The evaluator is intentionally conservative.

## Boundary

This layer does **not**:

- connect to a broker;
- enable live trading;
- change signal generation;
- change risk limits or sizing;
- authorize capital deployment.

Before demo work, the next required step is an actual Doto/MT5 demo adapter with broker-specific order semantics and end-to-end reconciliation tests. Live execution remains disabled.
