# Extension Guide — Implementing and Extending a Layer

> How to provide a concrete implementation of any ECL component. The SDK
> ([`../../sdk/`](../../sdk/)) is **interfaces only** — every method body is `...`. Your job as
> an implementer is to honor the contract in each module's `interfaces.py`, respect the
> invariants in `CANON-001` and `ARCH-01`…`07`, and validate what you emit against the JSON
> Schemas in [`../../schemas/`](../../schemas/).

This guide gives a concrete recipe per module. For plugin **packaging and registration** (entry
points, discovery, versioning), read [`plugin-guide.md`](plugin-guide.md). For building a whole
Worker, read [`worker-guide.md`](worker-guide.md).

---

## The universal pattern

Every extension follows the same three steps:

1. **Pick the interface.** Each module exposes abstract bases (`abc.ABC`) you subclass and
   structural types (`typing.Protocol`) you satisfy by shape.
2. **Implement the contract.** Fill in method bodies. Produce canonical objects
   (`sdk.objects`) that validate against the matching schema, carry a globally unique
   never-reused `id`, and cross-reference other objects by canonical ID (`ADR-0023`).
3. **Register and test.** Register via plugin entry points (`RFC-0027`); validate emitted
   objects against the schemas (see [`schema-guide.md`](schema-guide.md)) and against the
   invariants below.

```python
# ABCs are subclassed; Protocols are satisfied structurally (no inheritance required).
from abc import ABC              # KnowledgeStore, ContextAssembler, Evaluator, ...
from typing import Protocol      # KnowledgeIndex, Retriever, Tool, ObjectiveGate, ModelProvider
```

Two invariants apply to **every** object you emit (`sdk/objects.py`, `ADR-0004/0005/0006/0022`):

- It carries a globally unique, never-reused `id`, plus `schema_version` and `created_at`.
- `KnowledgeObject` is immutable once published; `ExperienceObject` is append-only;
  `ContextObject` is ephemeral and must never be persisted as durable truth.

---

## `sdk.knowledge` — Knowledge Layer (`ARCH-02`)

**Interfaces:** `KnowledgeStore` (ABC), `KnowledgeRetriever` (ABC), `KnowledgeGovernance` (ABC),
`KnowledgeIndex` (Protocol); value types `KnowledgeQuery`, `KnowledgeCandidate`.

**Extension points**
- **Index backend** — implement the `KnowledgeIndex` Protocol (`upsert` / `search` /
  `neighbors`) over your vector DB, search engine, and graph store.
- **Retrieval strategy** — subclass `KnowledgeRetriever` to change ranking/fusion.
- **Governance** — implement `KnowledgeGovernance` to encode your approval workflow.

**Contracts to honor**
- `publish()` assigns a version and **never mutates prior versions** (`ADR-0004`).
- `deprecate()` retains history — never hard-delete.
- `resolve_contradiction()` must let **canon break ties** (`CANON-001`).
- Every emitted `KnowledgeObject` validates against
  [`knowledge_object.schema.json`](../../schemas/knowledge_object.schema.json): `authority ∈
  {canon, owner-approved, provisional}`, `sensitivity ∈ {public, internal, pci, pii}`.

```python
from sdk.knowledge.interfaces import KnowledgeRetriever, KnowledgeQuery, KnowledgeCandidate
from typing import Sequence

class HybridRetriever(KnowledgeRetriever):
    def retrieve(self, query: KnowledgeQuery) -> Sequence[KnowledgeCandidate]:
        raise NotImplementedError  # fuse semantic + keyword + graph; score authority/freshness
```

---

## `sdk.context` — Context Layer (`ARCH-01`)

**Interfaces:** `ContextAssembler` (ABC), `BudgetPolicy` (ABC), `Retriever` (Protocol); value
types `TaskIntent`, `Candidate`.

**Extension points**
- **Retrievers** — implement the `Retriever` Protocol per source (knowledge, experience, live
  code/state); the assembler composes any set.
- **Budgeting** — implement `BudgetPolicy` (`fits` / `evict`) to change eviction strategy.
- **Ranking** — subclass `ContextAssembler` to change selection.

