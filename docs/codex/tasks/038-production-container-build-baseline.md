# Task 038 — Production container build baseline

## Objective

Establish a reproducible production-oriented Linux container build for the FastAPI backend without enabling live trading or changing execution authority.

## Scope

- Python 3.12 slim runtime.
- Install backend dependencies from the pinned requirement ranges already used by CI.
- Run the API as a non-root user.
- Expose port 8000.
- Provide a container health check against the existing read-only `/api/health` endpoint.
- Exclude credentials, local databases, virtual environments and CI metadata from the image build context.
- Add a GitHub Actions container-build job that builds the image but does not publish or deploy it.

## Safety boundary

This task does not:
- enable LIVE trading;
- add broker credentials to the image;
- publish an image to a registry;
- deploy to a production host;
- change the DEMO execution authorization boundary;
- authorize scheduler-driven live or demo execution.

## Validation

The repository now contains `Dockerfile`, `.dockerignore` and `.github/workflows/container-build.yml`.

The local environment used for development does not provide the Docker CLI, so the image was not built locally. CI is the authoritative build validation path and must pass before this baseline is considered validated.

Status

VALIDATED — CI green.

Validation completed successfully in Container Build run `36278613121` for commit `3e3071a2a2f12df2ebd70f5c311a74cca10f41b7`. The workflow built the production image, started the container, waited for the Docker health check and executed an in-container `/api/health` smoke test. Cleanup ran regardless of outcome.

The same commit also passed CI, Security and Dependency Scan, External Intelligence Validation, Cross-Asset ML Experiment and Phase 10 Live Gate Tests.

Production hosting, domain/TLS, runtime secret injection, persistent storage strategy and operational monitoring remain separate deployment work.
