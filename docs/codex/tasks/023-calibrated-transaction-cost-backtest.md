# Task 023 — Calibrated transaction-cost backtest integration

**Status:** COMPLETE

## Objective

Connect the validated venue transaction-cost calibration profile to the deterministic economic backtest through an explicit, opt-in configuration boundary.

## Scope

- construct a backtest cost configuration from a validated `VenueCostCalibration`;
- support median or P95 calibrated commission/slippage assumptions;
- preserve venue/source provenance at the configuration boundary;
- keep existing manual backtest configuration semantics unchanged;
- fail closed on invalid percentile selections;
- validate deterministic replay configuration using calibrated costs.

## Non-goals

- no automatic replacement of existing backtest assumptions;
- no live or broker cost discovery;
- no MT5/DOTO execution;
- no model tuning, threshold optimization or promotion;
- no profitability or production-readiness claim.

## Acceptance criteria

1. A validated venue calibration can produce a deterministic `BacktestConfig`. **PASS**
2. Median and P95 cost profiles map commission and slippage bps correctly. **PASS**
3. Venue/source provenance is retained by the calibrated configuration boundary. **PASS**
4. Invalid percentile selections fail closed. **PASS**
5. Existing explicit `commission_rate`/`slippage_bps` behavior remains unchanged. **PASS**
6. No broker, MT5/DOTO or financial transaction is accessed. **PASS**
7. Backend tests remain green. **PASS**
8. Compilation and security checks remain green. **PASS**
9. Validation and limitations are documented. **PASS**

## Implementation

`BacktestConfig.from_calibration(...)` was added as an explicit opt-in factory. It accepts a validated `VenueCostCalibration`, selects either the median or P95 commission/slippage profile, converts commission basis points to the existing decimal commission-rate representation, and retains venue/source provenance in the resulting immutable configuration.

Existing callers that construct `BacktestConfig` directly continue to use the original defaults and explicit commission/slippage parameters. The calibrated path does not automatically replace existing assumptions.

## Validation

- Phase 10 Live Gate Tests: run `36039678561` — **success**.
- Security and Dependency Scan: run `36039678583` — **success**.
- Security workflow completed dependency audit, static security scan, backend tests and backend compilation successfully.
- The Phase 10 gate completed successfully with the calibrated-cost changes present.
- Validation was performed without broker execution, MT5/DOTO submission or financial transaction.

## Limitations

The calibrated profile remains descriptive historical evidence supplied by the existing calibration framework. This task does not establish that median or P95 costs are representative of future execution conditions, does not automatically discover live venue costs, and does not make any profitability, robustness or production-readiness claim.

The selected percentile is an explicit caller decision. Existing manual backtest assumptions remain available and are not silently replaced.

## Safety boundary

This task only connects descriptive historical cost calibration to an offline deterministic replay configuration. It does not authorize execution, discover live costs, replace assumptions automatically, or establish profitability, robustness or production readiness.
