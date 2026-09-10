# Controlled DEMO runbook

This runbook describes the first manual DEMO validation. It does not authorize an order by itself.

## Before execution

- Confirm MT5 desktop is connected to the intended DOTO account.
- Confirm the expected login and exact server match configuration.
- Confirm the preflight script succeeds.
- Confirm live trading remains disabled.
- Confirm DEMO execution is explicitly enabled only for the controlled validation window.
- Confirm the intended order is a single market order of `0.01` volume.

## During execution

The only supported path is:

`preflight -> fresh reconciliation -> authorization -> order_check -> order_send -> post-reconciliation -> ledger`

The scheduler must not invoke this path during the first validation.

## After execution

Record the broker order/deal identifiers. If the result is ambiguous, do not retry. Leave the ledger record in `SUBMITTED` and use the read-only recovery component to reconcile the broker history.

A successful first DEMO order does not enable live trading and does not authorize scheduler integration. Those are separate gates.
