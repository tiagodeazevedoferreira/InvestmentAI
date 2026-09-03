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

## Current execution target
Stabilize the scheduler with real CI runs, then add outcome attribution/calibration, paper-to-TradingView reconciliation, kill switch/reconciliation and only afterward a broker demo adapter. No live execution should be enabled as part of these steps.

## Handoff rule
A new conversation should read this file plus `DEVELOPMENT_STATUS.md`, `DECISIONS.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `docs/OPENBB_B3_PROVIDER.md` and `docs/PAPER_SIGNAL_AUTOMATION.md`, then inspect current source/workflows before changing anything.
