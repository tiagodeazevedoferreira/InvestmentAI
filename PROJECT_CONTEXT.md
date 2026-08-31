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
4. Firebase Realtime Database is operational/state storage, not unlimited raw market history.
5. Simulation → Paper → Demo → Live is mandatory.
6. Live trading is disabled by architecture until explicit promotion gates pass.
7. Risk controls are independent from prediction models.
8. Secrets never enter source code or frontend bundles.
9. TradeMaster is not vendored; its simulator/RL/evaluation concepts are used as design references.
10. XGBoost is the first supervised baseline; LSTM and RL are experimental extensions.
11. Every material change updates this context/status/decision documentation.

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

## Handoff rule
A new conversation should read this file plus `DEVELOPMENT_STATUS.md`, `DECISIONS.md`, `ARCHITECTURE.md` and `ROADMAP.md`, then inspect current source/workflows before changing anything.

## Current target
Complete CI/integration validation and continue hardening the end-to-end research → model → simulator → paper/demo pipeline before any live capability is considered.
