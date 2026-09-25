# Task 030 — Production-grade portfolio risk limits

## Objective
Provide a deterministic, provider-neutral portfolio risk-limit evaluator that validates proposed portfolio weights against explicit hard limits before any downstream allocation or execution decision.

## Scope
- Validate finite portfolio weights and positive portfolio value.
- Validate asset labels and covariance dimensions.
- Enforce maximum absolute position weight.
- Enforce maximum gross exposure and absolute net exposure.
- Calculate annualized portfolio volatility from an explicitly annualized covariance matrix.
- Calculate parametric one-day VaR as a fraction of portfolio value from a daily covariance matrix and confidence.
- Return a deterministic approval result with structured breach reasons.
- Fail closed on malformed inputs and invalid configurations.
- Keep the evaluator advisory/authorization-boundary only: it never submits orders, changes weights, selects assets, or promotes models.

## Hard-limit definitions
For weights w:
- position exposure_i = |w_i|
- gross exposure = sum(|w_i|)
- net exposure = sum(w_i)
- annualized volatility = sqrt(w' Σ_annual w)
- one-day parametric VaR fraction = z_confidence * sqrt(w' Σ_daily w)

A limit is breached when the measured value is strictly greater than its configured maximum, subject to a small numerical tolerance.

## Validation
The implementation must reject:
- non-finite weights/covariance/portfolio value;
- mismatched covariance dimensions or labels;
- non-symmetric covariance;
- materially non-PSD covariance;
- duplicate asset labels;
- invalid confidence or negative limits;
- portfolio values that are not positive.

The evaluator must not silently repair covariance matrices or weights.

## Non-goals
- No asset selection or ranking.
- No portfolio optimization or automatic resizing.
- No broker calls, order submission, or live authorization.
- No claim that thresholds are empirically optimal.
- No model promotion.

## Limitations
Risk estimates depend on covariance quality, return frequency, confidence assumption and market regime. A passed limit check is a constraint check, not a guarantee against losses.
