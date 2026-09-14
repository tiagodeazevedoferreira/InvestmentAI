# Task 009 — Real Historical Data Validation

**TASK_ID:** codex-20260914-009
**STATUS:** PASS — validation gate completed on 2026-09-14

## OBJECTIVE

Validate the InvestmentAI historical market-data pipeline against a small, controlled set of real historical datasets before any real-dataset model training or strategy calibration.

The validation must remain broker-independent and must not submit, simulate, or authorize any MT5/DOTO order.

## SCOPE

Primary symbols:

- PETR4.SA
- VALE3.SA
- ITUB4.SA

Default interval:

- 1 day

The task covers:

1. Retrieval through the existing OpenBB/yfinance adapter.
2. Normalization to the canonical internal OHLCV contract.
3. Execution of the historical market-data quality gate.
4. Validation of indicators and feature engineering on real data.
5. Validation of the purged walk-forward pipeline on real data.
6. Reproducible reporting of dataset coverage and quality findings.
7. Documentation of limitations and observations without tuning the model to the observed data.

## CONTEXT

Task 008 established and validated the canonical historical OHLCV contract and quality gate using deterministic synthetic data. The adapter normalizes provider-specific columns to:

- Open
- High
- Low
- Close
- Volume

Task 008 did not establish that real historical provider data is suitable for training, backtesting, or calibration.

The existing provider uses OpenBB with the yfinance provider and exposes `historical()`, `quality()`, and `historical_with_quality()`.

## ACCEPTANCE CRITERIA

### Data retrieval

- [x] PETR4.SA historical daily data can be retrieved successfully.
- [x] VALE3.SA historical daily data can be retrieved successfully.
- [x] ITUB4.SA historical daily data can be retrieved successfully.
- [x] The retrieval path uses the existing provider adapter rather than MT5/DOTO.
- [x] The validation is reproducible with an explicit date range and interval.

### Normalization and quality

- [x] Every dataset is normalized to the canonical OHLCV columns.
- [x] The resulting index is a sorted `DatetimeIndex` named `date`.
- [x] Required-column, duplicate, null, nonfinite, monotonicity, OHLC consistency, and negative-volume checks pass.
- [x] Calendar gaps are reported and investigated rather than silently discarded.
- [x] Dataset row counts and effective start/end timestamps are recorded.

### Pipeline compatibility

- [x] Technical indicators execute successfully on each real dataset.
- [x] Feature engineering produces non-empty feature/target datasets.
- [x] Purged walk-forward validation executes successfully with the existing leakage-safe horizon.
- [x] The number of folds and rows per fold are recorded.
- [x] No model hyperparameter is changed solely to make the real dataset pass validation.

### Reproducibility and documentation

- [x] The exact symbols, date range, interval, provider, and validation date are recorded.
- [x] Provider/data-source limitations are documented.
- [x] Corporate actions/adjustment assumptions are documented where observable.
- [x] Survivorship bias, transaction costs, slippage, and other backtest limitations are explicitly distinguished from data-quality validation.
- [x] The task does not claim real-dataset training or production-readiness.

## RESULTS

Validation window:

- requested start: `2024-01-01`
- requested end: `2025-03-31`
- interval: `1d`
- provider: OpenBB with yfinance
- effective coverage: `2024-01-02` through `2025-03-31`

All three symbols returned 312 observations and passed the shared market-data quality gate:

| Symbol | Rows | Valid | Duplicates | Nulls | Nonfinite | Non-monotonic | Invalid OHLC | Negative volume | Calendar gaps | Max gap |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| PETR4.SA | 312 | PASS | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 5 days |
| VALE3.SA | 312 | PASS | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 5 days |
| ITUB4.SA | 312 | PASS | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 5 days |

Additional provider fields were observable for corporate actions: `Dividend` for VALE3.SA and `Split_Ratio`/`Dividend` for ITUB4.SA. These were not required OHLCV fields and were not independently used to reconstruct adjustment factors.

