# Development Status

Last updated: 2026-09-28

## Foundation
- [x] Repository and persistent handoff context
- [x] Architecture/decision records
- [x] Environment separation contract
- [x] Firebase repository abstraction
- [x] FastAPI application skeleton
- [x] PWA frontend skeleton
- [x] CI and Firebase smoke-test workflows
- [x] OpenBB provider boundary
- [x] Yahoo fallback provider
- [x] OpenBB/yfinance B3 proof-of-concept adapter
- [x] Historical OHLCV normalization and quality-gate contract

## Value Investing
- [x] Fundamental data service boundary
- [x] P/E, P/B, EV/EBITDA, ROE and dividend-yield primitives
- [x] DCF/Gordon valuation primitives
- [x] Provider-normalized historical statements
- [x] ROIC with invested-capital definition and validation
- [x] Fundamental score/ranking and margin-of-safety engine

## Trading
- [x] EMA 9/21
- [x] RSI 14
- [x] Bollinger Bands
- [x] RSI oversold/overbought strategy
- [x] Basic backtester
- [x] Cost/slippage-aware market simulator
- [x] Market replay
- [x] Walk-forward evaluation
- [x] Transaction-cost calibration by venue and calibrated backtest integration
- [x] Causal ML trading backtest
- [x] ML robustness audit
- [x] ML cross-asset model diagnosis and improvement

## Portfolio/Risk
- [x] Markowitz optimization
- [x] Maximum Sharpe
- [x] Efficient frontier
- [x] Parametric daily VaR 95%
- [x] Robust covariance/shrinkage
- [x] Initial paper position sizing and order risk limits
- [x] Production-grade portfolio risk limits

## AI/ML
- [x] Technical feature engineering
- [x] Five-day directional target
- [x] Chronological train/validation/test split
- [x] Leakage-safe temporal purge for five-bar target horizon
- [x] XGBoost training interface
- [x] Model metadata/registry artifact
- [x] Financial evaluation metrics
- [x] Training workflow on real datasets
- [x] Out-of-sample ML evaluation
- [x] Empirical financial promotion gate evaluator (human-review only)
- [x] LSTM experiment
- [x] RL agent experiment

## External Intelligence
- [x] Doto AI Market Insights normalization boundary
- [x] Trading Central read-only API boundary
- [x] Provider-neutral signal contract
- [x] Signal fusion engine
- [x] Independent-evidence risk gate
- [x] TradingView Pine technical-validator and webhook contract
- [x] TradingView reconciliation
- [x] TradingView evidence connected to SignalFusion/RiskGate
- [x] Decision observability record
- [ ] Real Trading Central credentials/entitlement validation
- [ ] Real Doto signal observation/export/approved bridge
- [ ] TradingView alert/webhook activation on an eligible plan
- [x] OpenBB/B3 provider capability validation
- [x] Provider calibration against historical outcomes
- [x] Persisted paper outcome calibration pipeline

## Execution
- [x] Simulation-only default
- [x] Demo/live separation
- [x] Risk gate skeleton
- [x] Deterministic paper broker
- [x] Paper execution engine with market/limit orders
- [x] Fees and slippage accounting
- [x] Paper portfolio mark-to-market and P&L accounting
- [x] Paper account persistence boundary in Firebase with bounded recent history
- [x] Paper execution API and lifecycle tests
- [x] Signal → risk gate → position sizing → paper order automation primitive
- [x] Paper-to-TradingView reconciliation primitive
- [x] Provider-backed paper scheduler/orchestrator
- [x] Doto/MT5 demo broker adapter contract (demo-only)
- [x] MT5 demo reconciliation validation harness (read-only; live disabled)
- [x] DEMO authorization gate with kill switch + reconciliation + fail-closed policy
- [x] Authorized DEMO execution coordinator with pre/post reconciliation
- [x] Controlled end-to-end validation against a real Doto/MT5 DEMO account
- [x] Durable DEMO restart/recovery coordinator with no automatic resubmission
- [x] Empirical restart/recovery validation against the persisted DEMO ledger, confirming an ambiguous SUBMITTED record remains pending without broker submission
- [x] Broker-connected read-only recovery validation using the confirmed Order 29453207 / Deal 28862296
- [x] Fault-injected submission-interruption test: exception after authorization remains recoverable SUBMITTED and never becomes an automatic retry
- [x] Durable DEMO submission correlation and deterministic recovery by broker evidence
- [x] Scheduler → DEMO fail-closed promotion boundary (plan-only; broker submission disconnected)
- [x] Scheduler → DEMO broker integration
- [ ] Real interrupted-broker-submission recovery validation without deliberately creating another DEMO transaction
- [ ] Live broker adapter
- [x] Empirical promotion gate evaluator (human-review only)
- [x] Kill switch and reconciliation engine (broker-neutral, read-only)
- [x] MT5 DEMO non-submitting order preflight

