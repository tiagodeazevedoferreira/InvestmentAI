# Task 021 — End-to-end training/backtest contract

**Status:** COMPLETE

## Objective

Close the remaining engineering gap between model training, persisted model artifacts, inference, OOS signal generation and deterministic economic replay in one automated contract.

## Scope

- deterministic provider fixture;
- XGBoost baseline training and artifact persistence;
- persisted-artifact inference;
- purged OOS prediction generation;
- probability-to-signal conversion;
- OOS-bounded MarketReplay/Backtester execution;
- deterministic economic invariants and fail-closed provider validation.

## Non-goals

- no real broker or MT5/DOTO execution;
- no model tuning or threshold optimization;
- no profitability claim;
- no production model promotion;
- no change to backtest semantics;
- no change to execution authorization.

## Acceptance criteria

1. A deterministic provider frame can flow through training and model artifact persistence. **PASS**
2. The persisted artifact can be loaded and used for inference with its feature-schema contract. **PASS**
3. The same validation run can generate purged OOS predictions and replay them economically. **PASS**
4. OOS timestamps are unique and chronological. **PASS**
5. The economic replay finishes flat with finite final cash and non-negative costs. **PASS**
6. Invalid provider output fails closed before model persistence. **PASS**
7. The contract uses no broker, MT5, DOTO or financial transaction. **PASS**
8. Existing backend tests remain green. **PASS**
9. Backend compilation and security checks remain green. **PASS**
10. Results and limitations are documented. **PASS**

## Validation

Validated after merge to `main` commit `5d20758c805e265242993c158e23085c3a413752`.

- CI workflow: **35924094964 — success**.
- Security and Dependency Scan: **35924094928 — success**.
- Paper Scheduler regression validation: **35931703323 — success**.
- Self-hosted runner: `ECTIN8F38594`.
- The end-to-end contract test is part of the backend test suite executed by CI.
- The contract exercises deterministic synthetic OHLCV data, XGBoost artifact persistence/inference, purged OOS prediction generation and deterministic economic replay.
- No MT5/DOTO execution or financial transaction occurred.

### Limitations

This validation establishes an engineering integration contract only. It does not establish profitability, robustness, model superiority, production readiness, model promotion or permission to execute trades.

The economic replay uses deterministic configured commission/slippage assumptions. Venue-specific empirical transaction-cost calibration remains a separate engineering task.

## Safety boundary

Passing this task validates engineering integration only. It does not establish profitability, robustness, model superiority, production readiness or permission to execute trades.
