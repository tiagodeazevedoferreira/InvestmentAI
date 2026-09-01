# Phase 10 — Live Trading

Phase 10 introduces the **authorization boundary** for real-money execution. It does not switch live trading on by itself.

## Required gates

All of the following must be true before a live order is even eligible:

1. `trading_mode=live`
2. `live_trading_enabled=true`
3. approved model
4. risk gate enabled
5. successful shadow validation
6. kill switch OFF
7. healthy broker reconciliation
8. broker demo validation completed
9. configured maximum position notional
10. proposed notional within that limit
11. signal confidence >= 0.75
12. authorization signal fresh (<5 minutes)
13. broker adapter reports `environment=live`

Any missing condition blocks the order (fail closed).

## Important

This phase intentionally does **not** provide a live broker implementation or credentials. The current Doto/MT5 integration remains a manual dependency because real-money execution requires an authorized broker endpoint/account and validated order semantics.

The architecture is:

`InvestmentAI -> Decision -> Risk -> LiveAuthorizationGate -> LiveBroker -> Doto/MT5`

Doto/Trading Central signals cannot authorize a live order directly.

## Promotion procedure

Before enabling a real account:

- complete a statistically meaningful shadow period;
- validate model calibration and drawdown limits;
- validate Doto/MT5 demo execution and reconciliation;
- set explicit position/notional limits;
- verify kill-switch behavior;
- configure secrets outside source control;
- execute a controlled first live order manually supervised;
- compare broker fills and internal ledger;
- keep automatic scaling disabled until reconciliation is proven.

No production credential belongs in Git history.
