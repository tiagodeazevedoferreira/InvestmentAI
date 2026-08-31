# Project Context

## Identity
- Repository: `tiagodeazevedoferreira/InvestmentAI`
- Firebase project: `investmentai-ae1e5`
- Realtime Database: `https://investmentai-ae1e5-default-rtdb.firebaseio.com`

## Objective
Build a production-oriented investment research and simulation platform integrating Value Investing, Trading, Portfolio/Risk Management and AI/ML, with a controlled path to automated execution.

## Core principles
1. Data quality and provenance before modeling.
2. No look-ahead bias or leakage in backtests/training.
3. Simulation and paper trading precede broker demo.
4. Live trading is disabled by architecture until explicit validation and promotion.
5. Risk controls are independent from prediction models.
6. Secrets never enter source code or frontend bundles.
7. Firebase Realtime Database stores operational/state data, not unlimited raw market history.
8. Every material change updates this context and status documentation.

## Modules
- Fundamental analysis: statements, P/E, P/B, EV/EBITDA, ROE, ROIC, dividend yield, DCF/Gordon valuation, margin of safety.
- Trading: OHLCV ingestion, EMA 9/21, RSI, Bollinger Bands, signal engine and backtesting.
- Portfolio: Markowitz optimization, efficient frontier, Sharpe maximization and parametric 95% daily VaR.
- AI/ML: technical feature engineering, 5-trading-day directional prediction, model validation and registry; XGBoost first, LSTM optional after baseline validation.
- Execution: simulation, paper, broker demo and eventual live order manager with risk gates.

## Environments
`simulation`, `paper`, `demo`, `live`.

`live` must require all of: approved model, approved risk gate, explicit live configuration and live broker credentials. Default is `simulation`.

## Current implementation
The repository foundation is being established with API contracts, services, data models, Firebase repository, risk/execution controls, PWA frontend, tests and CI.

## Data strategy
Use provider adapters so Yahoo Finance/yfinance can be replaced without rewriting domain logic. Cache/aggregate derived data and enforce retention policies before writing to Firebase.

## Handoff rule
A new conversation should read this file plus `DEVELOPMENT_STATUS.md`, `DECISIONS.md` and `ROADMAP.md`, then inspect the current source before making changes.

## Next development target
Validate CI and Firebase connectivity, then expand provider coverage and quantitative/ML services based on test results.
