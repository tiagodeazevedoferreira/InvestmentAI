# Task 047 — Production hosting and deployment contract

## Status

COMPLETED — validated

## Objective

Define the provider-neutral production hosting and deployment boundary for the InvestmentAI API without selecting or provisioning a cloud provider.

The contract connects the existing container, runtime configuration, persistence and backup/recovery contracts into an explicit deployment topology.

## Target topology

### Linux production runtime

The production Linux container hosts:

- FastAPI API;
- provider-backed research/data services;
- PAPER services and scheduler;
- readiness/liveness endpoints;
- operational request logging.

The container is stateless with respect to durable operational state. Firebase remains the authoritative external store for PAPER account and decision state. Model artifacts must be supplied through durable deployment storage or an equivalent immutable artifact mechanism.

### Windows DOTO/MT5 execution boundary

The authenticated Windows workstation remains a separate execution boundary for DOTO/MT5 DEMO operations.

The Linux production container must not:

- install or require the MT5 desktop terminal;
- access the Windows terminal executable;
- own the DEMO SQLite ledger;
- submit broker orders;
- become a network route that bypasses the controlled DEMO authorization boundary.

The existing controlled DEMO runner and broker adapter remain responsible for DEMO execution.

## Network and ingress contract

A future production deployment must provide:

1. TLS termination before public API exposure;
2. a stable HTTPS origin;
3. an ingress/reverse-proxy boundary that forwards only required API traffic;
4. restricted administrative access to infrastructure and deployment controls;
5. network egress limited according to the selected provider's capabilities and application requirements;
6. no public exposure of Firebase service-account material, database administration interfaces, or the Windows DOTO/MT5 workstation.

The exact cloud, ingress product, DNS provider and firewall implementation are intentionally deferred.

## Runtime contract

Production deployment must consume the existing runtime configuration contract from Task 043 and secret-injection requirements from Task 044.

The safe baseline remains:

- `TRADING_MODE=simulation`;
- `LIVE_TRADING_ENABLED=false`;
- `MODEL_APPROVED=false`;
- `MT5_DEMO_EXECUTION_ENABLED=false`;
- `API_DOCS_ENABLED=false`;
- `LOG_LEVEL=INFO`.

Secrets must be injected by the hosting platform's secret mechanism and must not be baked into images, Docker build arguments, source control or frontend bundles.

## Readiness and health contract

The deployment platform must distinguish:

- liveness: `GET /api/health`;
- readiness: `GET /api/ready`.

The existing Docker health check remains on liveness. Deployment routing should use readiness so an unsafe or incompletely configured runtime is not considered eligible for normal traffic.

A deployment must not interpret HTTP liveness as proof that durable state, model artifacts, external providers or execution controls are operational.

## Persistence and recovery integration

Deployment must preserve the Task 045 and Task 046 boundaries:

- PAPER authoritative state remains external to the container filesystem;
- DEMO SQLite state remains on the controlled Windows workstation;
- model artifacts remain independently recoverable;
- backup/restore is independent from container lifecycle;
- state-mutating PAPER scheduling resumes only after recovery validation;
- DEMO remains disabled until its separate read-only reconciliation gate is healthy.

No numeric RPO/RTO is prescribed by this task; those values remain an operational service-level decision.

## Deployment lifecycle

A future implementation should follow this sequence:

1. Build and scan the immutable container image.
2. Publish the image to a controlled artifact registry.
3. Inject configuration and secrets at runtime.
4. Start the new revision with execution disabled.
5. Validate liveness and readiness.
6. Validate durable-state connectivity and model artifact identity where required.
7. Perform application smoke tests.
8. Route production traffic only after readiness and operational checks succeed.
9. Monitor request errors, latency, dependency failures and resource health.
10. Roll back to the previous immutable revision if deployment validation fails.
11. Record deployment and recovery evidence.

No automatic model promotion or execution authorization is implied by deployment success.

## Operational monitoring contract

The production implementation must monitor at minimum:

- liveness/readiness state;
- API error rate and latency;
- container restart/crash state;
- Firebase/provider dependency failures;
- durable-state write failures;
- model artifact load/readiness failures;
- deployment revision identity.

Monitoring and alert thresholds are provider-specific and remain outside this task.

## Explicit non-goals

- Cloud-provider selection;
- production account/resource provisioning;
- DNS registration;
- TLS certificate issuance;
- secret-manager provisioning;
- automated deployment pipeline;
- public exposure of the API;
- LIVE trading;
- new DEMO transactions;
- automatic model promotion.

## Validation evidence

Regression tests must verify that the repository preserves the Linux/Windows execution boundary, safe runtime defaults, readiness/liveness distinction and provider-neutral deployment posture.
