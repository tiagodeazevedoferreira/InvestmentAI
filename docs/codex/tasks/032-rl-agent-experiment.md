# Task 032 — RL agent experiment

## Objective
Add a reproducible, dependency-light reinforcement-learning experiment boundary for directional trading research without changing production models, execution policy, risk limits or promotion authority.

## Scope
- Provide a chronological, purge-aware train/evaluation split.
- Provide a deterministic tabular Q-learning research agent with explicit actions, learning rate, discount factor, exploration schedule and seed.
- Model actions as target positions and include an explicit transaction-cost penalty in the research reward.
- Evaluate the learned policy only on a separately supplied held-out sequence.
- Keep the existing RLPolicy adapter boundary and NoOp policy compatible.

## Validation
- Chronological split preserves order and purges the train/evaluation boundary.
- Q-learning is deterministic for a fixed seed/configuration.
- Unseen evaluation states fail safe to a neutral action.
- Invalid and non-finite inputs fail closed.
- The implementation has no broker, order, execution, risk-gate or model-promotion side effects.

## Non-goals
- No profitability or superiority claim.
- No live or DEMO execution.
- No automatic model selection or promotion.
- No change to the existing XGBoost/LSTM production or research pipelines.
- No mandatory RL framework dependency.

## Limitations
This is a controlled research primitive, not a production trading agent. Tabular state representations can discard information, hyperparameters are engineering defaults, and results are sensitive to market regime, reward definition, transaction-cost assumptions and sample size.
