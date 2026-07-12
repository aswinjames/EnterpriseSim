"""Decision Intelligence interfaces (ARCH-06). The sole orchestrator.

No implementation. See ``sdk/decision/README.md`` and ``docs/architecture/06_decision_intelligence.md``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from sdk.context.interfaces import TaskIntent
from sdk.objects import (
    CanonicalId,
    Confidence,
    ContextObject,
    DecisionObject,
    EvaluationObject,
    PlanningObject,
)


class Control(str, Enum):
    """Control decisions available to the orchestrator (ARCH-06 lifecycle)."""

    PROCEED = "proceed"
    RE_RETRIEVE = "re-retrieve"
    REPLAN = "replan"
    RETRY = "retry"
    ESCALATE = "escalate"
    ABORT = "abort"


@dataclass(frozen=True)
class PolicyVerdict:
    """Outcome of a guardrail check performed before any execution."""

    allowed: bool
    reason: str
    requires_human: bool = False


class ConfidencePolicy(ABC):
    """Fuses per-layer confidences into an autonomy decision (ADR-0013/0014, RFC-0009)."""

    @abstractmethod
    def fuse(self, inputs: Mapping[str, Confidence]) -> Confidence:
        """Combine context/knowledge/experience/evaluation confidences into one value."""
        ...

    @abstractmethod
    def control_for(self, fused: Confidence, risk_tier: int) -> Control:
        """Map fused confidence + risk tier to a control decision (risk-adaptive autonomy)."""
        ...


class PolicyGuard(ABC):
    """Enforces guardrails *before* execution (ADR-0041): approvals, PCI, SoD, fairness."""

    @abstractmethod
    def check(self, plan: PlanningObject, context: ContextObject) -> PolicyVerdict:
        ...


class Orchestrator(ABC):
    """Interprets intent, drives the loop, routes models, and records the decision trace."""

    @abstractmethod
    def interpret(self, trigger: CanonicalId, context_hint: Mapping[str, object]) -> TaskIntent:
        """Turn a task trigger into structured intent."""
        ...

    @abstractmethod
    def decide(
        self,
        plan: PlanningObject,
        context: ContextObject,
        evaluation: EvaluationObject | None,
    ) -> DecisionObject:
        """Produce the next control decision with fused confidence and rationale."""
        ...

    @abstractmethod
    def trace(self, run_id: CanonicalId) -> Sequence[DecisionObject]:
        """Return the immutable decision trace for a run (ADR-0021)."""
        ...
