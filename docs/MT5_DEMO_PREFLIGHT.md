# MT5 DEMO preflight

This check is the operational gate immediately before the first controlled DEMO execution.

## What it does

`scripts/check_doto_mt5_demo.py` connects to the already authenticated DOTO Global MT5 desktop terminal and validates:

- terminal connectivity;
- exact DEMO login;
- exact DEMO server;
- account currency, balance and equity;
- whether the terminal reports trading as allowed.

The script constructs the broker with `execution_enabled=False`. It never calls `order_check()` or `order_send()` and therefore cannot place an order.

## Run

From the repository root:

```powershell
$env:PYTHONPATH="backend"
.\.venv\Scripts\python.exe scripts\check_doto_mt5_demo.py --login <DEMO_LOGIN> --server <EXACT_DEMO_SERVER>
```

The terminal path defaults to the installed DOTO Global MT5 executable. It can be overridden with `--terminal` or `MT5_DEMO_TERMINAL_PATH`.

The login and server can also be supplied through `MT5_DEMO_EXPECTED_LOGIN` and `MT5_DEMO_EXPECTED_SERVER`.

## Safety

Do not use the current `DOTOGlobal-Real` account as the DEMO target. Do not enable `mt5_demo_execution_enabled` merely to run this preflight.

A successful preflight means only that the intended DEMO account is connected and identified correctly. It is **not** authorization to automate trading. The first order remains a separate, manually controlled gate with minimum volume and post-trade reconciliation.
