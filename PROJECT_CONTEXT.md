# Project Context

## Identity
- Repository: `tiagodeazevedoferreira/InvestmentAI`
- Firebase project: `investmentai-ae1e5`
- Realtime Database: configured via GitHub variable `FIREBASE_DATABASE_URL`

## Objective
Build a production-oriented investment research, simulation and automated-trading platform integrating Value Investing, Technical/Quant Trading, Portfolio/Risk Management and AI/ML, with a controlled path to demo and eventual live execution.

## Architecture principles
1. Data quality and provenance before modeling.
2. No look-ahead bias or leakage in backtests/training.
3. Provider abstraction; OpenBB is the preferred integration layer, with Yahoo/yfinance fallback.
4. Firebase RTDB is operational/state storage, not unlimited raw market history.
5. Simulation → Paper → Demo → Live is mandatory.
6. Live trading is disabled by architecture until explicit promotion gates pass.
7. Risk controls are independent from prediction models.
8. Secrets never enter source code or frontend bundles.
9. TradeMaster is not vendored; its simulator/RL/evaluation concepts are used as design references.
10. XGBoost is the first supervised baseline; LSTM and RL are experimental extensions.
11. Every material change updates this context/status/decision documentation.
12. Paper automation must be deterministic, bounded and idempotent before any broker integration.

## Modules
- Fundamental analysis: statements, P/E, P/B, EV/EBITDA, ROE, ROIC, dividend yield, DCF/Gordon valuation, margin of safety.
- Data layer: OpenBB-first provider abstraction and normalized feature/data interfaces.
- Trading: OHLCV, EMA 9/21, RSI, Bollinger, signal engine and cost-aware backtesting/simulation.
- Portfolio: Markowitz optimization, efficient frontier, Sharpe maximization and parametric 95% daily VaR.
- AI/ML: technical feature engineering, five-trading-day directional target, chronological train/validation/test split, XGBoost registry metadata and financial evaluation.
- RL: framework-neutral policy boundary, market simulator with commission/slippage for future TradeMaster-inspired agents.
- Execution: simulation, paper, broker demo and eventual live order manager with independent risk gates.

## Environments
`simulation`, `paper`, `demo`, `live`.

`live` requires all of: approved model, approved risk gate, explicit live configuration and live broker credentials. Default is `simulation`.

## Data/storage strategy
OpenBB/provider adapters supply market and fundamental data. Large historical datasets/model artifacts should not be copied wholesale into Firebase. Firebase should retain bounded operational state, signals, predictions, positions, orders, executions, configuration and audit metadata.

## TradingView integration
TradingView is an independent technical-evidence source and manual paper-trading validation venue. The repository contains a versioned Pine validator plus webhook normalization/authentication, reconciliation, SignalFusion/RiskGate integration and decision observability. TradingView does not have execution authority in InvestmentAI.

## OpenBB/B3 provider status
The current OpenBB catalog does not expose a dedicated B3 provider. For the first B3 proof of concept, InvestmentAI selects the OpenBB `yfinance` provider extension, using Yahoo's `.SA` symbol convention for PETR4, VALE3 and ITUB4. This selection is for research/backtesting and is not treated as authoritative exchange-grade production data.

The repository now contains an OpenBB market-data adapter, symbol normalization and a quality gate requiring OHLCV fields, non-empty data, unique chronological timestamps and no null required values. A CI smoke workflow validates PETR4, VALE3 and ITUB4 through the complete OpenBB/yfinance path.

## Paper execution
The internal paper engine is deterministic and broker-independent. It supports market and limit orders, crossed-limit fills on market marks, configurable fee/slippage, cash and position validation, weighted-average cost, realized/unrealized P&L, mark-to-market and bounded Firebase persistence. API endpoints are under `/api/paper/*`. It never contacts TradingView or a live venue.