## Paper/Shadow
- [x] Paper execution primitive
- [x] End-to-end paper order -> fill -> portfolio accounting
- [x] Bounded paper account state persistence
- [x] Deterministic technical signal → risk → sizing → paper execution path
- [x] Signal automation scheduler
- [x] Idempotent decision ledger
- [x] Shadow decision ledger (deterministic, idempotent and observational; no execution authority)
- [x] Outcome attribution primitives for forward-return observation and hit-rate summaries
- [x] Persisted paper outcomes with resumable horizons
- [x] Descriptive calibration statistics with confidence intervals and explicit cost assumptions
- [x] Causal volatility regime classification
- [x] Paper/TradingView evidence reconciliation
- [x] Conservative empirical evidence gate with explicit criteria and no automatic promotion

## Firebase/data governance
- [x] Operational repository abstraction
- [x] Retention-aware storage boundary
- [x] Execute Firebase smoke test against configured secret
- [x] Production security rules
- [x] Data-size monitoring/quotas dashboard
- [x] Automated retention cleanup

## Quality
- [x] External-intelligence unit tests
- [x] TradingView webhook normalization/authentication tests
- [x] TradingView reconciliation/fusion tests
- [x] OpenBB B3 adapter unit tests
- [x] OpenBB B3 live smoke-test workflow
- [x] ML trading backtest tests
- [x] ML robustness audit helper tests
- [x] ML model diagnosis helper tests
- [x] Causal pooled cross-asset ML experiment tests
- [x] Cross-asset diagnostic helper tests
- [x] Paper execution accounting tests
- [x] Paper API lifecycle tests
- [x] Paper signal automation tests
- [x] Paper scheduler/ledger unit tests
- [x] Paper outcome attribution unit tests
- [x] Paper calibration unit tests
- [x] Persisted paper outcome calibration runner and ledger persistence tests
- [x] Causal regime/reconciliation unit tests
- [x] Empirical promotion gate unit tests
- [x] Operational safety unit tests
- [x] MT5 demo adapter contract tests
- [x] MT5 demo reconciliation harness tests
- [x] DEMO authorization gate tests
- [x] Authorized DEMO execution coordinator tests
- [x] MT5 DEMO preflight tests
- [x] DEMO restart/recovery tests
- [x] Fault-injected DEMO submission-interruption test
- [x] DEMO submission-correlation recovery tests
- [x] Scheduler → DEMO promotion-boundary unit tests
- [x] Historical OHLCV pipeline and temporal-purge tests
- [x] Full integration test suite against provider mocks
- [x] End-to-end training/backtest test
- [x] Security/dependency scan
- [ ] Production deployment
- [x] Production API runtime hardening (Task 039)
- [x] API observability baseline (Task 040)
- [x] Production persistence contract (Task 045)
- [x] Backup and recovery contract (Task 046)

## Current ML validation gate
The causal ML trading backtest, robustness audit and model diagnosis are complete. The robustness gate is not yet passed because performance is not stable across all evaluated assets and assumptions. A causal pooled cross-asset model experiment is implemented to test whether normalized technical features transfer across PETR4, VALE3 and ITUB4 without changing execution policy. Task 011 diagnostics are now validated in CI and recorded as research/observability evidence. The pooled experiment remains research-only until its out-of-sample evidence is reviewed.

## Current historical-data validation gate
Task 008 is complete and validated offline with deterministic synthetic data. Task 009 is also complete and validated against real daily B3 datasets for PETR4.SA, VALE3.SA and ITUB4.SA using the existing OpenBB/yfinance provider boundary.

Task 009 validation used 2024-01-01 through 2025-03-31, interval 1d. Each symbol returned 312 observations covering 2024-01-02 through 2025-03-31 and passed the shared quality gate for required columns, duplicates, nulls, non-finite values, timestamp monotonicity, OHLC consistency and negative volume. Two calendar gaps were reported per dataset, with a maximum gap of five days; these remained observability metadata rather than automatic failures. VALE3 returned an additional Dividend field, and ITUB4 returned Split_Ratio and Dividend; these were not required OHLCV fields and were not independently used to reconstruct corporate-action adjustments.

The real data also passed technical indicators and feature engineering. A PETR4 smoke window produced 61 indicator rows, 36 feature rows and 36 targets. The existing purged walk-forward pipeline then executed with horizon 5, train size 120, test size 40 and step 40, producing four folds per asset. Aggregate model/baseline balanced accuracy was 0.5895/0.3358 for PETR4, 0.5026/0.3773 for VALE3 and 0.4771/0.4671 for ITUB4. These are diagnostic validation results only and do not imply profitability or production readiness.

Task 009 validation completed with 39/39 backend tests passing and compileall -q backend clean. A static scan found only pre-existing MT5/DOTO/execution references in unrelated backend components. No mt5.order_send() call was made and no financial transaction was submitted during the task.

Detailed reproducible results are recorded in docs/validation/009-real-historical-data-validation-results.md.

