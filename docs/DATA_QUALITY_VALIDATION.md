# B3 market data quality validation

## Scope

The validation currently covers daily OHLCV history retrieved through the InvestmentAI OpenBB adapter using the `yfinance` provider for:

- PETR4.SA
- VALE3.SA
- ITUB4.SA

The validation window is 2021-01-01 through 2026-09-01.

## Hard quality gates

A dataset fails when any of the following occurs:

- no rows;
- missing required OHLCV columns;
- duplicate timestamps;
- null required values;
- non-finite required values;
- non-monotonic timestamps;
- invalid OHLC relationships (`high` below open/close/low, `low` above open/close/high, or non-positive OHLC);
- negative volume.

## Observability checks

Calendar gaps greater than four days are reported as suspicious but do not automatically fail the gate. B3 holidays and other legitimate exchange closures mean that a naive business-day expectation would create false positives. The maximum observed gap and count of large gaps are included in the JSON artifact.

## Interpretation

A green run means the retrieved dataset is structurally suitable for the next pipeline stage. It does **not** prove that the provider is tick-for-tick equivalent to an exchange-authoritative/licensed source, nor does it prove that historical data is adjusted in the exact way required by every strategy. Those questions remain part of provider calibration.
