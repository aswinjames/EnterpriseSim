# Reference Runtime — Foundation Project Charter

> The **open, simple, educational runtime that executes Enterprise Workers**. Where the SDK
> (EWSDK) defines *what* a Worker is and EnterpriseSim defines the *world and the ruler*, the
> Reference Runtime is the *player you can read*: a working implementation of the ECL cognitive
> cycle whose highest priority is that a newcomer can trace one Mission end to end.

| Field | Value |
|---|---|
| Document | `OEAF-CHARTER-C` (Reference Runtime) |
| Project | **C — Reference Runtime**, of the Open Enterprise AI Foundation (OEAF) |
| Status | Foundation Charter — Draft for ratification |
| Version | `0.1.0` (charter); runtime ships `0.x` under SemVer |
| License | Apache-2.0 (open source) |
| Depends on | Project B (Enterprise Worker SDK / EWSDK), Project D (OEAS schemas) |
| Executes in | Project A (EnterpriseSim environment + benchmark) |
| Ontology | Event · Actor · Objective · Constraint/Policy · Belief/Knowledge · Capability · Asset · Mission; Memory = derived projection (7 types); Experience = one memory type |
| Standards | JSON Schema, CloudEvents, OpenTelemetry, OpenAPI, MCP |
| Non-goal | Being competitive. It does not race commercial runtimes on the benchmark. |

---

## 1. Purpose

EnterpriseSim V1 delivered the *contracts* — the ECL architecture (`ARCH-01`…`ARCH-07`), the
typed SDK interfaces, the frozen schemas, and 100 illustrative `WorkerExecutionBundle`s. It
never shipped a **runtime**: the corpus bundles were generated deterministically, not
*executed*. The single sharpest criticism in the ontology study (Part 5) was that "a generator
asserted improvement." A specification with no readable, runnable reference is a specification
people misread.

The **Reference Runtime** closes that gap. It is a concrete, executable implementation of the
ECL cognitive cycle that:

1. **Proves the SDK is implementable** — every abstract interface in the EWSDK has at least one
   honest, working implementation here, so the contracts are demonstrably buildable rather than
   aspirational.
2. **Turns the corpus from asserted into earned** — it *runs* Missions in the EnterpriseSim
   world, computes outcomes deterministically, and emits corpus-compatible bundles, so
   improvement is measured rather than claimed (ontology Part 5).
3. **Teaches the whole field** — it is the artifact a student, a standards reviewer, or a
   commercial-runtime engineer reads to understand what "an Enterprise AI Worker executing a
   Mission" actually means, step by step.

It is deliberately the *slow, clear* player. Its worth is measured in comprehension and
correctness, never in throughput or leaderboard rank.

---

## 2. Scope

**In scope.** A single-process, single-tenant, locally runnable runtime that: accepts a Mission
trigger; assembles context from knowledge and memory; plans; runs a confidence-gated decision
loop; executes tools (MCP-aligned) against the EnterpriseSim world; evaluates outcomes against
Objectives; reflects; applies reversible learning; and emits an OpenTelemetry trace plus a
corpus-compatible `WorkerExecutionBundle` for every run. It implements the EWSDK interfaces and
validates all artifacts against OEAS schemas.

**Out of scope** (see §14 in full). Proprietary ranking/memory/decision algorithms; production
multi-tenancy, scaling, and SLAs; anything whose presence would either make the runtime compete
with commercial engines or obscure the educational intent.

**Boundary rule.** If a feature makes the runtime *faster* at the cost of being *harder to
read*, it belongs in a commercial runtime, not here. If a feature makes the runtime *clearer*
at the cost of being slower, it belongs here.

---

## 3. Educational goals

The Reference Runtime is the primary teaching instrument of the ecosystem. Concretely, after
working with it a reader should be able to:

- **Trace one Mission end to end** — follow a single trigger from Objective interpretation
  through context assembly, planning, decision, tool execution, evaluation, reflection, and
  learning, with every intermediate object inspectable on disk and every step a named span in
  one trace.
- **Name where every ontology concept lives** — point to the code path that produces each
  primitive (Event, Actor, Objective, Constraint, Belief, Capability, Asset, Mission) and each
  derived projection (the 7 memory types, Decision, Plan, Evaluation, Reflection, Learning).
- **See the stateless-model boundary** — observe that all memory and learning live *outside*
  the model, behind the Model Gateway, exactly as `ARCH-07` requires, by swapping the model and
  watching every accumulated lesson still apply.
- **Reproduce a result** — re-run a golden Mission from a seed and get byte-identical cognition
  artifacts, then flip memory on/off and watch outcomes change.
