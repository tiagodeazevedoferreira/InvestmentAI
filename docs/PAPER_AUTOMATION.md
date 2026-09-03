# Paper automation

The paper automation boundary connects a market-data provider to the existing signal/order infrastructure without exposing a live broker.

## Flow

`Provider -> technical decision -> deterministic signal_id -> Risk/OrderManager -> Paper Broker -> portfolio accounting`

`signal_id` is derived from symbol, latest bar timestamp and action so the same market bar/action can be recognized across repeated scheduler runs.

## Safety

- Paper execution only.
- No live broker credentials are read by this module.
- Missing/insufficient data raises a controlled `ValueError`.
- Orders are generated only for BUY/SELL decisions; HOLD creates no order.
- Position sizing remains bounded by the downstream order/risk layer.

## Current strategy adapter

The first provider-backed adapter uses RSI(14): BUY below 30, SELL above 70, otherwise HOLD. This is intentionally a baseline execution path, not the production investment policy. XGBoost, fundamental valuation, portfolio optimization and the final RiskGate remain higher-level decision components.

## Next integration

The scheduler should call the provider for the configured B3 universe, persist the last processed bar/signal state, and pass every candidate through the same RiskGate and Paper Execution boundary. A reconciliation job must compare internal positions/orders/fills with the paper account state before any future demo broker is enabled.