This task closes the real historical-data validation gate only. It does not mark real-dataset production training, venue-specific cost/slippage calibration, production readiness, live trading or MT5/DOTO execution validation as complete.

### Task 010 — Real dataset training workflow

Completed and validated on 2026-09-16.

The first reproducible real-dataset training workflow is complete for the controlled B3 sample. PETR4.SA, VALE3.SA and ITUB4.SA were trained using OpenBB with yfinance, interval 1d, period 5y and horizon 5.

The canonical validate_market_data() gate executes before feature engineering and invalid datasets fail closed. The existing feature pipeline, XGBoost engine and five-bar temporal purge were preserved.

Validation completed with 43 passed backend tests and clean compileall -q backend.

Important boundary: Task 010 is diagnostic only. It does not establish profitability, production readiness, model superiority, live-trading readiness, complete-universe robustness or permission to execute trades.

### Task 011 — Cross-asset ML diagnostic harness

Completed and validated on 2026-09-16.

The causal pooled-vs-asset-specific experiment now has a dedicated diagnostic layer reporting actual positive rate, predicted positive rate, mean predicted probability, probability/prediction bias, accuracy, Brier score, ECE, first-vs-last fold temporal deltas and causal reference-vs-OOS feature distribution shift. CI runs the diagnostic unit tests before the real-data experiment and report generation.

Workflow .github/workflows/ml-cross-asset.yml completed successfully in run 35131993552 on main commit e17ddc0. The ml-cross-asset-experiment artifact was generated with SHA-256 cd1b20126b8f9e0c49f98295dbc9c933051c82e212100a191d17670f242781e6. The experiment covered PETR4, VALE3 and ITUB4 with 8 paired OOS folds.

Task 011 is research/observability only. It does not establish profitability or robustness, and it does not change model thresholds, execution policy, risk gates, broker integration or promotion authority.

Dedicated task and validation records are published at docs/codex/tasks/011-cross-asset-ml-diagnostics.md and docs/validation/011-cross-asset-ml-diagnostics-results.md.

### Task 023 — Calibrated transaction-cost backtest integration

Completed and validated on 2026-09-24.

The deterministic backtest now exposes an explicit opt-in BacktestConfig.from_calibration() boundary for a validated VenueCostCalibration. The caller can select the median or P95 calibrated commission/slippage profile, commission basis points are converted to the existing decimal commission-rate representation, and venue/source provenance is retained in the immutable configuration.

Existing direct commission_rate/slippage_bps configuration remains unchanged; there is no automatic replacement of prior backtest assumptions. The task does not discover live venue costs, contact a broker, invoke MT5/DOTO execution, tune or promote a model, or establish profitability or production readiness.

Validation completed successfully in Phase 10 Live Gate Tests run 36039678561 and Security and Dependency Scan run 36039678583. The security workflow completed dependency audit, static security scan, backend tests and backend compilation successfully. The Phase 10 gate also completed successfully with the calibrated-cost changes present.

Detailed task record: docs/codex/tasks/023-calibrated-transaction-cost-backtest.md.

### Task 024 — Provider calibration against historical outcomes

Completed and validated on 2026-09-24.

A deterministic, provider-neutral calibration primitive now relates externally supplied signal confidence to realized historical outcomes. Results are grouped by provider and horizon and report hit rate, mean confidence, Brier score, calibration gap and mean signed return. Invalid confidence/return values and empty datasets fail closed.

The implementation is research-only: it does not rank or select providers, modify signal weights or thresholds, change risk gates, promote models, contact brokers, or authorize execution. Statistical interpretation remains descriptive and is subject to sample-size, selection, market-regime and timestamp-alignment limitations.

Validation completed successfully in CI run 36050009093, External Intelligence Validation run 36050009099, Phase 10 Live Gate Tests run 36050009108, Cross-Asset ML Experiment run 36050009287 and Security and Dependency Scan run 36050009126.

Detailed task record: docs/codex/tasks/024-provider-calibration-historical-outcomes.md.

## Current execution gate
The internal paper execution path is deterministic and broker-independent. Provider-backed scheduling obtains B3 history through the OpenBB/yfinance boundary, evaluates the existing RSI paper policy, persists a deterministic decision key, and skips duplicates. Completed decisions receive persisted 1/5/20-bar forward outcomes. The calibration layer reports directional hit rate, confidence intervals and return statistics under an explicit transaction-cost assumption, and the runner can partition results by a causal trailing-volatility regime. Paper decisions can also be reconciled against TradingView validator evidence using an explicit timestamp tolerance. The empirical gate evaluates predefined evidence criteria, but a passing result only permits human review and can never authorize promotion automatically. Operational kill-switch and broker-neutral reconciliation primitives are hardened. The Doto/MT5 demo-only adapter, read-only reconciliation harness, fail-closed authorization gate, and pre/post-reconciled DEMO execution coordinator are implemented. The adapter rejects unsupported limit intents, uses bid/ask semantics for market orders, requires a successful order_check result, and verifies DEMO status during initialization. A non-submitting preflight path builds the exact market request and runs order_check without order_send().

