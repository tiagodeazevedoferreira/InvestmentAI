# Task 028 — Fundamental score/ranking and margin-of-safety engine

## Objective

Provide a deterministic, provider-neutral fundamental scoring and ranking primitive, plus an explicit margin-of-safety calculation, using already normalized/derived fundamental metrics.

## Scope

- Score the existing fundamental metrics P/E, P/B, EV/EBITDA, ROE, ROIC and dividend yield on a normalized 0–1 scale.
- Make metric direction and threshold assumptions explicit and configurable.
- Combine component scores using validated weights that sum to 1.
- Produce deterministic rankings with a documented tie-break.
- Calculate margin of safety from an externally supplied intrinsic value and market price.
- Fail closed on invalid configuration, non-finite values, invalid intrinsic value and missing required metrics.
- Keep the implementation provider-neutral and independent of execution, broker integration and model-promotion logic.

## Scoring model

Each metric uses a configurable lower and upper bound.

For higher-is-better metrics:

score = clamp((value - lower) / (upper - lower), 0, 1)

For lower-is-better metrics:

score = clamp((upper - value) / (upper - lower), 0, 1)

The default metric directions are:

- Lower is better: P/E, P/B, EV/EBITDA.
- Higher is better: ROE, ROIC, dividend yield.

Default thresholds are explicit in code and are configuration inputs rather than hidden constants.

The aggregate fundamental score is the weighted sum of component scores. The default configuration requires all six metrics; callers may provide another explicit configuration with a different metric set and weights.

## Ranking

Ranking is descending by aggregate score. Ties are resolved deterministically by normalized symbol in ascending lexical order.

The engine does not select an investment, allocate capital, modify execution policy or authorize broker submission.

## Margin of safety

For positive intrinsic value:

margin_of_safety = (intrinsic_value - market_price) / intrinsic_value

A negative result means market price is above the supplied intrinsic value; a positive result means it is below the supplied intrinsic value. The engine reports the arithmetic result only and does not classify it as a buy/sell decision.

## Validation

- Valid higher-is-better and lower-is-better component scores.
- Clamping outside configured bounds.
- Weight validation and weight-sum validation.
- Missing required metrics.
- Non-finite metric/configuration values.
- Deterministic ranking and tie-break.
- Valid and invalid margin-of-safety inputs.
- No changes to broker/execution or model-promotion boundaries.

## Non-goals

- Provider selection or provider ranking.
- Automatic investment recommendations.
- Portfolio allocation or position sizing.
- DCF/Gordon assumption generation.
- Broker/MT5/DOTO integration.
- Live or DEMO order submission.
- Automatic model promotion.

## Limitations

The default thresholds are engineering defaults, not empirically validated investment thresholds. They must not be interpreted as evidence of expected return or profitability. Ranking is descriptive of the supplied metrics and configuration only. Margin of safety is entirely dependent on the supplied intrinsic-value methodology and assumptions.
