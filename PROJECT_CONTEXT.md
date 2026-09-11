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
- The preflight explicitly reported `submitted=false`; **no `order_send()` was called and no DEMO order was submitted**.
- The validator now accepts `DOTO_MT5_TERMINAL_PATH` and passes the configured terminal path to `mt5.initialize()`.
- GitHub commit `b262cc90b7a3f0cb0d219b2bf80f6ea8f55729fd` contains that terminal-path fix.
- The current PowerShell session uses `DOTO_MT5_SERVER`, `DOTO_MT5_LOGIN`, `DOTO_MT5_PASSWORD` and `DOTO_MT5_TERMINAL_PATH`; the password must remain outside source control and must never be written to this file.

## Current execution target
The real Doto/MT5 DEMO account connectivity and non-submitting order semantics have now passed the required checkpoint. The next application-level task is to make the FastAPI/settings layer consume the same configured MT5 terminal path (`DOTO_MT5_TERMINAL_PATH`) used by the validator, add regression coverage, and keep execution fail-closed. After that, review the durable internal DEMO ledger and reconciliation gates before considering any single controlled DEMO order test. **Do not call `order_send()` during the current validation/integration stage.** Automatic scheduler-to-broker execution remains disconnected. Live execution remains disabled.

## Known configuration integration gap
`backend/app/settings.py` currently exposes `mt5_terminal_path`, which Pydantic naturally maps to `MT5_TERMINAL_PATH`. The validator uses `DOTO_MT5_TERMINAL_PATH`. Therefore, unless alias support is added (or a second environment variable is manually maintained), FastAPI routes such as `/broker/mt5/status` and `/market/mt5/{symbol}` will not automatically see the same terminal-path variable used by the validator. This must be corrected in the application settings layer rather than by storing a terminal path in source code.

## Recent commits / handoff checkpoint
Latest verified `main` commit before this context update: `b262cc90b7a3f0cb0d219b2bf80f6ea8f55729fd` — `fix: use configured DOTO MT5 terminal in demo gateway`.
Previous related commits: `b4700f4d924ff0c7702cbdb38c7d35dd31aeccd4` (tests) and `d2cc3e3776f05d933eff53689ff0e03681e9108e` (DOTO DEMO login recognition).

## Handoff rule
A new conversation should read this file plus `DEVELOPMENT_STATUS.md`, `DECISIONS.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `docs/OPENBB_B3_PROVIDER.md` and `docs/PAPER_SIGNAL_AUTOMATION.md`, then inspect current source/workflows before changing anything. The context files are part of the project's continuity mechanism: after every material change, update the relevant documentation so a new chat can resume from the recorded state without relying on an old conversation.
