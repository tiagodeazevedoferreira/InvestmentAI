# DEMO execution gates

The controlled path has four independent gates:

1. **Identity gate** — exact MT5 login/server must match configuration.
2. **Intent gate** — `DemoOrderPreflight` validates environment, symbol, side, volume and order type.
3. **Authorization gate** — fresh reconciliation, kill switch and operational checks must pass.
4. **Broker gate** — MT5 account trading permission, market data and `order_check()` must pass before `order_send()`.

The durable ledger records the lifecycle but does not bypass any gate.

The first live broker validation remains a separate manual step and is not part of this code change.
