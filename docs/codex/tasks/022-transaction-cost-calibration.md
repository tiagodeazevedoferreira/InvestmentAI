# Task 022 — Transaction-cost calibration framework

**Status:** IN PROGRESS

## Objective

Create a deterministic, provider-neutral transaction-cost calibration layer that converts observed execution-cost records into validated venue profiles that can be consumed by economic backtests without changing model signals, thresholds or execution authorization.

## Scope

- normalize observed commission and slippage into basis-point metrics;
- calculate descriptive median and p95 transaction-cost statistics by venue;
- validate cost observations and fail closed on invalid values;
- expose a reusable immutable calibration profile;
- preserve explicit provenance for the observation set;
- add deterministic contract tests;
- keep the existing XGBoost OOS artifacts and backtest semantics unchanged.

## Non-goals

- no broker or MT5/DOTO execution;
- no new DEMO transaction;
- no automatic live-cost discovery;
- no threshold optimization;
- no model tuning;
- no model promotion;
- no automatic replacement of existing backtest assumptions;
- no profitability claim.

## Acceptance criteria

1. A valid set of observed execution records can be calibrated into a venue profile.
2. Commission and slippage are normalized to basis points with deterministic median and p95 statistics.
3. Invalid or negative monetary values, zero/negative notional and non-finite values fail closed.
4. The calibration profile preserves venue and source provenance.
5. Repeated calibration over the same ordered observations is deterministic.
6. The layer does not access a broker or submit financial transactions.
7. Existing backend tests remain green.
8. Backend compilation and security checks remain green.
9. Validation results and limitations are documented.

## Safety boundary

This task establishes a transaction-cost measurement/calibration primitive only. It does not establish profitability, robustness, production readiness, live-trading readiness or authorization to execute trades.

## Validation record

Pending CI validation.

Runner: ECTIN8F38594
