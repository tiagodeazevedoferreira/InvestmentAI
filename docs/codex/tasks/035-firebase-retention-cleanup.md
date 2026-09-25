# Task 035 — Firebase automated retention cleanup

## Objective

Introduce a fail-closed retention mechanism for Firebase ledgers so historical observational records can be removed after an explicit retention period without affecting current paper-account state or trading behavior.

## Scope

- Add an explicit Firebase delete primitive.
- Define retention policies per authorized Firebase child collection.
- Select records using an explicit timestamp field and UTC cutoff.
- Default to dry-run behavior.
- Require explicit non-dry-run execution for deletion.
- Enforce a maximum deletion batch size.
- Skip malformed timestamps or records without an immutable supported key.
- Keep `paper/account` outside the cleanup policy.
- Publish a machine-readable cleanup report.

## Initial policy

The initial engineering defaults are:

- `paper/decision_ledger`: 180 days
- `paper/shadow_decision_ledger`: 180 days
- maximum deletions per run: 100
- dry-run: enabled

These are storage-governance defaults, not claims about an optimal business or legal retention period. They must be reviewed before production scheduling.

## Safety boundaries

The cleanup mechanism:

- cannot delete records with invalid timestamps;
- cannot delete records without a recognized immutable key (`signal_id` or `shadow_id`);
- cannot operate when Firebase is unavailable;
- does not delete `paper/account`;
- does not submit orders or alter execution/risk policy;
- does not automatically infer a retention period from payload size;
- does not bypass the Firebase Admin SDK boundary.

## Validation

1. Unit tests cover cutoff selection, malformed timestamps, dry-run, explicit deletion and batch limits.
2. CI/security/Phase 10/External Intelligence/Cross-Asset workflows must remain green.
3. The retention workflow is initially manual and dry-run only.
4. No production deletion is authorized by this task.

## Follow-up

After observing actual Firebase growth and obtaining an explicit governance decision on retention periods, a scheduled non-dry-run cleanup may be considered separately.
