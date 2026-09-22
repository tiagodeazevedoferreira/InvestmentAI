# Task 018 — Source-Data Provenance for Shared XGBoost OOS Artifacts

**Status:** COMPLETED

## Objective

Bind each shared XGBoost OOS artifact to deterministic provenance for the exact normalized market-data input used to generate it, without changing model parameters, thresholds, backtest semantics, execution policy or broker controls.

## Scope

1. Record deterministic source provenance for every per-symbol OOS artifact:
   - provider identity;
   - normalized symbol;
   - requested date range;
   - effective data start/end;
   - normalized source row count;
   - canonical normalized OHLCV data SHA-256;
   - canonical market-data quality report.
2. Preserve this provenance in the shared artifact and manifest.
3. Provide reusable validation that rejects incompatible or altered source provenance.
4. Add focused contract coverage for provenance round-trip, source-data digest mismatch and metadata mismatch.
5. Keep standalone focused workflows usable without shared artifacts.
6. Validate through GitHub Actions on runner `ECTIN8F38594`.

## Non-goals

- No retraining or hyperparameter tuning.
- No threshold optimization.
- No changes to backtesting execution semantics.
- No MT5/DOTO or broker execution.
- No profitability, robustness or model-promotion claim.
- No change to the source provider or historical date range.

## Acceptance criteria

1. Every shared OOS artifact records the required source provenance.
2. The source-data fingerprint is deterministic for the normalized OHLCV input.
3. Manifest verification rejects altered source provenance and incompatible source metadata.
4. Focused provenance tests pass.
5. Complete backend test suite and compileall pass.
6. The orchestrated real-data pipeline preserves the same shared OOS architecture and remains green.

## Validation

Completed on 2026-09-21 through the XGBoost OOS validation pipeline on runner `ECTIN8F38594`.

- Workflow run: `35650687196`
- Commit: `a5939792a673bdbf47263cfbdd0ad978d4bb6544`
- Result: **success**
- Shared OOS provenance contract tests: **passed**
- Shared OOS artifact generation and provenance verification: **passed**
- Real-data economic report: **passed**
- Real-data cost attribution: **passed**
- Real-data fold stability: **passed**
- Complete backend test suite: **passed**
- Backend compileall: **passed**
- Validation artifact: `xgboost-oos-validation-pipeline-5`
- Artifact ID: `10662546139`
- Artifact ZIP SHA-256: `9ffa87b2441b5096e24bf20b614a9cafa1f1570558dc1496d224d1205f8566c4`

Task 018 is therefore closed as an engineering/reproducibility task. It does not establish profitability, robustness, model superiority, production readiness or permission to execute trades.