**Contracts to honor**
- Enforce the token budget **before** the Gateway call — never rely on provider truncation
  (`ADR-0006`).
- `evict()` must record drops for the **dropped-candidate log** (reflection reads it later).
- `expire()` tears down ephemeral context and hands provenance to Evaluation & Learning.
- The emitted `ContextObject` validates against
  [`context_object.schema.json`](../../schemas/context_object.schema.json): `included`/`excluded`
  are provenance entries; `coverage_confidence ∈ [0,1]`.

```python
from sdk.context.interfaces import ContextAssembler, Retriever, TaskIntent
from sdk.objects import ContextObject, Confidence, Provenance
from typing import Sequence

class BudgetedAssembler(ContextAssembler):
    def assemble(self, intent: TaskIntent, retrievers: Sequence[Retriever]) -> ContextObject: ...
    def enrich(self, context: ContextObject, extra) -> ContextObject: ...
    def coverage_confidence(self, context: ContextObject) -> Confidence: ...
    def expire(self, context: ContextObject) -> Sequence[Provenance]: ...
```

---

## `sdk.planner` — Planning (`ARCH-06`)

**Interfaces:** `Planner` (ABC), `PlanValidator` (ABC); value type `PlanCheck`.

**Extension points**
- **Planning strategy** — subclass `Planner` (`plan` / `replan`).
- **Validation rules** — implement `PlanValidator` (`validate` / `required_approvals`) to add
  org standards.

**Contracts to honor**
- Every `PlanningObject` includes success criteria, tests, a `rollback` string, and a
  `risk_tier` (validated by [`planning_object.schema.json`](../../schemas/planning_object.schema.json)).
- `replan()` must preserve lineage to the previous plan.
- `validate()` checks rollback presence, risk-tier approvals (`CANON-001` §7), **dependency
  direction** (§3 — never a reverse dependency), and coverage (§4). `required_approvals()`
  returns 2 for Tier 0/1 and PCI/auth changes.

---

## `sdk.decision` — Decision Intelligence (`ARCH-06`)

**Interfaces:** `Orchestrator` (ABC), `ConfidencePolicy` (ABC), `PolicyGuard` (ABC); the
`Control` enum and `PolicyVerdict`.

**Extension points**
- **Confidence fusion** — implement `ConfidencePolicy` (`fuse` / `control_for`) to change how
  uncertainty gates autonomy.
- **Guardrails** — implement `PolicyGuard` (`check`) per domain (PCI vs. fairness vs. SoD).
- **Orchestration** — subclass `Orchestrator` (`interpret` / `decide` / `trace`).

**Contracts to honor**
- `control_for()` must be **risk-adaptive**: higher risk tier ⇒ higher confidence bar; low
  fused confidence on Tier 0 must not `PROCEED` (`ADR-0014`, `RFC-0009`).
- `PolicyGuard.check()` runs **before** execution (`ADR-0041`); a failed check returns a
  `PolicyVerdict(allowed=False, ...)`, optionally `requires_human=True`.
- `trace()` returns an **immutable** decision trace (`ADR-0021`).
- Never import a provider SDK here — route only through `sdk.models`.

```python
from sdk.decision.interfaces import ConfidencePolicy, Control
from sdk.objects import Confidence
from typing import Mapping

class RiskAdaptivePolicy(ConfidencePolicy):
    def fuse(self, inputs: Mapping[str, Confidence]) -> Confidence: ...
    def control_for(self, fused: Confidence, risk_tier: int) -> Control:
        raise NotImplementedError  # e.g. Tier 0 requires fused >= 0.9 to PROCEED, else ESCALATE
```

---

## `sdk.execution` — Execution Runtime

**Interfaces:** `ExecutionRuntime` (ABC), `ToolRegistry` (ABC), `Tool` (Protocol); value types
`ToolSpec`, `ToolResult`.

**Extension points**
- **Tools** — implement the `Tool` Protocol per enterprise capability (GitHub, Jira, CI,
  TestRail, runbooks). This is the primary per-Worker specialization axis for *tools*.
- **Runtime** — subclass `ExecutionRuntime` for different backends (local, sandboxed, remote).
- **Registry/policy** — implement `ToolRegistry` to enforce least-privilege scopes.

