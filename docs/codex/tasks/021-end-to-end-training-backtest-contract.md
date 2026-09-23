# Task 021 — End-to-end training/backtest contract

Status: IN PROGRESS

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

1. A deterministic provider frame can flow through training and model artifact persistence.
2. The persisted artifact can be loaded and used for inference with its feature-schema contract.
3. The same validation run can generate purged OOS predictions and replay them economically.
4. OOS timestamps are unique and chronological.
5. The economic replay finishes flat with finite final cash and non-negative costs.
6. Invalid provider output fails closed before model persistence.
7. The contract uses no broker, MT5, DOTO or financial transaction.
8. Existing backend tests remain green.
9. Backend compilation and security checks remain green.
10. Results and limitations are documented.

## Safety boundary

Passing this task validates engineering integration only. It does not establish profitability, robustness, model superiority, production readiness or permission to execute trades.

## Validation record

Pending CI validation.

Runner: ECTIN8F38594