The controlled Doto/MT5 DEMO end-to-end gate was completed on 2026-09-11. The first explicitly authorized EURUSD BUY 0.01 was accepted and filled: order 29453207, deal 28862296, position 29453207, open at 1.15960. External MT5 inspection confirmed exactly one open EURUSD BUY position with volume 0.01; no pending open order remained because the market order was filled. Targeted post-execution reconciliation was validated using broker history lookup by deal/order/position identifiers after a time-window lookup proved unreliable because the broker/server history clock differed from the Python UTC window. The corrected reconciliation path recovered execution 28862296 and position EURUSD: BUY 0.01 without submitting another order. The durable demo ledger reports the valid transaction as FILLED, and the local demo portfolio state mirrors the external position. The restart/recovery coordinator was then exercised against the actual persisted local ledger. The historical ambiguous SUBMITTED record remained SUBMITTED with no broker identifiers, while the already FILLED reference transaction remained untouched. The recovery call did not invoke broker submission, did not create a new intent and did not alter the existing EURUSD position. This empirically validates the restart/recovery no-duplicate boundary for the current persisted state.

A broker-connected, read-only recovery harness was then validated using a disposable SQLite ledger. It seeded the already confirmed Order 29453207 / Deal 28862296 and a separate synthetic unknown submission. Targeted MT5 history promoted only the confirmed record to FILLED; the unknown record remained SUBMITTED; order_send was not called; and temporary SQLite state was successfully discarded on Windows. A separate fault-injected coordinator test confirms that a timeout after local authorization preserves SUBMITTED uncertainty rather than classifying the intent as FAILED or retrying automatically. The new scheduler-to-DEMO boundary now exposes the scheduler's deterministic decision, quantity, reference price and risk result to a fail-closed promotion planner. The planner is disabled by default, requires an explicit symbol mapping, and stops at an OrderIntent; it does not own a broker or call order_send. Actual scheduler-driven DEMO submission remains disconnected pending a separate promotion step. Live execution remains disabled.

The controlled runner remains manual and fail-closed: read-only mode does not call order_send(), and execution requires both explicit --execute and the dedicated DEMO execution arm. No additional DEMO order should be sent solely for verification. Automatic scheduler-to-broker execution remains disconnected, and live execution remains disabled.

## Promotion boundary
Phases 1-9 remain non-live. Phase 10/live is intentionally disabled and requires explicit authorization after empirical validation and operational readiness, including kill-switch and reconciliation hardening.

### Task 025 — Persisted paper outcome calibration pipeline

Completed and validated on 2026-09-24.

The persisted PAPER decision ledger now retains the causal decision reference price, and the historical calibration runner reads persisted decisions, attributes forward outcomes at configured horizons, persists outcomes idempotently and feeds completed observations into the existing descriptive calibration report. Incomplete future horizons remain pending rather than being treated as failures, while malformed provenance or market data fails closed.

The pipeline remains research-only: it does not submit orders, change policy thresholds or risk gates, rank providers, promote models, or claim profitability or production readiness.

Validation completed successfully in CI run 36057607054, Security and Dependency Scan run 36057607141, Phase 10 Live Gate Tests run 36057607186, External Intelligence Validation run 36057607020 and Cross-Asset ML Experiment run 36057607036, all for commit 3c7b812124e47acfb444c687595247edfcba3f97.

Detailed task record: docs/codex/tasks/025-persisted-paper-outcome-calibration.md.

### Task 026 — Provider-normalized historical statements

Completed and validated on 2026-09-24.

The fundamental-data boundary now normalizes provider-specific historical statement aliases into an immutable provider-neutral schema while retaining symbol, period-end and statement-type provenance. Numeric values are validated for finiteness and normalized statements are sorted deterministically by period. The implementation remains limited to data normalization and does not calculate ROIC, score investments, alter valuation assumptions or authorize execution.

Validation completed successfully in CI run 36058759389, Security and Dependency Scan run 36058759361, Phase 10 Live Gate Tests run 36058759323, External Intelligence Validation run 36058759373 and Cross-Asset ML Experiment run 36058759402 for commit a6ce3461f80b4d58794ece7c062d927fe81f73a2.

Detailed task record: docs/codex/tasks/026-provider-normalized-historical-statements.md.


### Task 027 — ROIC with invested-capital definition and validation

Completed and validated on 2026-09-25.

The fundamental service now exposes an explicit ROIC primitive using NOPAT divided by invested capital. Invested capital is defined as equity + total debt - cash using point-in-time balance-sheet values. NOPAT uses an explicitly supplied effective tax rate; missing required inputs return None, while invalid tax rates, non-finite inputs and non-positive invested capital fail closed.

Validation completed successfully in CI run 36068342082, Phase 10 Live Gate Tests run 36068342080, External Intelligence Validation run 36068342083, Cross-Asset ML Experiment run 36068342116, Paper Scheduler run 36072169092 and Security and Dependency Scan run 36068342141 for the Task 027 head commit 4f1b1ab5585760f319647f3c4174cbee02412ffe.

