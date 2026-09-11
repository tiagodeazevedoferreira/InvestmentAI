from __future__ import annotations

from typing import Any, Callable, Mapping

from .controlled_demo_execution import ControlledDemoExecutionResult, ControlledDemoExecutionService
from .scheduler_demo_bridge import DemoPromotionPlan


class SchedulerDemoExecutionBlocked(PermissionError):
    """Raised when a scheduler promotion is not explicitly authorized."""


class SchedulerDemoExecutionAdapter:
    """Explicit handoff from a scheduler DEMO plan to the DEMO execution layer.

    This adapter is intentionally not part of the scheduler runtime. It accepts
    an already-created ``DemoPromotionPlan`` and requires an independent,
    explicit execution authorization before delegating to the controlled DEMO
    service. It owns no broker and never calls ``order_send`` itself.
    """

    def __init__(self, execution_service: ControlledDemoExecutionService) -> None:
        self.execution_service = execution_service

    def execute(
        self,
        plan: DemoPromotionPlan,
        *,
        execution_authorized: bool = False,
        internal_before: Mapping[str, Any],
        internal_after_provider: Callable[[], Mapping[str, Any]],
    ) -> ControlledDemoExecutionResult:
        if plan.status != "ready" or plan.intent is None:
            raise SchedulerDemoExecutionBlocked(
                "scheduler DEMO plan is not ready for execution"
            )
        if not execution_authorized:
            raise SchedulerDemoExecutionBlocked(
                "scheduler-originated DEMO execution requires explicit independent authorization"
            )

        return self.execution_service.execute(
            plan.intent,
            internal_before=internal_before,
            internal_after_provider=internal_after_provider,
        )
