# Task 039 — Production API runtime hardening

## Objective

Harden the FastAPI runtime for deployment without changing trading authority or broker behavior.

## Scope

- Make CORS origins configurable through `CORS_ALLOWED_ORIGINS`.
- Allow production operators to disable interactive API documentation through `API_DOCS_ENABLED=false`.
- Add baseline response security headers for content sniffing, framing and referrer policy.
- Preserve existing health and API behavior by default.

## Safety boundary

This task does not:
- enable LIVE trading;
- change DEMO execution authorization;
- add broker credentials;
- publish or deploy the container;
- alter trading signals, risk limits or model promotion.

## Validation

Backend regression coverage was added for the new runtime settings and CORS parsing. Full CI, Security and Dependency Scan, External Intelligence Validation, Cross-Asset ML Experiment and Phase 10 Live Gate validation must pass before this task is marked complete.

## Status

IMPLEMENTED — validation pending.
