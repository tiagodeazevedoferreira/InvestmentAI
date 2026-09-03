# Empirical paper promotion gate

The promotion gate is an evidence evaluator, not an execution switch. It evaluates persisted paper calibration evidence against predefined criteria and always returns `promotion_allowed=false`. A passing result only means the evidence is eligible for explicit human review.

## Default criteria

The v1 gate evaluates BUY at the 5-bar horizon using:

- at least 30 completed observations;
- lower bound of the 95% Wilson hit-rate interval at least 50%;
- mean net signed return non-negative after the configured round-trip cost assumption;
- no causal volatility regime with hit-rate degradation greater than 10 percentage points versus the all-regime baseline;
- TradingView conflict rate no greater than 10%, when reconciliation evidence is supplied.

These values are deliberately conservative and transparent. They are not claims of statistical sufficiency for live trading.

## Interpretation

A failed criterion produces an explicit reason code. A passed gate does not establish economic significance, robustness, capacity, liquidity, or broker/exchange executability. The gate also does not correct for multiple testing or replace the broader ML robustness audit.

The TradingView condition is evidence reconciliation only. Missing TradingView evidence does not automatically fail the gate; supplied conflict evidence can fail it.

## Safety boundary

This component does not alter signal generation, risk limits, sizing, order routing, broker connectivity, or live enablement. No result from this gate can authorize capital deployment automatically. Any future promotion requires separate human approval and a subsequent operational readiness gate, including kill-switch and reconciliation hardening.

All functionality is PAPER/research-only.
