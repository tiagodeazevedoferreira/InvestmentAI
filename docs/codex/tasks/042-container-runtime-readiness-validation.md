# Task 042 — Container runtime readiness validation contract

## Status
IN PROGRESS

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
Pending.