- **Extend one seam** — implement one plugin (a retriever, a rubric, a tool) against an EWSDK
  interface and see the runtime wire it in without touching the core.

The measure of success is pedagogical: **time-to-first-traced-Mission** for a newcomer, and the
fraction of the ontology a reader can locate in the code unaided. These are treated as
first-class quality metrics, tracked like tests.

---

## 4. Reference-implementation philosophy

Five commitments, in priority order, and they are ranked deliberately:

1. **Readable before fast.** Straight-line, well-named code over clever abstraction. No
   micro-optimization, no caching that hides control flow, no concurrency that reorders the
   narrative of a run. A method should read like the sentence in `ARCH-07` it implements.
2. **Every step observable.** No hidden state. Each cognition step produces a typed, schema-
   valid artifact written where it can be read, and emits exactly one OpenTelemetry span. If it
   isn't traceable and inspectable, it isn't allowed in the loop (the ontology's
   "cognition-as-typed-governed-events" contribution, made literal).
3. **Correctness over completeness.** A naive implementation that is *provably faithful* to the
   contract beats a sophisticated one that is merely plausible. Every memory type is present
   even if its retrieval is a simple scored scan; presence-and-honesty over cleverness.
4. **One obvious way.** For each ECL step there is a single default path a reader will find
   first. Alternatives are plugins, off by default, discovered only when the reader goes
   looking — progressive disclosure applied to a runtime.
5. **Explain, don't impress.** Comments and structure exist to teach the architecture, not to
   showcase engineering. The runtime is a textbook that happens to execute.

Corollary: the Reference Runtime will sometimes be visibly *worse* than a commercial runtime on
the benchmark. That is correct and intended. It establishes the floor and the contract; it does
not defend a rank.

---

## 5. Mandatory features

Every item below MUST exist in the runtime, implements a named EWSDK interface, produces a
schema-valid OEAS artifact, and emits an OpenTelemetry span. "Naive is fine; absent is not."

### 5.1 Mission execution loop
The orchestrator that drives one Mission through the full `ARCH-07` cycle: interpret →
assemble context → plan → decide → execute → evaluate → (loop or finalize) → reflect → learn.
Implements EWSDK `workers.WorkerRuntime` / `decision.Orchestrator`. It is an **explicit,
re-entrant, checkpointed control loop** (LangGraph-style shape, per ontology Part 2) — cyclic
and interruptible so a reader can pause at any node and read the state. Iteration and
reasoning-cost budgets are enforced (the `ARCH-07` runaway-cost mitigation), with simple
constant defaults.

### 5.2 Knowledge retrieval
Implements `knowledge.KnowledgeRetriever` over `knowledge.KnowledgeStore`. Retrieves
`KnowledgeObject` candidates for an Objective using a transparent hybrid of lexical and
similarity scoring. The ranking is intentionally simple and readable (see §14 — advanced
ranking is a commercial concern); what matters is that it is honest about what it surfaced and
why, and that provenance is preserved.

