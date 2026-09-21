# Task 016 — Shared XGBoost OOS validation artifact

## Status

IN PROGRESS

## Objective

Generate the XGBoost out-of-sample prediction set once per symbol and make the Economic Report, Cost Attribution and Fold Stability analyses consume that same immutable OOS artifact.

## Scope

- Add a versioned JSON artifact contract for XGBoostOOSRun.
- Serialize probabilities, predictions and fold metadata without losing timestamps.
- Validate artifacts before they are consumed.
- Add a single real-data artifact generation script.
- Allow the three existing downstream reports to consume the shared artifact through an explicit directory argument.
- Keep standalone report workflows functional when no artifact directory is supplied.
- Update the single-entry validation pipeline so OOS generation happens once per symbol.
- Add focused contract tests proving artifact round-trip and downstream reuse.
- Upload the shared OOS artifact with the validation outputs.

## Non-goals

- No threshold optimization.
- No hyperparameter tuning.
- No model promotion.
- No changes to trading or broker execution.
- No MT5/DOTO execution.
- No claim of profitability or robustness.

## Acceptance criteria

1. Each symbol has exactly one generated XGBoostOOSRun in the orchestrated pipeline.
2. Economic Report, Cost Attribution and Fold Stability consume the same serialized OOS predictions.
3. Artifact loading rejects malformed, non-chronological, duplicated or out-of-range prediction data.
4. Existing focused workflows remain usable without the shared artifact argument.
5. Focused tests, complete backend tests and compileall pass.
6. Pipeline uploads the shared artifact and all three downstream reports.
