# Decision observability

InvestmentAI records the evidence and gate outcome for each evaluated decision before any execution layer is considered.

## Record

A `DecisionRecord` contains:

- deterministic decision identifier;
- symbol and UTC timestamp;
- fused direction, score and confidence;
- allowed/blocked outcome;
- environment (`paper`, `demo`, or `live`);
- each contributing source and its direction/confidence/reference;
- risk-gate reasons.

The record is immutable and serializable. It deliberately contains no credentials and has no broker dependency.

## Boundary

`evidence -> fusion -> risk gate -> DecisionRecord -> execution boundary`

A record with `allowed=false` remains an auditable decision and must not be interpreted as an order. Persistence and reconciliation will be connected in a later step so that failed or duplicated execution cannot silently change the audit trail.

## Minimum evidence

TradingView is represented as one independent source. Model, fundamentals, Doto and Trading Central can be represented through the same evidence contract as their adapters become active. No provider is granted implicit execution authority.
