# Task 009 — Real Historical Data Validation

**TASK_ID:** codex-20260914-009
**STATUS:** OPEN

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

- [ ] PETR4.SA historical daily data can be retrieved successfully.
- [ ] VALE3.SA historical daily data can be retrieved successfully.
- [ ] ITUB4.SA historical daily data can be retrieved successfully.
- [ ] The retrieval path uses the existing provider adapter rather than MT5/DOTO.
- [ ] The validation is reproducible with an explicit date range and interval.

### Normalization and quality

- [ ] Every dataset is normalized to the canonical OHLCV columns.
- [ ] The resulting index is a sorted `DatetimeIndex` named `date`.
- [ ] Required-column, duplicate, null, nonfinite, monotonicity, OHLC consistency, and negative-volume checks pass.
- [ ] Calendar gaps are reported and investigated rather than silently discarded.
- [ ] Dataset row counts and effective start/end timestamps are recorded.

### Pipeline compatibility

- [ ] Technical indicators execute successfully on each real dataset.
- [ ] Feature engineering produces non-empty feature/target datasets.
- [ ] Purged walk-forward validation executes successfully with the existing leakage-safe horizon.
- [ ] The number of folds and rows per fold are recorded.
- [ ] No model hyperparameter is changed solely to make the real dataset pass validation.

### Reproducibility and documentation

- [ ] The exact symbols, date range, interval, provider, and validation timestamp are recorded.
- [ ] Provider/data-source limitations are documented.
- [ ] Corporate actions/adjustment assumptions are documented where observable.
- [ ] Survivorship bias, transaction costs, slippage, and other backtest limitations are explicitly distinguished from data-quality validation.
- [ ] The task does not claim real-dataset training or production-readiness.

## TESTS

At minimum:

1. A focused real-data validation test or reproducible validation script covering the three symbols.
2. Existing historical-data pipeline tests must remain green.
3. Full backend test suite must remain green.
4. `python -m compileall -q backend` must remain clean.
5. A static scan must confirm that the task introduces no new execution dependency or `order_send` path.

## DOCUMENTATION

Update, after successful validation:

- `DEVELOPMENT_STATUS.md`
- `docs/PROJECT_CONTEXT.md`
- this task document with results, dataset coverage, quality findings, and final status

Do not mark the following as complete merely because Task 009 passes:

- real-dataset model training
- model calibration
- production readiness
- live trading
- MT5/DOTO execution validation

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

The expected outcome is a documented data-validation decision, not a trading decision.