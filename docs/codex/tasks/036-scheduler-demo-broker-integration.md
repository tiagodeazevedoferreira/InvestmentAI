# Task 036 — Scheduler-to-DEMO broker integration

**Status:** IN PROGRESS

## Objective

Connect the existing PAPER scheduler to the controlled DEMO execution boundary without bypassing authorization, reconciliation, durable DEMO lifecycle state or the fail-closed promotion boundary.

## Scope

- preserve the existing scheduler-to-DEMO `DemoPromotionPlan`;
- allow an explicit `SchedulerDemoExecutionAdapter` to be supplied to the scheduler;
- require explicit independent `demo_execution_authorized=True` before broker execution;
- require application-owned DEMO state before and after execution;
- keep the controlled DEMO service responsible for preflight, authorization, reconciliation and durable lifecycle;
- return structured scheduler status for successful or blocked DEMO execution;
- keep normal scheduler behavior unchanged when no DEMO execution adapter is supplied.

## Safety boundary

- DEMO execution remains disabled unless explicitly enabled by the caller;
- no live broker is accepted by the DEMO execution layer;
- no automatic retry is introduced;
- ambiguous broker submission remains recoverable as `SUBMITTED`;
- the scheduler does not call `order_send` directly;
- no change is made to model selection, risk thresholds or live-trading authorization.

## Non-goals

- no live broker integration;
- no automatic scheduler-triggered DEMO execution;
- no automatic retry/recovery submission;
- no deliberate new financial transaction for validation.

## Acceptance criteria

1. Existing PAPER scheduler behavior remains unchanged without a DEMO adapter.
2. A ready DEMO plan is not executed without explicit independent authorization.
3. An authorized scheduler DEMO plan delegates only to the controlled DEMO execution boundary.
4. Missing application-owned post-execution state blocks execution safely.
5. Unit/integration tests cover both blocked and explicitly authorized paths.
6. CI, security, Phase 10, External Intelligence and Cross-Asset validation remain green.

## Validation

Pending validation after implementation commit.
