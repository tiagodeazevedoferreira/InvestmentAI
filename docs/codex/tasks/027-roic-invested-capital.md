# Task 027 — ROIC with invested-capital definition and validation

## Objective
Implement a deterministic, provider-neutral ROIC primitive with an explicit invested-capital definition and fail-closed validation.

## Scope
- Define invested capital as equity + total debt - cash.
- Define NOPAT as operating income × (1 - effective tax rate).
- Define ROIC as NOPAT / invested capital.
- Require finite numeric inputs and an effective tax rate in [0, 1].
- Reject non-positive invested capital because ROIC would not represent the intended capital-base measure.
- Preserve missing-data semantics by returning None when required inputs are unavailable.
- Expose the calculation through the existing fundamental multiples helper without changing its existing positional inputs.
- Keep the feature descriptive/research-only; it does not rank securities, alter valuation assumptions, change risk gates or authorize execution.

## Validation cases
1. Standard calculation with known NOPAT and invested capital.
2. Missing required inputs return None.
3. Tax rates outside [0, 1] fail closed.
4. Non-positive invested capital fails closed.
5. Existing derived-multiple inputs remain compatible while ROIC is populated when the new optional inputs are supplied.

## Boundaries and limitations
This task uses point-in-time invested capital. It does not average beginning/end invested capital, infer tax expense from incomplete statements, or silently substitute provider-specific fields. The caller must supply an explicit effective tax-rate assumption.

## Non-goals
- Fundamental score/ranking.
- Margin-of-safety decisions.
- Provider selection.
- Portfolio allocation.
- Broker/MT5/DOTO access or order submission.
- Model promotion or production-readiness claims.
