# Task 041 — API operational readiness contract

## Objective

Add a provider-neutral readiness contract for the production API container, separating basic liveness from runtime safety/configuration readiness.

## Scope

- Add `GET /api/ready` as a readiness endpoint.
- Keep `GET /api/health` as the lightweight liveness endpoint.
- Return HTTP 503 when the configured trading mode violates existing fail-closed safety prerequisites.
- In LIVE mode, require LIVE enablement, model approval and an enabled risk gate.
- Reject DEMO execution enablement when the configured trading mode is not DEMO.
- Cover ready and fail-closed scenarios with regression tests.

## Safety boundary

This task does not:
- enable LIVE trading;
- change DEMO execution authorization;
- add broker credentials;
- publish or deploy the container;
- contact external brokers;
- change trading signals, risk limits or model promotion rules.

The readiness endpoint only evaluates existing configuration flags. It does not grant execution authority.

## Validation

Full CI, Security and Dependency Scan, External Intelligence Validation, Cross-Asset ML Experiment, Phase 10 Live Gate Tests and Container Build must pass before completion.

## Status

IMPLEMENTED — validation pending.
