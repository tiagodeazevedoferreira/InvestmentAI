# InvestmentAI — Project Context / Handoff

Last updated: 2026-09-16

## Purpose

InvestmentAI is a research, validation, paper-trading and controlled broker-integration platform. The project combines value investing, technical/quant research, portfolio/risk analytics, AI/ML, external intelligence and a deliberately gated execution layer.

The system is designed to fail closed. Research, simulation, paper, DEMO and LIVE execution remain distinct environments. No scheduler has financial execution authority, and no validation task should weaken the execution gates.

## Current validated baseline

### Task 004 — Shadow scheduler integration

Completed and validated.

- Shadow Decision Ledger is deterministic, idempotent and observational.
- Repeated logical events do not create duplicate shadow records.
- Paper Decision Ledger semantics remain idempotent.
- Shadow records have `execution_authority="none"`.
- No broker or MT5 execution is involved.

### Task 005 — Provider-backed paper scheduler integration

Completed and validated.

The integration test validates a deterministic mocked OpenBB provider boundary through the paper scheduler and both decision ledgers.

Validated behavior:

- `get_provider("openbb")` resolves the provider boundary.
- Provider history is mocked; no network access is required.
- `PETR4` is normalized to `PETR4.SA`.
- The expected `3mo` history request is made.
- Paper and shadow decisions are deterministic.
- `execute=False` is preserved.
- No Paper broker order is created.
- Shadow output remains observational with `execution_authority="none"`.
- No MT5, DOTO, `order_send` or financial execution is involved.

Validation completed with the full backend test suite at 18 tests, followed by successful `compileall` and safety scan.

### Task 006 — End-to-end backtest validation

Completed and validated on 2026-09-11.

Scope was intentionally limited to the deterministic backtesting layer. It does **not** claim that a real-dataset training workflow has been validated.

Validated with `MarketReplay`, synthetic OHLCV and `Backtester`:

- signal generated on candle `t` executes at the open of candle `t+1`;
- final open positions are liquidated;
- commission is accounted deterministically;
- slippage is accounted deterministically;
- invalid signals outside `-1, 0, 1` are rejected.

Validation results:

- Task 006 focused tests: **3 passed**.
- Complete `backend/tests` suite: **21 passed**.
- `compileall` for `backend/app` and `backend/tests`: passed.
- Safety scan of the new Task 006 test: no `MetaTrader5`, `mt5.order_send`, `order_send`, `OrderIntent` or `DOTOGlobal-Real` references.

### Task 007 — Leakage-safe ML temporal splitting

Completed and validated.

- `chronological_split()` now accepts an explicit `purge_bars` parameter.
- The active XGBoost training path uses `purge_bars=5`.
- Train and validation samples adjacent to temporal boundaries are purged so their future five-bar targets cannot depend on observations belonging to the next temporal set.
- Chronological ordering remains deterministic; no shuffle was introduced.
- Validation: 4/4 focused ML tests, 25/25 complete backend tests, and `compileall` passed.
- This does not complete real-dataset training or the broader end-to-end training/backtest workflow.

### Task 008 — Historical data pipeline validation

Completed and validated offline on 2026-09-14.

The historical OHLCV contract is now consistent across the provider boundary, quality gate, technical indicators, feature engineering and purged walk-forward validation.

Validated behavior:

- `OpenBBMarketDataProvider` normalizes historical frames to canonical `Open`, `High`, `Low`, `Close`, `Volume` columns with a datetime index.
- `validate_market_data()` is the shared full quality gate for historical OHLCV.
- The quality gate rejects missing columns, duplicate timestamps, non-monotonic timestamps, null/non-numeric or non-finite required values, invalid OHLC relationships and negative volume.
- Large calendar gaps are reported as observability metadata and do not automatically invalidate otherwise consistent market data.
- The normalized frame flows directly through `technical.indicators()` and `build_features(..., horizon=5)`.
- `purged_walk_forward(..., horizon=5)` preserves the intended temporal separation, with the explicit five-observation purge between train and test.
- `normalize_symbol()` remains deterministic (`PETR4` → `PETR4.SA`; blank symbols are rejected).
- Tests use only deterministic synthetic DataFrames and do not initialize OpenBB, yfinance or MT5.
- No financial execution path was modified.

