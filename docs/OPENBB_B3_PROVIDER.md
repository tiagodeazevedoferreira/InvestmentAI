# OpenBB + B3 provider decision

## Investigation result — 2026-09-01

OpenBB is an integration layer, not a market-data owner. Its current provider catalog lists multiple independent extensions, and coverage varies by provider and subscription. The official catalog does not list a dedicated B3 provider extension.

For the first B3 proof of concept, InvestmentAI therefore selects the OpenBB `yfinance` provider extension. Yahoo Finance exposes Brazilian symbols using the `.SA` convention, for example `PETR4.SA`, `VALE3.SA` and `ITUB4.SA`.

This is a **research/backtest provider selection**, not a claim that Yahoo is authoritative for production trading.

## Why this provider first

- no API credential is required for the selected connector;
- it supports historical equity prices through OpenBB's standardized equity-price router;
- it covers the B3 symbols required for the first proof of concept;
- it allows the CI environment to validate the complete path without requiring a user machine;
- the provider remains replaceable because the InvestmentAI domain depends on `OpenBBMarketDataProvider`, not Yahoo-specific calls.

## Scope of the first validation

Symbols:

- PETR4 → PETR4.SA
- VALE3 → VALE3.SA
- ITUB4 → ITUB4.SA

Interval:

- daily (`1d`)

Required fields:

- open
- high
- low
- close
- volume

Quality gates:

- non-empty dataset;
- required columns present;
- no duplicate timestamps;
- no null required values;
- chronological index.

## Important limitation

Yahoo/yfinance is not a substitute for licensed exchange-grade B3 market data. Before production or live trading, InvestmentAI must validate a licensed/authoritative provider or B3 data product and compare its values against the research provider.

B3's own public materials and COTAHIST ecosystem remain candidates for an independent historical-validation adapter. This is intentionally separate from the first OpenBB provider integration.

## Architecture

`InvestmentAI → MarketDataProvider → OpenBB → yfinance → B3 symbol`

The existing direct yfinance implementation remains available as a fallback during migration. Future providers can be added without changing the feature engine, ML, backtester, SignalFusion or RiskGate.
