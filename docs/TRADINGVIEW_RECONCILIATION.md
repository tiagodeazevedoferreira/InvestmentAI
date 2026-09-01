# TradingView reconciliation

TradingView is an independent technical-evidence source. This layer converts a validated webhook event into the same provider-neutral `ExternalSignal` contract used by InvestmentAI's signal-fusion engine.

## Acceptance rules

An event is accepted only when:

- the bar is confirmed;
- all numeric technical values are finite;
- Bollinger upper >= basis >= lower;
- EMA state agrees with EMA values;
- Bollinger state agrees with price when outside a band;
- RSI is within 0..100;
- EMA/RSI conditions form an actionable direction.

A bullish EMA 9/21 state with RSI not overbought produces `LONG`. A bearish EMA 9/21 state with RSI not oversold produces `SHORT`. Otherwise the event is `NEUTRAL` and is not actionable.

## Architectural boundary

`TradingViewWebhook -> reconciliation -> ExternalSignal(source=tradingview) -> SignalFusion -> RiskGate`

The reconciliation service has no broker dependency and cannot submit orders. TradingView therefore contributes evidence rather than authority.

The next stage is to connect this normalized signal to the existing fusion/risk pipeline and add persistence/replay tests. Live execution remains outside this stage.
