# Task 017 — OOS Artifact Provenance and Configuration Integrity Results

**Status:** COMPLETE

## Validation run

- GitHub Actions run: **35649061333**
- Commit: `8213f6cbb0a6ecab2ef60ca95ab8b2f244c24b48`
- Runner: `ECTIN8F38594` (Windows/X64)
- Workflow: **XGBoost OOS Validation Pipeline**
- Date: 2026-09-21

## What was validated

The shared XGBoost OOS artifact pipeline now enforces two complementary integrity dimensions:

1. **configuration integrity** — downstream consumers reject artifacts whose horizon, train size, test size, step, threshold or initial cash differ from the expected research configuration;
2. **artifact integrity** — the shared manifest records both file size and SHA-256 for each per-symbol OOS artifact, and verification rejects missing files, size mismatches, digest mismatches and incompatible metadata.

The orchestrated pipeline performs provenance verification before the three downstream real-data analyses consume the shared artifacts.

The digest contract test was specifically corrected so that the mutated artifact preserves its original file size. This isolates the SHA-256 failure mode rather than accidentally exercising the size guard first.

## CI results

- Provenance/configuration contract tests: **5 passed**.
- XGBoost OOS contract tests: passed.
- Economic report contract: passed.
- Cost attribution contract: passed.
- Fold stability contract: passed.
- Shared OOS artifact generation and provenance verification: passed.
- Real-data Economic Report: passed.
- Real-data Cost Attribution: passed.
- Real-data Fold Stability: passed.
- Complete backend suite: **64 passed**.
- Backend `compileall`: passed.

## Real-data validation envelope

The same shared OOS prediction artifact remained the source for Economic Report, Cost Attribution and Fold Stability.

For each of PETR4, VALE3 and ITUB4:

- provider dataset: **1,248 rows**;
- quality gate: **valid**;
- OOS folds: **7**;
- OOS prediction rows: **700**;
- threshold: **0.60**;
- OOS start: **2023-10-23**;
- OOS end: PETR4 **2026-08-12**, VALE3 **2026-08-13**, ITUB4 **2026-08-12**.

These figures are validation metadata, not evidence of profitability or production readiness.

## Validation artifact

Uploaded GitHub Actions artifact:

- Name: `xgboost-oos-validation-pipeline-4`
- Artifact ID: `10661990547`
- Size: **38,845 bytes**
- ZIP SHA-256: `afd781781f977310eb87e52364e1d08e2443c1feb283675c53882cd388901bc5`

## Boundary

Task 017 is an engineering/reproducibility hardening task. It does not establish profitability, robustness, model superiority, production readiness or permission to trade.

No retraining, threshold optimization, hyperparameter tuning, backtest-semantic change, MT5/DOTO execution or broker transaction occurred as part of this task.
