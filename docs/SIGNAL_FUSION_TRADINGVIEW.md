# TradingView in signal fusion

TradingView is now connected to the existing provider-neutral signal-fusion contract as an independent technical evidence source.

Flow:

`TradingView webhook -> reconciliation -> ExternalSignal -> SignalFusion -> RiskGate`

The fusion layer does not give TradingView authority over the decision. It combines weighted confidence from all supplied sources. The existing independent-evidence gate remains mandatory, so a TradingView-only signal cannot pass when `min_sources` is two or greater.

Conflicting evidence is preserved rather than silently overridden. For example, a strong TradingView LONG combined with a strong model SHORT can produce a low-confidence fused result and be blocked by the risk gate.

No broker adapter is imported by this pipeline. It returns a decision object only. Execution remains a separate concern.
