# Task 016 — Shared XGBoost OOS validation artifact

## Status

COMPLETE

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

1. Each symbol has exactly one generated XGBoostOOSRun in the orchestrated real-data pipeline.
2. Economic Report, Cost Attribution and Fold Stability consume the same serialized OOS predictions.
3. Artifact loading rejects malformed, non-chronological, duplicated or out-of-range prediction data.
4. Existing focused workflows remain usable without the shared artifact argument.
5. Focused tests, complete backend tests and compileall pass.
6. Pipeline uploads the shared artifact and all three downstream reports.

## Validation

Validated in GitHub Actions run `35644076311` on `main`, commit `24580d55c8aa9e275c8197a68ba95169cea0933b`, using runner `ECTIN8F38594`.

- Shared-artifact contract test passed.
- Existing OOS, economic-report, cost-attribution and fold-stability contract tests passed.
- Real-data shared OOS artifacts were generated for PETR4, VALE3 and ITUB4.
- The three downstream real-data reports consumed `--oos-artifact-dir artifacts/xgboost-oos-shared`.
- Complete backend suite: 64 passed.
- `compileall -q backend`: passed.
- Validation artifact `xgboost-oos-validation-pipeline-2` uploaded successfully, containing 7 files.
- Artifact ID: `10659666493`.
- Artifact ZIP SHA-256: `e80aef1f987deacabfecf2e1d482ecad30ed56c9334be980e2619de03c955db5`.

The real-data OOS contract remained 7 folds / 700 OOS rows per symbol, with 1,248 provider rows and a valid quality gate for PETR4, VALE3 and ITUB4.

No threshold optimization, hyperparameter tuning, model promotion, MT5/DOTO execution or financial transaction was performed.

Detailed results are recorded in `docs/validation/016-shared-oos-validation-artifact-results.md`.
