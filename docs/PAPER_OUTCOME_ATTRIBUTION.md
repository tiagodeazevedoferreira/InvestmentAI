# Paper Outcome Attribution

Outcome attribution is the first measurement layer after scheduled paper execution. It deliberately does not change the trading policy or authorize model promotion.

## Measurement contract

For each paper decision, the attribution layer aligns the decision bar with future completed bars and calculates forward price return at configurable horizons. The default horizons are 1, 5 and 20 bars.

- BUY signed return = forward return.
- SELL signed return = negative forward return.
- HOLD signed return = market forward return, with no hit classification.
- `hit=true` means the signed return is strictly positive.
- A horizon without enough future bars is marked incomplete rather than treated as a loss.

## Calibration interpretation

The initial summary reports observation count, hit rate, mean signed return and median signed return by action and horizon. These are descriptive statistics only. They are not sufficient for promotion because they do not yet include confidence intervals, transaction-cost calibration, regime stratification, or out-of-sample model evidence.

The next implementation step is to persist completed outcome observations alongside the Firebase decision ledger and produce a historical calibration report for PETR4, VALE3 and ITUB4. The report must distinguish completed and pending horizons and preserve the original decision timestamp and action so the evaluation remains causal.

## Safety boundary

Outcome attribution is read-only with respect to the trading policy. It cannot alter an order, bypass the risk gate, enable a broker, or promote a model. All measurements remain PAPER-only until the empirical promotion gate is explicitly satisfied.
