# Task 033 — Firebase data governance hardening

## Objective

Harden the Firebase Realtime Database boundary so that production access is denied by default and application-server access remains mediated by the Firebase Admin SDK.

## Scope

- Enforce default-deny Realtime Database rules.
- Remove unauthenticated public read paths that are not currently required by the frontend.
- Add a regression test for the rule posture.
- Preserve the existing Firebase Admin SDK repository boundary.
- Keep the Firebase smoke test available for configured environments.

## Security posture

The current frontend does not access Firebase directly; it calls the backend API. Therefore the Realtime Database does not require anonymous client reads for the current application surface.

The backend uses the Firebase Admin SDK through FirebaseRepository. Admin SDK operations are server-side and are not governed by Realtime Database client security rules in the same way as unauthenticated client access.

## Validation

- Static regression test verifies .read=false and .write=false.
- CI and Security workflows must pass.
- Firebase connectivity remains a separate environment-dependent smoke test and requires the repository's configured Firebase service-account secret and database URL variable.

## Non-goals

- No production Firebase credentials are added to the repository.
- No live trading or execution behavior is changed.
- No data-retention deletion is introduced in this task.
- No unauthenticated Firebase client access is enabled.

## Follow-up

After a configured Firebase environment is available, execute the smoke test and then define retention/monitoring controls based on actual stored paths and data volumes.
