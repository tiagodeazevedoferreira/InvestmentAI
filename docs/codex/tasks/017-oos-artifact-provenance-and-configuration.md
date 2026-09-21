# Task 017 — OOS Artifact Provenance and Configuration Integrity

**Status:** IN PROGRESS

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

The task is complete only after the full XGBoost OOS validation pipeline is green on runner ECTIN8F38594, including the new provenance checks.
