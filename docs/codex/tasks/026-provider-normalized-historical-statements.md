# Task 026 — Provider-normalized historical statements

**Status:** IN PROGRESS

## Objective

Create a provider-neutral, deterministic normalization boundary for historical fundamental statements so downstream valuation and ROIC work does not depend on provider-specific field names.

## Scope

- normalize annual or other explicitly identified statement periods;
- normalize common aliases for revenue, operating income, net income, EBITDA, assets, debt, cash, equity, operating cash flow and capex;
- preserve symbol, period end and statement type provenance;
- sort normalized statements deterministically by period;
- fail closed on missing period provenance or non-finite numeric values;
- remain calculation/data-normalization only, without scoring or investment recommendations.

## Non-goals

- no provider ranking;
- no fundamental score;
- no ROIC calculation;
- no DCF/Gordon assumption changes;
- no trading/execution integration.

## Acceptance criteria

1. Provider-specific aliases normalize into a stable immutable statement schema. **PENDING**
2. Symbol, period and statement type provenance are retained. **PENDING**
3. Output ordering is deterministic by period. **PENDING**
4. Missing period provenance and non-finite numeric values fail closed. **PENDING**
5. Existing valuation behavior is unchanged. **PENDING**
6. Backend tests and compilation are green. **PENDING**
7. No investment-ranking or execution authority is introduced. **PENDING**
