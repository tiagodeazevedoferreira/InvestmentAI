# Task 020 — Security and dependency scan

**Status:** COMPLETE

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

1. CI installs the declared backend dependencies from `backend/requirements.txt`. **PASS**
2. `pip-audit` completes against the declared dependency set and reports no unresolved known vulnerabilities, or each finding is explicitly documented with disposition. **PASS**
3. Bandit scans `backend/app` and reports no unresolved high-severity/high-confidence findings, or each finding is explicitly documented with disposition. **PASS**
4. The security workflow does not initialize MT5 or submit broker orders. **PASS**
5. Existing application tests remain green. **PASS**
6. Backend compilation remains green. **PASS**
7. Findings and limitations are recorded in a validation document. **PASS**
8. The task does not modify execution gates, DEMO/LIVE authorization, scheduler behavior, model policy or trading logic. **PASS**

## Remediation

The initial dependency audit identified a known vulnerability in `pytest 8.4.2` (PYSEC-2026-1845), fixed by updating the declared constraint to `pytest>=9.0.3,<10`. The application runtime dependencies and trading behavior were not changed by this remediation.

The self-hosted runner environment did not have Python 3.11 available and the GitHub `setup-python` action could not complete under the machine's PowerShell execution-policy constraints. The workflow was therefore changed to use the existing user-installed Python 3.12 interpreter explicitly.

The backend test step also required the repository root on `PYTHONPATH` because an existing test imports the top-level `scripts` package while the workflow working directory is `backend`.

## Validation

Validated on `main` commit `5d20758c805e265242993c158e23085c3a413752`.

- Security and Dependency Scan workflow: **35924094928 — success**.
- CI workflow: **35924094964 — success**.
- Self-hosted runner: `ECTIN8F38594`.
- Dependency audit: **PASS**.
- Bandit static scan: **PASS**.
- Backend tests: **PASS**.
- Backend compilation: **PASS**.

The clean scan is a repeatable baseline, not proof of complete application security or penetration-test coverage.

## Safety boundary

Passing this task establishes only a repeatable dependency/static-analysis baseline. It does not establish production security, penetration-test coverage, profitability, robustness, model superiority, live readiness or permission to execute trades.
