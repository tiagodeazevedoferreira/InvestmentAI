# Task 040 — API observability baseline

## Objective

Add deployment-neutral API observability needed to operate the production container without changing trading authority or broker behavior.

## Scope

- Add configurable API log level through `LOG_LEVEL`.
- Emit one structured, low-cardinality access-log event per completed request with method, path, status, duration and request ID.
- Emit an exception log for unhandled request failures without logging request bodies, query parameters, credentials or response payloads.
- Accept a valid `X-Request-ID` for request correlation and generate a UUID when absent or invalid.
- Return `X-Request-ID` in API responses.
- Preserve the existing security headers and API behavior.

## Safety boundary

This task does not:
- enable LIVE trading;
- change DEMO execution authorization;
- add broker credentials;
- publish or deploy the container;
- log request bodies, query parameters, authentication secrets or broker credentials;
- alter trading signals, risk limits or model promotion.

## Validation

Regression tests cover request ID generation/preservation, security headers and the health endpoint. Full CI, Security and Dependency Scan, External Intelligence Validation, Cross-Asset ML Experiment, Phase 10 Live Gate Tests and Container Build must pass before completion.

## Status

COMPLETED — validated.

## Validation record

Validated on 2026-09-28. Final implementation commit: `5aee55e561317e007c003c0650d4090125986712`.

All required workflows completed successfully:
- CI: `36418918794`
- Security and Dependency Scan: `36418918741`
- External Intelligence Validation: `36418918759`
- Cross-Asset ML Experiment: `36418918739`
- Phase 10 Live Gate Tests: `36418918776`
- Container Build: `36418918784`

The Security workflow completed dependency audit, static security scan, backend tests and backend compilation successfully.
