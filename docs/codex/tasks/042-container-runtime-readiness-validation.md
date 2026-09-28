# Task 042 — Container runtime readiness validation contract

## Status
COMPLETED — validated

## Objective
Extend the production container validation baseline so deployment automation verifies both liveness and the API operational-readiness contract without changing trading authority.

## Scope
- Keep the Docker health check mapped to `/api/health` as a lightweight liveness signal.
- Extend the container CI smoke test to validate `/api/ready` under the default safe `simulation` configuration.
- Validate that the readiness contract fails closed when the container is started with an unsafe LIVE configuration.
- Keep the validation deployment-neutral: no broker credentials, broker submission, LIVE execution, model promotion, or cloud-provider deployment.
- Document the distinction between container liveness and application readiness.

## Acceptance criteria
1. The production image still builds successfully.
2. A default container reports HTTP 200 from both `/api/health` and `/api/ready`.
3. A container started with LIVE mode but without the existing LIVE safety prerequisites reports HTTP 503 from `/api/ready`.
4. The readiness response identifies the unsafe configuration without exposing secrets.
5. No execution endpoint or broker call is introduced.
6. Existing CI, Security, External Intelligence, Cross-Asset ML, Phase 10 and Container Build gates remain green.

## Explicit non-goals
- Production hosting or cloud deployment.
- TLS/domain configuration.
- Runtime secret-management implementation.
- Changing Docker HEALTHCHECK from liveness to readiness.
- Enabling LIVE trading.
- Creating another DEMO broker transaction.

## Validation record

Validated on commit `2a5346c89aa99cdfff0f49eeb7bd2abff538b88a`.

- Container Build: `36426269273` — success
- CI: `36426269293` — success
- Security and Dependency Scan: `36426269385` — success
- External Intelligence Validation: `36426269281` — success
- Cross-Asset ML Experiment: `36426269365` — success
- Phase 10 Live Gate Tests: `36426269224` — success

The Container Build now validates safe liveness/readiness and an intentionally unsafe LIVE configuration that must return HTTP 503 from `/api/ready`. The Docker HEALTHCHECK remains on `/api/health` because health is the liveness signal; readiness is validated separately by deployment automation.

No broker credentials, broker calls, LIVE execution, model promotion or DEMO transaction were introduced.
