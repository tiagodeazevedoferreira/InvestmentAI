# Task 048 — Production deployment artifact pipeline

## Status

COMPLETED — validation in progress

## Objective

Create a provider-neutral CI/CD boundary that produces an immutable production container artifact and validates its runtime safety without provisioning or deploying infrastructure.

## Scope

The pipeline:

1. builds the production Docker image from the repository;
2. tags the image with the immutable Git commit SHA;
3. starts a production-safe candidate with execution disabled;
4. validates liveness and readiness;
5. exports the exact image as a compressed deployment artifact;
6. generates a SHA-256 checksum;
7. stores the artifact in GitHub Actions for controlled downstream deployment.

The workflow supports manual dispatch in addition to normal main-branch and pull-request validation.

## Safety boundary

The pipeline does not:

- push an image to an external registry;
- provision cloud resources;
- configure DNS or TLS;
- modify secrets;
- deploy a public endpoint;
- enable LIVE trading;
- enable DEMO execution;
- submit broker orders;
- promote a model automatically.

The candidate runtime explicitly uses simulation mode, disabled LIVE trading, absent model approval and disabled MT5 DEMO execution.

## Artifact integrity

The image is identified by the source Git SHA. The exported compressed image artifact receives a SHA-256 checksum in SHA256SUMS.

A downstream deployment implementation must verify the checksum and deploy only the intended immutable artifact.

## Provider-neutral deployment handoff

The resulting artifact is deliberately independent of cloud vendor, registry, orchestration platform and hosting implementation. A later provider-specific task may consume the artifact after defining authentication, secret injection, network controls, TLS, persistence, backup/recovery and rollback.

## Validation

Regression tests verify the workflow's immutable-artifact behavior, safe runtime defaults and absence of provider-specific deployment commands.

CI, Container Build, Security, External Intelligence, Cross-Asset ML and Phase 10 gates must pass on the final commit.

## Non-goals

Actual production deployment remains outside this task.