A PETR4 smoke window (`2025-01-01` to `2025-03-31`) also validated downstream compatibility: 61 raw rows, 61 indicator rows, 36 feature rows and 36 targets, with target counts `{0: 16, 1: 20}`.

Purged walk-forward was executed on real data with the same fixed parameters for all three symbols:

- horizon: `5`
- train size: `120`
- test size: `40`
- step: `40`
- folds: `4` per symbol
- test rows: `40` per fold

Aggregate results:

| Symbol | Model balanced accuracy | Baseline balanced accuracy | Model macro-F1 | Baseline macro-F1 | Raw Brier | Calibrated Brier | Selected Brier |
|---|---:|---:|---:|---:|---:|---:|---:|
| PETR4.SA | 0.5895 | 0.3358 | 0.5416 | 0.3219 | 0.2308 | 0.2651 | 0.2253 |
| VALE3.SA | 0.5026 | 0.3773 | 0.3870 | 0.3012 | 0.3433 | 0.2788 | 0.2819 |
| ITUB4.SA | 0.4771 | 0.4671 | 0.4585 | 0.3870 | 0.2876 | 0.2722 | 0.2992 |

The results are diagnostic only. They do not establish profitability, production readiness or model promotion. ITUB4 in particular showed only a small balanced-accuracy advantage over its baseline. Calibration behavior varied by asset.

## TESTS

Validation completed:

1. Real-data retrieval and quality validation for PETR4.SA, VALE3.SA and ITUB4.SA.
2. Existing historical-data pipeline tests: **39 passed**.
3. `python -m compileall -q backend`: **passed**.
4. Static scan of backend execution references: only pre-existing MT5/DOTO references were found; no new execution dependency was introduced by this task.
5. Working tree remained unchanged except for the intentionally preserved local untracked items.

No `mt5.order_send()` call was made and no financial transaction was submitted.

## DOCUMENTATION

Detailed reproducible results are recorded in:

- `docs/validation/009-real-historical-data-validation-results.md`
- `DEVELOPMENT_STATUS.md`
- `docs/PROJECT_CONTEXT.md`

## LIMITATIONS

This task validates real-provider data ingestion, normalization, quality gating and leakage-safe evaluation behavior. It does not establish:

- profitability or expected trading returns;
- production-ready real-dataset training;
- venue-specific transaction-cost calibration;
- realistic execution slippage calibration;
- immunity to survivorship or universe-selection bias;
- independent corporate-action/adjustment correctness beyond the provider output observed;
- live or DEMO execution readiness.

The walk-forward pipeline fits models transiently as part of evaluation; no real-data model artifact was promoted or registered as production-ready, and no strategy parameters were optimized against the observed sample.

## SAFETY_CONSTRAINTS

- Never call `mt5.order_send()` as part of this task.
- Never submit a financial transaction.
- Do not require MT5 or DOTO to retrieve historical data.
- Keep execution authority completely outside the historical-data validation path.
- Fail closed on invalid market data.
- Do not auto-retry any ambiguous financial execution state.
- Preserve the existing DEMO/LIVE separation.

## DO_NOT

- Do not repeat the existing EURUSD DEMO transaction.
- Do not introduce live broker connectivity.
- Do not optimize model parameters against the real historical sample.
- Do not silently drop quality failures.
- Do not commit large raw market-data snapshots before determining that versioned snapshots are necessary.
- Do not use `git reset --hard` or `git clean -fd`.
- Do not delete or overwrite existing untracked local files.

## EXPECTED_OUTPUT

A reproducible validation result showing, for PETR4.SA, VALE3.SA, and ITUB4.SA:

- provider and retrieval parameters
- row count
- effective start/end
- quality-gate result
- reported calendar gaps
- indicator/feature compatibility
- purged walk-forward fold count
- relevant limitations

**Final decision:** PASS for the Task 009 historical-data validation gate. This is a data-validation decision only, not a trading decision or production-readiness approval.
