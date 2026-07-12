# Enterprise Worker SDK (EWSDK) — Project Charter

| Field | Value |
|---|---|
| **Project** | Enterprise Worker SDK (EWSDK) |
| **Foundation** | Open Enterprise AI Foundation (OEAF, working name) |
| **Status** | **Draft** — foundation-project charter (strategy/design; no code) |
| **Evolves from** | EnterpriseSim V1 `sdk/` (10 interface-only modules, FROZEN) |
| **Depends on** | **OEAS** (Open Enterprise AI Specification) — schemas/protocol the SDK types against |
| **Validated against** | **EnterpriseSim** — the simulation environment, reference enterprise, and benchmark |
| **Executed by** | **Reference Runtime** — an open, educational runtime that *runs* EWSDK-built workers |
| **Governance** | SemVer + expand/contract; changes via RFC (contract) and ADR (invariant), per V1 `CANON.md` |
| **License intent** | Apache-2.0 (open contract layer; algorithms stay in commercial runtimes) |

> This charter defines **the framework and contracts a team builds workers *with***. It is
> deliberately **not** the thing that *runs* workers (that is the Reference Runtime), **not**
> the schemas themselves (those are OEAS), and **not** the world they are scored in (that is
> EnterpriseSim). EWSDK is the developer-facing SDK that sits between them.

---

## 1. Purpose

The Enterprise Worker SDK is the **abstract contract layer and developer toolkit for building
Enterprise AI Workers** — stateless Actors that advance a Mission toward its Objectives, within
its Constraints, with calibrated confidence and full provenance.

EWSDK carries forward V1's founding discipline (interfaces-only, model-agnostic,
domain-agnostic, contract-first — V1 `sdk/README.md`) and re-anchors it on the ontology
settled in the ontology study and architecture review: the platform is organized around
**Missions over shared memory under governance**, and the **Worker is one kind of Actor**, not
the center of the universe. The V1 "Enterprise Cognitive Layer" (ARCH-01…07) is **not deleted**
— it is **reframed as the Worker's inner cognitive cycle** and specified here as a set of
replaceable capabilities.

EWSDK exists so that:

1. A worker author writes against **typed, stable interfaces**, not a runtime's internals.
2. Every worker is **portable** across runtimes (Reference Runtime, commercial engines) because
   both sides agree on OEAS schemas and EWSDK contracts.
3. Every worker is **testable and comparable** because it can be scaffolded, validated, replayed,
   and scored against EnterpriseSim with no code change.
4. Domain workers (QA, Security, Support, …) are **compositions** (`WorkerProfile`), not
   subclasses — shipping independently as plugins.

---

## 2. Scope

EWSDK owns, and only owns:

- **Core worker abstractions** — `Actor`, `Worker`, the binding of a Worker to a `Mission`, and
  the worker/mission/objective lifecycles.
