# Task 037 — Interrupted DEMO submission recovery correlation

## Status

IMPLEMENTED — deterministic fault-injected validation added. Real interrupted-broker validation remains pending because it would require deliberately creating another DEMO transaction.

## Objective

Close the recovery gap where MT5 may accept an order but the application loses the broker response before receiving the order/deal identifiers.

The recovery boundary must preserve uncertainty as SUBMITTED, avoid automatic retry, and later identify the exact broker execution through a durable correlation identifier.

## Scope

- Persist a bounded DEMO correlation identifier alongside the durable intent.
- Propagate the identifier through OrderIntent.
- Send the identifier to MT5 through the order comment field.
- Normalize broker history comments back into correlation evidence.
- Recover a SUBMITTED record using correlation + symbol + side + quantity when the original deal ID was not returned to the application.
- Preserve fail-closed behavior when evidence is missing or mismatched.
- Prove that recovery does not resubmit the order.

## Safety boundary

No additional DEMO transaction is created for this task. Validation uses a deterministic fault-injected executor that simulates an accepted broker submission followed by loss of the response.

Real broker-connected validation of an actually interrupted order_send() remains a separate operational validation item because reproducing that condition against the DEMO account would require deliberately creating another transaction.

## Implementation

### Durable ledger

DemoOrderLedger now persists correlation_id with SQLite migration support for existing databases.

Recovery accepts either:

1. an already-known exact deal_id, or
2. an exact correlation_id match combined with symbol, side and quantity validation.

The second path is intentionally fail-closed: correlation alone is not sufficient.

### Controlled execution

ControlledDemoExecutionService creates a bounded correlation identifier before broker submission and persists it with the intent.

If the executor raises after local authorization, the durable state remains SUBMITTED; the service never retries the broker submission.

### MT5 adapter

The MT5 request comment uses the compact form IAI:<correlation_id>, bounded to the platform comment field. Broker deal normalization exposes the correlation identifier from the persisted comment.

If no correlation identifier exists, the adapter preserves the legacy InvestmentAI-DEMO comment.

## Validation

Added backend/tests/test_demo_failure_recovery.py covering:

- exception after authorization leaves the intent SUBMITTED;
- correlation identifier is durable;
- recovery promotes the exact matching broker evidence to FILLED;
- recovery does not increase broker submission calls;
- matching correlation with wrong side is rejected and remains SUBMITTED;
- MT5 correlation comment round-trips within the bounded length;
- legacy comment behavior remains unchanged.

## Explicit limitation

This task does not claim that an actual interrupted MT5 order_send() has been reproduced against the DEMO account. That validation remains pending and must not be performed by creating an unnecessary additional transaction.
