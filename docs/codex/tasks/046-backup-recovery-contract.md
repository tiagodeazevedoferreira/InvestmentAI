# Task 046 — Backup and recovery contract

## Status
COMPLETED — validated

## Objective

Define a provider-neutral backup, restore and recovery-validation contract for the durable state identified by Task 045.

The objective is to prevent a production restart, storage incident or deployment replacement from becoming an unrecoverable loss of operational state.

## Recovery domains

### 1. PAPER / Firebase

Authoritative PAPER state includes:

- paper account state at `PAPER_ACCOUNT_PATH`;
- `paper/decision_ledger`;
- `paper/shadow_decision_ledger`;
- persisted outcome/calibration state covered by the existing Firebase services.

Recovery requirements:

1. Backups must preserve the logical Firebase paths and their child keys.
2. Restore must not silently overwrite newer state without an explicit operator procedure.
3. After restore, PAPER idempotency must be validated before scheduler execution is resumed.
4. Firebase retention cleanup must not be treated as a backup mechanism.
5. A backup must be independent from the application container lifecycle.

### 2. DEMO / Windows workstation

The DEMO order ledger is a local SQLite database on the controlled Windows DOTO/MT5 workstation.

Recovery requirements:

1. The SQLite database must reside on durable workstation storage.
2. Backups must preserve the SQLite file and its schema.
3. Recovery must be performed before enabling any controlled DEMO execution.
4. The recovered ledger must be inspected for pending `SUBMITTED` records.
5. Pending DEMO records must never trigger automatic broker resubmission.
6. A recovered ledger must be reconciled read-only against broker evidence before execution is considered safe.

No new DEMO transaction is required by this task.

### 3. Model artifacts

Approved model artifacts under `XGBOOST_MODEL_DIR` must be recoverable independently of the container image.

Recovery requirements:

1. Model artifacts must be versioned or content-addressed.
2. A restored artifact must retain its metadata/provenance.
3. The deployed runtime must identify the exact artifact version it loaded.
4. Missing or unverifiable artifacts must fail model-dependent readiness/inference.
5. Backup/restore must not silently substitute a different model.

## Recovery sequence

A future production incident should follow this logical sequence:

1. Stop or isolate state-mutating workloads.
2. Establish the incident timestamp and affected state domain.
3. Restore the selected durable state from an approved recovery point.
4. Validate structural integrity.
5. Validate application-level invariants and idempotency.
6. Validate model artifact identity where applicable.
7. Run read-only reconciliation.
8. Re-enable PAPER scheduling only after state validation succeeds.
9. Keep DEMO execution disabled until its separate reconciliation gate succeeds.
10. Record the recovery event and evidence.

## Recovery point objectives

This task does not prescribe numeric RPO/RTO targets. Those values depend on the production hosting and operational service level selected later.

The deployment design must explicitly define:

- maximum acceptable PAPER data loss;
- maximum acceptable recovery duration;
- model artifact recovery point;
- DEMO workstation ledger recovery expectations;
- operational log retention.

## Backup validation

Backups are not considered usable merely because they exist.

A production implementation must periodically demonstrate:

- successful backup creation;
- successful restore into an isolated environment;
- Firebase logical-state verification;
- PAPER idempotency verification;
- SQLite integrity verification for the DEMO ledger;
- model artifact checksum/provenance verification;
- documented recovery evidence.

## Security requirements

Backups must:

- inherit appropriate access controls;
- encrypt sensitive data at rest and in transit where supported;
- never expose Firebase service-account material or webhook secrets as application data;
- have retention rules independent from application data retention;
- support auditable access where the selected provider permits it.

## Explicit non-goals

- Cloud-provider selection.
- Backup product selection.
- Automated backup jobs.
- Automated restore.
- Production hosting.
- TLS/domain provisioning.
- LIVE execution.
- New DEMO broker transactions.
