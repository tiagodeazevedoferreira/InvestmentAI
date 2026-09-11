# Controlled DOTO/MT5 DEMO runner

The script `scripts/run_doto_mt5_controlled_demo.py` is the manual boundary for the first controlled DOTO/MT5 DEMO execution.

## Safety defaults

- Default invocation is read-only readiness mode.
- `execution_enabled` remains false unless `--execute` is supplied.
- `--execute` additionally requires `INVESTMENTAI_DEMO_EXECUTION_ARMED=true`.
- The runner is not connected to the scheduler and has no automatic retry.
- The broker remains restricted to the configured DEMO login/server and a maximum volume of `0.01`.
- Post-execution state is refreshed through a callable provider before post-reconciliation.

## Current limitation

The runner currently uses a temporary workstation-state bridge for the internal-state boundary. Before relying on the first real DEMO execution as application evidence, the bridge must be replaced by the application's own portfolio/accounting state provider. This avoids treating the broker as the application's source of truth.

## Execution procedure

1. Run the script without `--execute` and confirm `CONTROLLED DEMO RUN: READY`.
2. Verify the terminal is authenticated to login `5344431` on `DOTOGlobal-Real`.
3. Verify the intended symbol, side and `0.01` volume.
4. Only after explicit human authorization, set `INVESTMENTAI_DEMO_EXECUTION_ARMED=true` and invoke `--execute`.
5. Inspect the resulting ledger state, order/deal identifiers and post-reconciliation result.
6. Any ambiguous result remains recoverable in the ledger; do not retry automatically.

No LIVE credentials or LIVE execution path are enabled by this runner.
