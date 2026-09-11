# Controlled DOTO/MT5 DEMO runner

The script `scripts/run_doto_mt5_controlled_demo.py` is the manual boundary for the first controlled DOTO/MT5 DEMO execution.

## Safety defaults

- Default invocation is read-only readiness mode.
- `execution_enabled` remains false unless `--execute` is supplied.
- `--execute` additionally requires `INVESTMENTAI_DEMO_EXECUTION_ARMED=true`.
- The runner is not connected to the scheduler and has no automatic retry.
- The broker remains restricted to the configured DEMO login/server and a maximum volume of `0.01`.
- Post-execution state is refreshed through a callable provider before post-reconciliation.

## Application portfolio state

The runner now uses `DemoPortfolioStateStore` as the application's persistent internal DEMO state provider.

- The first explicitly armed execution bootstraps the provider once from the broker's pre-execution reconciliation snapshot.
- Subsequent executions use the persisted application state for the authorization boundary; they do not silently replace it with a fresh broker snapshot before authorization.
- After broker submission, the runner captures a fresh external snapshot and explicitly synchronizes the application state provider before the executor performs post-reconciliation.
- The provider stores only the normalized state required by reconciliation: cash, positions, open orders and executions.
- The broker remains the authoritative external execution system; the application provider is the internal state boundary used by InvestmentAI.
- If the application state is missing or malformed, the path fails closed.

This removes the previous direct workstation-state bridge from the runner.

## Execution procedure

1. Run the script without `--execute` and confirm `CONTROLLED DEMO RUN: READY`.
2. Verify the terminal is authenticated to login `5344431` on `DOTOGlobal-Real`.
3. Verify the intended symbol, side and `0.01` volume.
4. Only after explicit human authorization, set `INVESTMENTAI_DEMO_EXECUTION_ARMED=true` and invoke `--execute`.
5. Inspect the resulting ledger state, order/deal identifiers and post-reconciliation result.
6. Any ambiguous result remains recoverable in the ledger; do not retry automatically.

No LIVE credentials or LIVE execution path are enabled by this runner.
