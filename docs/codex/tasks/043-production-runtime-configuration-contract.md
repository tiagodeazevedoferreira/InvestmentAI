# Task 043 — Production runtime configuration contract

## Status
IN PROGRESS

## Objective
Define a provider-neutral runtime configuration contract for the production-oriented API container before selecting a hosting platform.

## Scope
- Document all deployment-relevant environment variables currently consumed by the API.
- Separate non-secret configuration from secret values that must be injected by the runtime.
- Provide a production environment template containing safe placeholders only.
- Document required safety posture for production configuration.
- Preserve the existing container image and execution boundaries.

## Acceptance criteria
1. Every deployment-relevant setting in `backend/app/settings.py` is accounted for.
2. No credential, token, private key or broker password is committed.
3. Production configuration explicitly keeps LIVE trading disabled unless a future, separate approval process changes it.
4. DEMO execution remains disabled by default and requires explicit account identity configuration.
5. CORS, API docs, logging and readiness-related settings are documented.
6. The contract remains independent of any cloud provider.
7. Existing CI, Security, External Intelligence, Cross-Asset ML, Phase 10 and Container Build gates remain green.

## Explicit non-goals
- Cloud/provider selection.
- Production hosting.
- TLS/domain provisioning.
- Secret-manager integration.
- LIVE trading enablement.
- DEMO broker execution.
- Database/persistent-volume provisioning.

## Validation record
Pending.
