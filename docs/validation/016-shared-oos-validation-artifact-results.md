# Task 016 — Shared XGBoost OOS validation artifact — Results

## Validation run

- GitHub Actions run: `35644076311`
- Commit: `24580d55c8aa9e275c8197a68ba95169cea0933b`
- Runner: `ECTIN8F38594`
- Status: successful
- Artifact: `xgboost-oos-validation-pipeline-2`
- Artifact ID: `10659666493`
- Artifact ZIP SHA-256: `e80aef1f987deacabfecf2e1d482ecad30ed56c9334be980e2619de03c955db5`

## Pipeline validation

The orchestrated workflow generated one shared real-data XGBoost OOS artifact per symbol and passed the resulting directory explicitly to:

1. Economic Report;
2. Cost Attribution;
3. Fold Stability.

The downstream scripts retain their standalone path when no artifact directory is provided, preserving focused workflow usability.

The generated OOS set contained 7 folds and 700 prediction rows for each symbol. Provider data contained 1,248 rows per symbol and passed the quality gate.

| Symbol | Provider rows | OOS folds | OOS rows | OOS start | OOS end |
|---|---:|---:|---:|---|---|
| PETR4 | 1,248 | 7 | 700 | 2023-10-23 | 2026-08-12 |
| VALE3 | 1,248 | 7 | 700 | 2023-10-23 | 2026-08-13 |
| ITUB4 | 1,248 | 7 | 700 | 2023-10-23 | 2026-08-12 |

## Automated checks

The workflow completed:

- shared OOS artifact contract tests;
- OOS economic contract tests;
- economic report contract test;
- cost attribution contract test;
- fold stability contract test;
- complete backend test suite: **64 passed**;
- backend compilation with `compileall`: **passed**.

The artifact contract preserves timestamps, predictions, probabilities and fold metadata and rejects duplicate/non-chronological timestamps and fold ranges outside the prediction set.

## Artifact packaging

The final validation artifact contains the shared OOS artifacts plus the Economic Report, Cost Attribution and Fold Stability outputs. Seven files were uploaded successfully.

This establishes the intended orchestration boundary: OOS generation is separated from downstream economic analyses, and the latter consume the serialized OOS result instead of regenerating the model signal.

## Interpretation and boundary

Task 016 is an engineering/reproducibility improvement to the research validation pipeline. It does not establish profitability, robustness, production readiness or model promotion.

No threshold optimization, hyperparameter tuning, broker execution, MT5/DOTO order submission or financial transaction occurred during this validation.
