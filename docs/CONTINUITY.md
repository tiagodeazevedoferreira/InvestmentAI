# Development continuity

## Current checkpoint

The repository has a paper execution engine and a first provider-backed automation boundary.

Implemented:
- technical RSI baseline decision (RSI14: <30 BUY, >70 SELL, otherwise HOLD)
- deterministic signal IDs based on symbol + bar timestamp + action
- provider abstraction for historical market data
- paper-only order submission through the existing OrderManager
- tests for BUY/SELL/data validation

Latest development commits:
- `01021a5` add provider-backed paper orchestration
- `cc3c935` cover provider-backed paper decisions
- `6e4c659` document paper automation boundary

## Immediate next work

1. Verify the exact OrderManager contract and adapt the orchestration layer to it.
2. Integrate the existing market-data provider abstraction instead of duplicating provider logic.
3. Add idempotency persistence for processed `signal_id` values in the bounded Firebase operational store.
4. Add a scheduler/job for the configured B3 universe (initially PETR4, VALE3, ITUB4), with market-hours guard.
5. Route automated candidates through the full SignalFusion/RiskGate/position-sizing path.
6. Add end-to-end tests covering provider -> decision -> risk -> paper fill -> portfolio -> Firebase.
7. Keep live execution disabled until explicit production-gate evidence exists.

TradingView Paper Trading remains an external validation tool and is not a broker dependency of the application.
