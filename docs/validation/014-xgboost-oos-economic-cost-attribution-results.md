# Task 014 — XGBoost OOS Economic Cost Attribution Results

## Validation configuration

- Symbols: PETR4, VALE3, ITUB4
- Requested period: 2021-09-15 through 2026-09-15
- Interval: 1d
- OOS horizon: 5
- Train size: 500
- Test size: 100
- Step: 100
- Threshold: 0.60
- Initial cash: 100,000
- Scenarios: zero cost; 0.1% commission; 5 bps slippage; 0.1% commission + 5 bps slippage
- Provider quality gate: valid for all three symbols
- OOS: 7 folds / 700 rows per symbol
- OOS start: 2023-10-23 for all symbols
- OOS end: 2026-08-12 for PETR4 and ITUB4; 2026-08-13 for VALE3

## Results

| Symbol | Scenario | Final cash | Return | Max drawdown | Trades | Commission | Slippage | Impact vs zero |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| PETR4 | zero cost | 126,477.77 | +26.48% | -20.89% | 158 | 0.00 | 0.00 | 0.00 pp |
| PETR4 | commission only | 107,993.01 | +7.99% | -21.97% | 158 | 18,238.20 | 0.00 | -18.48 pp |
| PETR4 | slippage only | 116,870.51 | +16.87% | -21.42% | 158 | 0.00 | 9,494.29 | -9.61 pp |
| PETR4 | commission + slippage | 99,789.86 | -0.21% | -22.52% | 158 | 17,526.32 | 8,763.16 | -26.69 pp |
| VALE3 | zero cost | 119,572.97 | +19.57% | -15.22% | 174 | 0.00 | 0.00 | 0.00 pp |
| VALE3 | commission only | 100,476.79 | +0.48% | -20.57% | 174 | 16,873.56 | 0.00 | -19.10 pp |
| VALE3 | slippage only | 109,609.80 | +9.61% | -16.75% | 174 | 0.00 | 8,819.93 | -9.96 pp |
| VALE3 | commission + slippage | 92,104.77 | -7.90% | -24.22% | 174 | 16,151.02 | 8,075.51 | -27.47 pp |
| ITUB4 | zero cost | 122,715.61 | +22.72% | -14.41% | 232 | 0.00 | 0.00 | 0.00 pp |
| ITUB4 | commission only | 97,306.86 | -2.69% | -20.09% | 232 | 22,489.23 | 0.00 | -25.41 pp |
| ITUB4 | slippage only | 109,275.21 | +9.28% | -16.54% | 232 | 0.00 | 11,935.28 | -13.44 pp |
| ITUB4 | commission + slippage | 86,649.35 | -13.35% | -23.49% | 232 | 21,212.08 | 10,606.04 | -36.07 pp |

## Observations

The zero-cost replay is positive for all three assets under the fixed OOS configuration. Introducing either commission or slippage reduces the economic result materially, and the combined 0.1% commission plus 5 bps slippage scenario produces negative final returns for all three assets.

The number of trades is unchanged across scenarios for each symbol. This is expected because the OOS probabilities and threshold are fixed; transaction costs affect economic outcomes, not signal generation.

The gap between explicit recorded transaction costs and the cash impact versus the zero-cost replay is path-dependent: transaction costs alter cash available for subsequent position sizing, so the difference in final cash is not required to equal the simple sum of commission and slippage.

These results are diagnostic. They do not establish profitability, robustness, production readiness, or an appropriate live-market transaction-cost assumption.

## Reproducibility hardening

The implementation was refactored so each symbol generates the XGBoost OOS run once. All four economic scenarios reuse the exact same OOS probability series and differ only in BacktestConfig commission/slippage parameters.

The deterministic contract test verifies one OOS generation call and four economic replay calls, with the same OOS object reused for every scenario.

## Validation status

- Cost-attribution contract test: passed.
- Real-data cost-attribution report: passed.
- Backend compilation: passed.
- Self-hosted Windows runner: ECTIN8F38594.
- Financial execution: none.
- MT5/DOTO: not invoked.