Validation results:

- Task 008 focused tests: **14 passed**.
- Complete `backend/tests` suite: **39 passed**.
- `compileall -q backend`: passed.
- Static scan found only pre-existing MT5/DOTO/execution references in unrelated backend components; Task 008 introduces no broker execution dependency.

Important boundary: Task 008 validates the pipeline contract and temporal behavior with synthetic data only. It does **not** validate a real historical dataset, real-provider ingestion, real-dataset training, or the broader end-to-end training/backtest workflow.

### Task 009 — Real historical data validation

Completed and validated on 2026-09-14.

The real OpenBB/yfinance B3 path was validated for `PETR4.SA`, `VALE3.SA` and `ITUB4.SA` using daily data from requested `2024-01-01` through `2025-03-31`.

Validated behavior:

- Each symbol returned 312 observations with effective coverage `2024-01-02` through `2025-03-31`.
- All three datasets passed the shared market-data quality gate.
- Each dataset reported two calendar gaps with a maximum gap of five days; these were retained as observability metadata.
- Canonical OHLCV columns were present and the normalized index was `date`.
- Provider-specific corporate-action-related fields were observable (`Dividend` for VALE3 and `Split_Ratio`/`Dividend` for ITUB4) without changing the canonical OHLCV contract.
- Technical indicators and feature engineering executed successfully on real data.
- The purged walk-forward pipeline executed with horizon `5`, train size `120`, test size `40` and step `40`, producing four folds per asset.
- Aggregate model/baseline balanced accuracy: PETR4 `0.5895/0.3358`, VALE3 `0.5026/0.3773`, ITUB4 `0.4771/0.4671`.
- These results are diagnostic only; they do not imply profitability or production readiness.

Validation checks:

- Complete `backend/tests`: **39 passed**.
- `compileall -q backend`: passed.
- Static scan: only pre-existing MT5/DOTO/execution references found.
- No `mt5.order_send()` call and no financial transaction were performed during the task.

Detailed results are recorded in `docs/validation/009-real-historical-data-validation-results.md`.

Important boundary: Task 009 closes the real historical-data validation gate only. It does not mark real-dataset production training, venue-specific transaction-cost/slippage calibration, production readiness, live trading or MT5/DOTO execution validation as complete.

### Task 010 — Real dataset training workflow

Completed and validated on 2026-09-16.

The first reproducible real-dataset training workflow is complete for the controlled B3 sample. PETR4.SA, VALE3.SA and ITUB4.SA were trained using OpenBB with yfinance, interval `1d`, period `5y` and horizon `5`.

Validated behavior:

- `train_symbol_baseline()` applies `validate_market_data()` before `build_features()`.
- Invalid market data fails closed before feature engineering.
- The existing `build_features()` implementation and XGBoost engine remain unchanged as the training path.
- The five-bar temporal purge remains enforced by `train_xgboost()`.
- The provider contract `history(symbol, period)` remains compatible; OpenBB translates the requested period into explicit dates and requests daily data from yfinance.
- Training metadata records provider, interval, period, horizon, feature configuration, parameters, metrics, sample counts and the canonical quality report.
- Model and metadata artifacts are persisted separately.
- No MT5/DOTO historical data or broker execution was used.

Real-data validation used the same configuration for all three symbols:

| Symbol | Samples | Positive labels | Accuracy | Precision | Recall | ROC AUC |
|---|---:|---:|---:|---:|---:|---:|
| PETR4.SA | 1223 | 651 | 0.4457 | 0.5182 | 0.5377 | 0.3990 |
| VALE3.SA | 1222 | 633 | 0.4946 | 0.5250 | 0.4330 | 0.5069 |
| ITUB4.SA | 1223 | 648 | 0.5543 | 0.5930 | 0.5204 | 0.6325 |

Each dataset contained 1248 daily observations from `2021-09-15` through `2026-09-15` and passed the canonical quality gate. Calendar gaps were retained as observability metadata rather than automatic failures.

Validation checks:

- Dedicated XGBoost tests: **3 passed**.
- Complete `backend/tests`: **43 passed**.
- `compileall -q backend`: passed.
- Static safety scan: clean.
- No `mt5.order_send()` call.
- No financial transaction submitted.
- No model promoted to production.

