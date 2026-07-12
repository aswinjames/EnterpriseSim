"""Canonical ECL object contracts (structural, no implementation).

These :class:`typing.Protocol` definitions are the in-code mirror of the JSON Schema
documents in ``schemas/`` (``KnowledgeObject``, ``ContextObject``, ...). They exist so
that the abstract interfaces in each SDK module can be typed precisely without
depending on any concrete data class or serialization library.

Rules (enforced by ADR-0004/0005/0006/0022):

* Every object carries a globally unique, never-reused ``id`` (see ``CANON.md`` §6).
* ``KnowledgeObject`` is immutable once published; new facts are new versions.
* ``ExperienceObject`` is append-only.
* ``ContextObject`` is ephemeral and must never be persisted as durable truth.
* Cross-references between objects use canonical IDs, preserving referential integrity.

Nothing here is implemented. Protocols describe *shape and intent only*.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

# ---------------------------------------------------------------------------
# Common value types (declared as aliases; formalized in schemas/common.schema.json)
# ---------------------------------------------------------------------------

#: An ECL identifier such as ``"KN-045"``, ``"CTX-0118"``, ``"PR-0312"``.
CanonicalId = str

#: An ISO-8601 timestamp string, e.g. ``"2026-06-30T12:00:00Z"``.
Timestamp = str

#: A confidence value in the closed interval [0.0, 1.0] (see RFC-0009).
Confidence = float


@runtime_checkable
class Provenance(Protocol):
    """Where a piece of information came from and why it was included."""

    source: CanonicalId
    kind: str            # knowledge | experience | code | state | ...
    reason: str          # human-readable rationale
    score: Confidence    # relevance/authority score at selection time


@runtime_checkable
class ECLObject(Protocol):
    """Common shape shared by every persisted ECL artifact."""

    id: CanonicalId
    schema_version: str
    created_at: Timestamp
    metadata: Mapping[str, Any]


# ---------------------------------------------------------------------------
# Durable memory
# ---------------------------------------------------------------------------

@runtime_checkable
class KnowledgeObject(ECLObject, Protocol):
    """Durable, governed enterprise truth (``KN-###``). Immutable once published."""

    title: str
    body: str
    owner_team: CanonicalId
    canon_refs: Sequence[CanonicalId]
    sensitivity: str                 # public | internal | pci | pii
    authority: str                   # canon | owner-approved | provisional
    version: int
    status: str                      # drafted | published | stale | deprecated
    relations: Mapping[str, Sequence[CanonicalId]]


@runtime_checkable
class ExperienceObject(ECLObject, Protocol):
    """Accumulated, situation-linked lesson (``EXP-###``). Append-only."""

    title: str
    situation: Mapping[str, Any]     # task_type, apps, failure_class, ...
    lesson: str
    evidence: Mapping[str, CanonicalId]   # origin_execution, evaluation, reflection
    value: Mapping[str, Any]         # application_frequency, outcome_lift, ...
    status: str                      # captured | retrievable | promotion_candidate | promoted | downweighted


# ---------------------------------------------------------------------------
# Ephemeral memory
# ---------------------------------------------------------------------------

@runtime_checkable
class ContextObject(ECLObject, Protocol):
    """Ephemeral, per-task working set (``CTX-###``). Never durable truth."""

    task: Mapping[str, Any]
    intent_ref: CanonicalId                 # PLAN-### / decision intent
    model_budget: Mapping[str, int]
    included: Sequence[Provenance]
    excluded: Sequence[Provenance]
    coverage_confidence: Confidence
    signals: Mapping[str, float]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

@runtime_checkable
class PlanningObject(ECLObject, Protocol):
    """An explicit, testable plan (``PLAN-###``)."""

    task: CanonicalId
    intent: str
    success_criteria: Sequence[str]
    steps: Sequence[Mapping[str, Any]]
    rollback: str
    risk_tier: int
    applied_experience: Sequence[CanonicalId]
    routing: Mapping[str, Any]


@runtime_checkable
class DecisionObject(ECLObject, Protocol):
    """A single control decision made by Decision Intelligence."""

    plan: CanonicalId
    choice: str                      # proceed | re-retrieve | replan | retry | escalate | abort
    rationale: str
    fused_confidence: Confidence
    inputs: Mapping[str, Confidence]  # per-layer confidences that were fused


@runtime_checkable
class WorkerDecision(DecisionObject, Protocol):
    """A decision as emitted onto the decision trace of a concrete Worker run."""

    worker: str
    trace_seq: int


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

@runtime_checkable
class WorkerArtifact(ECLObject, Protocol):
    """A concrete artifact produced by execution (PR, test run, comment, file)."""

    artifact_type: str               # pull_request | test_run | comment | file | incident_action
    ref: CanonicalId                 # e.g. PR-0312, TR-0442
    uri: str


@runtime_checkable
class ExecutionObject(ECLObject, Protocol):
    """The record of a plan step (or full plan) being executed via tools."""

    plan: CanonicalId
    step: int
    tool: str
    directives: Mapping[str, Any]
    artifacts: Sequence[WorkerArtifact]
    status: str                      # succeeded | failed | partial


@runtime_checkable
class WorkerExecution(ExecutionObject, Protocol):
    """Execution record scoped to a concrete Worker run (adds worker/run identity)."""

    worker: str
    run_id: CanonicalId


# ---------------------------------------------------------------------------
# Judgment & improvement
# ---------------------------------------------------------------------------

@runtime_checkable
class EvaluationObject(ECLObject, Protocol):
    """Scored, evidence-linked judgment of an execution (``EVAL-###``)."""

    execution: CanonicalId
    plan: CanonicalId
    rubric: Mapping[str, Any]        # id + version
    objective: Sequence[Mapping[str, Any]]
    rubric_items: Sequence[Mapping[str, Any]]
    verdict: Mapping[str, Any]       # outcome, score, outcome_confidence, judgment_confidence


@runtime_checkable
class ReflectionObject(ECLObject, Protocol):
    """Root-cause reasoning about an evaluated outcome (``REF-###``)."""

    evaluation: CanonicalId
    execution: CanonicalId
    plan: CanonicalId
    what_happened: str
    root_cause: Mapping[str, Any]    # category, detail, confidence
    lessons: Sequence[Mapping[str, Any]]
    policy_updates: Sequence[Mapping[str, Any]]
    loop_closed_by: CanonicalId | None


@runtime_checkable
class LearningEvent(ECLObject, Protocol):
    """A discrete change to durable memory or policy emitted by the Learning Engine."""

    kind: str                        # experience_written | promotion_proposed | policy_updated | pattern_detected
    source_reflection: CanonicalId
    target: CanonicalId              # the KN/EXP/policy affected
    payload: Mapping[str, Any]
    loop_closed: bool
