# Task 011 — Cross-Asset ML Diagnostics

- **TASK_ID:** `codex-20260916-011`
- **STATUS:** PASS
- **Date:** 2026-09-16
- **Scope:** offline/research diagnostics only

## Objective

Add a dedicated diagnostic layer for the causal pooled cross-asset ML experiment so that model quality can be inspected beyond headline accuracy. The diagnostics must remain observational and must not change model thresholds, portfolio risk controls, broker execution, or production-promotion gates.

## Implemented

The diagnostic helper reports:

- actual positive rate;
- predicted positive rate;
- mean predicted probability;
- probability bias and prediction bias;
- accuracy;
- Brier score;
- expected calibration error (ECE);
- first-vs-last OOS fold temporal deltas for Brier and ECE;
- causal reference-vs-OOS feature distribution shift, including per-feature standardized mean shift and maximum shift.

Dedicated unit tests cover normal inputs, calibration, causal feature-shift behavior, invalid probabilities, and finite diagnostics.

The CI workflow executes the diagnostic unit tests before the real-data causal cross-asset experiment and report generation.

## Validation

GitHub Actions workflow `.github/workflows/ml-cross-asset.yml` completed successfully on `main` commit `e17ddc0` (run `35131993552`). The workflow included dependency installation, diagnostic unit tests, the causal cross-asset experiment, report generation, and artifact upload.

Artifact: `ml-cross-asset-experiment`  
SHA-256: `cd1b20126b8f9e0c49f98295dbc9c933051c82e212100a191d17670f242781e6`

The controlled experiment covered PETR4, VALE3, and ITUB4 with 8 paired OOS folds and reported Brier/ECE, probability/class bias, temporal degradation, feature distribution shift, and pooled-vs-asset-specific comparisons.

## Acceptance

- [x] Diagnostic helper implemented.
- [x] Dedicated diagnostic tests implemented.
- [x] Diagnostic tests run in CI before the experiment.
- [x] Real-data causal cross-asset experiment completed successfully in CI.
- [x] Auditable experiment artifact generated.
- [x] Scope remains research/observability only.
- [x] No broker order, execution, risk-control, or promotion behavior changed.

## Limitations

The diagnostics do not establish profitability, robustness, or production readiness. The existing robustness gate remains separate and is not passed merely by completing this task.
