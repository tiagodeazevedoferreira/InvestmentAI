# Task 011 — Cross-Asset ML Diagnostics Results

- **TASK_ID:** `codex-20260916-011`
- **STATUS:** PASS
- **Validation date:** 2026-09-16

## CI validation

Workflow: `.github/workflows/ml-cross-asset.yml`  
Run: `35131993552`  
Commit: `e17ddc0`

The workflow completed successfully and included:

1. dependency installation;
2. diagnostic unit tests;
3. causal cross-asset experiment;
4. report generation;
5. artifact upload.

## Experiment coverage

The controlled real-data experiment covered:

- PETR4;
- VALE3;
- ITUB4;
- 8 paired out-of-sample folds.

Reported diagnostics include Brier score, ECE, actual and predicted positive rates, mean probability, probability/prediction bias, first-vs-last fold temporal deltas, per-feature distribution shift, maximum standardized mean shift, and pooled-vs-asset-specific comparisons.

Artifact: `ml-cross-asset-experiment`  
Size: 3,059 bytes  
SHA-256: `cd1b20126b8f9e0c49f98295dbc9c933051c82e212100a191d17670f242781e6`

## Interpretation boundary

This is a research and observability result. It does not establish profitability, robustness across all assets or market regimes, or production readiness. No trading threshold, portfolio-risk rule, broker integration, or execution behavior was changed.

## Reproducibility

The validation is tied to the successful CI run and its uploaded artifact. Future changes to feature engineering, data sources, model configuration, or evaluation methodology require a new validation artifact rather than reusing this result.
