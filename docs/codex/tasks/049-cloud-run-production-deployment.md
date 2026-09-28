# Task 049 — Cloud Run production deployment

## Status

IMPLEMENTED — validation requires configured GCP environment

## Objective

Implement the first provider-specific production deployment boundary for the immutable container artifact produced by Task 048, using Google Cloud Run and Artifact Registry.

## Scope

The deployment boundary authenticates GitHub Actions through Workload Identity Federation, publishes the production image to Artifact Registry with the Git commit SHA, resolves its immutable digest, deploys that digest to Cloud Run, injects runtime secrets through Secret Manager, validates liveness/readiness over HTTPS, and supports manual rollback to an existing immutable digest.

## Safety boundary

The workflow is manual-dispatch only. It does not automatically deploy on every push to main.

It must never enable LIVE trading, enable MT5/DEMO execution, submit broker orders, run on the Windows DOTO/MT5 workstation, store cloud credentials in the repository, deploy a mutable latest image, or promote a model.

## Required Google Cloud configuration

Provision outside Git:

- Google Cloud project;
- Artifact Registry Docker repository;
- dedicated GitHub Actions deployment service account;
- Workload Identity Federation trust for this repository;
- Artifact Registry push, Cloud Run deployment and service-level invocation permissions;
- Cloud Run runtime service account;
- Secret Manager secrets required by the application;
- least-privilege access from the Cloud Run runtime service account to those secrets.

The deployment workflow grants the deployment service account service-level Cloud Run Invoker permission after creating/updating the service so private endpoint smoke tests can run without making the service public.

GitHub Actions variables:

- GCP_PROJECT_ID
- GCP_REGION
- ARTIFACT_REGISTRY_REPOSITORY
- CLOUD_RUN_SERVICE
- GCP_WIF_PROVIDER
- GCP_DEPLOY_SERVICE_ACCOUNT
- GCP_RUNTIME_SERVICE_ACCOUNT

Secret Manager names expected by the workflow:

- investmentai-firebase-database-url
- investmentai-firebase-service-account
- investmentai-tradingview-webhook-secret

## Runtime safety defaults

The deployment explicitly sets ENVIRONMENT=production, TRADING_MODE=simulation, LIVE_TRADING_ENABLED=false, MODEL_APPROVED=false, RISK_GATE_ENABLED=true, MT5_DEMO_EXECUTION_ENABLED=false, API_DOCS_ENABLED=false and LOG_LEVEL=INFO.

No DOTO/MT5 terminal path, login or password is injected into Cloud Run.

## Rollback

Rollback references an existing immutable Artifact Registry sha256 digest. latest and mutable deployment tags are not accepted.

## Non-goals

This task does not provision the Google Cloud project, create IAM resources, create secrets, configure a custom domain/TLS certificate, enable broker execution, or promote a model.
