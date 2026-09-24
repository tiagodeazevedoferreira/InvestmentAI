# Task 025 — Persisted paper outcome calibration pipeline

**Status:** IN PROGRESS

## Objective

Connect the existing Firebase paper decision ledger and provider-independent outcome attribution to the historical calibration layer, producing a deterministic research-only report from persisted paper decisions and historical OHLCV data.

## Scope

- preserve the decision reference price in the Firebase ledger;
- retrieve persisted paper decisions without changing execution state;
- attribute completed forward outcomes at configured horizons;
- persist attributed outcomes idempotently to the originating ledger record;
- aggregate completed observations with the existing descriptive calibration service;
- distinguish incomplete horizons from completed outcomes;
- preserve symbol, decision timestamp, action and signal provenance;
- fail closed on malformed decisions or invalid market data;
- remain PAPER/research-only with no execution or promotion authority.

## Non-goals

- no broker, MT5 or DOTO calls;
- no model or provider ranking;
- no weight, threshold or risk-gate changes;
- no automatic model promotion;
- no live-cost discovery;
- no claim of profitability or production readiness.

## Acceptance criteria

1. Ledger records retain the decision reference price required for causal outcome attribution. **PENDING**
2. Historical calibration reads persisted decisions and attributes only completed horizons. **PENDING**
3. Outcomes are persisted idempotently without creating duplicate decision records. **PENDING**
4. Calibration uses the existing descriptive report and preserves action/horizon provenance. **PENDING**
5. Missing future bars remain incomplete rather than being counted as failures. **PENDING**
6. Invalid records/data fail closed. **PENDING**
7. No execution authority, policy mutation or model promotion is introduced. **PENDING**
8. Backend tests are green. **PENDING**
9. Compilation and security checks are green. **PENDING**

## Interpretation boundary

The resulting statistics are historical observational evidence. They remain subject to sample-size, selection bias, market-regime and timestamp-alignment limitations. They do not establish tradability or authorize promotion.

## Safety boundary

The pipeline is read/measurement oriented except for writing attributed outcome metadata to the existing PAPER decision ledger. It cannot submit orders, enable a broker or bypass risk controls.
