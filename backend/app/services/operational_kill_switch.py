from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class KillSwitchState:
    active: bool
    reason: str | None = None
    activated_at: str | None = None
    operator: str | None = None


class OperationalKillSwitch:
    """Fail-closed operational stop state.

    The switch is intentionally independent from model signals. A future
    execution adapter may consume this state, but this service never submits
    or cancels orders itself.
    """

    def __init__(self, state: KillSwitchState | None = None) -> None:
        self._state = state or KillSwitchState(active=False)

    @property
    def state(self) -> KillSwitchState:
        return self._state

    def activate(self, reason: str, *, operator: str = "system", now: datetime | None = None) -> KillSwitchState:
        reason = reason.strip()
        operator = operator.strip()
        if not reason:
            raise ValueError("kill switch reason is required")
        if not operator:
            raise ValueError("kill switch operator is required")
        timestamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        self._state = KillSwitchState(True, reason, timestamp, operator)
        return self._state

    def reset(self, *, operator: str, now: datetime | None = None) -> KillSwitchState:
        operator = operator.strip()
        if not operator:
            raise ValueError("kill switch reset operator is required")
        self._state = KillSwitchState(False, None, None, operator)
        return self._state

    def allows_operation(self) -> bool:
        return not self._state.active

    def require_clear(self) -> None:
        if self._state.active:
            detail = self._state.reason or "no reason supplied"
            raise PermissionError(f"operation blocked by kill switch: {detail}")
