# Task 029 — Robust covariance/shrinkage

## Objective

Add a deterministic, validated covariance-estimation boundary for portfolio/risk analytics, using Ledoit-Wolf shrinkage as an opt-in alternative to the sample covariance matrix.

## Scope

- Accept a numeric return matrix with observations in rows and assets in columns.
- Validate finite, non-empty data and minimum dimensionality.
- Estimate the sample covariance matrix and Ledoit-Wolf shrinkage covariance.
- Expose the estimated covariance matrix, shrinkage coefficient and asset labels.
- Preserve the existing sample-covariance portfolio behavior by making shrinkage explicitly opt-in.
- Provide a helper for annualization through an explicit periods-per-year parameter.
- Reject malformed or non-finite inputs rather than silently repairing them.

## Validation

- Sample and Ledoit-Wolf covariance dimensions match the input.
- Estimated covariance is finite and symmetric.
- Ledoit-Wolf output is positive semidefinite within numerical tolerance.
- Shrinkage coefficient is in [0, 1].
- Asset names are preserved.
- Annualization is explicit and deterministic.
- Invalid/empty/non-finite data fails closed.
- Existing portfolio optimizer behavior remains unchanged unless the caller explicitly selects the new estimator.

## Boundaries

This task improves covariance estimation for portfolio analytics only. It does not change asset selection, position sizing policy, execution, broker integration, live-trading authorization or model promotion.

## Limitations

Shrinkage improves numerical conditioning and can reduce estimation noise; it does not establish future return predictability or profitability. The estimator remains sensitive to the return sample, observation frequency and regime changes.