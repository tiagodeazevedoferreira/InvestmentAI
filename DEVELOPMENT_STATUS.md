# Development Status

Last updated: 2026-08-31

## Foundation
- [x] Repository established
- [x] Persistent project context
- [x] Architecture and decision records
- [x] Environment separation contract
- [x] Firebase repository abstraction
- [x] FastAPI application skeleton
- [x] PWA frontend skeleton
- [x] CI workflow
- [x] Firebase integration smoke-test workflow

## Value Investing
- [x] Fundamental domain models and metric service skeleton
- [x] DCF/Gordon valuation primitives
- [ ] Production-grade provider coverage and historical fundamentals
- [ ] Fundamental scoring/ranking

## Trading
- [x] Technical indicator implementation
- [x] RSI oversold/overbought strategy
- [x] Basic backtester
- [ ] Transaction-cost/slippage calibration
- [ ] Walk-forward evaluation

## Portfolio/Risk
- [x] Markowitz optimization primitives
- [x] Sharpe maximization
- [x] Parametric VaR 95%
- [ ] Constraints and robust covariance methods

## AI/ML
- [x] Feature engineering interface
- [x] Time-series-safe dataset split primitives
- [x] XGBoost-compatible training interface
- [ ] Real historical training dataset
- [ ] Out-of-sample validation and model registry
- [ ] LSTM experiment

## Execution
- [x] Simulation-only default
- [x] Demo/live separation in domain model
- [x] Risk gate skeleton
- [ ] Paper broker adapter
- [ ] Demo broker adapter
- [ ] Live broker adapter
- [ ] Promotion gate based on empirical validation

## Firebase/data
- [x] Operational repository abstraction
- [x] Retention policy abstraction
- [ ] Deploy/test against configured Firebase secret
- [ ] Production security rules
- [ ] Data-size monitoring
