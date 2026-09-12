# InvestmentAI — Project Context / Handoff

Last updated: 2026-09-11

## Purpose

InvestmentAI is a research, validation, paper-trading and controlled broker-integration platform. The project combines value investing, technical/quant research, portfolio/risk analytics, AI/ML, external intelligence and a deliberately gated execution layer.

The system is designed to fail closed. Research, simulation, paper, DEMO and LIVE execution remain distinct environments. No scheduler has financial execution authority, and no validation task should weaken the execution gates.

## Current validated baseline

### Task 004 — Shadow scheduler integration

Completed and validated.

- Shadow Decision Ledger is deterministic, idempotent and observational.
- Repeated logical events do not create duplicate shadow records.
- Paper Decision Ledger semantics remain idempotent.
- Shadow records have `execution_authority="none"`.
- No broker or MT5 execution is involved.

### Task 005 — Provider-backed paper scheduler integration

Completed and validated.

The integration test validates a deterministic mocked OpenBB provider boundary through the paper scheduler and both decision ledgers.

Validated behavior:

- `get_provider("openbb")` resolves the provider boundary.
- Provider history is mocked; no network access is required.
- `PETR4` is normalized to `PETR4.SA`.
- The expected `3mo` history request is made.
- Paper and shadow decisions are deterministic.
- `execute=False` is preserved.
- No Paper broker order is created.
- Shadow output remains observational with `execution_authority="none"`.
- No MT5, DOTO, `order_send` or financial execution is involved.

Validation completed with the full backend test suite at 18 tests, followed by successful `compileall` and safety scan.

### Task 006 — End-to-end backtest validation

Completed and validated on 2026-09-11.

Scope was intentionally limited to the deterministic backtesting layer. It does **not** claim that a real-dataset training workflow has been validated.

Validated with `MarketReplay`, synthetic OHLCV and `Backtester`:

- signal generated on candle `t` executes at the open of candle `t+1`;
- final open positions are liquidated;
- commission is accounted deterministically;
- slippage is accounted deterministically;
- invalid signals outside `-1, 0, 1` are rejected.

Validation results:

- Task 006 focused tests: **3 passed**.
- Complete `backend/tests` suite: **21 passed**.
- `compileall` for `backend/app` and `backend/tests`: passed.
- Safety scan of the new Task 006 test: no `MetaTrader5`, `mt5.order_send`, `order_send`, `OrderIntent` or `DOTOGlobal-Real` references.

## Current execution state

The paper execution path is deterministic and broker-independent. Provider-backed scheduling obtains B3 history through the OpenBB/yfinance boundary, evaluates the existing RSI paper policy, persists deterministic decision keys and skips duplicates.

The DEMO execution layer is implemented behind explicit authorization, reconciliation and fail-closed controls. Automatic scheduler-to-broker execution remains disconnected.

A controlled DOTO/MT5 DEMO validation was completed on 2026-09-11 using one explicitly authorized transaction:

- EURUSD BUY 0.01
- order `29453207`
- deal `28862296`
- position `29453207`
- open price `1.15960`

This transaction must **not** be repeated merely for verification. The existing ambiguous historical `SUBMITTED` record must remain pending and must never be automatically retried.

LIVE execution remains disabled.

## Current ML state

- Technical feature engineering: complete.
- Chronological train/validation/test split: complete.
- XGBoost training interface: complete.
- Out-of-sample evaluation: complete.
- Causal ML trading backtest: complete.
- Robustness audit: complete.
- Robustness gate: **not passed** because performance is not stable across all evaluated assets and assumptions.
- Causal pooled cross-asset experiment: implemented, research-only.
- Real-dataset training workflow: still pending.
- LSTM and RL experiments: still pending.

## Important open quality items

- Full integration suite against provider mocks.
- End-to-end training/backtest validation as a broader combined workflow.
- Security/dependency scan.
- Production deployment.

Task 006 does not close the broader `End-to-end training/backtest test` item because it validates backtesting only.

## Immediate development direction

The next candidate development stage is broker-independent validation of backtesting against realistic historical market data with:

1. leakage-safe historical data handling;
2. explicit train/test or evaluation boundaries where applicable;
3. realistic transaction-cost and slippage assumptions;
4. venue-specific cost calibration where data is available;
5. deterministic reproducibility;
6. no MT5, DOTO or broker submission.

This candidate stage must be scoped and inspected against the current repository before implementation. It must not be treated as complete merely because Task 006 passed.

## Safety constraints

- Never automatically submit financial trades.
- Never call `mt5.order_send()` during normal development or validation.
- Never create or modify DEMO/LIVE orders without fresh explicit user authorization for the exact transaction.
- Do not repeat the existing EURUSD DEMO transaction for verification.
- Ambiguous broker execution states fail closed and remain pending.
- Automatic scheduler-to-broker execution is disconnected.
- LIVE execution is disabled.
- Never expose or request passwords/secrets.
- Preserve local `.runtime/`, `AGENTS.md` and `scripts/diagnose_first_demo_attempt.py`.
- Never use `git reset --hard` or `git clean -fd`.
- Do not delete or overwrite local untracked operational files without explicit authorization.
- Recovery validation should use disposable temporary state when possible.

## Local repository state known at the last validation

The working tree was clean except for these intentionally preserved local untracked items:

```text
.runtime/
AGENTS.md
scripts/diagnose_first_demo_attempt.py
```

These files are not project defects and must be preserved.

## Handoff rule

Before starting the next task:

1. inspect the current repository state;
2. inspect the relevant implementation and existing tests;
3. define a narrowly scoped task and acceptance criteria;
4. implement only the demonstrated need;
5. run focused tests;
6. run the full backend suite when appropriate;
7. run compile/security checks;
8. update this context and the appropriate status/task documentation;
9. commit the result;
10. never weaken financial safety gates merely to make a test pass.
