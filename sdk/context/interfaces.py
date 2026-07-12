"""Context Layer interfaces (ARCH-01). Ephemeral, per-task working memory.

No implementation. See ``sdk/context/README.md`` and ``docs/architecture/01_context_layer.md``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from sdk.objects import CanonicalId, Confidence, ContextObject, Provenance


@dataclass(frozen=True)
class TaskIntent:
    """Structured interpretation of a task, produced by Decision Intelligence."""

    task_ref: CanonicalId                 # e.g. "CHK-1421"
    goal: str
    constraints: Sequence[str]
    success_criteria: Sequence[str]
    apps: Sequence[CanonicalId]


@dataclass(frozen=True)
class Candidate:
    """A retrieval candidate from any source before selection."""

    ref: CanonicalId
    kind: str                             # knowledge | experience | code | state
    score: Confidence
    tokens: int
    payload: Mapping[str, object]


class Retriever(Protocol):
    """A source of candidates (knowledge, experience, live state). Composable."""

    def fetch(self, intent: TaskIntent) -> Sequence[Candidate]: ...


class BudgetPolicy(ABC):
    """Enforces the model's token/window budget *before* the Gateway call (ADR-0006)."""

    @abstractmethod
    def fits(self, selected: Sequence[Candidate], window_tokens: int, reserved_output: int) -> bool:
        ...

    @abstractmethod
    def evict(self, ranked: Sequence[Candidate], window_tokens: int, reserved_output: int) -> Sequence[Candidate]:
        """Return the subset that fits, recording drops for the dropped-candidate log."""
        ...


class ContextAssembler(ABC):
    """Assembles the right, minimal, sufficient ``ContextObject`` for one task."""

    @abstractmethod
    def assemble(self, intent: TaskIntent, retrievers: Sequence[Retriever]) -> ContextObject:
        """Retrieve, rank, select within budget, and compose a CTX-### with provenance."""
        ...

    @abstractmethod
    def enrich(self, context: ContextObject, extra: Sequence[Candidate]) -> ContextObject:
        """Iterative re-retrieval during reasoning (the Active self-loop)."""
        ...

    @abstractmethod
    def coverage_confidence(self, context: ContextObject) -> Confidence:
        """Estimate sufficiency of the assembled context (fed to Decision Intelligence)."""
        ...

    @abstractmethod
    def expire(self, context: ContextObject) -> Sequence[Provenance]:
        """Tear down the ephemeral context; hand provenance to Evaluation & Learning."""
        ...
