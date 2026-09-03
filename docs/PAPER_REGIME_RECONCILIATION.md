# Paper Regime and TradingView Reconciliation

## Purpose

PR #33 adds two research-only evidence layers:

1. a causal volatility regime label for persisted paper decisions;
2. reconciliation between paper decisions and TradingView validator evidence.

Neither layer changes signal policy, risk limits, sizing, execution, or broker behavior.

## Causal regime

The calibration runner computes the standard deviation of the trailing 20 daily log returns using only bars whose timestamp is at or before the paper decision bar.

Fixed thresholds are explicit:

- `low`: volatility < 1.5%
- `normal`: 1.5% <= volatility < 3.0%
- `high`: volatility >= 3.0%
- `insufficient_history`: fewer than 21 closes available

The implementation deliberately avoids thresholds learned from the full historical sample, which could introduce lookahead leakage into an empirical promotion study.

## TradingView reconciliation

Paper decisions are matched to TradingView events by normalized symbol and timestamp proximity. The default tolerance is 60 seconds.

Statuses:

- `aligned`: paper direction and TradingView direction agree;
- `conflict`: both exist but directions disagree;
- `paper_only`: paper decision has no TradingView event within tolerance;
- `tradingview_only`: TradingView event has no paper decision match.

Missing TradingView evidence is not interpreted as a trading failure. TradingView remains a validation/evidence source and never becomes an execution authority.

## Promotion boundary

These outputs are descriptive evidence only. They do not authorize model promotion or changes to the RSI policy. Empirical promotion requires a separate out-of-sample gate with predefined acceptance criteria, costs, robustness checks and causal evidence.
