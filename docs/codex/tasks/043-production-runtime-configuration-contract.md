# Task 043 — Production runtime configuration contract

## Status
COMPLETED — validated

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

Validated on commit `9bf2fa27645ad1d7ccf0a14687414be7de739f06`.

- CI: `36430394082` — success
- Security and Dependency Scan: `36430393911` — success
- External Intelligence Validation: `36430394353` — success
- Cross-Asset ML Experiment: `36430394262` — success
- Phase 10 Live Gate Tests: `36430394033` — success
- Container Build: `36430394126` — success

The first CI attempt on commit `2432abe720802cfb2a24eb6cea76a0c9dcbc109c` failed only because the new test rejected the word "password" inside a documentation comment; the implementation and all other tests passed. The test was corrected to inspect configuration assignments instead of prose, and the final validation above is green.

No real secret, credential, broker password, LIVE authorization or DEMO transaction was introduced.
