# Task 020 — Security and dependency scan

Status: IN PROGRESS

## Objective

Establish a repeatable CI security baseline for the Python backend before any production-deployment work.

## Scope

- audit the declared backend dependencies from `backend/requirements.txt` with `pip-audit`;
- scan first-party backend Python code with Bandit;
- run both checks on the existing self-hosted Windows CI environment;
- record findings without changing application behavior unless a demonstrated vulnerability requires remediation.

## Non-goals

- no broker connectivity or financial execution;
- no MT5/DOTO transactions;
- no model tuning or promotion;
- no production deployment;
- no automatic dependency upgrades;
- no claim that a clean static/dependency scan proves complete application security.

## Acceptance criteria

1. CI installs the declared backend dependencies from `backend/requirements.txt`.
2. `pip-audit` completes against the declared dependency set and reports no unresolved known vulnerabilities, or each finding is explicitly documented with disposition.
3. Bandit scans `backend/app` and reports no unresolved high-severity/high-confidence findings, or each finding is explicitly documented with disposition.
4. The security workflow does not initialize MT5 or submit broker orders.
5. Existing application tests remain green.
6. Backend compilation remains green.
7. Findings and limitations are recorded in a validation document.
8. The task does not modify execution gates, DEMO/LIVE authorization, scheduler behavior, model policy or trading logic.

## Validation record

Pending CI validation.

Runner: ECTIN8F38594

## Safety boundary

Passing this task establishes only a repeatable dependency/static-analysis baseline. It does not establish production security, penetration-test coverage, profitability, robustness, model superiority, live readiness or permission to execute trades.