### 5.3 Context assembly
Implements `context.ContextAssembler` with a `context.BudgetPolicy`. Assembles a `ContextObject`
(`CTX-###`) — the ephemeral, per-run working set — from retrieved knowledge, retrieved memory,
and live EnterpriseSim world state, subject to a budget. Context **never persists** (the
durable/ephemeral distinction is sacred, per `ARCH-07` best practice). Coverage confidence is
reported honestly, including when the budget forced a drop (the `RUN-0001` "loyalty rules
dropped for budget" case is a first-class teaching example).

### 5.4 Memory interfaces (projection; all 7 types)
Memory is a **derived projection over the Event log + Beliefs**, not a primitive (ontology Part
3). The runtime MUST expose a single retrieval interface backed by all **seven** memory types —
**semantic, episodic, procedural, temporal, organizational, policy, execution** — even where an
implementation is naive:

| Memory type | Reference implementation (naive is fine) |
|---|---|
| Semantic | scored scan over curated Beliefs/Knowledge |
| Episodic | recency × importance × relevance over past run Events |
| Procedural | successful prior Plans indexed by situation (`experience`/`Capability`) |
| Temporal | as-of-time filter over the bitemporal Event log |
| Organizational | graph walk over Actor/Asset/ownership edges |
| Policy | governed lookup over Constraint/Policy events |
| Execution | trace/span query over tool-action Events (OTel-native) |

`experience.ExperienceStore` / `ExperienceRetriever` are implemented as **one memory type**
(experiential/procedural), not a privileged layer — correcting V1's Experience-as-first-class.
All projections are rebuildable from the log; nothing is hard-deleted (append-only substrate,
governed decay only).

### 5.5 Planning
Implements `planner.Planner` producing a `PlanningObject` (`PLAN-###`) and a
`planner.PlanValidator`. A Plan is a revisable Intention (BDI): ordered steps, tests,
rollback/guard, and a risk tier. The reference planner is a straightforward prompt-and-validate
step through the Model Gateway; planning heuristics are a documented plugin seam, learned
heuristics arrive via the reversible learning hooks (§5.10), never baked in.

### 5.6 Decision pipeline (with calibrated-confidence hooks, simple defaults)
Implements `decision.Orchestrator`, `decision.ConfidencePolicy`, `decision.PolicyGuard`,
producing `WorkerDecision`/`DecisionObject`. The decision is modeled as the ontology's Part 4
form — a choice over feasible actions weighted by **calibrated confidence**, with policy
pre-checks as hard gates and humans-as-Actors able to enter as approvals/escalation. The runtime
exposes a **calibrated-confidence hook** (a pluggable estimator interface) but ships a **simple,
honest default** (e.g. transparent fused confidence from coverage + retrieval + evaluation
signals, no learned calibrator). It is **confidence-honest**: no step launders uncertainty as
certainty, and no high-stakes autonomous action is taken at low fused confidence. Advanced
calibration and multi-objective optimization are explicitly a commercial concern (§14).

### 5.7 Tool execution (MCP-aligned)
Implements `execution.ExecutionRuntime`, `execution.Tool`, `execution.ToolRegistry`, producing
`ExecutionObject`/`WorkerArtifact`s. Tools are the external-action surface onto Assets. The tool
interface is **MCP-aligned** (tool descriptors, structured inputs/outputs, capability grants) so
the runtime speaks the ecosystem's standard tool protocol; EnterpriseSim world operations are
exposed as MCP-shaped tools. Every tool call is an Event with a span — the execution memory type
is literally these traces.

### 5.8 Evaluation (outcome-verified, not asserted)
Implements `evaluation.Evaluator`, `evaluation.Rubric`, `evaluation.ObjectiveGate`, producing an
`EvaluationObject` (`EVAL-###`). Verdicts are **computed against Objectives by running the
deterministic outcome model of the EnterpriseSim world** — *run the effect, don't rubric it*
(ontology Part 5). Objective gates are hard, evidence-linked, and versioned. This is the feature
that most distinguishes the runtime from the V1 generator: the corpus it produces is
*outcome-verified*, so any claim of learning is falsifiable.

### 5.9 Reflection
Implements `learning.Reflector` producing a `ReflectionObject` (`REF-###`): an internal action
(CoALA sense) that diagnoses root cause from the evaluation and its evidence and distills a
lesson. Reflection reads Events; it produces the candidate updates that the learning hooks may
apply.

### 5.10 Learning hooks (external, reversible; no fine-tuning by default)
Implements `learning.LearningEngine` and `learning.PromotionPolicy`, emitting `LearningEvent`s.
Learning **lives entirely outside the model** — it updates data (memory, retrieval policy,
planning heuristics, calibration inputs) and **never touches model weights**. **No fine-tuning
is performed by default.** Every learning effect is:
- **External** — a written Event/projection update, portable across any model behind the
  Gateway (change providers on Monday, every lesson still applies Tuesday — `ARCH-07`).
- **Reversible** — expressed as a governed, append-only edit that can be down-weighted or
  superseded, never a destructive mutation. Promotion between memory types (episodic →
  experiential → semantic) is governed edge creation past a trust threshold — the
  memory-poisoning defense made concrete.
This is the mechanism that lets the corpus show a family go from cold-start `fail` to `pass`.

### 5.11 Plugin architecture
Every mandatory feature is registered through a plugin/entry-point mechanism (per the SDK's
`RFC-0027` extension pattern). The core provides the loop and the seams; each ECL step is a
swappable implementation of an EWSDK interface. The default implementations are themselves
plugins, so "replace the retriever" and "add a tool" are the same one gesture.

### 5.12 OpenTelemetry span emission for every cognition step
Non-negotiable and pervasive: **every** cognition step — retrieve, assemble, plan, decide,
execute, evaluate, reflect, learn — emits exactly one OpenTelemetry span, nested under one
Mission-level root trace. Spans follow (and help shape) the ecosystem's OTel semantic
conventions for agent cognition. The trace *is* the primary observability surface and doubles as
the execution memory type. A reader watches one Mission as one waterfall.

---

## 6. Optional features (pluggable, off by default)

Provided as plugins, shipped disabled, documented as "beyond the reference floor." Turning any
of these on must never be required to run a Mission or the benchmark. Examples:

- **Vector-index retrieval** backend (default is an in-memory scored scan).
- **Graph-store projections** for organizational/temporal memory (default is a straightforward
  in-memory graph).
- **Memory consolidation / "sleep" compaction** (clustering episodes into procedural skills).
- **Learned confidence calibration** estimator (default is transparent fused confidence).
- **Multi-provider routing / fallback** in the Gateway (default is a single configured model).
- **Human-in-the-loop console** for approvals and escalation (default is policy-driven auto
  escalation recorded as an Event).
- **Alternative planners** (search/tree-of-thought) behind the same `Planner` interface.

Each optional feature ships with its own golden traces so that enabling it remains reproducible.

---

## 7. Plugin boundaries — what the runtime provides vs delegates

| The runtime **provides** (core) | The runtime **delegates** to plugins |
|---|---|
| The Mission execution loop and its control flow | Knowledge/memory retrieval strategy |
| The step sequence and checkpoint/replay machinery | Context ranking and budget policy |
| Typed-artifact I/O and schema validation | Planner strategy and planning heuristics |
| OpenTelemetry span emission and trace shape | Confidence estimator / calibration |
| The bundle writer (corpus-compatible output) | Concrete tools (MCP servers) |
| Policy-gate enforcement points | Rubrics and objective gates |
| Governance of learning writes (reversibility, promotion thresholds) | Reflection strategy; learning update policy |
| The EWSDK interface wiring and entry-point registry | Model provider adapters (behind the Gateway) |

**Rule:** the core owns *sequence, safety, observability, and reproducibility*; plugins own
*strategy and quality*. Anything that competes on strategy/quality is a plugin, which is exactly
where commercial runtimes differentiate — the boundary is the same boundary the ontology draws
between the open contract and the commercial engine.

---

## 8. Testing philosophy

The runtime is validated as a *reference*, so its tests double as executable specification:

- **Golden traces.** Canonical Missions have committed reference traces (the full artifact set +
  OTel spans). A change that alters cognition output must consciously update the golden trace —
  drift is caught, not silent. `RUN-0001` (cold-start fail → creates `EXP-090`) and `RUN-0002`
  (loop closed → pass) are the anchor golden traces, reproducing the exact frozen V1 example
  objects.
- **Deterministic replay.** Given a seed and a recorded/mocked model transcript, a run
  reproduces byte-identically. This is what makes counterfactuals (memory on/off) honest and is
  the backbone of the learning proof.
- **Conformance to OEAS + SDK contracts.** Every emitted artifact validates against the OEAS
  JSON Schemas; the runtime is checked to implement each EWSDK interface it claims. Conformance
  is a gate, not a courtesy.
- **Runs the EnterpriseSim benchmark.** The runtime executes the benchmark task families end to
  end and produces outcome-verified results. It is the **reference baseline** on the leaderboard
  — the honest floor every commercial runtime must clear, not a contender for the top.
- **Learning-curve check.** The 13 task families must show the corpus property — first-run
  outcome trends to `fail`, later runs to `pass`, fused confidence rising — *when computed*, not
  asserted, or the run is a failure of the runtime.

---

## 9. Performance philosophy

**Explicitly de-prioritized.** The Reference Runtime states, as policy, that latency, throughput,
memory footprint, and cost are *not* optimization targets. Correctness and clarity win every
trade-off against speed. There are no performance SLAs, no benchmarks of the runtime's own speed,
and no performance-driven refactors. Where a naive algorithm is O(worse), that is accepted and
documented as a teaching note pointing to where a commercial runtime would optimize. Performance
is somebody else's competitive advantage; here it would only obscure the lesson.

---

## 10. Compatibility

- **SemVer**, strictly. The runtime versions independently but declares the EWSDK version and
  OEAS `SCHEMA_VERSION` it targets.
- **Backward compatibility is first-class.** Reading and replaying an older golden trace or
  corpus bundle must keep working across minor versions; breaking changes are major-only and
  follow the ecosystem's schema-versioning RFC and SemVer policy (`RFC-0021`, `ADR-0032`).
- **Evolution over replacement.** New capabilities arrive as plugins or additive interfaces, not
  by rewriting the core. Expand-only, mirroring the corpus's `ADR-0051` discipline.
- **Standards alignment as a compatibility contract.** JSON Schema (artifacts), CloudEvents
  (Event envelope), OpenTelemetry (cognition spans), OpenAPI (any served endpoints), MCP (tools)
  are the interop surfaces; conformance to them is part of the compatibility promise.

---

## 11. Relationship to the SDK (EWSDK, Project B)

The Reference Runtime is the **canonical implementation of the EWSDK interfaces**. Every module
in the SDK module map has a corresponding reference implementation here:

`knowledge.*`, `context.*`, `planner.*`, `decision.*`, `execution.*`, `evaluation.*`,
`experience.*`, `learning.*`, `models.*`, `workers.*`.

The SDK defines *what* (abstract `abc.ABC`/`Protocol`, every body `...`); the runtime supplies
*how* (the simplest honest body). The runtime imports the SDK; the SDK never imports the runtime.
If an SDK interface cannot be implemented cleanly here, that is a signal the *contract* is wrong —
so the Reference Runtime is also the EWSDK's continuous proof-of-implementability. The one place
providers are touched is `models.*` (the Model Gateway), preserving the model-agnostic invariant.

---

## 12. Relationship to EnterpriseSim (Project A)

The runtime **executes Missions inside the EnterpriseSim environment**. EnterpriseSim provides
the world (Meridian Commerce Group), the deterministic outcome model, the task families, and the
benchmark ruler; the runtime is a player that acts in that world through MCP-shaped tools and is
scored by that ruler.

Its outputs are **corpus-compatible `WorkerExecutionBundle`s**: for every Mission it runs, the
runtime writes a bundle with the same stage structure the V1 corpus documents —
`knowledge_retrieved → context → experience_retrieved → decision → plan → execution →
evaluation → reflection → experience_update (+ evolving confidence)` — each stage a schema-valid
OEAS object. This is the through-line that upgrades the corpus from *generated/asserted* (V1) to
*executed/outcome-verified*: the same bundle shape, now earned. The runtime must be able to
**produce and replay** these bundles, so V1's illustrative corpus and the runtime's live output
are the same artifact type on the same schemas.

---

## 13. Relationship to the other ecosystem projects

- **Project D (OEAS).** The schemas the runtime validates against are the standard; the runtime
  is a conformance witness for OEAS. Where the runtime needs a shape the schema lacks, that is an
  OEAS change request, decided in the open.
- **Commercial runtimes (e.g. Bytesurge).** They implement the same EWSDK and OEAS and compete on
  the EnterpriseSim benchmark using proprietary strategy plugins. The Reference Runtime is their
  shared, readable baseline and the thing that proves the contract is neutral — it deliberately
  does **not** compete with them (§14). Healthy ecosystem: one open floor, many commercial
  ceilings, one neutral ruler.

---

## 14. What intentionally NOT to implement

The following are excluded **on purpose**. Their absence is a feature; a PR adding them to the
core should be declined and redirected to a plugin or a commercial runtime.

- **Proprietary ranking algorithms.** No learned rerankers, no sophisticated hybrid-fusion
  scoring. Retrieval stays transparently simple; ranking quality is where commercial engines
  compete.
- **Proprietary memory internals.** No production memory-graph engine, no clever consolidation
  heuristics in the core, no opaque trust models. The seven memory types exist naively; their
  optimization is commercial.
- **Proprietary decision/optimization algorithms.** No constrained multi-objective optimizer, no
  advanced risk model, no learned calibrator in the default path. Hooks exist; sophistication is
  a plugin.
- **Fine-tuning / weight updates.** Learning is external and reversible by charter; the runtime
  never trains a model.
- **Production multi-tenancy.** No tenant isolation, no per-tenant quotas, no auth/RBAC plane. It
  is single-tenant and local.
- **Scale optimizations.** No distributed execution, no sharding, no async concurrency for
  throughput, no caching layers that hide control flow, no connection pooling. Single process,
  one Mission at a time, readably.
- **Production operations.** No HA, no autoscaling, no SLAs, no ops/monitoring beyond the OTel
  spans that exist for *teaching*, no secrets management beyond the minimum to reach a provider.
- **Anything that competes with commercial runtimes or obscures the educational intent.** This is
  the catch-all test applied to every proposed feature: *does it make the runtime a better
  product, or a clearer textbook?* Only the latter belongs here.

**The governing principle:** the Reference Runtime earns its place by being the one player
everyone can read and trust as correct — the ImageNet/Gym/SWE-bench "reference agent" of
enterprise cognition. The moment it optimizes for rank or product polish, it stops being the
reference. Simplicity, correctness, clarity, education, and reproducibility are not phases on the
way to something better; they are the whole and permanent mandate.

---

*End of Reference Runtime Charter (`OEAF-CHARTER-C`). Subordinate to the frozen EnterpriseSim V1
architecture (`ARCH-01`…`ARCH-07`) and the OEAF locked ecosystem decisions. This document is
strategy and design; it defines no code and modifies no frozen V1 artifact.*