Detailed results are recorded in `docs/validation/010-real-dataset-training-workflow-results.md`.

Important boundary: Task 010 is diagnostic only. It does not establish profitability, production readiness, model superiority, live-trading readiness, complete-universe robustness or permission to execute trades.

## Current execution state

The paper execution path is deterministic and broker-independent. Provider-backed scheduling obtains B3 history through the OpenBB/yfinance boundary, evaluates the existing RSI paper policy, persists deterministic decision keys and skips duplicates.

The DEMO execution layer is implemented behind explicit authorization, reconciliation and fail-closed controls. Automatic scheduler-to-broker execution remains disconnected.

A controlled DOTO/MT5 DEMO validation was completed on 2026-09-11 using one explicitly authorized transaction:

- EURUSD BUY 0.01
- order `29453207`
- deal `28862296`
- position `29453207`
- open price `1.15960`

This transaction must **not** be repeated merely for verification. The existing ambiguous historical `SUBMITTED` record must remain pending and must never be automatically retried.

LIVE execution remains disabled.

## Current ML state

- Technical feature engineering: complete.
- Chronological train/validation/test split: complete.
- XGBoost training interface: complete.
- Out-of-sample evaluation: complete.
- Causal ML trading backtest: complete.
- Robustness audit: complete.
- Robustness gate: **not passed** because performance is not stable across all evaluated assets and assumptions.
- Causal pooled cross-asset experiment: implemented, research-only.
- Real-dataset training workflow: complete for the controlled B3 validation sample; diagnostic only.
- LSTM and RL experiments: still pending.

## Important open quality items

- Full integration suite against provider mocks.
- End-to-end training/backtest validation as a broader combined workflow.
- Security/dependency scan.
- Production deployment.

Task 006 does not close the broader `End-to-end training/backtest test` item because it validates backtesting only. Task 008 does not close it because its historical pipeline validation is synthetic and contract-focused. Task 009 validated the real provider/data path and evaluation pipeline. Task 010 now validates the first reproducible real-dataset XGBoost training workflow for the controlled B3 sample, but neither task establishes production-grade economic performance.

## Immediate development direction

With Tasks 009 and 010 complete, the next candidate development stage should be selected explicitly from the remaining research gates. The controlled B3 real-data training path is now reproducible and quality-gated, but further work should still consider:

1. broader real-dataset training coverage and robustness controls;
2. realistic transaction-cost and slippage assumptions;
3. venue-specific cost calibration where data is available;
4. broader historical coverage and universe-selection controls where justified;
5. deterministic reproducibility and versioned validation artifacts;
6. no MT5, DOTO or broker submission unless a separate execution task is explicitly authorized.

Task 010 must not be treated as an approval for production training, strategy promotion or live execution.

## Safety constraints

- Never automatically submit financial trades.
- Never call `mt5.order_send()` during normal development or validation.
- Never create or modify DEMO/LIVE orders without fresh explicit user authorization for the exact transaction.
- Do not repeat the existing EURUSD DEMO transaction for verification.
- Ambiguous broker execution states fail closed and remain pending.
- Automatic scheduler-to-broker execution is disconnected.
- LIVE execution is disabled.
- Never expose or request passwords/secrets.
- Preserve local `.runtime/`, `AGENTS.md` and `scripts/diagnose_first_demo_attempt.py`.
- Never use `git reset --hard` or `git clean -fd`.
- Do not delete or overwrite local untracked operational files without explicit authorization.
- Recovery validation should use disposable temporary state when possible.

## Local repository state known at the last validation

The working tree was clean except for these intentionally preserved local untracked items:

```text
.runtime/
AGENTS.md
scripts/diagnose_first_demo_attempt.py
```

These files are not project defects and must be preserved.

## Handoff rule

Before starting the next task:

1. inspect the current repository state;
2. inspect the relevant implementation and existing tests;
3. define a narrowly scoped task and acceptance criteria;
4. implement only the demonstrated need;
5. run focused tests;
6. run the full backend suite when appropriate;
7. run compile/security checks;
8. update this context and the appropriate status/task documentation;
9. commit the result;
10. never weaken financial safety gates merely to make a test pass.
