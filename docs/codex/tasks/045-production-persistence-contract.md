# Task 045 — Production persistence contract

## Status
IN PROGRESS

## Objective

Define the provider-neutral persistence boundary for production deployment so container replacement, restart or rescheduling cannot silently destroy state that the application treats as durable.

This task does not select a cloud provider, persistent-volume implementation or database service.

## State classification

| State | Current location | Durability requirement | Production boundary |
|---|---|---|---|
| PAPER account | Firebase Realtime Database at `PAPER_ACCOUNT_PATH` | Durable | External authoritative state |
| PAPER decision ledger | Firebase Realtime Database at `paper/decision_ledger` | Durable | External authoritative state |
| PAPER shadow decision ledger | Firebase Realtime Database at `paper/shadow_decision_ledger` | Durable | External authoritative state |
| PAPER outcomes/calibration | Firebase-backed ledgers/artifacts according to the existing services | Durable where persisted | External state/artifact storage |
| DEMO order ledger | Local SQLite on the authenticated Windows DOTO/MT5 workstation | Durable for the DEMO boundary | Windows workstation storage; not the Linux container |
| XGBoost model artifacts | `models/xgboost` | Durable versioned artifacts required by inference | External artifact storage or a deployment volume in a future hosting design |
| Application source/dependencies | Docker image | Immutable per image | Container image |
| Logs | Container/runtime logging system | Operational retention | External runtime logging in production |
| Temporary files/cache | Container filesystem | Ephemeral | May be discarded on restart |

## Production invariants

1. A container restart must not reset the authoritative PAPER account.
2. A container restart must not reset the PAPER idempotency ledger.
3. A container restart must not delete required model artifacts used by the deployed application.
4. The Linux container must not become the persistence boundary for DOTO/MT5 DEMO execution state.
5. DEMO SQLite state must remain on the controlled Windows execution workstation unless a future architecture explicitly migrates that responsibility.
6. No credential or secret is persisted as application state.
7. Persistence failures must fail closed rather than silently creating a fresh authoritative account or ledger.
8. Storage limits must remain bounded by the existing Firebase write-size and retention controls.

## PAPER behavior

The existing `PaperAccountStore` loads the account from Firebase when configured and persists bounded recent order/execution history back to the configured Firebase path.

The existing paper decision ledger requires Firebase and therefore does not silently fall back to local ephemeral storage. This behavior is required for deterministic idempotency across process/container restarts.

Production deployment must provide Firebase connectivity whenever PAPER scheduling or persistent PAPER state is enabled.

## DEMO behavior

The DEMO ledger is implemented with SQLite because the controlled DOTO/MT5 execution boundary is a Windows desktop terminal. The ledger path must be backed by durable local storage on that workstation.

The Linux production API container must not mount or manipulate the DEMO SQLite database. DEMO execution remains a separate controlled boundary and is disabled by default.

## Model artifacts

`XGBOOST_MODEL_DIR` identifies the runtime model artifact directory. A production deployment must make approved model artifacts available independently of the container's writable ephemeral filesystem.

The current task does not define a model registry or artifact provider.

## Backup and recovery

A production deployment design must define:

- backup/restore for Firebase data required by PAPER operation;
- retention and recovery procedures for the controlled DEMO workstation ledger;
- immutable/versioned storage for deployed model artifacts;
- operational log retention;
- recovery validation after restoring each durable state class.

These are deployment/operations concerns and are not implemented by this task.

## Failure behavior

The application must not interpret an unavailable durable store as an empty authoritative state.

Examples:

- Firebase unavailable when a persistent PAPER operation requires it: fail the operation.
- Existing PAPER ledger unavailable: do not claim the decision is new.
- Required model artifact unavailable: fail model-dependent readiness/inference rather than silently using an unapproved fallback.
- DEMO ledger unavailable: the controlled DEMO execution boundary must not proceed.

## Explicit non-goals

- Cloud-provider selection.
- Persistent-volume provisioning.
- Database migration.
- Backup automation.
- Production hosting.
- TLS/domain provisioning.
- LIVE execution.
- New DEMO broker transactions.
