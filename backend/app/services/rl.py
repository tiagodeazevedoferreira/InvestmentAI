from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class RLConfig:
    actions: tuple[int, ...] = (-1, 0, 1)
    alpha: float = 0.1
    gamma: float = 0.95
    epsilon: float = 0.1
    epsilon_decay: float = 0.99
    min_epsilon: float = 0.01
    episodes: int = 25
    seed: int = 42

    def __post_init__(self) -> None:
        if not self.actions or len(set(self.actions)) != len(self.actions):
            raise ValueError("actions must be non-empty and unique")
        if not 0 < self.alpha <= 1 or not 0 <= self.gamma <= 1:
            raise ValueError("alpha/gamma out of range")
        if not 0 <= self.epsilon <= 1:
            raise ValueError("epsilon out of range")
        if not 0 < self.epsilon_decay <= 1:
            raise ValueError("epsilon_decay out of range")
        if not 0 <= self.min_epsilon <= self.epsilon:
            raise ValueError("min_epsilon out of range")
        if self.episodes <= 0:
            raise ValueError("episodes must be positive")


@dataclass(frozen=True)
class RLResult:
    q_table: dict[int, tuple[float, ...]]
    train_rewards: tuple[float, ...]
    epsilon: float


class RLPolicy:
    name = "abstract-rl"

    def act(self, observation: dict) -> dict:
        raise NotImplementedError


class NoOpRLPolicy(RLPolicy):
    name = "noop"

    def act(self, observation: dict) -> dict:
        symbols = observation.get("symbols", [])
        if not symbols:
            return {}
        weight = 1.0 / len(symbols)
        return {s: weight for s in symbols}


def chronological_rl_split(states: Sequence[int], returns: Sequence[float], train_ratio: float = 0.7, purge: int = 1):
    s = np.asarray(states)
    r = np.asarray(returns, dtype=float)
    if s.ndim != 1 or r.ndim != 1 or len(s) != len(r):
        raise ValueError("states and returns must be one-dimensional and aligned")
    if len(s) < 4:
        raise ValueError("at least four observations are required")
    if not 0 < train_ratio < 1 or purge < 0:
        raise ValueError("invalid split configuration")
    if not np.isfinite(r).all():
        raise ValueError("returns must be finite")
    split = max(1, int(len(s) * train_ratio))
    test_start = split + purge
    if test_start >= len(s):
        raise ValueError("purge leaves no evaluation observations")
    return (s[:split], r[:split]), (s[test_start:], r[test_start:])


def _validate(states: np.ndarray, returns: np.ndarray) -> None:
    if len(states) != len(returns) or len(states) < 2:
        raise ValueError("aligned episode with at least two observations required")
    if not np.isfinite(returns).all():
        raise ValueError("returns must be finite")


def train_tabular_q(states: Sequence[int], returns: Sequence[float], config: RLConfig | None = None, transaction_cost: float = 0.0) -> RLResult:
    cfg = config or RLConfig()
    s = np.asarray(states)
    r = np.asarray(returns, dtype=float)
    _validate(s, r)
    if not np.isfinite(transaction_cost) or transaction_cost < 0:
        raise ValueError("transaction_cost must be finite and non-negative")
    q = {int(state): np.zeros(len(cfg.actions), dtype=float) for state in np.unique(s)}
    rng = np.random.default_rng(cfg.seed)
    epsilon = cfg.epsilon
    rewards = []
    for _ in range(cfg.episodes):
        total = 0.0
        previous = 0
        for t in range(len(s) - 1):
            state, next_state = int(s[t]), int(s[t + 1])
            index = int(rng.integers(len(cfg.actions))) if rng.random() < epsilon else int(np.argmax(q[state]))
            position = cfg.actions[index]
            reward = position * float(r[t + 1]) - transaction_cost * abs(position - previous)
            target = reward + cfg.gamma * float(np.max(q[next_state]))
            q[state][index] += cfg.alpha * (target - q[state][index])
            total += reward
            previous = position
        rewards.append(float(total))
        epsilon = max(cfg.min_epsilon, epsilon * cfg.epsilon_decay)
    return RLResult({state: tuple(values.tolist()) for state, values in q.items()}, tuple(rewards), epsilon)


def greedy_actions(states: Sequence[int], result: RLResult, config: RLConfig | None = None) -> tuple[int, ...]:
    cfg = config or RLConfig()
    actions = []
    for state in states:
        row = result.q_table.get(int(state))
        actions.append(0 if row is None else int(cfg.actions[int(np.argmax(row))]))
    return tuple(actions)


def evaluate_greedy(states: Sequence[int], returns: Sequence[float], result: RLResult, config: RLConfig | None = None, transaction_cost: float = 0.0) -> float:
    cfg = config or RLConfig()
    s = np.asarray(states)
    r = np.asarray(returns, dtype=float)
    _validate(s, r)
    if not np.isfinite(transaction_cost) or transaction_cost < 0:
        raise ValueError("transaction_cost must be finite and non-negative")
    actions = greedy_actions(s, result, cfg)
    previous = 0
    total = 0.0
    for t in range(1, len(actions)):
        total += actions[t - 1] * float(r[t]) - transaction_cost * abs(actions[t - 1] - previous)
        previous = actions[t - 1]
    return float(total)
