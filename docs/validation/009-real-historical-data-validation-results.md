# Task 009 — Real Historical Data Validation Results

**TASK_ID:** `codex-20260914-009`
**Validation date:** 2026-09-14
**Status:** PASS — data-validation gate completed

## Scope

Controlled validation of the existing broker-independent historical market-data path using the OpenBB/yfinance adapter and real daily B3 data for:

- `PETR4.SA`
- `VALE3.SA`
- `ITUB4.SA`

Retrieval window:

- start: `2024-01-01`
- end: `2025-03-31`
- interval: `1d`
- effective data coverage: `2024-01-02` through `2025-03-31`
- provider path: OpenBB → yfinance

No MT5/DOTO historical retrieval and no broker execution were used.

## Data-quality validation

All three symbols returned 312 daily observations and passed the shared `validate_market_data()` quality gate.

| Symbol | Rows | Valid | Duplicates | Nulls | Nonfinite | Non-monotonic | Invalid OHLC | Negative volume | Calendar gaps | Max gap |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| PETR4.SA | 312 | PASS | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 5 days |
| VALE3.SA | 312 | PASS | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 5 days |
| ITUB4.SA | 312 | PASS | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 5 days |

The calendar gaps are consistent with non-trading periods and were reported by the quality gate rather than silently discarded.

Canonical required columns were present:

- `Open`
- `High`
- `Low`
- `Close`
- `Volume`

The normalized index was named `date` and was monotonic.

The provider also returned observable corporate-action-related fields for some symbols:

- `VALE3.SA`: `Dividend`
- `ITUB4.SA`: `Split_Ratio`, `Dividend`

Those additional fields were not treated as canonical OHLCV inputs. This validation did not independently reconstruct or audit provider adjustment factors; corporate-action treatment remains a data-source limitation to document before any research result is interpreted economically.

## Pipeline compatibility

A controlled PETR4 real-data run validated the complete downstream transformation:

- raw rows: 61 for the 2025-01-01 → 2025-03-31 smoke window;
- indicator rows: 61;
- feature rows: 36;
- target rows: 36;
- target distribution: 16 negative / 20 positive observations;
- technical indicators executed successfully;
- `build_features(..., horizon=5)` produced non-empty output.

The purged walk-forward validation was then executed for all three symbols on the 2024-01-01 → 2025-03-31 real-data window with the same fixed parameters:

- horizon: `5`
- train size: `120`
- test size: `40`
- step: `40`

Each symbol produced 4 folds, with 40 test rows per fold.

## Walk-forward results

| Symbol | Folds | Model balanced accuracy | Baseline balanced accuracy | Model macro-F1 | Baseline macro-F1 | Raw Brier | Calibrated Brier | Selected Brier |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| PETR4.SA | 4 | 0.5895 | 0.3358 | 0.5416 | 0.3219 | 0.2308 | 0.2651 | 0.2253 |
| VALE3.SA | 4 | 0.5026 | 0.3773 | 0.3870 | 0.3012 | 0.3433 | 0.2788 | 0.2819 |
| ITUB4.SA | 4 | 0.4771 | 0.4671 | 0.4585 | 0.3870 | 0.2876 | 0.2722 | 0.2992 |

The walk-forward implementation preserved temporal ordering and the explicit five-observation purge. No model hyperparameter was changed to make a real dataset pass validation.

The results are diagnostic only. PETR4 showed a larger separation from its baseline than VALE3 and ITUB4; ITUB4's balanced-accuracy advantage over baseline was small. Calibration behavior also varied by asset, so these observations do not justify a production promotion or an economic-performance claim.

## Reproducibility and controls

The validation was executed locally using the repository's existing `.venv` and the existing provider/service interfaces. The provider interface was inspected before execution, and the exact historical date range and interval were kept fixed across all three symbols.

Validation checks completed:

- `backend/tests`: **39 passed**
- `python -m compileall -q backend`: **passed**
- static execution-path scan: only pre-existing MT5/DOTO references were found in unrelated execution/integration components
- working tree remained unchanged except for the intentionally preserved untracked local items:
  - `.runtime/`
  - `AGENTS.md`
  - `scripts/diagnose_first_demo_attempt.py`

No `mt5.order_send()` call was made and no financial transaction was submitted.

## Limitations

This validation establishes provider/data-pipeline compatibility and leakage-safe evaluation behavior. It does **not** establish:

- profitability or expected trading returns;
- production-ready model quality;
- real-dataset training workflow readiness;
- venue-specific transaction-cost calibration;
- realistic slippage calibration for a target execution venue;
- immunity to survivorship bias or other dataset-selection bias;
- independent corporate-action/adjustment correctness beyond the provider output observed here;
- live or DEMO execution readiness.

Transaction costs and slippage were not inferred from this data-quality exercise. Survivorship bias and universe-selection effects remain separate research concerns.

The walk-forward fits models transiently as part of the existing evaluation pipeline; no trained real-data model artifact was promoted or registered as production-ready, and no strategy parameters were optimized against the observed sample.

## Decision

**PASS for Task 009's historical-data validation gate.**

The real OpenBB/yfinance path successfully retrieved, normalized, quality-checked and evaluated the three controlled B3 datasets, and the existing technical/feature/purged-walk-forward pipeline executed successfully on real data.

**Not passed / not implied:** real-dataset production training, economic profitability, venue calibration, production readiness, live trading or MT5/DOTO execution validation.
