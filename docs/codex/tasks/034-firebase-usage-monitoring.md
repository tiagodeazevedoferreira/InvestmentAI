# Task 034 — Firebase usage monitoring

## Objective
Add a deterministic operational usage monitor for the Firebase Realtime Database so monitored application paths expose approximate serialized size, record count and threshold status without changing trading behavior.

## Scope
- Monitor current bounded Firebase application paths.
- Report serialized UTF-8 payload size and record count per path.
- Aggregate status using explicit warning and critical thresholds.
- Publish a JSON artifact from GitHub Actions and expose the result in the workflow summary.
- Fail the monitoring job only at the critical threshold.
- Keep credentials server-side through the Firebase Admin SDK boundary.

## Monitored paths
- `paper/account`
- `paper/decision_ledger`
- `paper/shadow_decision_ledger`
- `system/diagnostics/github_actions`

The monitor is path-scoped rather than reading the Firebase root, reducing unnecessary data transfer and avoiding a false impression of exact Firebase billing/storage usage.

## Thresholds
Defaults are 500,000 bytes for warning and 900,000 bytes for critical. They are operational guardrails, not Firebase billing limits. They can be overridden through GitHub Actions variables.

## Validation
- Unit tests cover sizing, record counting, warning/critical classification and fail-closed configuration.
- CI and Security must pass.
- The scheduled workflow must authenticate against the configured Firebase environment and publish `firebase-usage-report.json`.

## Non-goals
- No automatic deletion.
- No changes to paper, DEMO or LIVE execution.
- No client-side Firebase access.
- No claim that serialized payload size equals Firebase billing/storage usage.

## Follow-up
Use measured path growth to define retention policies before implementing automated cleanup.
