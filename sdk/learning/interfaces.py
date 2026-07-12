"""Learning Engine interfaces (ARCH-05). Reflection + learning, outside the model.

No implementation. See ``sdk/learning/README.md`` and ``docs/architecture/05_learning_engine.md``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping, Sequence

from sdk.objects import (
    CanonicalId,
    Confidence,
    ContextObject,
    EvaluationObject,
    ExperienceObject,
    LearningEvent,
    PlanningObject,
    ReflectionObject,
)


@dataclass(frozen=True)
class RootCause:
    """A diagnosed cause with confidence (ADR-0035: root cause, not symptom)."""

    category: str                     # missing_knowledge | dropped_context | flawed_plan | tool_error | ...
    detail: str
    confidence: Confidence


class Reflector(ABC):
    """Produces root-cause ``ReflectionObject``s grounded in evaluation evidence."""

    @abstractmethod
    def reflect(
        self,
        evaluation: EvaluationObject,
        plan: PlanningObject,
        context: ContextObject,
    ) -> ReflectionObject:
        """Explain *why* the outcome occurred; inspect the dropped-candidate log first."""
        ...

    @abstractmethod
    def diagnose(self, reflection: ReflectionObject) -> RootCause: ...


class PromotionPolicy(ABC):
    """Decides when an experience is ready to be proposed for promotion to Knowledge."""

    @abstractmethod
    def ready(self, experience: ExperienceObject) -> bool:
        """Require repeated corroboration before promotion (ADR-0036)."""
        ...


class LearningEngine(ABC):
    """Converts evaluated outcomes into durable memory and policy changes."""

    @abstractmethod
    def distill(self, reflection: ReflectionObject) -> ExperienceObject:
        """Turn a reflection into a reusable, situation-linked lesson."""
        ...

    @abstractmethod
    def emit(self, reflection: ReflectionObject) -> Sequence[LearningEvent]:
        """Emit experience-written / promotion-proposed / policy-updated / pattern events."""
        ...

    @abstractmethod
    def loop_closed(self, learning_event: CanonicalId) -> bool:
        """Return True once a lesson has measurably changed a later execution (ADR-0034)."""
        ...

    @abstractmethod
    def systemic_patterns(self, window: Mapping[str, object]) -> Sequence[LearningEvent]:
        """Detect organization-level lessons across many executions."""
        ...
