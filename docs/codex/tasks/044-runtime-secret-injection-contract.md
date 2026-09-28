# Task 044 — Runtime secret injection contract

## Status
IN PROGRESS

## Objective
Define a provider-neutral contract for delivering secret values to the InvestmentAI runtime without committing them to source control, embedding them in the container image, exposing them through logs, or placing them in versioned configuration templates.

## Current secret-bearing settings

The application currently treats these settings as secret material:

- `FIREBASE_SERVICE_ACCOUNT` — Firebase service-account JSON used by the Firebase repository.
- `TRADINGVIEW_WEBHOOK_SECRET` — high-entropy token used to authenticate TradingView webhook requests.

DOTO/MT5 credentials are intentionally outside the application configuration contract. The authenticated Windows DOTO/MT5 terminal remains a separate execution boundary; no broker password is stored in `Settings`, the image, or the production environment template.

## Injection contract

Secrets must be supplied only at runtime by the hosting/orchestration environment or an external secret-management mechanism selected in a future deployment task.

Required properties:

1. Secret values must not be committed to Git.
2. Secret values must not be copied into the Docker image during build.
3. Secret values must not be supplied through Dockerfile `ARG` instructions.
4. Secret values must not be written to versioned `.env` files.
5. The production environment template contains variable names only, with blank secret values.
6. Runtime configuration may expose secret values to the process environment because the application reads them through Pydantic Settings.
7. Operators must not pass secrets as command-line arguments or include them in CI logs.
8. Runtime logs must not contain secret values. In particular, webhook access logs must use the route template rather than the token-bearing request path.

## Secret lifecycle

The intended deployment flow is:

`secret manager / protected runtime configuration -> process environment -> Settings -> service`

The repository deliberately does not choose AWS Secrets Manager, Azure Key Vault, Google Secret Manager, Kubernetes Secrets, or another provider in this task. Provider selection belongs to the production-hosting task.

## Container boundary

The production Docker image is built without secret values. The Docker build receives only application source and dependency metadata. Runtime secrets, when eventually required, must be injected when the container is started by the selected hosting platform.

The Linux container is not the DOTO/MT5 execution workstation.

## Logging boundary

The TradingView webhook endpoint contains its authentication token in the URL path because TradingView webhook delivery does not provide a custom authentication header in the current integration. Therefore access logging must never record the concrete request path for this route.

The API middleware now logs the FastAPI route template, for example:

`/api/integrations/tradingview/webhook/{webhook_token}`

instead of the supplied token value.

## Safe defaults

The production configuration remains:

- `TRADING_MODE=simulation`
- `LIVE_TRADING_ENABLED=false`
- `MODEL_APPROVED=false`
- `MT5_DEMO_EXECUTION_ENABLED=false`

Secret injection does not grant LIVE or DEMO execution authority.

## Validation

Automated regression tests verify:

- all runtime settings remain represented by the production template;
- secret-bearing template variables have no committed values;
- Dockerfile does not receive the current secrets through build arguments;
- `.env` files remain excluded from the Docker build context;
- API logging uses the route template for secret-bearing webhook paths.

## Explicit non-goals

- Cloud/provider selection.
- Production hosting.
- TLS/domain provisioning.
- LIVE trading enablement.
- DEMO broker execution.
- Broker password management.
- Persistent-volume provisioning.
