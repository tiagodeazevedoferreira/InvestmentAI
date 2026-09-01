# Decisions

## ADR-001 — Firebase Realtime Database
Firebase RTDB is the initial operational store because it integrates naturally with a lightweight frontend and server-side Admin SDK. It is not the authoritative store for unlimited raw market history.

## ADR-002 — FastAPI
FastAPI provides typed Python APIs and automatic OpenAPI/Swagger documentation while keeping domain services framework-independent.

## ADR-003 — GitHub Pages + PWA
The frontend is static and deployable from GitHub Pages. No private credential may be bundled into the frontend.

## ADR-004 — XGBoost before LSTM
The first ML baseline uses tabular Python features and XGBoost-compatible interfaces. LSTM is an experiment after a leakage-safe baseline exists.

## ADR-005 — Simulation/Paper/Demo before Live
The execution lifecycle is strictly staged. Live trading is opt-in and blocked by default.

## ADR-006 — Independent risk engine
Model confidence is never a substitute for portfolio/order risk controls.

## ADR-007 — Provider abstraction
Market data and broker integrations are adapters. Domain code must not depend directly on one vendor.

## ADR-008 — Persistent handoff documentation
Project context, status and decisions are versioned with code and updated with material changes.

## ADR-009 — Firebase size discipline
Do not persist every raw market bar indefinitely. Apply retention, deduplication, aggregation and compact derived-state storage.

## ADR-010 — OpenBB as preferred data integration layer
OpenBB is the preferred data-access abstraction because it provides a unified Python/REST interface over multiple financial data providers. yfinance remains a fallback adapter for resilience.

## ADR-011 — TradeMaster is a reference, not the core
TradeMaster and related research are used for simulator, RL and evaluation design patterns. The InvestmentAI domain architecture remains independent to avoid dependency and lifecycle coupling.

## ADR-012 — Cost-aware simulation
All strategy validation must support commission and slippage assumptions. A backtest that ignores trading frictions is not sufficient for promotion.

## ADR-013 — Model promotion gate
Models cannot progress from research to demo/live based on prediction accuracy alone. Out-of-sample financial and risk metrics must pass explicit gates.

## ADR-014 — Broker isolation
Broker SDKs are isolated behind an adapter and order-manager boundary. Simulation, demo and live credentials/endpoints are never mixed.

## ADR-015 — TradingView is validation-only
TradingView/Pine is an independent technical-validation source. It must never bypass the InvestmentAI signal engine, independent risk gate, position sizing or broker adapter. TradingView webhook events are read-only inputs until independently validated.

## ADR-016 — TradingView webhook authentication
TradingView webhook requests are authenticated with a high-entropy route token stored in `TRADINGVIEW_WEBHOOK_SECRET`. Custom HTTP authentication headers are not assumed because the TradingView webhook workflow does not provide arbitrary header configuration. The endpoint fails closed when the secret is absent and rejects invalid tokens.

## ADR-017 — Canonical technical contract
The InvestmentAI TradingView validator uses EMA 9/21, RSI 14 with 30/70 levels, Bollinger 20 with multiplier 2.0, and a 20-period volume moving average. The Pine implementation is versioned in the repository rather than depending on a community script.

## ADR-018 — OpenBB/B3 provider validation before adapter implementation
The next data-integration decision is provider selection for Brazilian equities. We will first validate current OpenBB-supported B3 coverage, provider licensing/entitlements, API-key requirements, historical depth, real-time/delayed characteristics, rate limits and symbol coverage. No provider-specific adapter will be promoted until these criteria are documented and tested.

## ADR-019 — OpenBB yfinance for first B3 proof of concept
The current OpenBB provider catalog does not expose a dedicated B3 provider. For the first B3 research/backtesting path, use the OpenBB `yfinance` extension with Yahoo `.SA` symbols. This choice requires no provider API credential and keeps the InvestmentAI domain vendor-neutral. It is not considered exchange-grade production data; an authoritative/licensed B3 source must be evaluated before live trading.

## ADR-020 — Robustness before financial promotion
The causal ML trading strategy must pass robustness checks before progressing from research toward paper/shadow execution. The audit must test probability-threshold sensitivity, transaction-cost sensitivity, performance by calendar regime, and return concentration. No single favorable backtest or prediction-accuracy result is sufficient. The result of the audit determines whether the model proceeds to stress testing/paper validation or returns to model/feature improvement. Live execution remains blocked.

## ADR-021 — Diagnose before optimizing the ML model
When robustness differs materially across assets, the next change must first quantify probability calibration, class balance, prediction bias, temporal degradation and feature distributions on the same out-of-sample walk-forward windows. Threshold selection or model changes must not be used to mask an asset-specific failure. The diagnosis is research-only and cannot authorize paper/live execution.
