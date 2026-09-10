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

`scripts/check_doto_mt5_order.py` is the next read-only gate. It validates the same account identity and market-order parameters, then calls MT5 `order_check()` only. It never calls `order_send()`.

## Run: account preflight

From the repository root:

```powershell
$env:PYTHONPATH="backend"
.\.venv\Scripts\python.exe scripts\check_doto_mt5_demo.py --login 5344431 --server DOTOGlobal-Real
```

The terminal path defaults to the installed DOTO Global MT5 executable. It can be overridden with `--terminal` or `MT5_DEMO_TERMINAL_PATH`.

The login and server can also be supplied through `MT5_DEMO_EXPECTED_LOGIN` and `MT5_DEMO_EXPECTED_SERVER`.

## Run: order_check preflight

The controlled default is EURUSD BUY `0.01` lot:

```powershell
$env:PYTHONPATH="backend"
.\.venv\Scripts\python.exe scripts\check_doto_mt5_order.py
```

Optional parameters:

```powershell
.\.venv\Scripts\python.exe scripts\check_doto_mt5_order.py --symbol EURUSD --side BUY --volume 0.01
```

A successful run proves only that MT5 accepted the request for `order_check()` under the connected account and current market conditions. It does **not** place an order.

## Safety

The current account identity is login `5344431` with server `DOTOGlobal-Real`, and that account is the account being treated as the controlled DEMO target for this validation. The server name alone is not evidence of live/demo status; the configured login/server pair and the connected account are the identity boundary.

Do not enable `mt5_demo_execution_enabled` merely to run either preflight.

A successful preflight means only that the intended account and, for the second gate, the proposed market-order request have passed their respective checks. It is **not** authorization to automate trading. The first order remains a separate, manually controlled gate with minimum volume and post-trade reconciliation.
