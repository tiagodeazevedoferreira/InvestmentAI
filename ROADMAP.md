# Roadmap

## Completed architecture/foundation
API, PWA, Firebase integration boundary, CI, environment separation, OpenBB provider boundary, Yahoo fallback, technical analytics, valuation primitives, Markowitz/efficient frontier/VaR, cost-aware simulator, XGBoost training boundary, financial evaluation metrics, model promotion gate and broker isolation.

## Quant research
Expand normalized fundamental statements, ROIC methodology, scoring/ranking, walk-forward validation, robust covariance and transaction-cost calibration.

## ML
Train on real historical datasets, out-of-sample validation, calibration, model registry persistence, drift monitoring, LSTM benchmark and RL experiments.

## Trading simulation
Integrate the simulator with the signal engine, portfolio accounting, fees/slippage, reconciliation and audit trail.

## Paper/Demo
- [x] Internal deterministic paper engine and scheduler
- [x] Doto/MT5 DEMO broker adapter contract
- [x] Read-only DEMO reconciliation harness
- [x] Fail-closed DEMO authorization with pre/post reconciliation
- [x] Non-submitting MT5 order preflight (`order_check`)
- [x] Broker-independent DEMO order preflight enforced by the executor
- [x] Durable independent DEMO order ledger
- [x] Conservative DEMO failure recovery without automatic retry
- [x] Manual controlled DEMO execution service (scheduler remains disconnected)
- [x] Controlled DEMO preflight harness against the authenticated DOTO/MT5 DEMO workstation, with execution disabled and `order_send` explicitly not called
- [ ] Controlled single-order validation against the DOTO/MT5 DEMO account
- [ ] Scheduler-to-DEMO integration after single-order validation
- [ ] Complete DEMO order lifecycle and failure-recovery validation against the broker

## Live promotion
Only after empirical evidence across backtest, paper and demo. Require explicit model approval, risk limits, kill switch, reconciliation and separate live credentials. Live remains disabled until then.

## Evolution
Multimodal research data, ensemble models, regime detection, robust optimization, execution-quality analytics and additional providers.
