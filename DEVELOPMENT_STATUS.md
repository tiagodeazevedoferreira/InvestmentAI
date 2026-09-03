# Development Status

Last updated: 2026-09-03

## Foundation
- [x] Repository and persistent handoff context
- [x] Architecture/decision records
- [x] Environment separation contract
- [x] Firebase repository abstraction
- [x] FastAPI application skeleton
- [x] PWA frontend skeleton
- [x] CI and Firebase smoke-test workflows
- [x] OpenBB provider boundary
- [x] Yahoo fallback provider
- [x] OpenBB/yfinance B3 proof-of-concept adapter

## Value Investing
- [x] Fundamental data service boundary
- [x] P/E, P/B, EV/EBITDA, ROE and dividend-yield primitives
- [x] DCF/Gordon valuation primitives
- [ ] Provider-normalized historical statements
- [ ] ROIC with invested-capital definition and validation
- [ ] Fundamental score/ranking and margin-of-safety engine

## Trading
- [x] EMA 9/21
- [x] RSI 14
- [x] Bollinger Bands
- [x] RSI oversold/overbought strategy
- [x] Basic backtester
- [x] Cost/slippage-aware market simulator
- [x] Market replay
- [x] Walk-forward evaluation
- [ ] Transaction-cost calibration by venue
- [x] Causal ML trading backtest
- [x] ML robustness audit
- [ ] ML cross-asset model diagnosis and improvement

## Portfolio/Risk
- [x] Markowitz optimization
- [x] Maximum Sharpe
- [x] Efficient frontier
- [x] Parametric daily VaR 95%
- [ ] Robust covariance/shrinkage
- [x] Initial paper position sizing and order risk limits
- [ ] Production-grade portfolio risk limits

## AI/ML
- [x] Technical feature engineering
- [x] Five-day directional target
- [x] Chronological train/validation/test split
- [x] XGBoost training interface
- [x] Model metadata/registry artifact
- [x] Financial evaluation metrics
- [ ] Training workflow on real datasets
- [x] Out-of-sample ML evaluation
- [x] Empirical financial promotion gate evaluator (human-review only)
- [ ] LSTM experiment
- [ ] RL agent experiment

## External Intelligence
- [x] Doto AI Market Insights normalization boundary
- [x] Trading Central read-only API boundary
- [x] Provider-neutral signal contract
- [x] Signal fusion engine
- [x] Independent-evidence risk gate
- [x] TradingView Pine technical-validator and webhook contract
- [x] TradingView reconciliation
- [x] TradingView evidence connected to SignalFusion/RiskGate
- [x] Decision observability record
- [ ] Real Trading Central credentials/entitlement validation
- [ ] Real Doto signal observation/export/approved bridge
- [ ] TradingView alert/webhook activation on an eligible plan
- [x] OpenBB/B3 provider capability validation
- [ ] Provider calibration against historical outcomes

## Execution
- [x] Simulation-only default
- [x] Demo/live separation
- [x] Risk gate skeleton
- [x] Deterministic paper broker
- [x] Paper execution engine with market/limit orders
- [x] Fees and slippage accounting
- [x] Paper portfolio mark-to-market and P&L accounting
- [x] Paper account persistence boundary in Firebase with bounded recent history
- [x] Paper execution API and lifecycle tests
- [x] Signal → risk gate → position sizing → paper order automation primitive
- [x] Paper-to-TradingView reconciliation primitive
- [x] Provider-backed paper scheduler/orchestrator
- [x] Doto/MT5 demo broker adapter contract (demo-only; end-to-end validation pending)
- [ ] Live broker adapter
- [x] Empirical promotion gate evaluator (human-review only)
- [x] Kill switch and reconciliation engine (broker-neutral, read-only)

## Paper/Shadow
- [x] Paper execution primitive
- [x] End-to-end paper order -> fill -> portfolio accounting
- [x] Bounded paper account state persistence
- [x] Deterministic technical signal → risk → sizing → paper execution path
- [x] Signal automation scheduler
- [x] Idempotent decision ledger
- [ ] Shadow decision ledger
- [x] Outcome attribution primitives for forward-return observation and hit-rate summaries
- [x] Persisted paper outcomes with resumable horizons
- [x] Descriptive calibration statistics with confidence intervals and explicit cost assumptions
- [x] Causal volatility regime classification
- [x] Paper/TradingView evidence reconciliation
- [x] Conservative empirical evidence gate with explicit criteria and no automatic promotion

## Firebase/data governance
- [x] Operational repository abstraction
- [x] Retention-aware storage boundary
- [ ] Execute Firebase smoke test against configured secret
- [ ] Production security rules
- [ ] Data-size monitoring/quotas dashboard
- [ ] Automated retention cleanup

## Quality
- [x] External-intelligence unit tests
- [x] TradingView webhook normalization/authentication tests
- [x] TradingView reconciliation/fusion tests
- [x] OpenBB B3 adapter unit tests
- [x] OpenBB B3 live smoke-test workflow
- [x] ML trading backtest tests
- [x] ML robustness audit helper tests
- [x] ML model diagnosis helper tests
- [x] Causal pooled cross-asset ML experiment tests
- [x] Paper execution accounting tests
- [x] Paper API lifecycle tests
- [x] Paper signal automation tests
- [x] Paper scheduler/ledger unit tests
- [x] Paper outcome attribution unit tests
- [x] Paper calibration unit tests
- [x] Causal regime/reconciliation unit tests
- [x] Empirical promotion gate unit tests
- [x] Operational safety unit tests
- [x] MT5 demo adapter contract tests
- [ ] Full integration test suite against provider mocks
- [ ] End-to-end training/backtest test
- [ ] Security/dependency scan
- [ ] Production deployment

## Current ML validation gate
The causal ML trading backtest, robustness audit and model diagnosis are complete. The robustness gate is not yet passed because performance is not stable across all evaluated assets and assumptions. A causal pooled cross-asset model experiment is implemented to test whether normalized technical features transfer across PETR4, VALE3 and ITUB4 without changing execution policy. The experiment remains research-only until its out-of-sample evidence is reviewed.

## Current execution gate
The internal paper execution path is deterministic and broker-independent. Provider-backed scheduling obtains B3 history through the OpenBB/yfinance boundary, evaluates the existing RSI paper policy, persists a deterministic decision key, and skips duplicates. Completed decisions now receive persisted 1/5/20-bar forward outcomes. The calibration layer reports directional hit rate, confidence intervals and return statistics under an explicit transaction-cost assumption, and the runner can partition results by a causal trailing-volatility regime. Paper decisions can also be reconciled against TradingView validator evidence using an explicit timestamp tolerance. The empirical gate now evaluates predefined evidence criteria, but a passing result only permits human review and can never authorize promotion automatically. Operational kill-switch and broker-neutral reconciliation primitives are hardened. A Doto/MT5 demo-only adapter contract now exists with account/position/order/execution normalization and order-check-before-send semantics; end-to-end demo reconciliation remains pending. This remains PAPER/DEMO only and does not contact a live venue.

## Promotion boundary
Phases 1-9 remain non-live. Phase 10/live is intentionally disabled and requires explicit authorization after empirical validation and operational readiness, including kill-switch and reconciliation hardening.