## Paper automation
`POST /api/paper/automate` connects supplied OHLCV bars to the deterministic RSI policy, risk gate, conservative position sizing and the internal paper executor. RSI<30 produces BUY, RSI>70 produces SELL, otherwise HOLD. BUY is capped by target allocation and paper order notional; SELL requires an existing position; HOLD never creates an order. `execute=false` supports shadow evaluation without account mutation. This remains PAPER only.

## Provider-backed paper scheduler
`scripts/run_paper_scheduler.py` obtains fresh B3 history through the OpenBB/yfinance provider boundary for PETR4, VALE3 and ITUB4, then invokes the existing paper automation policy. It is restricted to a weekday post-close B3 window, requires Firebase for durable state, and persists a deterministic decision ledger key based on symbol/bar timestamp/action. Repeated scheduler runs therefore skip already-processed decisions. GitHub Actions serializes runs and invokes the scheduler at 20:30 UTC (17:30 BRT) on weekdays. Manual dispatch supports shadow mode and an explicit guard bypass for validation.

## DEMO broker boundary
The Doto/MT5 adapter is DEMO-only and fail-closed. It verifies the DEMO server during initialization, normalizes account/positions/open orders/executions for reconciliation, uses bid/ask semantics for market orders, requires `order_check()` before `order_send()`, rejects unsupported limit intents and refuses cancellation until pending-order semantics are validated. `AuthorizedDemoExecutor` requires kill-switch clearance plus healthy/fresh pre-execution reconciliation and healthy post-execution reconciliation. The scheduler is intentionally disconnected from the DEMO broker.

### Doto/MT5 DEMO validation checkpoint — 2026-09-11
- DEMO account: `5344431`
- MT5 server: `DOTOGlobal-Real` (the server name does **not** mean LIVE; the connected account reports `trade_mode=0`, i.e. DEMO).
- Correct Doto terminal executable: `C:\Users\tiago.ferreira\AppData\Roaming\DOTO Global MT5 Terminal\terminal64.exe`
- Explicit MT5 initialization with that terminal path succeeds (`initialize=True`, `last_error=(1, 'Success')`).
- Terminal state validated: connected, `trade_allowed=True`, `tradeapi_disabled=False`.
- Account state validated: company `DOTO Global Ltd`, currency `BRL`, balance/equity `52000.0`, leverage `500`, `trade_allowed=True`, `trade_expert=True`.
- `EURUSD` is confirmed as an available MT5 symbol; the terminal exposes 216 symbols in the tested session.
- Non-submitting order preflight for `EURUSD BUY quantity=1` succeeded: `order_check()` returned `retcode=0`, `comment=Done`.
- The exact non-submitting preflight for `EURUSD BUY quantity=0.01` also succeeded: `order_check()` returned `retcode=0`, `comment=Done` and explicitly reported `submitted=false`.
- The validator accepts `DOTO_MT5_TERMINAL_PATH` and passes the configured terminal path to `mt5.initialize()`.
- The validator now accepts decimal lot volume, including the intended `0.01` EURUSD test volume.
- GitHub commits `b262cc90b7a3f0cb0d219b2bf80f6ea8f55729fd` and `6f9c85643e3a679a61698d5cbea64b49daa7f8bd` contain the terminal-path and decimal-volume fixes.
- The current PowerShell session uses `DOTO_MT5_SERVER`, `DOTO_MT5_LOGIN`, `DOTO_MT5_PASSWORD` and `DOTO_MT5_TERMINAL_PATH`; the password must remain outside source control and must never be written to this file.