The implementation remains descriptive/research-only and does not score investments, authorize allocation, promote models or execute trades.

Detailed task record: docs/codex/tasks/027-roic-invested-capital.md.

### Task 028 — Fundamental score/ranking and margin-of-safety engine

Implementation completed on 2026-09-25.

A provider-neutral deterministic engine now normalizes P/E, P/B, EV/EBITDA, ROE, ROIC and dividend yield into configurable 0–1 component scores, combines them with explicitly validated weights, produces deterministic rankings with a symbol tie-break, and calculates margin of safety from a supplied intrinsic value and market price.

Default thresholds are explicit engineering assumptions and are not presented as empirically validated investment thresholds. Missing metrics, invalid configuration and non-finite inputs fail closed. The engine does not select investments, allocate capital, change execution policy, promote models or authorize broker submission.

Detailed task record: docs/codex/tasks/028-fundamental-score-margin-of-safety.md.


### Task 030 — Production-grade portfolio risk limits

Implementation completed on 2026-09-25.

A deterministic provider-neutral portfolio risk-limit evaluator now validates proposed weights against explicit hard limits for maximum position weight, gross exposure, absolute net exposure, annualized volatility and optional one-day parametric VaR. Inputs fail closed on malformed weights, covariance matrices, labels, confidence levels and limits. The evaluator reports structured breach reasons without resizing positions or authorizing execution.

The task is an authorization-boundary primitive only. It does not select assets, optimize or resize portfolios, submit broker orders, promote models or establish empirically optimal thresholds.

Detailed task record: docs/codex/tasks/030-production-grade-portfolio-risk-limits.md.

### Task 029 — Robust covariance/shrinkage

Implementation completed on 2026-09-25.

A provider-neutral covariance estimation boundary now supports the existing sample covariance and an explicit Ledoit-Wolf shrinkage estimator. Inputs are validated for dimensions, unique asset labels and finite values; outputs preserve asset labels, are symmetrized and validated. Annualization is explicit through periods_per_year and is never implicit. Existing portfolio optimization behavior remains unchanged because the new estimator is an opt-in service boundary.

Validation covers sample covariance, Ledoit-Wolf positive-semidefinite output, shrinkage bounds, annualization, labels and fail-closed invalid inputs. The task does not change asset selection, allocation policy, execution, broker integration or model promotion.

Detailed task record: docs/codex/tasks/029-robust-covariance-shrinkage.md.


### Task 031 — LSTM experiment

Completed and validated on 2026-09-25.

A provider-neutral, leakage-safe LSTM experiment foundation now builds fixed-length causal sequences from the existing five-day directional target, uses explicit hyperparameters and seed, and applies a purged chronological split so overlapping sequence windows are not shared across train/validation/test boundaries. The experiment remains research-only and does not change the XGBoost model, execution policy, risk gates or promotion authority.

Validation completed successfully in CI run 36172852145, Security and Dependency Scan run 36172852062, Phase 10 Live Gate Tests run 36172852026, External Intelligence Validation run 36172852092 and Cross-Asset ML Experiment run 36172852034 for commit 3e7ae09cb5bd13c2dc910acf31563a58f61edd23.

The current CI environment does not require PyTorch as a core backend dependency; the training path fails clearly when PyTorch is unavailable. No profitability, robustness or model-superiority claim is made.

Detailed task record: docs/codex/tasks/031-lstm-experiment.md.

### Task 032 — RL agent experiment

Completed and validated on 2026-09-25.

A dependency-light tabular Q-learning research boundary was added with chronological/purged splitting, explicit hyperparameters and seed, transaction-cost-aware reward, deterministic greedy evaluation and fail-closed handling of unseen states and invalid inputs. The existing RLPolicy/NoOpRLPolicy boundary remains compatible. The implementation is research-only and does not connect to brokers, execution, risk authorization or model promotion.

Validation completed successfully in CI run 36173391620, Security and Dependency Scan run 36173391649, Phase 10 Live Gate Tests run 36173391610, External Intelligence Validation run 36173391707 and Cross-Asset ML Experiment run 36173391677 for commit badd2c1a168eb40d611f70c7a97adde9d2931f9f.


### Task 033 — Firebase data governance hardening

Completed and validated on 2026-09-25.

The Realtime Database rules are default-deny for both reads and writes, with a regression test enforcing the posture. The Firebase smoke test was executed successfully against the configured service-account/database environment after correcting the repository import. The backend remains the server-side Firebase Admin SDK boundary.

No credentials were added to the repository and no trading/execution behavior was changed.

Detailed task record: docs/codex/tasks/033-firebase-data-governance-hardening.md.

### Task 034 — Firebase usage monitoring

Completed and validated on 2026-09-25.

