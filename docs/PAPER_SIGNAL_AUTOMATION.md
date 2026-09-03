# Paper Signal Automation

InvestmentAI now has a controlled first automation policy connecting technical evidence to the internal paper executor.

## Pipeline

`OHLCV → technical indicators → RSI signal → risk gate → position sizing → paper order → fill → account persistence`

The policy is intentionally deterministic for the first stage:

- RSI14 < 30 → BUY
- RSI14 > 70 → SELL
- otherwise → HOLD
- short selling is not permitted by this policy
- BUY size is capped by the smaller of target portfolio allocation and `paper_max_order_notional`
- SELL requires an existing position
- HOLD never creates an order

## API

`POST /api/paper/automate`

The endpoint accepts normalized OHLCV bars and returns the decision, risk result and optional paper execution. `execute=false` is available for shadow evaluation without changing the account.

This endpoint is not a market-data downloader and does not call a broker. A future scheduler/orchestrator will obtain fresh market data through the provider abstraction and invoke this policy once per eligible bar.

## Safety

This automation remains strictly PAPER. It has no live broker authority and cannot promote the application to `live`. Model predictions are not yet allowed to override the deterministic risk gate.

## Next step

Add the provider-backed scheduler/orchestrator, idempotency by symbol/bar timestamp, shadow decision ledger, outcome attribution and reconciliation. Only after those controls are stable should a broker demo adapter be introduced.
