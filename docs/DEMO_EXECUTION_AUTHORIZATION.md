# Authorized DEMO Execution

`AuthorizedDemoExecutor` is the execution boundary between an already-created `OrderIntent` and the DEMO broker adapter.

## Safety sequence

1. Verify the broker declares `environment=demo`.
2. Capture a fresh external broker snapshot.
3. Run `DemoAuthorizationGate` against the internal pre-execution state and external snapshot.
4. Submit the `OrderIntent` to the DEMO broker.
5. Capture a new external snapshot.
6. Reconcile it against the caller-provided internal post-execution state.
7. Return success only when the post-execution reconciliation is healthy.

Any failed precondition raises before submission. A failed post-execution reconciliation raises after the broker operation so the caller cannot treat an unverified state as successful.

## Deliberate boundaries

- The scheduler is not connected to this executor.
- No live broker is accepted.
- The executor does not bypass `MT5DemoBroker.order_check()` / `order_send()`.
- Internal ledger/account state remains the application source of truth; the broker snapshot is external evidence.
- Pending-order cancellation remains unsupported.

The MT5 adapter continues to use `order_check()` before `order_send()`. MQL5 documents that `TRADE_ACTION_DEAL` is a market-order operation and that a successful `order_check()` does not guarantee execution. The adapter therefore requires a post-operation external reconciliation before reporting an authorized execution as healthy.

## Next step

Validate the complete executor against a controlled fake gateway and then perform a read-only/manual Doto/MT5 DEMO validation before considering any scheduler integration.
