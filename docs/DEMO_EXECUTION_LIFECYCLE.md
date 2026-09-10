# DEMO execution lifecycle

The controlled DEMO path is intentionally split into three layers:

1. `DemoOrderLedger` — durable operational record, independent from MT5.
2. `ControlledDemoExecutionService` — manual orchestration of one explicit order.
3. `AuthorizedDemoExecutor` — preflight, authorization, broker submission and post-reconciliation gates.

The scheduler is not connected to this path. There is no automatic retry.

## State machine

```text
INTENDED
   |
   v
AUTHORIZED
   |
   v
SUBMITTED
  /   \
 v     v
FILLED  unresolved -> recovery
         |
         +--> FILLED only after observed broker deal

Known broker rejection -> REJECTED
Known pre-submission failure -> FAILED
```

An uncertain broker response is never converted into `FAILED` merely because the
process raised an exception. The record remains recoverable so a later read-only
reconciliation can determine whether the broker accepted the order.
