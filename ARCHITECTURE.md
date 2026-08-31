# Architecture

## Logical layers

1. **Presentation**: static HTML/CSS/JS PWA on GitHub Pages.
2. **API**: FastAPI REST endpoints and OpenAPI documentation.
3. **Domain services**: valuation, technical analysis, backtesting, portfolio optimization, risk, ML and execution.
4. **Infrastructure**: market-data providers, Firebase Realtime Database and future broker adapters.
5. **Automation**: GitHub Actions for tests, data jobs and model training.

## Execution boundary
Prediction never directly places an order. The path is:

`model -> signal engine -> risk engine -> position sizing -> order manager -> broker adapter`.

The broker adapter is environment-aware and refuses live operations unless the live promotion gate is satisfied.

## Firebase boundary
Firebase stores compact operational state: watchlists, portfolios, signals, predictions, orders, executions, configuration, model metadata and audit records. Large raw time series should remain in external/ephemeral datasets or artifacts and be transformed before persistence.

## Resilience
Provider failures return explicit domain errors; API endpoints use stable response models. Missing fields are represented as null/optional values rather than silently fabricated. Retries and rate limiting belong to infrastructure adapters.

## Quantitative integrity
- Adjusted vs unadjusted price semantics must be explicit.
- Features use information available at prediction time only.
- Train/validation/test are chronological.
- Backtests account for cash, position state and eventually fees/slippage.
- Model metrics must be evaluated out-of-sample.
