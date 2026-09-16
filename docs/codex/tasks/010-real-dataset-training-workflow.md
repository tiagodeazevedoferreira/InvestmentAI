# Task 010 — Real Dataset Training Workflow

- **TASK_ID:** `codex-20260915-010`
- **STATUS:** PASS
- **Date:** 2026-09-16
- **Scope:** offline diagnostic training only

## Objective

Formalize and validate the first reproducible InvestmentAI XGBoost training workflow using real historical datasets while preserving the existing feature engineering, leakage-safe temporal split and model engine. Invalid market data must be rejected before feature engineering/training and the resulting artifacts must remain auditable.

## Scope

Controlled B3 sample:

- `PETR4.SA`
- `VALE3.SA`
- `ITUB4.SA`

Default configuration:

- provider: OpenBB with yfinance;
- interval: `1d`;
- period: `5y`;
- horizon: `5` bars.

The workflow is broker-independent and never submits MT5/DOTO orders.

## Implemented

`train_symbol_baseline()` now:

1. validates its symbol, period and provider contract;
2. obtains historical data from the provider;
3. applies the canonical `validate_market_data()` quality gate;
4. fails closed on invalid market data;
5. reuses the existing `build_features()` pipeline;
6. reuses the existing XGBoost engine and five-bar temporal purge;
7. persists model and metadata artifacts;
8. records provider, interval, period, horizon, feature configuration, parameters, metrics, sample counts and the quality report.

The OpenBB history provider translates the requested period into explicit dates and requests daily data from yfinance, preserving the `history(symbol, period)` provider contract.

## Validation

Dedicated XGBoost tests covered successful persistence, metadata, invalid-data rejection and the provider contract.

- Focused tests: **3 passed**.
- Complete backend suite: **43 passed**.
- `compileall -q backend`: passed.
- Static safety scan: clean.

Real-data run:

| Symbol | Raw rows | Training samples | Positive labels | Accuracy | Precision | Recall | ROC AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| PETR4.SA | 1248 | 1223 | 651 | 0.445652 | 0.518182 | 0.537736 | 0.399008 |
| VALE3.SA | 1248 | 1222 | 633 | 0.494565 | 0.525000 | 0.432990 | 0.506932 |
| ITUB4.SA | 1248 | 1223 | 648 | 0.554348 | 0.593023 | 0.520408 | 0.632534 |

All three datasets covered `2021-09-15` through `2026-09-15` and passed the canonical quality gate. Calendar gaps were retained as observability metadata rather than automatic failures.

## Acceptance

- [x] Real historical datasets accepted only after the canonical quality gate.
- [x] Invalid datasets fail before feature engineering/training.
- [x] Existing feature engineering preserved.
- [x] Existing five-bar temporal purge preserved.
- [x] XGBoost baseline training remains chronological and offline.
- [x] Model and auditable metadata are persisted.
- [x] Controlled PETR4/VALE3/ITUB4 validation completed.
- [x] No MT5/DOTO execution or financial transaction performed.

## Boundary

Task 010 is diagnostic only. The results do not establish profitability, model superiority, complete-universe robustness, production readiness or permission to execute trades.