A path-scoped Firebase usage monitor measures serialized UTF-8 payload size and record count for the current application paths, classifies each path with explicit warning/critical thresholds, and publishes a JSON artifact through a scheduled GitHub Actions workflow. The monitor is observational only and does not delete data or alter trading behavior.

Validation completed successfully in Firebase Usage Monitor run 36189145824, CI run 36189145841, Security and Dependency Scan run 36189145888, External Intelligence Validation run 36189145939, Cross-Asset ML Experiment run 36189145798 and Phase 10 Live Gate Tests run 36189146243 on commit b378edf5d9c4158c190b905aa5571abb0abe0034.

The Firebase Usage Monitor successfully connected to the configured Firebase environment, measured the monitored paths and published the usage report artifact. The workflow returns a critical exit code only when a monitored path reaches the configured critical serialized-size threshold; it does not perform automatic deletion or retention changes.

Detailed task record: docs/codex/tasks/034-firebase-usage-monitoring.md.

### Task 035 — Firebase retention cleanup

Completed and validated on 2026-09-25.

A fail-closed, path-scoped Firebase retention mechanism was added for the paper decision and shadow decision ledgers. The initial policy uses a 180-day engineering retention default with a 100-record batch cap and dry-run behavior by default. Invalid or timezone-less timestamps are skipped, Firebase availability is required, and `paper/account` is outside the cleanup policy. The cleanup is exposed through a manual GitHub Actions workflow and does not perform scheduled or automatic deletion.

Validation completed successfully in CI, Security and Dependency Scan, Phase 10 Live Gate Tests, External Intelligence Validation and Cross-Asset ML Experiment for commit `78bb5d4de0010bc1a492d753a399dd674d4893ce`.

The current Firebase environment contains no records in the monitored ledger paths, so no retention deletion has been performed. The retention periods are engineering defaults, not legal or business retention requirements; enabling non-dry-run deletion requires a separate governance decision.

Detailed task record: `docs/codex/tasks/035-firebase-retention-cleanup.md`.

### Task 036 — Scheduler-to-DEMO broker integration

Implementation completed and validated on 2026-09-26.

The PAPER scheduler now exposes an explicit integration path to the existing controlled DEMO execution boundary through `SchedulerDemoExecutionAdapter`. DEMO execution remains fail-closed: a ready promotion plan is not executed without independent explicit authorization, application-owned pre/post state, and the existing controlled execution service. The scheduler does not call `order_send` directly and no automatic retry or live-broker path was introduced.

Final validation completed successfully on commit `2d827275e3c904c61df74f15bd98d5bab5e6797f`: CI run `36271207460`, External Intelligence run `36271207458`, Cross-Asset ML run `36271207490`, Phase 10 Live Gate Tests run `36271207493` and Security/Dependency Scan run `36271207472`. The Security workflow also confirmed the Windows runner PowerShell execution-policy correction and completed dependency audit, static security scan, backend tests and compilation successfully.

The Firebase retention governance checklist is also marked complete: the cleanup mechanism remains manual, fail-closed and dry-run-only pending a separate governance decision for deletion.

### Task 038 — Production container build baseline

Completed and validated on 2026-09-26.

A production-oriented Linux container baseline was added for the FastAPI backend: Python 3.12 slim runtime, non-root application user, port 8000, `/api/health` container health check, and a `.dockerignore` that excludes credentials and local state. The GitHub Actions workflow builds the image, starts the container, validates its health check and exercises the API health endpoint before cleanup.

Validation completed successfully in Container Build run `36278613121` for commit `3e3071a2a2f12df2ebd70f5c311a74cca10f41b7`. The same commit passed CI, Security and Dependency Scan, External Intelligence Validation, Cross-Asset ML Experiment and Phase 10 Live Gate Tests.

This remains a deployment foundation only. Production hosting, domain/TLS, runtime secret injection, persistent storage and operational monitoring remain separate work.

Detailed task record: `docs/codex/tasks/038-production-container-build-baseline.md`.

### Task 039 — Production API runtime hardening

Completed and validated on 2026-09-28.

FastAPI runtime hardening is complete with configurable CORS origins via `CORS_ALLOWED_ORIGINS`, optional disabling of interactive API documentation via `API_DOCS_ENABLED=false`, and baseline security response headers for content sniffing, framing and referrer policy. Default API behavior remains unchanged.

The final commit `8f429f1a51ef8c041c52239c119ae60f3a4bbc68` passed CI `36279159400`, Security and Dependency Scan `36279159348`, External Intelligence Validation `36279159374`, Cross-Asset ML Experiment `36279159343`, Phase 10 Live Gate Tests `36279159369` and Container Build `36279159358`.

The task does not enable LIVE trading, change DEMO authorization, add broker credentials, publish the container, or alter signals, risk limits or model promotion.

Detailed task record: `docs/codex/tasks/039-production-api-runtime-hardening.md`.

### Task 037 — Interrupted DEMO submission recovery correlation

Implementation completed on 2026-09-26.

