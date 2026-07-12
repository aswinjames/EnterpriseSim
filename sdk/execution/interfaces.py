"""Execution Runtime interfaces. The Worker acts on the enterprise via tools.

No implementation. See ``sdk/execution/README.md`` and ``docs/architecture/07_architecture.md``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from sdk.objects import CanonicalId, ExecutionObject, PlanningObject, WorkerArtifact


@dataclass(frozen=True)
class ToolSpec:
    """Declarative description of a tool a Worker may act through (RFC-0013)."""

    name: str
    description: str
    input_schema: Mapping[str, object]   # JSON Schema of arguments
    side_effects: str                    # none | read | write | irreversible
    least_privilege_scope: str           # ADR-0042


@dataclass(frozen=True)
class ToolResult:
    """The outcome of a single tool invocation."""

    ok: bool
    output: Mapping[str, object]
    artifacts: Sequence[WorkerArtifact]
    error: str | None = None


class Tool(Protocol):
    """A capability the Worker can invoke (GitHub, Jira, CI, TestRail, ...)."""

    spec: ToolSpec

    def invoke(self, args: Mapping[str, object]) -> ToolResult: ...


class ToolRegistry(ABC):
    """Resolves the tools available to a Worker, subject to least-privilege policy."""

    @abstractmethod
    def available(self, worker: str) -> Sequence[ToolSpec]: ...

    @abstractmethod
    def get(self, name: str) -> Tool: ...


class ExecutionRuntime(ABC):
    """Carries out plan directives via tools, producing execution records & artifacts."""

    @abstractmethod
    def execute_step(self, plan: PlanningObject, step: int) -> ExecutionObject:
        """Execute a single plan step idempotently (ADR-0045)."""
        ...

    @abstractmethod
    def rollback(self, plan: PlanningObject) -> ExecutionObject:
        """Invoke the plan's rollback strategy (e.g. disable a feature flag)."""
        ...

    @abstractmethod
    def artifacts(self, run_id: CanonicalId) -> Sequence[WorkerArtifact]:
        """Return all artifacts produced during a run (PR-####, TR-####, ...)."""
        ...
