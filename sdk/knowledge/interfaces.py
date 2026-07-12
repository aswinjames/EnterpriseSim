"""Knowledge Layer interfaces (ARCH-02). Durable enterprise truth.

No implementation. See ``sdk/knowledge/README.md`` and ``docs/architecture/02_knowledge_layer.md``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from sdk.objects import CanonicalId, Confidence, KnowledgeObject


@dataclass(frozen=True)
class KnowledgeQuery:
    """A request for knowledge candidates, driven by task intent."""

    text: str
    filters: Mapping[str, str]            # e.g. {"app": "APP-003", "sensitivity": "internal"}
    top_k: int = 20
    modes: Sequence[str] = ("semantic", "keyword", "graph")


@dataclass(frozen=True)
class KnowledgeCandidate:
    """A retrieved knowledge item with scoring metadata."""

    object: KnowledgeObject
    relevance: Confidence
    authority: Confidence
    freshness: Confidence


class KnowledgeIndex(Protocol):
    """Pluggable index backend (vector / lexical / graph). See RFC-0005, RFC-0006."""

    def upsert(self, obj: KnowledgeObject) -> None: ...
    def search(self, query: KnowledgeQuery) -> Sequence[KnowledgeCandidate]: ...
    def neighbors(self, node: CanonicalId, relation: str) -> Sequence[CanonicalId]: ...


class KnowledgeStore(ABC):
    """System of record for governed ``KnowledgeObject`` items (immutable once published)."""

    @abstractmethod
    def get(self, knowledge_id: CanonicalId) -> KnowledgeObject:
        """Return a published knowledge object by ID (ADR-0004: immutable)."""
        ...

    @abstractmethod
    def publish(self, draft: KnowledgeObject) -> KnowledgeObject:
        """Publish an approved draft, assigning it a version. Never mutates prior versions."""
        ...

    @abstractmethod
    def deprecate(self, knowledge_id: CanonicalId, superseded_by: CanonicalId | None) -> None:
        """Mark deprecated; retain for history (never hard-delete)."""
        ...

    @abstractmethod
    def is_stale(self, knowledge_id: CanonicalId) -> bool:
        """Report freshness-SLA breach (ADR-0046)."""
        ...


class KnowledgeRetriever(ABC):
    """Serves ranked candidates to the Context Layer using hybrid retrieval (ADR-0019)."""

    @abstractmethod
    def retrieve(self, query: KnowledgeQuery) -> Sequence[KnowledgeCandidate]:
        """Return authority/freshness/relevance-scored candidates."""
        ...


class KnowledgeGovernance(ABC):
    """Approves promotions and resolves contradictions. See RFC-0018."""

    @abstractmethod
    def review(self, draft: KnowledgeObject) -> bool:
        """Return True if the draft may be published."""
        ...

    @abstractmethod
    def resolve_contradiction(self, a: CanonicalId, b: CanonicalId) -> CanonicalId:
        """Return the ID that wins; canon breaks ties (CANON-001)."""
        ...
