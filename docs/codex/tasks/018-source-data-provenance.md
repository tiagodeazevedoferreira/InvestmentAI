# Task 018 — Source-Data Provenance for Shared XGBoost OOS Artifacts

**Status:** IN PROGRESS

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

The task is complete only after the XGBoost OOS validation pipeline is green on runner `ECTIN8F38594` with the new source-provenance contracts.
