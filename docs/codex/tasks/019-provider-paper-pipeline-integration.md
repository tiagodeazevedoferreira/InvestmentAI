# Task 019 — Provider/Paper Pipeline Integration Contract

**Status:** IN PROGRESS

## Objective

Close the remaining integration-quality gap by validating the existing provider-backed PAPER scheduling path as one fail-closed contract, using deterministic provider mocks and disposable in-memory ledger state.

The task validates the existing architecture without changing trading policy, model parameters, backtest semantics, broker controls or financial execution behavior.

## Scope

Validate the path:

`provider mock → symbol normalization → historical data → OHLCV quality boundary → signal evaluation → PAPER scheduler → Paper Decision Ledger → Shadow Decision Ledger → optional DEMO promotion plan`

Explicitly cover:

- successful provider-to-scheduler flow without network access;
- empty provider data;
- invalid/missing OHLCV columns;
- invalid symbol input;
- HOLD decisions;
- duplicate decision/idempotency;
- risk-rejected decisions;
- DEMO bridge disabled by default;
- DEMO bridge requiring explicit symbol mapping;
- DEMO intent preparation without submission;
- provider failure converted to a scheduler error result;
- `execute=False` preserving zero paper account mutations;
- no broker submission path being reached.

## Non-goals

- No MT5/DOTO connection or execution.
- No `mt5.order_send()`.
- No broker transaction.
- No repeat of the existing EURUSD DEMO transaction.
- No changes to signal thresholds or risk parameters.
- No ML retraining, tuning or optimization.
- No changes to backtest semantics.
- No production deployment or production-readiness claim.

## Acceptance criteria

1. The focused Task 019 integration suite uses deterministic mocks only and requires no external network.
2. The provider boundary normalizes `PETR4` to `PETR4.SA` and preserves the requested period.
3. Empty or malformed OHLCV input fails closed before a paper decision is persisted.
4. A valid dry-run creates one completed Paper Decision Ledger record and one observational Shadow Decision Ledger record.
5. Repeating the same logical decision is idempotent across both ledgers.
6. HOLD and risk-rejected decisions cannot produce a DEMO `OrderIntent`.
7. DEMO promotion remains disabled unless explicitly enabled and mapped.
8. A ready DEMO plan stops at `OrderIntent`; no broker submission is reachable.
9. Provider failures are surfaced by `run_scheduler` as an `error` result.
10. The focused suite, complete backend suite, compilation and existing CI checks pass on the designated GitHub Actions runner.

## Validation record

To be completed after GitHub Actions validation.

- Focused test result: pending
- Complete backend suite: pending
- compileall: pending
- Runner: `ECTIN8F38594`
- Validation workflow/run: pending

## Safety boundary

This task is an integration-contract validation only. A passing result does not establish profitability, robustness, model superiority, production readiness, live-trading readiness or authorization to execute trades.
