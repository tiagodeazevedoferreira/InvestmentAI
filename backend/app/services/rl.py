from __future__ import annotations

class RLPolicy:
    """Adapter boundary for TradeMaster-inspired RL policies.

    The project intentionally does not vendor TradeMaster. A policy receives an
    observation and returns target weights/actions. Optional RL dependencies can
    be plugged in later without coupling the core engine to one framework.
    """
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
