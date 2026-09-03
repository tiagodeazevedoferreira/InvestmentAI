# Paper automation runbook

Automation is intentionally disabled by default.

## Dry run

Run the automation decision path without submitting orders. This mode is the required first operational test for every new provider or symbol.

## Paper execution

Enable only after the dry-run output has been reviewed. The execution boundary must remain the existing paper broker/order manager. No live adapter is permitted in this workflow.

## Initial universe

- PETR4
- VALE3
- ITUB4

These are initial test symbols only; they are not investment recommendations.

## Operational controls

- Market-hours guard before automated execution.
- One decision per symbol/bar/action through deterministic signal IDs.
- Bounded target weight.
- Downstream risk/notional limits remain authoritative.
- Firebase stores bounded operational state, not full market history.
- Every accepted/rejected order and fill must be auditable.
- Reconciliation must pass before enabling any future demo broker.
