# Paper calibration report

The calibration report is a descriptive measurement layer over persisted paper outcomes. It does not change signal policy, risk limits, position sizing or execution behavior.

## Metrics

For each action and horizon (1, 5 and 20 bars), the report calculates:

- observation count;
- directional hit rate;
- Wilson 95% confidence interval for hit rate;
- mean gross signed return;
- 95% Student-t confidence interval for the mean gross signed return;
- median net signed return;
- mean net signed return after an explicit round-trip transaction-cost assumption.

The cost assumption is expressed in basis points and is intentionally explicit. It is not presented as venue-calibrated until real paper/execution evidence supports that conclusion.

## Regime analysis

The aggregation API accepts a `regime_by_signal` mapping so that a separate, causal regime classifier can partition results without coupling market-regime logic to the statistical aggregator. Missing labels remain `all`.

A future runner may classify regimes from information available at the decision timestamp, for example realized volatility bands. It must not use future prices when assigning the regime.

## Interpretation boundary

Confidence intervals quantify sampling uncertainty; they do not establish economic significance, robustness or tradability. A positive paper result is not sufficient for model promotion. Promotion remains blocked until transaction costs, regime stability, out-of-sample evidence, operational reconciliation and the empirical promotion gate are satisfied.

All functionality in this report is PAPER/research-only.
