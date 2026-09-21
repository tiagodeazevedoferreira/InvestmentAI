# Task 013 — Real-data XGBoost OOS Economic Report

- **TASK_ID:** `codex-20260921-013`
- **STATUS:** IN PROGRESS
- **Scope:** offline/research validation only

## Objective

Produce a reproducible economic report from the existing real-data XGBoost OOS pipeline for the controlled B3 sample, separating model/OOS behavior from economic backtest behavior.

## Fixed configuration

- Symbols: PETR4, VALE3, ITUB4
- Historical range: 2021-09-15 through 2026-09-15
- Interval: 1d
- Horizon: 5 bars
- Train size: 500 observations
- Test size: 100 observations
- Step: 100 observations
- Signal threshold: 0.60
- Initial cash: 100000
- Commission: 0.1%
- Slippage: 5 bps

## Required outputs

For each asset:

- data-quality status and row count;
- OOS fold and prediction counts;
- OOS evaluation interval;
- strategy final cash and return;
- buy-and-hold benchmark return over the OOS interval;
- excess return versus that benchmark;
- maximum drawdown;
- trade count;
- total commission;
- total slippage;
- final position.

## Controls

- Reuse the existing `run_xgboost_oos_backtest()` implementation.
- Do not introduce a second backtesting engine.
- Do not optimize the threshold from the observed report.
- Do not modify robustness gates from report results.
- Do not invoke MT5, DOTO or any broker order submission.
- Treat results as diagnostic rather than evidence of production readiness or profitability.

## CI

Workflow: `.github/workflows/xgboost-oos-economic-report.yml`

The workflow runs on the designated self-hosted Windows runner, installs the project dependencies, executes the real-data report and uploads the JSON artifact.

## Acceptance criteria

- [ ] Real-data report completes for all three controlled B3 assets.
- [ ] Report artifact is generated.
- [ ] Backend compilation passes.
- [ ] No broker execution is invoked.
- [ ] Results are documented without threshold optimization or performance ranking.

## Next stage

After the report is validated, review temporal stability and economic sensitivity without tuning to the same evaluation sample. Any robustness conclusion must remain descriptive and preserve the existing fail-closed execution controls.