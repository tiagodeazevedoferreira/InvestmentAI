# InvestmentAI — Doto + Trading Central

## Scope
InvestmentAI is the equity/market-asset project. This integration is intentionally independent from `autonomous-crypto-trading`.

## Target architecture

`market/fundamental/technical/ML + Doto AI + Trading Central -> signal fusion -> risk gate -> portfolio sizing -> paper -> demo -> live`

## Phase status

### Phase 1 — Audit
Repository already has provider abstraction, Yahoo fallback, fundamental/valuation services, technical indicators, XGBoost boundary, portfolio/VaR, simulator, broker abstraction, OrderManager and simulation/paper/demo/live environment separation. The current gaps were paper broker, demo adapter, stronger external-intelligence boundary and empirical shadow evaluation.

### Phase 2 — Doto
Doto AI Market Insights is represented by a provider-neutral adapter. It accepts an approved observation/export/integration payload; it does not scrape the web UI or automate credentials.

### Phase 3 — Trading Central
A read-only API adapter exposes documented technical summary, support/resistance, instrument events, article sentiment/analytics, latest articles, economic events, anticipated events and stops. API base URL and token are environment variables.

### Phase 4 — Intelligence Layer
External evidence is normalized into `ExternalSignal`. Missing values remain null. Source and provider version/reference are retained for audit.

### Phase 5 — Signal Fusion
`SignalFusion` produces a normalized direction, score, confidence and source set. It is evidence aggregation, not a replacement for the existing ML model.

### Phase 6 — Risk Engine
`RiskGate` requires actionable direction, minimum confidence, at least two independent evidence sources and fresh signals. Live is explicitly blocked in phases 1–9.

### Phase 7 — Paper
A deterministic in-process `PaperBroker` simulates fills, cash, positions and order history without external services or paid software.

### Phase 8 — Demo
The existing `BrokerAdapter` boundary remains the integration point. A Doto/MT5 demo connector is intentionally not enabled until credentials/API access and an approved sandbox endpoint are available.

### Phase 9 — Shadow
Shadow mode should record the hypothetical fused decision and compare it against subsequent market outcomes without placing orders. This can run in GitHub Actions and persist bounded audit metrics in Firebase.

## Safety
- No live trading is enabled by this integration.
- No broker credential is stored in source code.
- Doto and Trading Central never bypass RiskGate.
- Provider failure is a data-quality event, not permission to trade.
- Live promotion remains a separate future phase requiring explicit approval.

## Doto execution path

The intended execution boundary is:

`InvestmentAI -> RiskGate -> OrderManager -> BrokerAdapter -> Doto/MT5 demo`

No direct order path exists from an external provider to Doto.

## Free testing strategy

Paper and shadow validation are implemented without requiring paid MT5 or TradingView plans. TradingView may be used only as an optional visual reference; it is not an execution dependency.