- **Cognitive-cycle capability interfaces** — perceive, retrieve, deliberate/plan, decide, act,
  evaluate, reflect — as swappable contracts (the evolution of V1's ECL modules).
- **Platform-service *client* interfaces** — how a worker *reads from* Knowledge, Memory, and a
  Model Gateway, and *proposes* durable writes. EWSDK defines the seams; it does not implement
  the services.
- **The `Tool` contract** and least-privilege grant model the worker acts through.
- **The plugin & extension architecture** — entry points (RFC-0027), capability packs, tool
  packs, rubric packs, policy packs, and `WorkerProfile` composition (ADR-0024/0025).
- **Developer experience** — a CLI to scaffold/run/validate/test, a testing framework (contract
  tests, replay, benchmark harness client), and the set of Reference Workers.
- **Versioning & compatibility policy** for the SDK surface and its schema-version pinning.

**In scope but *by reference*, not by ownership:** the object shapes (owned by OEAS), the
executable enterprise world and benchmark (owned by EnterpriseSim), the concrete execution loop,
scheduler, and service implementations (owned by the Reference Runtime and commercial runtimes).

---

## 3. Non-goals (explicit)

EWSDK is deliberately **not** the following, and PRs that drift toward them are out of charter:

- **Not a runtime.** EWSDK does not execute workers, schedule missions, host services, manage
  processes, or own an event loop. It defines interfaces with `...` bodies (the V1 rule: "every
  method body is `...`; the SDK defines *what*, never *how*"). The **Reference Runtime** wires
  and runs implementations of these interfaces.
- **Not proprietary algorithms.** EWSDK does not ship context-ranking, memory-graph internals,
  decision optimization, calibration, credit-assignment, or distillation logic. Per the OEAF
  separation rule, those are where commercial runtimes **compete on the open benchmark**. EWSDK
  specifies the *interface* to a decision or a reranker; the *how* is a runtime's business.
- **Not the benchmark.** EWSDK does not define task families, outcome-verification, scoring, or
  leaderboards. Those belong to **EnterpriseSim**. EWSDK ships only a *client-side harness* that
  submits an EWSDK worker to the EnterpriseSim benchmark and reads results.
- **Not the schema source of truth.** Object *shapes* live in **OEAS** (JSON Schema). EWSDK
  mirrors them as typing Protocols and pins a schema version; it never forks the shapes.
- **Not a model provider or gateway implementation.** Only the gateway *client* contract
  (evolving from `sdk.models`) is in scope; provider coupling stays out (V1 ADR-0009/0010).

---

## 4. Core abstractions

### 4.1 The Worker as a stateless Actor bound to a Mission

The organizing correction from the architecture review: **the Worker is the ephemeral,
interchangeable part; the Mission is the durable unit of accountable work.** EWSDK encodes this
directly.

- **`Actor`** (new, from ontology P2) — the unifying supertype for anything that perceives →
  decides → acts: human, AI, or automated system. `Worker` is an AI `Actor` subtype. Humans are
  first-class Actors and mission participants, not just escalation endpoints.
- **`Worker`** (evolves `sdk.workers.Worker`) — a **stateless, domain-agnostic executor** bound
  to one `Mission`. It holds only *working memory* (ephemeral context); it owns no truth, no
  durable memory, no policy, no model. It *uses* platform-service clients for those.
- **`Mission`** (new; the operational root, ontology P8) — a durable, governed handle carrying
  **Intent + Objectives + Constraints + State**. A Mission outlives any single worker run and
  can be advanced by many workers and humans. This is the object V1 was missing entirely.

A worker run is: `bind(mission) → cognitive cycle → propose durable deltas → update mission
state`. Durable writes are **propose-then-govern**; the worker never writes governed stores
directly.

### 4.2 Lifecycles

**Worker lifecycle** (evolves V1 `RFC-0019`; re-entrant, not linear):
`Bound → Perceive → Retrieve → Deliberate → Decide → {Act | Retrieve | Deliberate | Collaborate}
→ Evaluate → Reflect → Propose → (released)`. The worker is interruptible and checkpointable;
`replay()` (V1 `RFC-0024`) deterministically re-runs a past run for debugging and benchmarking.

**Mission lifecycle** (new):
`Proposed → Scoped (objectives + constraints attached) → Active → {Blocked ↔ Active} → Review →
{Fulfilled (outcome-verified) | Active (shortfall) | Superseded (intent evolved)}`.

**Objective lifecycle** (new):
`Declared → Measured (measurement_fn bound to telemetry/data) → Active → {Attained | Regressed |
Abandoned}`, with an explicit `Outcome` (verified world-delta) as the evaluation and learning
signal. An Objective without a `measurement_fn` is not an Objective (review Part 2).

### 4.3 Cognitive-cycle capabilities → V1 module mapping (Keep / Extend / Rename / Add)

Each capability is a **replaceable interface** the worker composes. The table maps every
capability to the V1 `sdk/` module it evolves from and states the disposition.

| Capability (worker inner cycle) | V1 module → interfaces | Disposition | Notes |
|---|---|---|---|
| **Perceive** (read mission state + beliefs) | *(new)* + `sdk.context` | **Add** | New `sdk.mission` client feeds perception; perception is explicit, was implicit in V1. |
| **Retrieve** (mission-conditioned context) | `sdk.context` → `ContextAssembler`, `Retriever`, `BudgetPolicy` | **Keep + Extend** | Extend retrieval to be conditioned on `(intent, objectives, as_of_time, policy)`; keep budget/assembly. |
| **Deliberate / Plan** | `sdk.planner` → `Planner`, `PlanValidator` | **Keep** | Plans are BDI Intentions: objective-linked, constraint-checked, revisable. Contracts unchanged; add objective/constraint inputs. |
| **Decide** | `sdk.decision` → `Orchestrator`, `ConfidencePolicy`, `PolicyGuard` | **Keep + Rename split** | **Rename** the control-flow role to `Orchestrator/Control` (kept). **Add** a true `Decision` capability contract (constrained multi-objective, risk-aware, calibrated) — the *interface* only; the optimizer is a runtime algorithm. |
| **Act** (via tools) | `sdk.execution` → `ExecutionRuntime`, `Tool`, `ToolRegistry` | **Keep** | `Tool` contract + least-privilege grants (V1 ADR-0042) kept; add side-effect class + dry-run to the `Tool` contract. |
| **Evaluate** | `sdk.evaluation` → `Evaluator`, `Rubric`, `ObjectiveGate` | **Keep + Extend** | Extend from process-only to **dual-track**: process (rubric/gate) **and** outcome (objective attainment). `ObjectiveGate` gains a verified-outcome check. |
| **Reflect** | `sdk.learning` → `Reflector` | **Keep** | Reflection stays a per-run worker capability that emits *proposals*. |

Platform-service **clients** the worker calls (EWSDK owns the client contract; runtime owns the service):

| Client contract | V1 module → interfaces | Disposition | Notes |
|---|---|---|---|
| **Knowledge** | `sdk.knowledge` → `KnowledgeStore`, `KnowledgeRetriever`, `KnowledgeIndex` | **Keep** | Durable governed truth (semantic memory). Client-read contract preserved. |
| **Memory** (generalized) | `sdk.experience` → `ExperienceStore`, `ExperienceRetriever` | **Rename + Extend → `sdk.memory`** | Experience is demoted to **one memory type**. Generalize into a unified Memory client over the 7 types (semantic/episodic/procedural/temporal/organizational/policy/execution). See §5.3. |
| **Learning** (propose) | `sdk.learning` → `LearningEngine`, `PromotionPolicy` | **Keep as propose-side** | Worker *proposes* `LearningEvent`s; the platform Learning service governs/promotes. EWSDK owns the proposal contract only. |
| **Model Gateway** | `sdk.models` → `ModelGateway`, `ModelProvider`, `ModelRouter`, `CapabilityDescriptor` | **Keep** | The one part V1 got unambiguously right. Provider-agnostic client contract kept verbatim. |
| **Mission** | *(new)* | **Add → `sdk.mission`** | Read Intent/Objectives/Constraints/State; report progress. |
| **Objective** | *(new)* | **Add → `sdk.objective`** | Declare/measure objectives; expose `Outcome`. |
| **Constraint / Policy** | *(new; extracted from `sdk.decision.PolicyGuard`)* | **Add → `sdk.constraint`** | First-class Constraint objects (hard/soft, penalty, scope); hard constraints prune the action space pre-action. |

**Net module disposition:** *Keep* `knowledge`, `context`, `planner`, `decision`, `execution`,
`evaluation`, `models`, `workers`. *Rename+generalize* `experience → memory`. *Keep-as-propose*
`learning`. *Add* `mission`, `objective`, `constraint`. No V1 module is removed — additive
evolution (see §8).

---

## 5. Interfaces

All EWSDK interfaces are `abc.ABC` / `typing.Protocol`, mirror OEAS schemas, and carry no
implementation. The V1 in-code contracts in `sdk/objects.py` (`KnowledgeObject`,
`ContextObject`, `PlanningObject`, `DecisionObject`, `EvaluationObject`, `ReflectionObject`,
`ExperienceObject`, `LearningEvent`, `WorkerArtifact`, …) remain the typing base and are
**extended, not broken**.

### 5.1 Knowledge

`KnowledgeStore`, `KnowledgeRetriever`, `KnowledgeIndex` (kept from `sdk.knowledge`). Read
contract over durable, governed, versioned truth (`KnowledgeObject`, immutable-once-published).
This is the **semantic** memory type; retrieval gains policy-filtering + redaction at assembly.

### 5.2 Context

`ContextAssembler`, `Retriever`, `BudgetPolicy` (kept from `sdk.context`). Produces the ephemeral
per-run working set (`ContextObject`, never persisted as durable truth). **Extended** so the
assembler is conditioned on the Mission's intent, objectives, as-of-time, and policy — not a bare
similarity call.

### 5.3 Memory (generalized from Experience)

The single most significant interface change. V1's `sdk.experience` (`ExperienceStore`,
`ExperienceRetriever`) is **generalized into `sdk.memory`**: one retrieval client over the seven
memory types (semantic, episodic, procedural, temporal, organizational, policy, execution), all
understood as **projections over the immutable Event log + Beliefs**. `ExperienceObject`
(append-only, `EXP-###`) survives as the *experiential/procedural* type — its schema is kept and
extended, not deleted (backward-compatible). New read modes: recency×importance×relevance×utility
ranking, bitemporal *as-of-time* queries, and graph traversal. EWSDK owns the **client** contract;
the bitemporal memory graph, trust/decay model, and consolidation are **runtime algorithms**
(non-goal §3).

### 5.4 Planning

`Planner`, `PlanValidator` (kept from `sdk.planner`). Plans are BDI **Intentions**: committed,
objective-linked, constraint-checked, revisable, hierarchically decomposable. `PlanningObject`
gains explicit objective/constraint linkage (additive fields).

### 5.5 Decision

Two contracts, splitting V1's overloaded `sdk.decision`:
- **`Orchestrator` / control** (kept) — proceed / re-retrieve / replan / retry / escalate / abort;
  `ConfidencePolicy`; `PolicyGuard` (now delegating hard checks to `sdk.constraint`).
- **`Decision`** (new interface) — the seam for constrained multi-objective, risk-adjusted,
  **calibrated** choice. EWSDK mandates *calibrated* confidence as a contract requirement
  (ECE-monitored; epistemic vs aleatoric separated) but ships no calibrator.

### 5.6 Evaluation

`Evaluator`, `Rubric`, `ObjectiveGate` (kept from `sdk.evaluation`), **extended** to dual-track:
process conformance **and** outcome attainment against declared objectives. Verdicts remain typed
`EvaluationObject`s; add a verified-outcome field.

### 5.7 Tool

`Tool`, `ToolRegistry`, `ExecutionRuntime` (kept from `sdk.execution`). The `Tool` contract is the
worker's external-action surface onto Assets. **Extended** with a side-effect class, idempotency
key, dry-run/simulation hook, and compensation — for saga-style recovery. Aligns to **MCP** so
tools authored for MCP are usable as EWSDK tools without re-wrapping.

### 5.8 Plugin architecture & extension model

The recurring V1 pattern (V1 `sdk/README.md` §Extension points) is preserved and widened:

- **Entry-point plugins (RFC-0027).** Every capability, client, and tool is discoverable and
  registered via Python entry points; the runtime wires them in. Implement the interface, declare
  the entry point, done.
- **Extension surfaces:** capability packs (perceive/retrieve/plan/decide/evaluate/reflect
  implementations), **tool packs**, **rubric packs**, **policy packs**, **knowledge-domain
  bindings**, and memory backends.
- **Extension model = composition, not inheritance.** A `WorkerProfile` (§6.4) *binds* packs; it
  does not subclass a worker. This is the mechanism the review endorsed (ADR-0024/0025).
- **Additive fields via `metadata`.** OEAS keeps the `metadata` object as the sanctioned home for
  non-semantic extension fields, so core validation stays strict while plugins annotate freely.

---

## 6. Developer experience

### 6.1 Principles

Contract-first, batteries-included-but-swappable, and "correct by scaffold." A developer should
go from zero to a worker running against EnterpriseSim in one command each for scaffold, run,
validate, and test.

### 6.2 CLI (`ewsdk`)

| Command | Purpose |
|---|---|
| `ewsdk new worker <name>` | **Scaffold** a worker: `WorkerProfile` stub, capability wiring, a `WorkerSpec` (knowledge domains / tools / rubrics / policies, per V1 ADR-0025), tests, and pinned schema version. |
| `ewsdk new profile <name>` | Scaffold a domain `WorkerProfile` (pack composition) without touching worker code. |
| `ewsdk run --env enterprisesim --mission <MI-###>` | **Run** the worker against the EnterpriseSim reference world via the Reference Runtime, streaming the typed cognition trace. |
| `ewsdk validate` | **Validate** the worker's emitted objects against OEAS schemas and check `schema_version` compatibility; lint capability wiring and tool grants. |
| `ewsdk test` | Run the worker's **contract tests + replay tests** (see §7). |
| `ewsdk bench --suite <name>` | Submit the worker to the EnterpriseSim **benchmark harness** (client-side; EnterpriseSim scores it) and print outcome-verified results. |
| `ewsdk replay <run_id>` | Deterministically **replay** a recorded run for debugging (V1 `RFC-0024`). |

The CLI is a thin client: `run`/`bench` delegate execution to the Reference Runtime and scoring
to EnterpriseSim — consistent with the non-goals.

### 6.3 Testing framework & strategy

Four layers, from cheapest/most-deterministic to most-integrated:

1. **Contract tests against OEAS.** Every object a worker emits (context, plan, decision, eval,
   reflection, proposal, artifact) is validated against the Draft 2020-12 schemas loaded into an
   `$id` registry (the V1 `schemas/README.md` pattern). A dependency-free structural validator is
   provided for offline CI.
2. **Capability unit tests.** Each capability implementation is tested behind its interface with
   fakes for the platform-service clients — no runtime, no models.
3. **Replay tests.** Recorded runs (deterministic, seeded) re-execute via `replay()`; the trace
   must reproduce byte-identical typed objects. Guards against silent contract drift.
4. **Benchmark harness (client).** The worker is scored on EnterpriseSim task families with
   **outcome-verified** results, baselines (no-memory / RAG), ablations (memory type on/off), and
   confidence intervals. EWSDK owns the *submission client and result types*; EnterpriseSim owns
   the *world, the ruler, and the verification*.

### 6.4 Reference Workers

Shipped as **`WorkerProfile`s = composition, not inheritance** (V1 ADR-0024/0025): QA, Security,
Support, Privacy/Compliance, Finance-reconciliation, Data-Quality. Each is a binding of
capability packs + tool grants + rubric packs + policy packs over the *same* stateless `Worker`
core; a Security review and a Finance reconciliation share ~90% of behavior and differ only in
those four axes. Reference Workers are (a) executable examples, (b) the smoke-test suite for the
contracts, and (c) the seed of a future `WorkerProfile` marketplace (V1 `RFC-0020`).

---

## 7. Versioning & compatibility

Backward compatibility is **first-class**; deprecation is **rare** and slow.

- **SemVer for the SDK surface** (V1 ADR-0032). Additive interface changes (new optional methods,
  new capability contracts, new fields on `metadata`) are **minor**. Removing/renaming a method or
  changing a signature is **major** and requires an ADR.
- **Schema-version pinning.** Each worker pins an OEAS `schema_version` (`^2020-12\.vN$`), tracked
  by `sdk.SCHEMA_VERSION`. `ewsdk validate` enforces the pin.
- **Expand → migrate → contract** (V1 ADR-0033 / `RFC-0021`). Add optional fields first; dual-write
  and backfill; only later make required or remove — never rewrite instances in place.
- **Compatibility window & adapters.** The SDK accepts the current and previous **major** schema
  version during a migration window; a small **adapter** layer up-converts prior-version objects at
  read time so old workers keep running. Readers always tolerate unknown `metadata`.
- **Referential integrity is invariant** (V1 ADR-0022/0023). Canonical IDs never change meaning
  across versions; a change that would break a cross-reference requires an ADR.
- **Renames are aliases, not breaks.** `sdk.experience → sdk.memory` ships the new module while
  keeping `sdk.experience` as a deprecated import alias through a long window; `ExperienceObject`
  remains a valid memory type throughout.

---

## 8. Long-term roadmap

Evolution over replacement — every step is additive until a major boundary is explicitly crossed.

**V1.5 — Additive foundation (backward-compatible, no breaks).**
- Add `sdk.mission`, `sdk.objective`, `sdk.constraint` alongside the existing 10 modules.
- Introduce `Actor` as the `Worker` supertype; introduce the `Mission` handle in `Worker.run`.
- Extend (not break) `sdk.context`, `sdk.evaluation`, `sdk.planner`, `sdk.execution.Tool` with
  the objective/constraint/outcome/side-effect additions as **optional** fields.
- Ship `sdk.memory` as a superset alias of `sdk.experience`; add the seven-type read modes.
- Ship the `ewsdk` CLI (scaffold/run/validate/test) and the first Reference Workers.
- All V1 workers keep running unchanged. This is the "regression fix" the review demanded made
  available *additively*.

**V2 — GA split (the one deliberate major boundary).**
- Formal split of EWSDK from EnterpriseSim/OEAS/Reference Runtime as **four independent
  versioned projects** under the Foundation, each SemVer-released.
- Promote the previously-optional Mission/Objective/Constraint inputs to **required** on the core
  worker contract (expand→contract completes). `sdk.experience` becomes a deprecated alias.
- The `Decision` capability (calibrated, multi-objective) becomes a first-class required seam.
- Stable plugin ABI (RFC-0027) with a compatibility guarantee; `WorkerProfile` marketplace opens.
- OTel-aligned cognition spans and CloudEvents-shaped event emission are part of the GA contract.

**V3 — Ecosystem maturity.**
- Multi-worker collaboration contracts over a shared Mission (V1 `RFC-0020` realized).
- Governed distillation path as an *optional, contracted* capability (two-speed learning) — still
  no algorithm shipped, only the seam.
- Cross-runtime certification: a worker certified against the OEAS spec + EnterpriseSim benchmark
  runs on any conformant runtime. This is the durable prize — **portability and measurement**, not
  any single engine.

---

## 9. Relationship summary (one screen)

- **OEAS** gives EWSDK the *shapes* (schemas/protocol). EWSDK types against them and pins a version.
- **EWSDK** (this project) gives worker authors the *contracts and toolkit* to build workers.
- **Reference Runtime** *executes* EWSDK workers; commercial runtimes do too, competing on algorithms.
- **EnterpriseSim** provides the *world and the ruler* — where EWSDK workers are run, ablated, and
  scored.

EWSDK's job is to be the stable, open seam in the middle: **build once, run on any runtime, score
on the open benchmark.** It keeps V1's interfaces-only discipline, generalizes Experience into
Memory, lifts Mission/Objective/Constraint to first-class above the worker, and reframes the ECL
as the worker's inner cognitive cycle — additively, compatibly, and for the long term.
