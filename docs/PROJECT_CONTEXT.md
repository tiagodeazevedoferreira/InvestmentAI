# InvestmentAI — Project Context / Handoff

Last updated: 2026-09-21

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

### Task 011 — Cross-asset ML diagnostics

Completed and validated on 2026-09-16.

The causal pooled-vs-asset-specific experiment now has a dedicated diagnostic layer reporting actual positive rate, predicted positive rate, mean predicted probability, probability/prediction bias, accuracy, Brier score, ECE, first-vs-last fold temporal deltas and causal reference-vs-OOS feature distribution shift.

CI workflow `.github/workflows/ml-cross-asset.yml` completed successfully in run `35131993552` on `main` commit `e17ddc0`. The workflow runs diagnostic unit tests before the real-data experiment, report generation and artifact upload. The `ml-cross-asset-experiment` artifact was generated with SHA-256 `cd1b20126b8f9e0c49f98295dbc9c933051c82e212100a191d17670f242781e6`. The experiment covered PETR4, VALE3 and ITUB4 with 8 paired OOS folds.

Dedicated Task 011 task and validation records are now published at `docs/codex/tasks/011-cross-asset-ml-diagnostics.md` and `docs/validation/011-cross-asset-ml-diagnostics-results.md`.

Important boundary: Task 011 is research/observability only. It does not establish profitability, robustness, production readiness or model superiority, and it does not change model thresholds, execution policy, risk gates, broker integration or promotion authority.

### Task 012 — XGBoost OOS → economic backtest contract

Completed and validated on 2026-09-21.

The existing XGBoost OOS pipeline was hardened with explicit per-fold metadata and non-overlap validation. A deterministic contract test validates the five-observation purge, exact test-window size and non-overlapping OOS windows. A second deterministic integration contract validates the existing OOS → signal → MarketReplay → Backtester path, including replay boundaries, flat final position, finite final cash and non-negative transaction costs.

The self-hosted Windows CI workflow passed the OOS contract, economic replay contract, complete backend suite and backend compilation.

Important boundary: Task 012 is offline/research validation only. It does not establish profitability, robustness, production readiness or permission to execute trades. No MT5/DOTO order submission is part of the task.

Detailed task definition: `docs/codex/tasks/012-xgboost-oos-economic-backtest-contract.md`.


### Task 013 — Real-data XGBoost OOS economic report

Completed and validated on 2026-09-21.

A reproducible real-data economic report was generated for PETR4, VALE3 and ITUB4 using the existing provider, feature, purged XGBoost OOS and cost-aware Backtester paths. The benchmark was hardened to use the exact economic replay window, including the bar required to execute the final OOS signal. A deterministic benchmark-window contract test was added.

Configuration: 2021-09-15 through 2026-09-15, horizon 5, train 500, test 100, step 100, threshold 0.60, initial cash 100,000, commission 0.1%, slippage 5 bps.

Detailed results are recorded in the corresponding Task 013 validation documentation.

Important boundary: Task 013 is diagnostic only. It does not establish profitability, robustness, production readiness or permission to execute trades.

### Task 014 — XGBoost OOS economic cost attribution

Completed and validated on 2026-09-21.

The real-data economic result was decomposed into four fixed transaction-cost scenarios for PETR4, VALE3 and ITUB4: zero cost, 0.1% commission only, 5 bps slippage only, and 0.1% commission plus 5 bps slippage. The implementation now generates one immutable OOS prediction set per asset and reuses it across all scenarios, so cost sensitivity does not retrain or regenerate the model signal.

All 12 symbol/scenario observations were produced successfully. The provider quality gate was valid for all three assets; each asset produced 7 OOS folds and 700 OOS rows. Under the combined 0.1% commission + 5 bps slippage scenario, final returns were PETR4 -0.21%, VALE3 -7.90% and ITUB4 -13.35%. The corresponding zero-cost returns were +26.48%, +19.57% and +22.72%.

Detailed results are recorded in docs/validation/014-xgboost-oos-economic-cost-attribution-results.md.

Important boundary: Task 014 is diagnostic only. It does not establish profitability, robustness, production readiness, venue-specific cost calibration or permission to execute trades.

### Task 015 — XGBoost OOS fold-level economic stability

Completed and validated on 2026-09-21.

The fixed XGBoost OOS prediction set was analyzed fold by fold for PETR4, VALE3 and ITUB4 under zero-cost and combined 0.1% commission + 5 bps slippage scenarios. Each symbol produced 7 OOS folds and 700 OOS rows. The workflow validates deterministic fold slicing, reuse of the same source OOS predictions, independent fold replay and descriptive dispersion statistics.

No threshold optimization, parameter tuning, model promotion or financial execution occurred.

Detailed results are recorded in `docs/validation/015-xgboost-oos-fold-stability-results.md`.

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
- Cross-asset diagnostic harness: complete and CI-validated, research-only.
- Real-dataset training workflow: complete for the controlled B3 validation sample; diagnostic only.
- LSTM and RL experiments: still pending.

## Important open quality items

- Full integration suite against provider mocks.
- End-to-end training/backtest validation as a broader combined workflow.
- Security/dependency scan.
- Production deployment.

Task 006 does not close the broader `End-to-end training/backtest test` item because it validates backtesting only. Task 008 does not close it because its historical pipeline validation is synthetic and contract-focused. Task 009 validated the real provider/data path and evaluation pipeline. Task 010 validates the first reproducible real-dataset XGBoost training workflow for the controlled B3 sample. Task 011 validates diagnostics around the causal cross-asset experiment. Neither establishes production-grade economic performance.

## Immediate development direction

Task 015 is now complete. The next engineering stage is validation-pipeline orchestration: reduce manual GitHub Actions launches by providing a single workflow entry point that executes the already validated XGBoost OOS contract, economic report, cost attribution and fold-stability validations in a controlled sequence.

The orchestration layer must remain research-only. It must not retrain models, optimize thresholds, promote models or invoke MT5/DOTO execution. Individual focused workflows remain available for targeted reruns and debugging.

After orchestration is validated, subsequent research can address:

1. broader real-dataset training coverage and robustness controls;
2. realistic transaction-cost and slippage assumptions;
3. venue-specific cost calibration where data is available;
4. broader historical coverage and universe-selection controls where justified;
5. deterministic reproducibility and versioned validation artifacts.

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

The working tree was clean except for the intentionally preserved local untracked `.runtime/` operational state. `AGENTS.md` and `scripts/diagnose_first_demo_attempt.py` are tracked project files and must also be preserved.

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
