"""Planner interfaces (ARCH-06, Planning). Produces explicit, testable plans.

No implementation. See ``sdk/planner/README.md`` and ``docs/architecture/06_decision_intelligence.md``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from sdk.context.interfaces import TaskIntent
from sdk.objects import CanonicalId, ContextObject, PlanningObject


@dataclass(frozen=True)
class PlanCheck:
    """The result of validating a plan against CANON standards."""

    ok: bool
    violations: Sequence[str]             # e.g. ["missing rollback plan", "reverse dependency"]


class Planner(ABC):
    """Turns intent + context into an explicit ``PlanningObject`` (PLAN-###)."""

    @abstractmethod
    def plan(self, intent: TaskIntent, context: ContextObject) -> PlanningObject:
        """Produce an ordered plan with success criteria, tests, rollback and risk tier."""
        ...

    @abstractmethod
    def replan(self, previous: PlanningObject, reason: str, context: ContextObject) -> PlanningObject:
        """Revise a plan invalidated mid-task, preserving lineage to the previous plan."""
        ...


class PlanValidator(ABC):
    """Validates a plan against CANON-001 §4/§7/§8 before execution."""

    @abstractmethod
    def validate(self, plan: PlanningObject) -> PlanCheck:
        """Check rollback presence, risk-tier approvals, dependency direction, test coverage."""
        ...

    @abstractmethod
    def required_approvals(self, plan: PlanningObject) -> int:
        """Approvals required by the plan's risk tier (CANON-001 §7)."""
        ...
