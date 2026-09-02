# Development Status

Last updated: 2026-09-02

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
- [ ] Position sizing and portfolio risk limits

## AI/ML
- [x] Technical feature engineering
- [x] Five-day directional target
- [x] Chronological train/validation/test split
- [x] XGBoost training interface
- [x] Model metadata/registry artifact
- [x] Financial evaluation metrics
- [ ] Training workflow on real datasets
- [x] Out-of-sample ML evaluation
- [ ] Empirical financial promotion gate
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
- [ ] Paper-to-Firebase persistence/reconciliation
- [ ] Doto/MT5 demo broker adapter
- [ ] Live broker adapter
- [ ] Empirical model promotion gate
- [ ] Kill switch and reconciliation engine

## Paper/Shadow
- [x] Paper execution primitive
- [ ] End-to-end signal -> paper -> portfolio accounting
- [ ] Shadow decision ledger
- [ ] Outcome attribution/calibration report

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
- [ ] Full integration test suite against provider mocks
- [ ] End-to-end training/backtest test
- [ ] Security/dependency scan
- [ ] Production deployment

## Current ML validation gate
The causal ML trading backtest, robustness audit and model diagnosis are complete. The robustness gate is not yet passed because performance is not stable across all evaluated assets and assumptions. A causal pooled cross-asset model experiment is now implemented to test whether normalized technical features transfer across PETR4, VALE3 and ITUB4 without changing execution policy. The experiment remains research-only until its out-of-sample evidence is reviewed.

## Promotion boundary
Phases 1-9 remain non-live. Phase 10/live is intentionally disabled and requires explicit authorization after empirical validation.