The controlled DEMO execution boundary now persists a bounded correlation identifier with each intent, propagates it through OrderIntent and into the MT5 order comment, and normalizes the broker history comment back into recovery evidence. When the broker response is lost after authorization, the durable ledger remains SUBMITTED and recovery can promote the exact execution to FILLED only when correlation, symbol, side and quantity all match. Missing or mismatched evidence remains SUBMITTED and no automatic retry is performed.

Validation is deterministic and fault-injected: the test simulates an accepted broker submission followed by loss of the response, confirms the correlation survives in the durable ledger, recovers the matching broker evidence, and confirms the broker submission count remains one. No additional DEMO transaction was created.

Real broker-connected validation of an actually interrupted MT5 order_send() remains intentionally pending because reproducing that condition would require deliberately creating another DEMO transaction.

Detailed task record: docs/codex/tasks/037-interrupted-demo-submission-recovery.md.


### Task 040 — API observability baseline

Completed and validated on 2026-09-28.

The FastAPI runtime now provides deployment-neutral request observability: configurable `LOG_LEVEL`, one low-cardinality access event per completed request, exception logging without request bodies/query parameters/secrets, and UUID-based `X-Request-ID` correlation with preservation of valid caller-supplied IDs. Existing security headers and API behavior were preserved.

Validation completed successfully in CI `36418918794`, Security and Dependency Scan `36418918741`, External Intelligence Validation `36418918759`, Cross-Asset ML Experiment `36418918739`, Phase 10 Live Gate Tests `36418918776` and Container Build `36418918784`.

The task does not enable LIVE trading, alter DEMO authorization, add broker credentials, publish/deploy the container, or change trading signals, risk limits or model promotion.

Detailed task record: `docs/codex/tasks/040-api-observability-baseline.md`.


### Task 041 — API operational readiness contract

Completed and validated on 2026-09-28.

A provider-neutral `GET /api/ready` readiness contract was added alongside the existing lightweight `GET /api/health` liveness endpoint. Readiness fails closed with HTTP 503 when LIVE mode lacks existing safety prerequisites (LIVE enablement, model approval or risk gate) or when DEMO execution is enabled outside DEMO trading mode. Regression tests cover the ready default and unsafe LIVE configuration.

Validation completed successfully on commit `78c5c620967f7e7f10a4abdb9678e9e4fbdbd4cb`: CI `36423195902`, Security and Dependency Scan `36423195901`, External Intelligence Validation `36423195898`, Cross-Asset ML Experiment `36423195908`, Phase 10 Live Gate Tests `36423196108` and Container Build `36423195962`.

The task does not enable LIVE trading, alter DEMO authorization, add broker credentials, publish/deploy the container, or change trading signals, risk limits or model promotion. The readiness endpoint evaluates existing configuration flags only.

Detailed task record: `docs/codex/tasks/041-api-operational-readiness-contract.md`.


### Task 042 — Container runtime readiness validation contract

Completed and validated on 2026-09-28.

The production container validation now exercises both application liveness and operational readiness. The default safe container must return HTTP 200 from `/api/health` and `/api/ready`. A separate intentionally unsafe LIVE container is started with LIVE trading disabled, model approval missing and the risk gate disabled; `/api/ready` must return HTTP 503 and expose only the readiness issue labels needed for diagnosis.

The Docker HEALTHCHECK remains mapped to `/api/health`, preserving the distinction between lightweight liveness and deployment readiness. The task is validation-only and does not introduce broker credentials, execution authority, LIVE enablement, model promotion or DEMO transactions.

Validation completed successfully on commit `2a5346c89aa99cdfff0f49eeb7bd2abff538b88a`: Container Build `36426269273`, CI `36426269293`, Security and Dependency Scan `36426269385`, External Intelligence Validation `36426269281`, Cross-Asset ML Experiment `36426269365` and Phase 10 Live Gate Tests `36426269224`.

Detailed task record: `docs/codex/tasks/042-container-runtime-readiness-validation.md`.


### Task 043 — Production runtime configuration contract

Completed and validated on 2026-09-28.

A provider-neutral runtime configuration contract was added for the production-oriented Linux API container. The contract inventories the settings consumed by `backend/app/settings.py`, documents which values are sensitive and must be injected by the eventual hosting platform, and provides `deploy/production.env.example` with safe placeholders only.

The production template defaults to simulation, LIVE disabled, model approval disabled and DEMO execution disabled. It also documents CORS, API documentation, logging, persistence-path limitations and the separation between the Linux container and the authenticated Windows DOTO/MT5 workstation.

Automated regression coverage verifies that the template accounts for the deployment settings and preserves the disabled execution defaults.

Final validation commit: `9bf2fa27645ad1d7ccf0a14687414be7de739f06`.
Validation runs: CI `36430394082`, Security and Dependency Scan `36430393911`, External Intelligence Validation `36430394353`, Cross-Asset ML Experiment `36430394262`, Phase 10 Live Gate Tests `36430394033`, Container Build `36430394126`.

