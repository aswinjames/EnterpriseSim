"""Evaluation Layer interfaces (ARCH-04). Measures Worker quality.

No implementation. See ``sdk/evaluation/README.md`` and ``docs/architecture/04_evaluation_layer.md``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from sdk.objects import (
    CanonicalId,
    Confidence,
    EvaluationObject,
    ExecutionObject,
    PlanningObject,
)


@dataclass(frozen=True)
class GateResult:
    """Result of a single objective, deterministic gate (ADR-0015)."""

    gate: str
    passed: bool
    evidence: CanonicalId
    value: float | None = None
    threshold: float | None = None


@dataclass(frozen=True)
class RubricItemResult:
    """Result of one rubric item, possibly model-assisted (evidence required, ADR-0016)."""

    item: str
    result: str                       # pass | partial | fail
    evidence: CanonicalId
    judgment_confidence: Confidence


class ObjectiveGate(Protocol):
    """A deterministic, reproducible check (tests, coverage, security, dependency rule)."""

    name: str

    def run(self, execution: ExecutionObject) -> GateResult: ...


class Rubric(ABC):
    """A versioned, task-type scoring rubric (ADR-0018) owned with Quality Engineering."""

    id: str
    version: int

    @abstractmethod
    def objective_gates(self) -> Sequence[ObjectiveGate]: ...

    @abstractmethod
    def rubric_items(self) -> Sequence[str]: ...

    @abstractmethod
    def weights(self) -> Mapping[str, float]: ...


class Evaluator(ABC):
    """Scores an execution against its plan and CANON standards."""

    @abstractmethod
    def evaluate(
        self,
        execution: ExecutionObject,
        plan: PlanningObject,
        rubric: Rubric,
    ) -> EvaluationObject:
        """Objective-first, evidence-linked scoring with dual confidence (ADR-0015/0017)."""
        ...

    @abstractmethod
    def check_regressions(
        self,
        execution: ExecutionObject,
        against: Sequence[CanonicalId],
    ) -> bool:
        """Return True if a previously-fixed defect (referenced EXP-###) was reintroduced."""
        ...
