# Task 015 — XGBoost OOS Fold-Level Economic Stability Results

## Validation status

COMPLETE

Validated through the self-hosted Windows runner `ECTIN8F38594`.

## Configuration

- Symbols: PETR4, VALE3, ITUB4
- Requested history: 2021-09-15 through 2026-09-15
- Horizon: 5
- Train size: 500
- Test size: 100
- Step: 100
- Threshold: 0.60
- Initial cash: 100,000
- OOS folds per symbol: 7
- OOS rows per symbol: 700
- Scenarios:
  - zero cost
  - 0.1% commission + 5 bps slippage

The OOS prediction set is generated once per symbol and then sliced into individual fold runs for the economic replays. The two scenarios for a fold therefore use the same predictions and threshold.

## Validation results

The focused contract test initially exposed two incorrect test expectations. The implementation itself required 100 OOS rows per production fold, while the test expected 3, and the test assumed an incorrect scenario ordering. Both test assertions were corrected without changing production logic.

The corrected focused tests passed in the subsequent self-hosted workflow execution.

The real-data fold stability report completed successfully and produced 7 folds for each of PETR4, VALE3 and ITUB4, with 100 test rows per fold.

The report confirmed the expected OOS start of 2023-10-23 for all three symbols. OOS end dates were:
- PETR4: 2026-08-12
- VALE3: 2026-08-13
- ITUB4: 2026-08-12

All three provider datasets reported 1,248 rows and a valid market-data quality gate.

### ITUB4 descriptive summary

Zero-cost:
- 7 folds
- 3 positive / 4 negative
- mean fold return: +3.2441%
- median: -0.6556%
- minimum: -5.2703%
- maximum: +22.1930%
- standard deviation: 9.1952%
- sum of arithmetic fold returns: +22.7089%

Combined transaction costs:
- 7 folds
- 2 positive / 5 negative
- mean fold return: -1.8085%
- median: -5.8779%
- minimum: -9.7099%
- maximum: +16.4663%
- standard deviation: 8.7172%
- sum of arithmetic fold returns: -12.6596%

The workflow output also showed the combined-cost scenario for the evaluated symbols had materially more negative folds than the zero-cost diagnostic scenario. The fold-level analysis is descriptive and does not rank assets or select a model.

## Interpretation boundary

The fold-level results separate temporal dispersion from the aggregate result, but they do not establish profitability or production readiness.

The arithmetic sum of fold returns is a dispersion statistic, not a compounded portfolio return.

No threshold optimization, parameter tuning, model promotion, MT5/DOTO execution or broker order submission occurred.

The generated artifact is the authoritative source for the complete per-fold table; this document records the validated configuration and representative summary output visible from the workflow execution.
