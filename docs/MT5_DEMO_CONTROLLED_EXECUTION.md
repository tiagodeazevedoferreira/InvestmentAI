# Controlled MT5 DEMO execution

This document defines the final operational gate for the first controlled DEMO order.

## Required sequence

1. Confirm the intended DOTO/MT5 account is connected.
2. Confirm exact login and server identity.
3. Capture a fresh broker reconciliation snapshot.
4. Validate the order with the broker-independent DEMO preflight.
5. Require `DemoAuthorizationGate` approval.
6. Keep the order volume at or below the controlled limit of `0.01`.
7. Run MT5 `order_check()`.
8. Only after all previous gates pass, submit the market order.
9. Capture a fresh post-execution snapshot.
10. Reconcile internal state against the broker state.
11. Record execution identifiers and outcome in the audit trail.

## Safety boundaries

- The preflight layer never calls MT5 execution APIs.
- `MetaTrader5DemoBroker` keeps execution disabled by default.
- `order_check()` is mandatory before `order_send()`.
- Live trading remains disabled.
- The current real-account server name must not be used as evidence that a separate DEMO account exists; account identity must be established from the connected account itself.
- No password is stored by InvestmentAI.

## First-order policy

The first controlled order must be a single market order with volume `0.01`. No pending orders are allowed by the current adapter. The scheduler must not be involved in the first validation.
