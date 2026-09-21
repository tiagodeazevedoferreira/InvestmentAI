# Task 012 — XGBoost OOS → Economic Backtest Contract

- **TASK_ID:** `codex-20260921-012`
- **STATUS:** IN PROGRESS
- **Date:** 2026-09-21
- **Scope:** offline/research validation only

## Objective

Harden and validate the existing XGBoost out-of-sample pipeline through the deterministic economic backtest boundary.

The task connects the existing feature engineering, purged XGBoost walk-forward predictions, probability-to-signal conversion, timestamped MarketReplay, and cost/slippage-aware Backtester.

No new training architecture, threshold optimization, broker integration, execution authority, or production promotion is part of this task.

## Implemented

### OOS contract metadata

`backend/app/services/xgboost_oos.py` now exposes per-fold metadata containing training and test start/end timestamps plus fold number.

The service validates that OOS test windows do not overlap.

The contract test validates fold metadata count, prediction/probability row counts, chronological boundaries, exact five-observation purge semantics, exact test-window size, and non-overlapping OOS windows.

The purge is represented positionally as `test_start - train_end == horizon + 1` because `train_end` is the last included training row and the horizon observations between the two boundaries are excluded.

### Economic replay contract

`tests/test_xgboost_oos_economic_contract.py` validates the existing `run_xgboost_oos_backtest()` path using deterministic synthetic OHLCV.

The test checks OOS predictions, flat final position, finite final cash, non-negative commission/slippage, replay start at the first OOS prediction, and replay end exactly one bar after the final OOS prediction.

No broker or external market-data dependency is used by this contract test.

## CI validation

Workflow: `.github/workflows/xgboost-oos-contract.yml`

The workflow runs on the designated self-hosted Windows runner and performs environment preparation, OOS contract tests, the economic replay contract test, the complete backend suite, and backend compilation.

The first OOS contract validation completed green after correcting the test positional purge assertion. The economic replay contract was added afterward and requires the updated workflow to be executed.

## Acceptance criteria

- [x] OOS fold metadata is explicit and timestamped.
- [x] OOS test windows are rejected if they overlap.
- [x] Purge semantics are covered by a deterministic contract test.
- [x] Existing economic replay path is covered by a deterministic integration contract.
- [ ] Updated workflow passes OOS contract tests.
- [ ] Updated workflow passes the complete backend suite.
- [ ] Updated workflow passes backend compilation.
- [ ] Validation confirms no financial execution path is invoked.

## Non-goals

This task does not retrain a new production model, tune thresholds for performance, change the robustness gate, claim profitability, authorize DEMO or LIVE execution, invoke MT5 order submission, or change execution authority.

## Next stage

After this contract is green, the next narrow validation should be a reproducible real-data economic report for the controlled B3 sample, explicitly separating model/OOS prediction metrics, economic backtest metrics, benchmark metrics, transaction costs, and robustness-gate observations.

That report must remain diagnostic and must not promote the model or alter execution controls.