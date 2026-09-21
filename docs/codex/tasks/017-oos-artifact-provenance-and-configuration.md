# Task 017 — OOS Artifact Provenance and Configuration Integrity

**Status:** COMPLETE

## Objective

Strengthen the provenance and configuration integrity of the shared XGBoost OOS validation artifacts without changing model parameters, thresholds, execution policy, broker controls, or trading behavior.

## Scope

1. Record a SHA-256 digest and file size for every per-symbol OOS artifact in the shared manifest.
2. Provide reusable validation for the OOS generation configuration.
3. Verify the shared manifest and every referenced artifact before downstream analysis.
4. Require downstream reports consuming shared artifacts to validate the artifact configuration against their CLI configuration.
5. Add focused contract coverage for configuration mismatch, digest verification, and manifest integrity.
6. Preserve standalone focused workflows when no shared artifact directory is supplied.
7. Validate through GitHub Actions on the designated self-hosted runner.

## Non-goals

- No retraining or hyperparameter tuning.
- No threshold optimization.
- No changes to backtesting execution semantics.
- No MT5/DOTO or broker execution.
- No profitability, robustness, or model-promotion claim.

## Acceptance criteria

1. Each shared OOS artifact has a deterministic SHA-256 digest recorded in manifest.json.
2. Manifest verification rejects missing files, size mismatches, digest mismatches, symbol mismatches, or configuration mismatches.
3. Shared-artifact downstream scripts reject incompatible horizon/train/test/step/threshold/initial-cash configuration.
4. Focused artifact and configuration contract tests pass.
5. Complete backend test suite and compileall pass.
6. The orchestrated pipeline verifies provenance before running the three downstream analyses.
7. Validation results are documented with the workflow run and artifact digest.

## Validation

Completed on 2026-09-21 through GitHub Actions run **35649061333** on commit `8213f6cbb0a6ecab2ef60ca95ab8b2f244c24b48`, using runner `ECTIN8F38594` (Windows/X64).

Validated:

- provenance/configuration contract tests: **5 passed**;
- XGBoost OOS contract tests: passed;
- economic report contract: passed;
- cost attribution contract: passed;
- fold stability contract: passed;
- shared OOS generation plus manifest provenance verification: passed;
- real-data Economic Report, Cost Attribution and Fold Stability: passed using the same shared OOS artifacts;
- complete backend suite: **64 passed**;
- backend `compileall`: passed;
- validation artifact: `xgboost-oos-validation-pipeline-4`, artifact ID `10661990547`, ZIP SHA-256 `afd781781f977310eb87e52364e1d08e2443c1feb283675c53882cd388901bc5`.

The digest-specific contract now mutates a byte while preserving file size, isolating SHA-256 mismatch detection from size mismatch detection. Configuration mismatch validation also passed. No model parameters, thresholds, backtest semantics, execution policy, MT5/DOTO integration or broker controls were changed.