**Contracts to honor**
- Every `Tool` declares a `ToolSpec` with `side_effects ∈ {none, read, write, irreversible}`
  and a `least_privilege_scope` (`ADR-0042`); `ToolRegistry.available()` returns only what a
  Worker is authorized to use.
- `execute_step()` is **idempotent** (`ADR-0045`); `rollback()` invokes the plan's rollback
  (e.g. disable a feature flag).
- Emitted `WorkerArtifact`s carry `artifact_type` and a canonical `ref` (`PR-####`, `TR-####`),
  validated by [`worker_artifact.schema.json`](../../schemas/worker_artifact.schema.json).

```python
from sdk.execution.interfaces import Tool, ToolSpec, ToolResult
from typing import Mapping

class GitHubPRTool:                      # satisfies the Tool Protocol structurally
    spec = ToolSpec(name="github", description="Open/manage PRs",
                    input_schema={"type": "object"},
                    side_effects="write", least_privilege_scope="repo:mcg-checkout-service:pr")
    def invoke(self, args: Mapping[str, object]) -> ToolResult:
        raise NotImplementedError
```

---

## `sdk.evaluation` — Evaluation Layer (`ARCH-04`)

**Interfaces:** `Evaluator` (ABC), `Rubric` (ABC), `ObjectiveGate` (Protocol); value types
`GateResult`, `RubricItemResult`.

**Extension points**
- **Rubrics** — implement `Rubric` (`objective_gates` / `rubric_items` / `weights`) per task
  type. Primary per-Worker specialization axis for *rubrics*.
- **Gates** — implement the `ObjectiveGate` Protocol for new deterministic checks.
- **Evaluator** — subclass `Evaluator` for alternative aggregation, including model-assisted
  judges (always evidence-linked).

**Contracts to honor**
- **Objective-first** (`ADR-0015`): deterministic gates outweigh model-assisted items.
- **No score without linked evidence** (`ADR-0016`): every `GateResult`/`RubricItemResult`
  carries an evidence ID (e.g. `TR-0442`).
- Report **two** confidences — outcome vs. judgment (`ADR-0017`).
- `Rubric` is **versioned** (`id` + `version`, `ADR-0018`) so benchmarks are reproducible.
- `check_regressions()` returns True if a previously-fixed defect (referenced `EXP-###`) was
  reintroduced. Output validates against
  [`evaluation_object.schema.json`](../../schemas/evaluation_object.schema.json).

```python
from sdk.evaluation.interfaces import ObjectiveGate, GateResult
from sdk.objects import ExecutionObject

class DependencyDirectionGate:           # satisfies ObjectiveGate Protocol
    name = "dependency_rule"
    def run(self, execution: ExecutionObject) -> GateResult:
        raise NotImplementedError  # fail if a reverse dependency (e.g. APP-012 -> APP-003) appears
```

---

## `sdk.experience` — Experience Layer (`ARCH-03`)

**Interfaces:** `ExperienceStore` (ABC), `ExperienceRetriever` (ABC); value types
`SituationDescriptor`, `ExperienceMatch`.

**Extension points**
- **Store backend** — implement `ExperienceStore` over your durable store + vector index.
- **Retrieval** — subclass `ExperienceRetriever` to change applicability/value ranking.
- **Decay models** — provide domain-specific down-weighting.

**Contracts to honor**
- **Append-only** (`ADR-0005`): `append()` never overwrites; `reinforce()` adds evidence.
- `downweight()` reduces relevance on contradiction but **retains history** (`ADR-0047`).
- Match by **structural** situation similarity (same `apps` + `failure_class`), not just
  semantics, to guard against overfitting.
- `promotion_candidates()` surfaces high-value, repeatedly-corroborated lessons (`RFC-0018`).
  Objects validate against
  [`experience_object.schema.json`](../../schemas/experience_object.schema.json).

---

## `sdk.learning` — Learning Engine (`ARCH-05`)

**Interfaces:** `Reflector` (ABC), `LearningEngine` (ABC), `PromotionPolicy` (ABC); value type
`RootCause`.

