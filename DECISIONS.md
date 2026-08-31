# Decisions

## ADR-001 — Firebase Realtime Database
Firebase RTDB is the initial operational store because it integrates naturally with a lightweight frontend and server-side Admin SDK. It is not the authoritative store for unlimited raw market history.

## ADR-002 — FastAPI
FastAPI provides typed Python APIs and automatic OpenAPI/Swagger documentation while keeping domain services framework-independent.

## ADR-003 — GitHub Pages + PWA
The frontend is static and deployable from GitHub Pages. No private credential may be bundled into the frontend.

## ADR-004 — XGBoost before LSTM
The first ML baseline uses tabular technical features and XGBoost-compatible interfaces. LSTM is an experiment after a leakage-safe baseline exists.

## ADR-005 — Simulation/Paper/Demo before Live
The execution lifecycle is strictly staged. Live trading is opt-in and blocked by default.

## ADR-006 — Independent risk engine
Model confidence is never a substitute for portfolio/order risk controls.

## ADR-007 — Provider abstraction
Market data and broker integrations are adapters. Domain code must not depend directly on one vendor.

## ADR-008 — Persistent handoff documentation
Project context, status, roadmap and decisions are versioned with code and updated with material changes.

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
