# Task 031 — LSTM experiment

## Objective
Add a reproducible, leakage-safe LSTM experiment for the existing five-day directional target without changing the production model, execution policy, risk limits or promotion authority.

## Scope
- Build fixed-length causal sequences from the existing feature/target schema.
- Preserve chronological ordering; no random split or future-feature leakage.
- Provide explicit LSTM hyperparameters and deterministic seed.
- Train only when PyTorch is available; fail clearly otherwise.
- Report validation loss, validation accuracy and mean validation probability.
- Keep the experiment research-only and observational.

## Validation
- Sequence construction preserves order and uses only historical rows for each sample.
- Chronological train/validation/test split contains no shuffle.
- Invalid inputs fail closed.
- CI tests cover sequence construction and split behavior.
- The experiment must not alter XGBoost defaults, execution policy, risk gates or promotion logic.

## Non-goals
- No claim of LSTM superiority or profitability.
- No automatic model selection or promotion.
- No broker calls or trade execution.
- No change to live/paper execution policy.

## Limitations
LSTM results depend on feature quality, sequence length, hyperparameters, regime and sample size. A single validation run is diagnostic evidence only.