**Extension points**
- **Reflection strategy** — implement `Reflector` (`reflect` / `diagnose`).
- **Promotion** — implement `PromotionPolicy` (`ready`) to tune the corroboration bar.
- **Engine** — subclass `LearningEngine` (`distill` / `emit` / `loop_closed` /
  `systemic_patterns`).

**Contracts to honor**
- Learning is **outside the model** — no fine-tuning (`ADR-0003`). Improvement is data.
- `reflect()` must inspect the **dropped-candidate log first** and diagnose a **root cause, not
  a symptom** (`ADR-0035`, `RFC-0016`). `RootCause.category` uses the documented vocabulary
  (`missing_knowledge`, `dropped_context`, `flawed_plan`, `tool_error`, …).
- `loop_closed()` returns True only once a lesson has **measurably changed a later execution**
  (`ADR-0034`) — the definition of learning.
- `PromotionPolicy.ready()` requires repeated corroboration (`ADR-0036`). Reflections validate
  against [`reflection_object.schema.json`](../../schemas/reflection_object.schema.json); events
  against [`learning_event.schema.json`](../../schemas/learning_event.schema.json).

---

## `sdk.models` — Model Gateway (`ARCH-07`)

**Interfaces:** `ModelGateway` (ABC), `ModelRouter` (ABC), `ModelProvider` (Protocol); value
types `CapabilityDescriptor`, `ModelRequest`, `ModelResponse`.

**Extension points**
- **Providers** — implement the `ModelProvider` Protocol per vendor/local model. **This is the
  only place a provider SDK may be imported** (`ADR-0009/0010`).
- **Routing** — implement `ModelRouter` (`route` / `fallback`) for cost/latency/quality policy.

**Contracts to honor**
- Every model call in the ECL flows through `ModelGateway.call()` — no layer bypasses it
  (`RFC-0011`).
- Build requests from a `ContextObject` (structured context, **not** a prompt string —
  `ADR-0011`); render per provider, normalize back to `ModelResponse`.
- Advertise a `CapabilityDescriptor` per model (`ADR-0012`); `fallback()` must reach a **local
  SLM as the availability floor** (`ADR-0044`).

```python
from sdk.models.interfaces import ModelProvider, CapabilityDescriptor, ModelRequest, ModelResponse

class AnthropicAdapter:                  # satisfies the ModelProvider Protocol
    def capabilities(self) -> CapabilityDescriptor: ...
    def render_and_call(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError  # the ONLY module that imports a vendor SDK
```

---

## `sdk.workers` — Enterprise AI Worker

**Interfaces:** `Worker` (ABC), `WorkerRuntime` (ABC); value types `WorkerSpec`, `RunResult`.
Implementing these ties the shared core together for a deployment. A **new Worker type usually
needs no new code here** — only a `WorkerSpec` (four bindings). See
[`worker-guide.md`](worker-guide.md). Implement `WorkerRuntime.bind()` to wire ECL components
for your deployment; subclass `Worker` only for bespoke `run`/`replay` behavior (`RFC-0024`
requires `replay()` to be deterministic).

---

## Testing your extension

1. **Schema conformance.** Validate every object your extension emits against its schema with a
   Draft 2020-12 validator, loading all schemas into a registry keyed by `$id` (recipe in
   [`schema-guide.md`](schema-guide.md)). CI can use the dependency-free structural validator in
   the test suite.
2. **Invariant checks.** Assert the module-specific contracts above — e.g. `publish()` leaves
   prior versions byte-identical; `ContextObject` never reaches a durable store; `evict()`
   populated the dropped-candidate log; every `EVAL` item has evidence; `loop_closed()` flips
   only after a later execution changed.
3. **Referential integrity.** Every cross-reference resolves to a real object of the right type
   (`ADR-0023`).
4. **Replay determinism.** If you touch execution/decision, confirm `Worker.replay(run_id)`
   reproduces the run for benchmarking (`RFC-0024`).
5. **Against the running example.** Reproduce the `CHK-1421` loop end to end (the
   [`../../schemas/examples/`](../../schemas/examples/) instances are your fixtures) and confirm
   your component slots in without changing any other layer.
