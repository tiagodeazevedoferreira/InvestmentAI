# Task 010 — Real Dataset Training Workflow Results

- **TASK_ID:** `codex-20260915-010`
- **STATUS:** PASS
- **Validation date:** 2026-09-16

## Configuration

- Symbols: `PETR4.SA`, `VALE3.SA`, `ITUB4.SA`
- Provider: OpenBB → yfinance
- Interval: `1d`
- Period: `5y`
- Horizon: `5`
- Feature version: `technical-v1`
- XGBoost: 300 estimators, depth 4, learning rate 0.05, subsample 0.8, column subsample 0.8, random state 42, `logloss`

## Dataset quality

Each symbol returned 1248 daily observations covering `2021-09-15` through `2026-09-15`. All three datasets passed the canonical market-data quality gate. Seven large calendar gaps were reported per dataset with a maximum gap of five days; these remained observability metadata and were not automatic failures.

## Results

| Symbol | Samples | Positive labels | Accuracy | Precision | Recall | ROC AUC |
|---|---:|---:|---:|---:|---:|---:|
| PETR4.SA | 1223 | 651 | 0.445652 | 0.518182 | 0.537736 | 0.399008 |
| VALE3.SA | 1222 | 633 | 0.494565 | 0.525000 | 0.432990 | 0.506932 |
| ITUB4.SA | 1223 | 648 | 0.554348 | 0.593023 | 0.520408 | 0.632534 |

## Validation checks

- Focused XGBoost tests: 3 passed.
- Complete backend suite: 43 passed.
- `compileall -q backend`: passed.
- Static safety scan: clean.
- No `mt5.order_send()` call.
- No financial transaction submitted.
- No model promoted to production.

## Interpretation

The run demonstrates a reproducible, quality-gated real-data training path for the controlled B3 sample. It is diagnostic evidence only and does not establish profitability, robustness across the universe or market regimes, production readiness, or live-trading authorization.
