# Paper Outcome Persistence

## Purpose

The paper scheduler creates deterministic decision records. Once additional market bars become available, the project must attach the realized forward outcomes to those decisions without changing the trading policy or requiring a broker.

## Storage contract

Outcome observations are persisted inside the corresponding Firebase decision-ledger record under `outcomes`.

Each horizon contains:

- `horizon_bars`
- `outcome_timestamp`
- `outcome_price`
- `forward_return`
- `signed_return`
- `hit`

The ledger keeps at most a bounded recent set when historical records are read for attribution. The default bound is 200 decision records per symbol per attribution run.

## Attribution lifecycle

1. GitHub Actions runs the existing paper scheduler after the B3 daily session.
2. The scheduler writes an idempotent decision record.
3. The outcome runner reads a bounded recent ledger window.
4. For each completed decision, the runner resolves the decision-bar close and applies the 1/5/20-bar attribution contract.
5. Completed horizons are persisted; incomplete horizons remain explicitly pending.
6. A later scheduled run can fill newly completed horizons without duplicating already persisted results.

## Historical compatibility

Older ledger records may not contain an explicit `price`. The runner resolves the close at the recorded decision timestamp from the same provider history before attribution. New integrations should persist the reference price directly when available.

## Safety boundary

Outcome persistence is observational. It does not:

- create or modify orders;
- bypass risk gates;
- authorize a broker;
- enable live trading;
- promote a model.

The resulting statistics remain descriptive until the project completes calibration, transaction-cost analysis, regime analysis and out-of-sample validation.

## Next step

Build a historical calibration report for PETR4, VALE3 and ITUB4 from persisted outcomes, including sample coverage, hit rate, signed-return distribution, confidence intervals and horizon-specific comparisons. The report must remain research-only until the empirical promotion gate is satisfied.
