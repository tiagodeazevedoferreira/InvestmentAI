# Task 022 — Transaction-cost calibration framework

**Status:** COMPLETE

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

Validation completed on 2026-09-24 against main commit `04989d545041360a1915e7352a76bfe5e2540a8a`.

Validation:
- CI run `36024066096`: success.
- Phase 10 Live Gate Tests run `36024066079`: success.
- External Intelligence Validation run `36024066058`: success.
- Cross-Asset ML Experiment run `36024066039`: success.
- Security and Dependency Scan run `36024066035`, attempt 2: success.
- Security attempt 2 completed dependency audit, Bandit static scan, backend tests and backend compilation successfully on runner `ECTIN8F38594`.

The initial security attempt was externally cancelled during the Bandit step after reporting no issues identified; the failed attempt was rerun and completed successfully.

Runner: ECTIN8F38594
