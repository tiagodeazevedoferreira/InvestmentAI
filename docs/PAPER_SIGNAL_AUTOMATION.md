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

This endpoint is not a market-data downloader and does not call a broker.

## Scheduled orchestration

`scripts/run_paper_scheduler.py` obtains daily B3 history through OpenBB/yfinance for PETR4, VALE3 and ITUB4 and invokes the same paper policy. The GitHub Actions workflow runs at 20:30 UTC (17:30 BRT) on weekdays. A post-close guard rejects weekends and runs outside 17:00–23:00 BRT.

Each decision receives a deterministic id from symbol + bar timestamp + action. The Firebase ledger persists the decision before execution and marks it completed afterward. Pending decisions are resumable, while completed decisions are skipped. Paper orders also receive the same deterministic client order id, so a retry cannot create a second fill for the same decision.

Manual dispatch supports `shadow` mode and an explicit `force` guard bypass for validation. Scheduled execution requires Firebase so the paper account and ledger survive separate GitHub Actions runners.

## Outcome attribution

`backend/app/services/paper_outcomes.py` provides a provider-independent attribution primitive. Given a completed decision and the corresponding OHLCV history, it evaluates forward returns at configurable horizons, defaulting to 1, 5 and 20 bars. BUY and SELL decisions use a signed return convention so a positive value means the decision direction was favorable; HOLD observations retain the market return but are not classified as hits.

If a horizon has not completed yet, the observation is explicitly returned without an outcome price, return or hit classification. This prevents incomplete paper observations from being counted as failures or successes. `summarize_outcomes()` aggregates completed observations by action and horizon into observation count, hit rate, mean signed return and median signed return.

These primitives are intentionally separate from model promotion. A future calibration report must use completed, timestamp-aligned paper observations and should report sample size and incomplete horizons before any empirical promotion decision is considered.

## Safety

This automation remains strictly PAPER. It has no live broker authority and cannot promote the application to `live`. Model predictions are not yet allowed to override the deterministic risk gate.

## Next step

Persist and retrieve attributed outcomes from the Firebase decision ledger, generate a calibration report across PETR4/VALE3/ITUB4, add paper-to-TradingView reconciliation automation, and then implement kill-switch/reconciliation controls. Only after those controls and empirical evidence are stable should a broker demo adapter be introduced.
