# Development Status

Last updated: 2026-09-25

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
- [x] Scheduler → DEMO fail-closed promotion boundary (plan-only; broker submission disconnected)
- [ ] Scheduler → DEMO broker integration
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
- [ ] Execute Firebase smoke test against configured secret
- [ ] Production security rules
- [ ] Data-size monitoring/quotas dashboard
- [ ] Automated retention cleanup

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
- [x] Scheduler → DEMO promotion-boundary unit tests
- [x] Historical OHLCV pipeline and temporal-purge tests
- [x] Full integration test suite against provider mocks
- [x] End-to-end training/backtest test
- [x] Security/dependency scan
- [ ] Production deployment

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

A broker-connected, read-only recovery harness was then validated using a disposable SQLite ledger. It seeded the already confirmed Order 29453207 / Deal 28862296 and a separate synthetic unknown submission. Targeted MT5 history promoted only the confirmed record to FILLED; the unknown record remained SUBMITTED; order_send was not called; and temporary SQLite state was successfully discarded on Windows. A separate fault-injected coordinator test confirms that a timeout after local authorization preserves SUBMITTED uncertainty rather than classifying the intent as FAILED or retrying automatically. The new scheduler-to-DEMO boundary now exposes the scheduler's deterministic decision, quantity, reference price and risk result to a fail-closed promotion planner. The planner is disabled by default, requires an explicit symbol mapping, and stops at an OrderIntent; it does not own a broker or call order_send. Actual scheduler-driven DEMO submission remains disconnected pending a separate promotion step. A real broker interruption is intentionally not induced merely for testing because doing so could create another DEMO transaction. Live execution remains disabled.

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

Detailed task record: docs/codex/tasks/032-rl-agent-experiment.md.


### Task 033 — Firebase data governance hardening

Completed and validated on 2026-09-25.

The Realtime Database rules are default-deny for both reads and writes, with a regression test enforcing the posture. The Firebase smoke test was executed successfully against the configured service-account/database environment after correcting the repository import. The backend remains the server-side Firebase Admin SDK boundary.

No credentials were added to the repository and no trading/execution behavior was changed.

Detailed task record: docs/codex/tasks/033-firebase-data-governance-hardening.md.

### Task 034 — Firebase usage monitoring

Implementation in progress on 2026-09-25.

A path-scoped Firebase usage monitor now measures serialized UTF-8 payload size and record count for the current application paths, classifies each path with explicit warning/critical thresholds, and publishes a JSON artifact through a scheduled GitHub Actions workflow. The monitor is observational only and does not delete data or alter trading behavior.

Validation workflows are currently running for the implementation commit; Task 034 will be marked complete after CI, Security and the Firebase Usage Monitor workflow complete successfully against the configured Firebase environment.

Detailed task record: docs/codex/tasks/034-firebase-usage-monitoring.md.
