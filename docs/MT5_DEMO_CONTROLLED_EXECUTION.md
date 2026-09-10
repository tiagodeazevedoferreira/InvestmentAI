# Controlled MT5 DEMO execution

This document defines the final operational gate for the first controlled DEMO order.

## Required sequence

1. Confirm the intended DOTO/MT5 account is connected.
2. Confirm exact login and server identity from the connected account.
3. Capture a fresh broker reconciliation snapshot.
4. Create a durable DEMO order intent in the independent ledger.
5. Validate the order with the broker-independent DEMO preflight.
6. Require `DemoAuthorizationGate` approval.
7. Persist `AUTHORIZED` before the broker submission boundary.
8. Keep the order volume at or below the controlled limit of `0.01`.
9. Run MT5 `order_check()`.
10. Only after all previous gates pass, submit the single market order.
11. Persist `SUBMITTED` with broker order/deal identifiers when available.
12. Capture a fresh post-execution snapshot.
13. Reconcile internal state against the broker state.
14. Persist the final outcome when it is unambiguous.

## Lifecycle and recovery

The independent SQLite DEMO ledger uses the states:

`INTENDED -> AUTHORIZED -> SUBMITTED -> FILLED`

with `REJECTED` and `FAILED` terminal outcomes where the broker outcome is known.

An uncertain outcome is deliberately left recoverable. The recovery component never
submits a new order. It marks a `SUBMITTED` record as `FILLED` only when the broker
snapshot contains the recorded deal identifier; otherwise it leaves the record
`SUBMITTED` for investigation. This prevents a timeout or process crash from causing
a duplicate automatic order.

## Safety boundaries

- The preflight layer never calls MT5 execution APIs.
- `MetaTrader5DemoBroker` keeps execution disabled by default.
- `order_check()` is mandatory before `order_send()`.
- Live trading remains disabled.
- `DOTOGlobal-Real` is the server name currently associated with the account being treated as the controlled DEMO account; the server name alone is not evidence of live/demo status.
- Account identity must always be established from the connected login and server pair expected by configuration.
- No password is stored by InvestmentAI.
- The controlled execution service is not connected to the scheduler.
- No automatic retry is permitted for an uncertain submitted order.

## First-order policy

The first controlled order must be a single market order with volume `0.01`. No pending orders are allowed by the current adapter. The scheduler must not be involved in the first validation.

The first-order validation is intentionally manual and one-shot. A successful preflight,
authorization, or ledger transition does not itself submit an order; MT5 execution remains
behind the explicit execution-enable flag and the broker's `order_check()` gate.
