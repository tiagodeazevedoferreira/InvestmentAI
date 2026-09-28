# Task 050 — GCP infrastructure bootstrap

## Status

IMPLEMENTED — operator-side Terraform validation/apply required

## Objective

Provision the Google Cloud resources required by Task 049 without storing secrets or broker credentials in Git.

## Scope

Terraform provisions required APIs, Artifact Registry, deployment/runtime service accounts, Workload Identity Federation restricted to the InvestmentAI main branch, and Secret Manager secret containers.

## Safety

No secret values are stored by this module. No Cloud Run service is deployed by Terraform. LIVE trading, DEMO execution and broker credentials remain outside this infrastructure boundary.

## Validation

terraform fmt -check, terraform validate and terraform plan must pass in an operator-authenticated GCP environment before apply.

## Remaining work

Create secret versions, configure GitHub production variables, run Task 049, and execute the first controlled deployment smoke test. Task 049 grants service-level Cloud Run Invoker to the deployment service account after the service is created.
