# TradingView integration

## Purpose

TradingView is an independent technical-validation source for InvestmentAI. It is not an order router and does not bypass the InvestmentAI signal, risk, position-sizing or broker boundaries.

The canonical Pine implementation is `tradingview/InvestmentAI_Validator.pine`.

## Technical contract

The validator calculates:

- EMA 9
- EMA 21
- RSI 14 with 30/70 reference levels
- Bollinger Bands 20 with multiplier 2.0
- Volume and 20-period volume moving average

The script exposes a dashboard and optional `alert()`/`alertcondition()` events. No order placement is implemented.

## Webhook contract

The backend exposes:

`POST /api/integrations/tradingview/webhook/{webhook_token}`

`TRADINGVIEW_WEBHOOK_SECRET` must be configured in the backend environment. The secret is used as a high-entropy path token because TradingView webhooks do not provide arbitrary custom HTTP authentication headers.

The endpoint:

1. Fails closed when the secret is not configured.
2. Rejects an invalid token with HTTP 401.
3. Validates the JSON payload against `TradingViewWebhook`.
4. Normalizes labels and timestamps.
5. Generates a deterministic SHA-256 event fingerprint.
6. Does not place, modify or cancel orders.
7. Does not change the trading mode.

The current endpoint is intentionally ingestion-only. Persistence, reconciliation and signal-fusion consumption are separate concerns and must remain behind their existing domain boundaries.

## Payload

The Pine validator sends a JSON object containing the source, symbol, exchange, timeframe, confirmed bar timestamp, close, EMA 9/21, RSI 14, Bollinger upper/basis/lower, volume and derived technical states.

Example shape:

```json
{
  "source": "tradingview",
  "symbol": "VALE3",
  "exchange": "BMFBOVESPA",
  "timeframe": "D",
  "bar_time": "2026-09-01T00:00:00Z",
  "close": 100.0,
  "ema_fast": 99.0,
  "ema_slow": 98.0,
  "rsi14": 62.5,
  "bb_upper": 105.0,
  "bb_basis": 100.0,
  "bb_lower": 95.0,
  "volume": 1000000,
  "ema_state": "bullish",
  "rsi_state": "neutral",
  "bb_state": "inside",
  "bar_confirmed": true
}
```

## Operational activation

The repository can be prepared without a paid TradingView alert plan. Actual webhook delivery requires a TradingView plan/account capability that permits the required alert and webhook workflow.

When enabled, configure the TradingView alert to use `Any alert() function call` from the InvestmentAI validator and point it to the HTTPS backend endpoint with the secret path token. The webhook must remain read-only from the trading system's perspective.

## Future validation flow

`TradingView -> webhook ingestion -> event normalization/fingerprint -> independent validation -> signal fusion/risk gate`

The TradingView event must never directly reach a broker adapter.
