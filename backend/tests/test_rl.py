import numpy as np
import pytest

from app.services.rl import (
    RLConfig,
    chronological_rl_split,
    evaluate_greedy,
    greedy_actions,
    train_tabular_q,
)


def test_chronological_split_purges_boundary():
    (train_s, train_r), (test_s, test_r) = chronological_rl_split(
        list(range(10)), np.arange(10, dtype=float), train_ratio=0.6, purge=2
    )
    assert train_s.tolist() == [0, 1, 2, 3, 4, 5]
    assert test_s.tolist() == [8, 9]
    assert train_r.tolist() == [0, 1, 2, 3, 4, 5]
    assert test_r.tolist() == [8, 9]


def test_q_learning_is_deterministic_with_seed():
    states = [0, 1, 0, 1, 0, 1]
    returns = [0.0, 0.02, -0.01, 0.02, -0.01, 0.02]
    cfg = RLConfig(episodes=10, seed=7)
    a = train_tabular_q(states, returns, cfg, transaction_cost=0.001)
    b = train_tabular_q(states, returns, cfg, transaction_cost=0.001)
    assert a == b
    assert len(a.train_rewards) == 10


def test_unseen_state_is_neutral_and_evaluation_is_finite():
    states = [0, 0, 1, 1, 0, 1]
    returns = [0.0, 0.01, 0.01, -0.01, 0.02, 0.01]
    result = train_tabular_q(states, returns, RLConfig(episodes=5))
    actions = greedy_actions([99, 0], result)
    assert actions[0] == 0
    value = evaluate_greedy([99, 0, 1, 0], [0.0, 0.01, -0.01, 0.02], result)
    assert np.isfinite(value)


def test_invalid_inputs_fail_closed():
    with pytest.raises(ValueError):
        chronological_rl_split([0, 1, 2], [0.0, 0.1, 0.2], purge=3)
    with pytest.raises(ValueError):
        train_tabular_q([0, 1], [0.0, float("nan")])
