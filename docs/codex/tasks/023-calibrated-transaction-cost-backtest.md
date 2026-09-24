# Task 023 — Calibrated transaction-cost backtest integration

**Status:** IN PROGRESS

## Objective

Connect the validated venue transaction-cost calibration profile to the deterministic economic backtest through an explicit, opt-in configuration boundary.

## Scope

- construct a backtest cost configuration from a validated `VenueCostCalibration`;
- support median or P95 calibrated commission/slippage assumptions;
- preserve venue/source provenance at the configuration boundary;
- keep existing manual backtest configuration semantics unchanged;
- fail closed on invalid percentile selections;
- validate deterministic replay using calibrated costs.

## Non-goals

- no automatic replacement of existing backtest assumptions;
- no live or broker cost discovery;
- no MT5/DOTO execution;
- no model tuning, threshold optimization or promotion;
- no profitability or production-readiness claim.

## Acceptance criteria

1. A validated venue calibration can produce a deterministic `BacktestConfig`. **PENDING**
2. Median and P95 cost profiles map commission and slippage bps correctly. **PENDING**
3. Venue/source provenance is retained by the calibrated configuration boundary. **PENDING**
4. Invalid percentile selections fail closed. **PENDING**
5. Existing explicit `commission_rate`/`slippage_bps` behavior remains unchanged. **PENDING**
6. No broker, MT5/DOTO or financial transaction is accessed. **PENDING**
7. Backend tests remain green. **PENDING**
8. Compilation and security checks remain green. **PENDING**
9. Validation and limitations are documented. **PENDING**

## Safety boundary

This task only connects descriptive historical cost calibration to an offline deterministic replay configuration. It does not authorize execution, discover live costs, replace assumptions automatically, or establish profitability, robustness or production readiness.
