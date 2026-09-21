# Task 015 — XGBoost OOS Fold-Level Economic Stability

STATUS: IN PROGRESS

## Objective

Describe the temporal stability of the already validated XGBoost OOS economic result at the individual OOS-fold level, without changing model parameters, regenerating different signals, optimizing the threshold or making model-promotion decisions.

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
- initial cash 100,000

Economic scenarios:
1. zero cost;
2. combined fixed costs: 0.1% commission + 5 bps slippage.

The same immutable OOS prediction set generated for each symbol must be reused for every fold and scenario.

## Analysis

For each symbol and OOS fold, report:
- fold number;
- train start/end;
- test start/end;
- test row count;
- fold return;
- fold max drawdown;
- trades;
- commission;
- slippage;
- final cash;
- scenario.

The primary stability interpretation uses the combined 0.1% commission + 5 bps slippage scenario. The zero-cost scenario is retained as a diagnostic reference so temporal signal economics can be distinguished from transaction-cost effects.

The report must also summarize:
- number of positive and negative folds;
- mean and median fold return;
- minimum and maximum fold return;
- standard deviation of fold returns;
- aggregate fold return dispersion;
- whether the overall result is visibly concentrated in a small number of OOS windows.

## Constraints

- Reuse the existing provider, feature engineering, purged XGBoost OOS and Backtester paths.
- Generate OOS predictions once per symbol.
- Do not optimize the threshold.
- Do not change XGBoost parameters.
- Do not rank assets or select a preferred model.
- Do not modify robustness gates or promotion logic.
- No MT5/DOTO execution or broker order submission.

## Acceptance criteria

- [ ] One immutable OOS run is generated per symbol and reused across all fold replays.
- [ ] Every OOS fold is replayed independently with the exact fold window plus the bar required for final signal execution.
- [ ] Per-fold return, drawdown and trading activity are reported for zero-cost and combined-cost scenarios.
- [ ] Aggregate descriptive dispersion statistics are reported without rankings or optimization.
- [ ] Deterministic tests verify fold slicing and OOS reuse.
- [ ] Self-hosted Windows workflow validates focused tests, real-data report and backend compilation.
- [ ] Validation documentation records the observed results and limitations.
- [ ] No financial execution occurs.
