"""Experience Layer interfaces (ARCH-03). Accumulated lessons, append-only.

No implementation. See ``sdk/experience/README.md`` and ``docs/architecture/03_experience_layer.md``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping, Sequence

from sdk.objects import CanonicalId, Confidence, ExperienceObject


@dataclass(frozen=True)
class SituationDescriptor:
    """Structural (not merely semantic) description of a task situation (ADR-0019)."""

    task_type: str
    apps: Sequence[CanonicalId]
    failure_class: str | None = None
    extra: Mapping[str, object] | None = None


@dataclass(frozen=True)
class ExperienceMatch:
    """A retrieved experience with applicability + value scoring."""

    object: ExperienceObject
    applicability: Confidence
    value: Confidence


class ExperienceStore(ABC):
    """Append-only store of ``ExperienceObject`` lessons (ADR-0005)."""

    @abstractmethod
    def append(self, experience: ExperienceObject) -> ExperienceObject:
        """Add a new lesson (never overwrites; reinforcement adds evidence)."""
        ...

    @abstractmethod
    def reinforce(self, experience_id: CanonicalId, evidence: CanonicalId) -> None:
        """Attach corroborating evidence and update value scores."""
        ...

    @abstractmethod
    def downweight(self, experience_id: CanonicalId, contradiction: CanonicalId) -> None:
        """Reduce relevance on contradiction; retain history (ADR-0047)."""
        ...

    @abstractmethod
    def promotion_candidates(self) -> Sequence[ExperienceObject]:
        """Lessons whose value + corroboration cross the promotion bar (RFC-0018)."""
        ...


class ExperienceRetriever(ABC):
    """Serves situationally-applicable lessons to the Context Layer."""

    @abstractmethod
    def retrieve(self, situation: SituationDescriptor, top_k: int = 10) -> Sequence[ExperienceMatch]:
        """Return lessons ranked by structural applicability and measured value."""
        ...