No real secret, credential, broker password, LIVE authorization or DEMO transaction was introduced.

Detailed task record: `docs/codex/tasks/043-production-runtime-configuration-contract.md`.


## Task 045 — Production persistence contract

Completed and validated on 2026-09-28. The production persistence boundary is explicit: Firebase is the authoritative external store for durable PAPER state and idempotency ledgers; the DEMO SQLite ledger remains on the controlled Windows DOTO/MT5 workstation; model artifacts under `models/xgboost` must be supplied independently of the container's ephemeral writable filesystem. Durable-state failures must fail closed rather than silently creating fresh authoritative state.

No LIVE authorization, DEMO transaction, broker credential or production hosting was introduced.


## Task 046 — Backup and recovery contract

Completed and validated on 2026-09-28. The repository now defines provider-neutral recovery requirements for Firebase/PAPER state, the Windows DEMO SQLite ledger and XGBoost model artifacts. Recovery must validate structural integrity, idempotency/provenance and read-only reconciliation before state-mutating execution resumes. No automated backup/restore provider or new DEMO transaction was introduced.


### Task 047 — Production hosting and deployment contract

Completed and validated on 2026-09-28. A provider-neutral production hosting/deployment contract now defines the Linux API/PAPER runtime, the separate Windows DOTO/MT5 DEMO execution boundary, TLS/ingress requirements, readiness/liveness usage, runtime secret handling, persistence/recovery integration, deployment lifecycle and minimum operational monitoring. The contract deliberately does not select or provision a cloud provider and does not enable LIVE or create a DEMO transaction.

Regression coverage verifies the Linux/Windows execution separation, safe runtime defaults, readiness/liveness distinction and provider-neutral deployment posture.

Detailed task record: `docs/codex/tasks/047-production-hosting-deployment-contract.md`.


### Task 048 — Production deployment artifact pipeline

Implemented a provider-neutral CI/CD boundary that builds the production container with the Git commit SHA, validates a simulation-only candidate through liveness/readiness, exports an immutable compressed image artifact and publishes a SHA-256 checksum to GitHub Actions artifacts. The pipeline does not push to an external registry, provision infrastructure, expose a public endpoint, enable LIVE/DEMO execution or submit broker orders.

Detailed task record: docs/codex/tasks/048-production-deployment-artifact-pipeline.md.


## Task 049 — Cloud Run production deployment

Implemented and merged on 2026-09-28. Cloud Run deployment is manual-dispatch only, authenticates GitHub Actions through OIDC/WIF, publishes commit-SHA images, deploys immutable Artifact Registry digests, references runtime secrets from Secret Manager, keeps the service private and verifies authenticated `/api/health` and `/api/ready` smoke tests. Runtime safety is explicitly simulation-only with LIVE, model approval and MT5/DEMO execution disabled. PR #72 subsequently corrected the service-level Invoker shell command.

Detailed task record: docs/codex/tasks/049-cloud-run-production-deployment.md.

## Task 050 — GCP infrastructure bootstrap

Implemented and merged on 2026-09-28. Terraform provisions the existing project's required APIs, Artifact Registry repository, deployment/runtime service accounts, deployment IAM, repository/main-restricted GitHub WIF and empty Secret Manager containers. Secret values, broker credentials, Cloud Run service creation and trading enablement remain outside Terraform. PR #71 removed duplicate Terraform outputs; PR #72 aligned the deployment Invoker command and bootstrap documentation.

The remaining gate is operator-side authenticated Terraform validation: `terraform init`, `terraform validate` and `terraform plan`, followed by explicit review before `terraform apply`.

Detailed task record: docs/codex/tasks/050-gcp-infrastructure-bootstrap.md.


## Task 051 — Fixed XGBoost OOS economic verdict

Implemented on 2026-10-06 in branch feat/xgboost-oos-economic-verdict.

The XGBoost OOS validation pipeline now produces artifacts/xgboost-oos-economic-verdict/report.json through scripts/run_xgboost_oos_economic_verdict.py. The decision is pre-specified: canonical policy baseline_060, one-bar confirmation, and the existing commission-plus-slippage scenario. A symbol must have positive after-cost strategy return and positive excess return versus buy-and-hold over the exact OOS replay window; PETR4, VALE3 and ITUB4 must all pass.

The verdict also cross-checks the canonical economic report against the signal-persistence report to detect semantic drift. It does not retrain, tune thresholds, select the best policy, or change execution behavior.

The latest validated pipeline run before this task was 37368612786 (commit 926757403211337b34f346cac0a8c895baa69bb6), which passed the existing XGBoost OOS pipeline but the current evidence does not satisfy the new economic-verdict criteria: canonical after-cost strategy returns were negative for all three symbols and underperformed buy-and-hold for all three. The appropriate conclusion is no economic validation / no model promotion, not a model-tuning action.

Detailed task implementation is in scripts/run_xgboost_oos_economic_verdict.py and tests/test_xgboost_oos_economic_verdict.py.
