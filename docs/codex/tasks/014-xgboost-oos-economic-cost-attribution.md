# Task 014 — XGBoost OOS Economic Cost Attribution

STATUS: IN PROGRESS

## Objective

Decompose the real-data XGBoost OOS economic result into model/signal performance and transaction-cost effects without changing model parameters or optimizing the decision threshold.

## Scope

Controlled B3 sample:
- PETR4
- VALE3
- ITUB4
- 2021-09-15 through 2026-09-15
- horizon 5
- train size 500
- test size 100
- step 100
- threshold 0.60

Cost scenarios:
1. zero commission / zero slippage;
2. commission only: 0.1%;
3. slippage only: 5 bps;
4. commission + slippage: 0.1% + 5 bps.

## Acceptance criteria

- Reuse the existing provider, feature, purged XGBoost OOS and Backtester paths.
- Keep model parameters and threshold unchanged across scenarios.
- Use the exact OOS replay window for every scenario.
- Report final cash, return, drawdown, trades, commission and slippage for every symbol/scenario.
- Report incremental impact attributable to commission and slippage relative to the zero-cost scenario.
- Do not optimize or select a threshold from the OOS results.
- Add deterministic contract tests for scenario consistency.
- Run the report through the self-hosted Windows runner.
- Keep the task research-only; no MT5/DOTO execution or model-promotion changes.