### First controlled DEMO transaction checkpoint — 2026-09-11
- User explicitly authorized the first controlled DEMO transaction: `EURUSD BUY 0.01`.
- The controlled runner executed the order through the guarded DEMO execution path.
- Reported lifecycle state: `FILLED`.
- Reported order ID: `29453207`.
- Reported deal ID: `28862296`.
- The broker submission itself succeeded sufficiently for the ledger to reach `FILLED` before the runner encountered a reporting bug.
- The runner then incorrectly attempted `.get()` on the `DemoExecutionResult` dataclass, producing `CONTROLLED DEMO RUN: BLOCKED` after the successful execution. This is a reporting defect, not evidence that the broker transaction failed.
- The reporting defect was fixed in commit `3ce15dd2c9336b037c899244c0d6afe3baaeca1e` by reading the nested `DemoExecutionResult.execution` mapping and `post_reconciliation` result explicitly.
- **Do not rerun the runner with `--execute` to verify the reporting fix**, because doing so would create another broker order. Verification must be read-only.
- Next required action: pull commit `3ce15dd2c9336b037c899244c0d6afe3baaeca1e`, then perform read-only external reconciliation against the live DEMO terminal and inspect the durable local ledger/portfolio state for order `29453207` / deal `28862296`.

## Application configuration checkpoint — 2026-09-11
- `backend/app/settings.py` now reads `DOTO_MT5_TERMINAL_PATH` as the canonical environment variable for `settings.mt5_terminal_path`.
- `MT5_TERMINAL_PATH` remains accepted as a backwards-compatible alias.
- Regression tests were added in `backend/tests/test_settings.py` for both environment-variable names.
- Commit `18a39412c312c29825299c5e637495c8cb0b0573` contains the settings fix and its tests in the same commit.

## API integration checkpoint — 2026-09-11
- The FastAPI application exposes the read-only endpoint `GET /api/broker/mt5/status`.
- The endpoint was validated against the configured Doto MT5 terminal and returned `connected=true`, login `5344431`, server `DOTOGlobal-Real`, company `DOTO Global Ltd`, currency `BRL`, balance/equity `52000.0`, `trade_allowed=true` and `trade_expert=true`.
- This confirms the application path `InvestmentAI → FastAPI → MT5 → DOTO` for read-only account state.
- No execution endpoint is enabled by this validation and no `order_send()` was called.
- Full automated test suite was green: `231 passed, 2 warnings`.

## Current execution target
The first controlled DEMO transaction has now been submitted and the runner's durable ledger reports `FILLED` for `EURUSD BUY 0.01`, order `29453207`, deal `28862296`. The remaining task is **read-only post-execution reconciliation and verification**: confirm the position/order/deal in the Doto MT5 terminal, confirm the persisted internal portfolio state matches the external snapshot, and verify the corrected runner reporting path without submitting another order. No additional DEMO order should be sent until this reconciliation is complete. Automatic scheduler-to-broker execution remains disconnected. Live execution remains disabled.

## Recent commits / handoff checkpoint
- `3ce15dd2c9336b037c899244c0d6afe3baaeca1e` — `Fix controlled DEMO runner result reporting`
- `6f9c85643e3a679a61698d5cbea64b49daa7f8bd` — `fix: support decimal DEMO order preflight volume`
- `ff90035e8cc6becb0c5d9a68ecac8fef3db93ae5` — `test: cover decimal DEMO preflight volume`
- `6949dbf` — `fix: configure pytest backend pythonpath`
- `18a39412c312c29825299c5e637495c8cb0b0573` — `fix: align MT5 terminal environment configuration`
- `eb01b016641edd7b46a41c74f71fc43656a93b57` — `docs: update project context with Doto MT5 demo validation checkpoint`
- `b262cc90b7a3f0cb0d219b2bf80f6ea8f55729fd` — `fix: use configured DOTO MT5 terminal in demo gateway`

## Handoff rule
A new conversation should read this file plus `DEVELOPMENT_STATUS.md`, `DECISIONS.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `docs/OPENBB_B3_PROVIDER.md` and `docs/PAPER_SIGNAL_AUTOMATION.md`, then inspect current source/workflows before changing anything. The context files are part of the project's continuity mechanism: after every material change, update the relevant documentation so a new chat can resume from the recorded state without relying on an old conversation.
