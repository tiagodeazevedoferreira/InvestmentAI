# Paper Execution

## Purpose

InvestmentAI now has a broker-independent paper execution engine. It is a controlled test environment between pure simulation and any future broker demo integration.

## Safety boundary

- The engine never calls TradingView, a broker or an exchange.
- The system default remains `simulation`.
- No endpoint in this module can enable live execution.
- Every order is explicitly marked `environment=paper`.
- A configurable notional ceiling limits individual paper orders.

## API

All endpoints are mounted below `/api`.

### `GET /api/paper/account`

Returns cash, market value, equity, realized/unrealized P&L, positions and operational order/execution counters.

### `POST /api/paper/order`

Example:

```json
{
  "symbol": "PETR4",
  "side": "BUY",
  "quantity": 10,
  "reference_price": 40.00,
  "order_type": "MARKET",
  "reason": "technical_signal"
}
```

Market orders fill immediately using the supplied reference price plus/minus configured slippage. Fees are then applied to the fill notional.

Limit orders remain `open` until a later market mark crosses the limit.

### `POST /api/paper/mark`

Example:

```json
{
  "prices": {
    "PETR4": 45.00,
    "VALE3": 60.00
  }
}
```

The mark-to-market operation updates held positions and also attempts to fill crossed limit orders.

### `POST /api/paper/reset`

Resets the internal paper account to the requested starting cash. Use only during controlled testing because it intentionally discards the current account state.

## Firebase footprint

The paper account is stored under the configured `paper_account_path` (default `paper/account`). The persisted payload contains current portfolio state and only the most recent 100 orders and 100 executions. This keeps the Realtime Database within the project's bounded operational-storage policy.

Historical market data, model artifacts and unlimited execution history must remain outside Firebase RTDB.

## Next integration

The next execution milestone is not a broker connection. It is the controlled pipeline:

`Signal → RiskGate → PositionSizing → PaperOrder → Fill → Portfolio → Firebase → Reconciliation`.

Only after this pipeline is stable should a demo-broker adapter be introduced.
