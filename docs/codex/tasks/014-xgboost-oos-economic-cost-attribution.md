# Task 014 — XGBoost OOS Economic Cost Attribution

STATUS: COMPLETE

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

- Reuse the existing provider, feature, purged XGBoost OOS and Backtester paths. **PASS**
- Keep model parameters and threshold unchanged across scenarios. **PASS**
- Use the exact OOS replay window for every scenario. **PASS**
- Report final cash, return, drawdown, trades, commission and slippage for every symbol/scenario. **PASS**
- Report incremental impact attributable to commission and slippage relative to the zero-cost scenario. **PASS**
- Do not optimize or select a threshold from the OOS results. **PASS**
- Add deterministic contract tests for scenario consistency. **PASS**
- Run the report through the self-hosted Windows runner. **PASS**
- Keep the task research-only; no MT5/DOTO execution or model-promotion changes. **PASS**

## Implementation hardening

The cost-attribution implementation was refactored so each symbol generates its XGBoost OOS predictions exactly once. The resulting immutable OOS run is reused across all four economic scenarios. Only the BacktestConfig transaction-cost parameters vary.

This separates model/signal generation from economic replay and prevents cost scenarios from implicitly retraining or regenerating the OOS predictions.

## Validation

The self-hosted Windows workflow completed successfully on runner ECTIN8F38594.

The deterministic cost-attribution contract test passed, the real-data report completed, the report artifact was generated, and backend compilation passed.

No MT5/DOTO execution or broker order submission was performed.

Detailed results: docs/validation/014-xgboost-oos-economic-cost-attribution-results.md.
