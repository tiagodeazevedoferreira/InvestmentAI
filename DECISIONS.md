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

## ADR-022 — Shared cross-asset model as a controlled experiment
After diagnosis, a candidate improvement may pool the same leakage-safe, scale-invariant technical features across assets into one shared supervised model. Each target asset keeps the existing walk-forward test windows; training uses only observations from all assets that precede the target fold's purge boundary. The experiment must compare pooled and asset-specific probabilities on identical OOS timestamps with paired statistics. It does not alter trading thresholds, execution policy, broker authorization or the live gate.

## ADR-023 — Broker-independent scheduled paper execution
The first scheduled automation uses the existing deterministic RSI paper policy, OpenBB/yfinance B3 daily data and Firebase as the durable decision ledger. It runs only in a weekday post-close window, is serialized through GitHub Actions concurrency, and derives idempotency from symbol + completed bar timestamp + action. A duplicate invocation must skip without submitting another paper order. Firebase is mandatory for scheduled execution so a retry cannot silently start from a fresh account. This stage does not add broker authority or change the live gate.

## ADR-024 — DEMO execution remains manually authorized and identifier-reconciled
The Doto/MT5 DEMO path may be used for controlled, explicitly authorized validation, but it must remain disconnected from the scheduler and permanently separated from LIVE execution. A market order is considered externally verified only when its broker lifecycle can be reconciled through stable identifiers (deal, order and/or position), not solely through a local UTC time-window query. This is necessary because broker/server history timestamps may differ from the local application clock. Post-execution reconciliation should query the specific deal first, then order/position fallbacks, and fail closed when expected external evidence cannot be recovered. Verification runs must be read-only and must never submit a second order merely to test reporting or reconciliation. The 2026-09-11 validation established order `29453207` → deal `28862296` → open position `29453207` for `EURUSD BUY 0.01`; this transaction is the reference DEMO validation and no duplicate verification order is permitted.

## ADR-025 — Submitted DEMO orders recover only from explicit broker evidence
A DEMO order left in `SUBMITTED`/uncertain state must not be retried merely because confirmation is delayed or a process restarts. Recovery may promote it to `FILLED` only when the persisted broker deal identifier is found in broker execution history. An open order, symbol position, elapsed time, or missing evidence is insufficient to infer execution. Until concrete deal evidence exists, the ledger remains `SUBMITTED` and the safe action is reconciliation rather than a new order. This policy prevents duplicate execution after timeouts, reporting failures, or application restarts.

## ADR-026 — Restart/recovery validation is read-only and preserves ambiguity
The 2026-09-11 empirical restart/recovery test uses the actual persisted DEMO ledger after the reference DOTO/MT5 transaction. A historical `SUBMITTED` record without broker order/deal identifiers remained `SUBMITTED`; the already confirmed `FILLED` reference transaction remained unchanged. The recovery coordinator did not call broker submission, create a new intent, or alter the existing EURUSD position. This validates that an application restart cannot turn ambiguous state into a duplicate broker submission and that recovery remains fail-closed when exact external evidence is unavailable.

## ADR-027 — Broker-connected recovery validation must use a disposable ledger
The DEMO recovery path can be empirically validated against real broker history without creating another order. The validation harness must use a temporary/disposable local ledger, seed it with the already confirmed broker order/deal identifiers, query targeted MT5 history, and verify `SUBMITTED -> FILLED` only from exact deal evidence. A second synthetic `SUBMITTED` record with unrelated identifiers must remain pending. The harness must prove `order_send` is not called and must discard its temporary state. This validates the recovery boundary without authorizing another broker transaction.

## ADR-028 — Submission-interruption recovery is fault-injected until a real interruption can be observed safely
The controlled DEMO execution coordinator must treat an exception after local authorization and before a broker response as uncertain, preserving the intent as recoverable `SUBMITTED` rather than `FAILED` and never retrying automatically. This boundary is covered by a fault-injected test that verifies the broker submission was attempted and the durable ledger remains `SUBMITTED`. A real broker interruption cannot be deliberately induced solely for validation because doing so could create an additional DEMO position or duplicate execution. Therefore the empirical broker-connected recovery harness remains read-only, while the actual interrupted-submission scenario remains an explicit promotion-gate item until it can be observed naturally without creating a new transaction.

## ADR-029 — Scheduler-to-DEMO integration stops at a fail-closed promotion plan
The PAPER scheduler may expose its deterministic decision, quantity, reference price and independent risk result to a dedicated DEMO promotion boundary. That boundary is disabled by default, requires an explicit PAPER-to-DEMO symbol mapping, and produces only an `OrderIntent` plan; it does not own a broker, call `order_send`, or invoke the controlled DEMO execution service. This establishes the integration contract without creating an automatic path to the existing DEMO position. Actual scheduler-driven DEMO submission remains a separate promotion step requiring explicit authorization and additional end-to-end validation.
