"""Enterprise AI Worker interfaces. Domain-agnostic core, edge specialization.

No implementation. See ``sdk/workers/README.md`` and ``docs/architecture/07_architecture.md``.

A Worker type is defined by FOUR specializations over the shared ECL core (ADR-0024/0025):
knowledge domains, tools, rubrics, policies. Everything else is inherited unchanged.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping, Sequence

from sdk.decision.interfaces import Orchestrator
from sdk.objects import CanonicalId, EvaluationObject, WorkerExecution


@dataclass(frozen=True)
class WorkerSpec:
    """The four-axis specialization that defines a Worker type (ADR-0025)."""

    name: str                              # e.g. "qa-worker", "privacy-worker"
    knowledge_domains: Sequence[str]       # which KN corpora are in scope
    tools: Sequence[str]                   # tool names the Worker may act through
    rubrics: Sequence[str]                 # evaluation rubric ids
    policies: Sequence[str]                # guardrail policy ids (PCI, fairness, SoD, ...)
    default_routing: Mapping[str, object]  # model-routing hints


@dataclass(frozen=True)
class RunResult:
    """The outcome of a single Worker run."""

    run_id: CanonicalId
    status: str                            # completed | escalated | aborted
    execution: WorkerExecution
    evaluation: EvaluationObject | None


class WorkerRuntime(ABC):
    """Wires the shared ECL components together for a specialized Worker."""

    @abstractmethod
    def bind(self, spec: WorkerSpec) -> Orchestrator:
        """Bind knowledge/tools/rubrics/policies and return a ready Orchestrator."""
        ...


class Worker(ABC):
    """A domain-agnostic Enterprise AI Worker. Specialized only via its ``WorkerSpec``."""

    spec: WorkerSpec

    @abstractmethod
    def run(self, trigger: CanonicalId) -> RunResult:
        """Execute one task end to end through the ECL loop (ARCH-07)."""
        ...

    @abstractmethod
    def replay(self, run_id: CanonicalId) -> RunResult:
        """Deterministically re-execute a past run for debugging/benchmarking (RFC-0024)."""
        ...
