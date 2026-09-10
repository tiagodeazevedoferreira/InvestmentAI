# MT5 DEMO execution

The InvestmentAI MT5 execution adapter is intentionally fail-closed.

## Required gates

1. `mt5_demo_execution_enabled` must be explicitly `true`.
2. `mt5_demo_expected_login` must identify the intended DEMO account.
3. `mt5_demo_expected_server` must exactly match the authenticated MT5 account server.
4. The terminal must be connected and authenticated before execution.
5. The adapter must remain in `environment=demo`.
6. The existing authorization, risk, kill-switch, and reconciliation layers must pass before an order is submitted.

No password is stored by InvestmentAI. Authentication is performed by the desktop MT5 terminal.

## First-order policy

The first real MT5 execution must be performed only after the intended DOTO DEMO account has been connected and independently verified. The current `DOTOGlobal-Real` account is not an acceptable target for this adapter.

Live trading remains disabled and is outside the scope of this component.
