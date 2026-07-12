# Open Standards Roadmap — Open Enterprise AI Specification (OEAS)

> **Part 6 of the Open Enterprise AI ecosystem series.**
> **Document type:** Strategy & design (prose). No code. Defines *what* to standardize, *how* it
> aligns to existing standards, and *the path* to ratification.
> **Status:** Draft for community circulation.
> **Evolves from:** EnterpriseSim V1 — a completed, **FROZEN** repository (`~/EnterpriseSim`). This
> roadmap does not modify any V1 artifact; V1 schemas are the empirical basis of the standard.
> **Governing inputs:** `schemas/README.md`, `schemas/common.schema.json` + the 12 object schemas,
> `review/Enterprise-AI-Ontology.md` (canonical ontology), `CANON.md §6` (ID conventions).
> **Standards body target:** neutral foundation (see §6.10).
> **License intent:** specification text CC-BY-4.0; reference schemas Apache-2.0.
> **Version of this roadmap:** 0.1 · **Date:** 2026-07-12 · **Owner:** OEAS Working Group (proposed).

---

## 6.0 Why a standard, and why now

EnterpriseSim V1 proved a rare thing: that enterprise cognition can be captured as **typed,
validated, cross-linked, regenerable artifacts** over a coherent enterprise world. The ontology
study (`review/Enterprise-AI-Ontology.md`, §8.3–8.5) concluded that V1's durable legacy is *not* a
cognitive architecture (those are superseded and forgotten) but **measurement and
interoperability** — "the world and the ruler," an ImageNet/Gym/SWE-bench for enterprise cognition,
plus an open event/interface standard for agent reasoning.

Interoperability is exactly the thing that cannot live inside one product. The wire formats and
interfaces are where a decade-scale reference architecture actually resides, and they only have
value if they are **vendor-neutral**. That is the mandate of the **Open Enterprise AI Specification
(OEAS)**: take the V1 schemas as the seed, align them to the existing standards the industry
already runs on, invent new schemas *only* where no standard exists, and donate the result to a
neutral foundation.

## 6.1 Design principles

1. **Align, do not reinvent.** Every OEAS specification either *is* an existing standard applied to
   Enterprise AI, or maps cleanly onto one. We contribute the enterprise-cognition *semantics*, not
   a competing serialization, transport, or schema language.
2. **JSON Schema (Draft 2020-12) stays the schema language.** V1 already uses it
   (`common.schema.json` and all object schemas declare `"$schema": ".../draft/2020-12/schema"`).
   No migration; the existing `$id` URIs (`https://enterprisesim.dev/schemas/2020-12/…`) become
   OEAS namespaces under the foundation domain via redirect, never rewrite.
3. **Backward compatibility is first-class.** V1 schemas remain valid forever. **OEAS v1 == the V1
   schema set + additive new objects.** SemVer semantics, expand→migrate→contract, long deprecation
   windows (§6.8). This is a promise, not an aspiration.
4. **Standardize the contract, not the algorithm.** We standardize object shapes, the event
   envelope, the telemetry vocabulary, and the interfaces. We do *not* standardize how a runtime
   ranks context, scores memory, or optimizes decisions (§6.11).
5. **Center on the Objective; source everything from an Event log.** The ontology's central
   correction — Objective is the missing semantic center, Event is the substrate — drives which
   *new* schemas are P0.

## 6.2 The specification catalog

Dispositions used throughout:
- **Keep** — the V1 schema becomes an OEAS specification essentially unchanged.
- **Extend** — the V1 schema is retained and gains *additive, optional* fields.
- **Promote** — a concept that exists in V1 only as a field, string, or ID convention is lifted
  into a first-class standalone schema.
- **New** — no V1 antecedent; invented because no standard exists for it.

### 6.2.1 Foundation layer

**OEAS-Common** — *what it standardizes:* shared `$defs` — canonical IDs, `confidence` [0,1],
`sensitivity` (`public|internal|pci|pii`), `provenance`, `timestamp`, and `eclObjectBase`
(`id`/`schema_version`/`created_at`/open `metadata`). *Evolves from:* `common.schema.json`.
*Aligns with:* JSON Schema 2020-12. *Disposition:* **Keep** (the `metadata` open object is the
sanctioned extension point that lets core validation stay strict). *Priority:* **P0**. The ID
grammar is lifted verbatim from `CANON.md §6`; the OEAS profile generalizes the prefix set from
MCG-specific (`APP`, `TEAM`, `SVC`…) to a registered-namespace scheme so any adopting enterprise
can mint IDs without colliding.

**OEAS-Event (Enterprise Event envelope)** — *what it standardizes:* the immutable, timestamped
fact envelope that is the event-sourced substrate; every cognition artifact is carried as an event.
*Evolves from:* **New** — V1 has no explicit `event.schema.json`; its objects *are* facts but are
not enveloped. *Aligns with:* **CloudEvents 1.0** (§6.5). *Disposition:* **New**. *Priority:*
**P0**. This is the substrate the ontology calls non-negotiable (`Enterprise-AI-Ontology.md` §3).

### 6.2.2 Cognition objects (the Enterprise Cognition Loop — kept from V1)

**OEAS-Knowledge** — durable, governed enterprise truth (Belief). *Evolves from:*
`knowledge_object.schema.json`. *Aligns with:* JSON Schema. *Disposition:* **Keep/Extend** (add an
optional `memory_type` discriminator so Knowledge is recognizable as the *semantic* memory type in
the seven-type taxonomy). *Priority:* **P0**.

**OEAS-Context** — ephemeral, per-task working set; never persisted as durable truth. *Evolves
from:* `context_object.schema.json`. *Aligns with:* JSON Schema. *Disposition:* **Keep**.
*Priority:* **P1**.

**OEAS-Plan** — explicit, testable plan (BDI *Intention*). *Evolves from:*
`planning_object.schema.json`. *Aligns with:* JSON Schema. *Disposition:* **Keep/Extend** (add
optional `objective_ref` and `mission_ref` to connect plans to the newly first-class Objective and
Mission). *Priority:* **P1**.

**OEAS-Decision** — a single control decision with fused confidence, rationale, and policy verdict.
*Evolves from:* `decision_object.schema.json` (+ the run-scoped `worker_decision.schema.json`).
*Aligns with:* JSON Schema; emitted as OEAS-Event; the `decide` cognition span (§6.4). *Disposition:*
**Keep**. *Priority:* **P1**.

**OEAS-Execution** — record of a plan step executed via a tool, producing artifacts. *Evolves
from:* `execution_object.schema.json` (+ `worker_execution.schema.json`). *Aligns with:* JSON
Schema; **OpenTelemetry** `act` spans (§6.4); the `tool` field aligns to **MCP** (§6.6).
*Disposition:* **Keep/Extend** (add optional `otel.trace_id`/`span_id` correlators). *Priority:*
**P1**.

**OEAS-Evaluation** — scored, evidence-linked judgment of an execution (objective-first; no score
without evidence; dual confidence). *Evolves from:* `evaluation_object.schema.json`. *Aligns with:*
JSON Schema. *Disposition:* **Keep/Extend** (add optional `outcome_ref` linking the judgment to a
first-class Outcome). *Priority:* **P0** — this is the *task/eval format* that the benchmark and any
conformance test depend on.

**OEAS-Reflection** — root-cause reasoning about an evaluated outcome. *Evolves from:*
`reflection_object.schema.json`. *Aligns with:* JSON Schema; `reflect` cognition span. *Disposition:*
**Keep**. *Priority:* **P1**.

**OEAS-Memory-record** — *what it standardizes:* a governed, situation-linked memory item across the
seven memory types (semantic, episodic, procedural, temporal, organizational, policy, execution) with
trust/decay attributes (provenance strength, corroboration, contradiction rate, measured utility).
*Evolves from:* `experience_object.schema.json` — V1's `ExperienceObject` is exactly *one* memory
type (experiential/procedural) and already carries `value.{corroboration,contradiction_rate,
outcome_lift,application_frequency}` and a lifecycle `status`. *Aligns with:* JSON Schema.
*Disposition:* **Promote** — generalize Experience into a `memory_type`-discriminated record so
episodic/temporal/organizational memory become expressible without breaking the Experience shape (V1
`EXP-###` instances remain valid as `memory_type: "experiential"`). *Priority:* **P1**.

**OEAS-Learning-event** — a discrete change to durable memory or policy, with a `loop_closed` flag.
*Evolves from:* `learning_event.schema.json`. *Aligns with:* CloudEvents (it is literally an event);
JSON Schema for the payload. *Disposition:* **Keep**. *Priority:* **P2**.

**OEAS-Worker-artifact** — a concrete artifact produced by execution (PR, test run, commit, …).
*Evolves from:* `worker_artifact.schema.json`. *Aligns with:* JSON Schema. *Disposition:* **Keep**.
*Priority:* **P2**.

### 6.2.3 New primitives (invented — no standard exists)

These are the ontology's primitives that V1 never made first-class. Inventing them is the substance
of OEAS's additive value; each is a *new* JSON Schema document, all P0/P1 because they close the
holes the ontology review named as fatal.

**OEAS-Objective** — a desired change in world-state: a target state or a target delta on a
measurable, with the collapsed `intent` (reason/trigger) and `metric`/`target` as attributes (the
ontology folds Goal and Intent into Objective — three layers were one primitive). *Evolves from:*
**New** (V1 `PlanningObject.intent` is a free-text string only). *Aligns with:* JSON Schema.
*Disposition:* **New**. *Priority:* **P0** — the ontology names the Objective as "the single most
important concept EnterpriseSim was missing."

**OEAS-Outcome** — observed world-delta attributable to actions, measured against an Objective.
*Evolves from:* **New**. *Aligns with:* JSON Schema; produced as an OEAS-Event; the settlement target
of an Evaluation. *Disposition:* **New**. *Priority:* **P0**. Outcomes must be *measured, not
asserted* — the schema forbids a verdict without an evidence reference (mirroring V1's `ADR-0016`
"no score without evidence").

**OEAS-Constraint/Policy** — a boundary on states/actions (permitted/required/forbidden); a Policy
is a governed set of Constraints. *Evolves from:* **New**, though embryonic in
`decision_object.schema.json`'s `policy_verdict` (`allowed`/`reason`/`requires_human`). *Aligns
with:* JSON Schema. *Disposition:* **New**. *Priority:* **P1**. The Constraint schema is the target
that `policy_verdict.reason` references.

**OEAS-Capability** — a repeatable competence (skill/procedure) an Actor can exercise, with success
statistics. *Evolves from:* **New**. *Aligns with:* JSON Schema. *Disposition:* **New**. *Priority:*
**P1**.

**OEAS-Mission** — an Actor committing to pursue Objective(s) under Constraints over time,
accountably; the operational unit of accountable work. *Evolves from:* **New**. *Aligns with:* JSON
Schema; its lifecycle is an OEAS-Event stream. *Disposition:* **New**. *Priority:* **P0** — the
operational root of the whole ontology.

**OEAS-Actor** — anything that can perceive→decide→act: human, AI, or system, modeled uniformly.
*Evolves from:* **Promote** — V1 encodes actors only as the `worker` *string* on
`worker_decision`/`worker_execution` and as `TEAM-###` owner IDs. *Aligns with:* JSON Schema.
*Disposition:* **New/Promote**. *Priority:* **P1**. Unifying human + AI + system is required for
governance and accountability (do not privilege the AI worker; do not bolt humans on).

**OEAS-Asset** — a durable thing with identity and state (system, dataset, artifact). *Evolves
from:* **Promote** — V1 has `APP-`, `SVC-`, `REPO-` ID conventions in `CANON.md §6` but no asset
schema. *Aligns with:* JSON Schema. *Disposition:* **Promote**. *Priority:* **P2**.

### 6.2.4 Interfaces & telemetry (align to existing wire standards)

**OEAS-Cognition-Telemetry** — OpenTelemetry semantic conventions for agent/worker cognition spans.
*Evolves from:* the V1 decision/execution traces (`worker_decision.trace_seq`,
`worker_execution.run_id`). *Aligns with:* **OpenTelemetry**. *Disposition:* **New** (semantic
conventions). *Priority:* **P0** — the flagship contribution (§6.4).

**OEAS-Tool (Action interface)** — the external-action surface onto Assets. *Evolves from:*
**Promote** — V1's `execution_object.tool` / `planning_object.steps[].tool` are free strings.
*Aligns with:* **Model Context Protocol (MCP)** (§6.6). *Disposition:* **New/Promote**. *Priority:*
**P1**.

**OEAS-Worker-Interface (Runtime API)** — the HTTP contract a runtime implements to accept Missions,
stream cognition events, and return Outcomes/Evaluations. *Evolves from:* **New** (V1's `sdk/`
interfaces are Python, not a wire API). *Aligns with:* **OpenAPI 3.1** (§6.7). *Disposition:*
**New**. *Priority:* **P1**.

## 6.3 Specification disposition matrix

| Spec | Evolves-from (V1 file / concept) | Aligns-with | Disposition | Priority |
|---|---|---|---|---|
| OEAS-Common | `common.schema.json` | JSON Schema 2020-12 | Keep | P0 |
| OEAS-Event | *(none — new envelope)* | CloudEvents 1.0 | New | P0 |
| OEAS-Objective | *(none; `PlanningObject.intent` string)* | JSON Schema | New | P0 |
| OEAS-Outcome | *(none)* | JSON Schema | New | P0 |
| OEAS-Mission | *(none)* | JSON Schema | New | P0 |
| OEAS-Evaluation | `evaluation_object.schema.json` | JSON Schema | Keep/Extend | P0 |
| OEAS-Knowledge | `knowledge_object.schema.json` | JSON Schema | Keep/Extend | P0 |
| OEAS-Cognition-Telemetry | decision/execution traces (`trace_seq`,`run_id`) | OpenTelemetry | New | P0 |
| OEAS-Context | `context_object.schema.json` | JSON Schema | Keep | P1 |
| OEAS-Plan | `planning_object.schema.json` | JSON Schema | Keep/Extend | P1 |
| OEAS-Decision | `decision_object.schema.json`, `worker_decision.schema.json` | JSON Schema + OTel | Keep | P1 |
| OEAS-Execution | `execution_object.schema.json`, `worker_execution.schema.json` | JSON Schema + OTel + MCP | Keep/Extend | P1 |
| OEAS-Reflection | `reflection_object.schema.json` | JSON Schema | Keep | P1 |
| OEAS-Memory-record | `experience_object.schema.json` | JSON Schema | Promote | P1 |
| OEAS-Constraint/Policy | `decision_object.schema.json` `policy_verdict` (embryonic) | JSON Schema | New | P1 |
| OEAS-Capability | *(none)* | JSON Schema | New | P1 |
| OEAS-Actor | `worker` string, `TEAM-###` | JSON Schema | New/Promote | P1 |
| OEAS-Tool | `execution_object.tool` string | MCP | New/Promote | P1 |
| OEAS-Worker-Interface | `sdk/` Python interfaces | OpenAPI 3.1 | New | P1 |
| OEAS-Learning-event | `learning_event.schema.json` | CloudEvents + JSON Schema | Keep | P2 |
| OEAS-Worker-artifact | `worker_artifact.schema.json` | JSON Schema | Keep | P2 |
| OEAS-Asset | `APP-`/`SVC-`/`REPO-` IDs (`CANON.md §6`) | JSON Schema | Promote | P2 |

## 6.4 Flagship contribution — OpenTelemetry semantic conventions for cognition

The single cheapest, highest-value standards contribution flagged across the reviews is to make
agent reasoning **observable with the tooling the industry already runs**. Rather than invent a new
tracing system, OEAS proposes a set of **OpenTelemetry semantic conventions** (an `agent.cognition.*`
attribute namespace and a fixed span vocabulary) so that any OTel backend — Jaeger, Tempo, Honeycomb,
vendor APM — can display and query enterprise-agent cognition with zero bespoke code.

**Span vocabulary (six cognition span kinds).** Each maps to a phase of the modernized-BDI/CoALA
loop and to a V1 artifact:

| Span name | Cognition phase | V1 artifact it wraps | Emits / correlates |
|---|---|---|---|
| `cognition.retrieve` | assemble working set | `context_object.schema.json` | context assembly, budget, hit-ratio |
| `cognition.plan` | form intention | `planning_object.schema.json` | plan id, step count, applied experience |
| `cognition.decide` | select action | `decision_object.schema.json` | choice, fused + per-layer confidence, policy verdict |
| `cognition.act` | external action via tool | `execution_object.schema.json` | tool name (MCP), status, artifacts |
| `cognition.evaluate` | judge outcome vs objective | `evaluation_object.schema.json` | verdict, score, dual confidence |
| `cognition.reflect` | root-cause + lesson | `reflection_object.schema.json` | root-cause category, lesson refs |

A Mission is the **root span**; a Worker run is a child trace; `cognition.*` spans nest beneath.
This gives V1's existing correlators a natural OTel home: `worker_execution.run_id` → OTel
`trace_id`; `worker_decision.trace_seq` → span ordering; each object's `id` → a span attribute so the
trace links back to the schema-valid record.

**Attribute conventions (mapping to the ontology).** Proposed stable attributes (namespaced
`agent.cognition.*` to avoid collision with future OTel GenAI conventions, which we track and
converge with):

- `agent.cognition.actor.id`, `agent.cognition.actor.kind` (`human|ai|system`) — the Actor primitive.
- `agent.cognition.mission.id`, `agent.cognition.objective.id`, `agent.cognition.objective.metric` —
  Mission/Objective linkage so every span answers "in service of what."
- `agent.cognition.confidence.fused` and `agent.cognition.confidence.<layer>` — the fused/per-layer
  confidences already modeled in `decision_object` `inputs`.
- `agent.cognition.policy.allowed`, `agent.cognition.policy.requires_human` — from `policy_verdict`.
- `agent.cognition.outcome.attained` and `agent.cognition.evaluation.score` — outcome-verification.
- `agent.cognition.memory.type` — which of the seven memory types a `retrieve` span drew on.

**Why this wins.** It is additive (V1 objects are unchanged; spans reference them by `id`), it rides
a ratified CNCF standard, it makes cognition auditable/replayable, and it is the one deliverable a
vendor can adopt in an afternoon. It is the wedge that gets OEAS into runtimes before the schemas do.
Proposed path: a public OTel semantic-convention proposal, then submission to the OpenTelemetry
Semantic Conventions repo (see timeline, §6.9).

## 6.5 CloudEvents mapping for Enterprise Events

Every cognition artifact is a *fact* — the ontology's substrate is an immutable event log. OEAS
adopts **CloudEvents 1.0** as the envelope and defines a binding for OEAS objects:

| CloudEvents attribute | OEAS binding |
|---|---|
| `id` | the object's canonical ID (`common.schema.json` `canonicalId`), globally unique, never reused |
| `source` | the emitting Actor/runtime URI (`agent.cognition.actor.id`) |
| `type` | `dev.oeas.<object>.<lifecycle>`, e.g. `dev.oeas.decision.made`, `dev.oeas.evaluation.scored`, `dev.oeas.learning.loop_closed` |
| `time` | the object's `created_at` (`common.schema.json` `timestamp`) |
| `dataschema` | the object's JSON Schema `$id` — the envelope self-describes which OEAS schema validates `data` |
| `datacontenttype` | `application/json` |
| `data` | the schema-valid OEAS object itself |
| `subject` | the Mission or Objective the event advances |

Extension attributes carry `sensitivity` (from `common.schema.json`) so classification travels with
the event (V1 `ADR-0043`), and the schema version. CloudEvents' HTTP, Kafka, and NATS bindings then
come for free — OEAS never defines a transport. The **Learning-event** and **Outcome** objects are
the most natural CloudEvents citizens, but *all* OEAS objects are emittable as events; persistence is
an append-only log of these envelopes, and Memory is a projection over it (per ontology §3).

## 6.6 MCP mapping for Tools / Actions

V1 represents the action surface only as a free-text `tool` string on `execution_object` and
`planning_object.steps[]`. OEAS promotes it to the **Model Context Protocol (MCP)** so tools and
connectors are discoverable and governable:

- An OEAS **Tool** corresponds to an MCP **tool/resource** exposed by an MCP server; the V1 `tool`
  string becomes a qualified MCP tool name.
- `execution_object.directives` maps to MCP tool **input arguments**; `worker_artifact` entries map
  to MCP tool **results/resources**.
- **Governance rides the boundary:** an OEAS Constraint/Policy gates which MCP tools an Actor may
  invoke; the `decision_object.policy_verdict` is evaluated *before* the MCP call, and
  `requires_human` maps to a human-approval interrupt. This keeps tool grants inside the standard's
  policy plane rather than inside each runtime.

OEAS does not fork MCP; it defines the *binding* (how an Execution event references an MCP
invocation) and the *governance overlay* (policy pre-checks on tool grants).

## 6.7 OpenAPI 3.1 for runtime APIs

The **Worker-Interface** is the HTTP contract any runtime implements to be OEAS-conformant, published
as an **OpenAPI 3.1** document (3.1 because it uses JSON Schema 2020-12 as its schema dialect — the
same dialect as every OEAS object, so schemas are shared, not duplicated). Minimum surface:

- `POST /missions` — submit a Mission (Objectives + Constraints + Actor assignment); returns a
  Mission ID.
- `GET /missions/{id}/events` — stream the CloudEvents cognition log (SSE/webhook) for that Mission.
- `GET /missions/{id}/outcome` — the outcome-verified Outcome + Evaluation.
- `GET /capabilities`, `GET /tools` — advertise Capabilities and MCP-backed Tools for conformance
  discovery.

The OpenAPI document's `components.schemas` `$ref` the OEAS object schemas directly. This is what lets
the benchmark score any runtime uniformly: submit Missions, read Outcomes, compare against the eval
protocol — "the world and the ruler," with runtimes as interchangeable players.

## 6.8 Versioning & compatibility rules

1. **OEAS v1 = V1 schema set + additive new objects.** Adopting OEAS never invalidates a V1
   `2020-12.v1` instance. This is the load-bearing promise.
2. **SemVer semantics (V1 `ADR-0032`).** Additive/optional field = **minor**; a new object schema =
   **minor**; a required-field addition, type change, or field removal = **major**. The
   `schema_version` pattern `^2020-12\.v\d+$` in `common.schema.json` carries the minor line; the
   OEAS spec version (`oeas.v1`, `oeas.v2`) carries the major line.
3. **Expand → migrate → contract (V1 `ADR-0033`).** New fields land optional (expand); producers
   dual-write and backfill; only after no producer emits the old shape may a field become required or
   be removed (contract). Instances are never rewritten in place — new versions are new records.
4. **Backward-compatibility window.** Validators MUST accept the current and previous *major* OEAS
   version during a migration window (proposed ≥ 18 months); readers MUST tolerate unknown
   `metadata` and unknown extension attributes.
5. **Referential integrity is invariant (V1 `ADR-0022`).** Canonical IDs never change meaning across
   versions; any change that would break a cross-reference requires a recorded decision (the OEAS
   analogue of an ADR).
6. **`metadata` is the only place for unblessed extension.** Core validation stays strict
   (`unevaluatedProperties: false` on every object); vendors extend via the open `metadata` object,
   never by adding top-level fields.
7. **Deprecation, not deletion.** Deprecated objects/fields are marked and retained through at least
   one major cycle with published migration notes; nothing is silently removed.

## 6.9 Phased standardization timeline

Three tracks — **draft → community review → foundation submission → ratification** — sequenced across
three release trains. Priorities from §6.3 gate what enters each train.

**V1.5 — "Additive core" (draft + community review).**
- Publish OEAS-Common, OEAS-Event (CloudEvents binding), and the P0 *new* schemas: Objective,
  Outcome, Mission — as **drafts** on the foundation site, `$id`-aliased to the frozen V1 namespace.
- Publish the **OpenTelemetry cognition semantic-convention** proposal (§6.4) as a public draft and
  open an upstream OTel discussion — the flagship, shipped first because it is cheapest and highest
  signal.
- Keep/Extend the P0 cognition objects (Evaluation, Knowledge) with additive `objective_ref`/
  `outcome_ref`/`memory_type`. **No breaking change; V1 instances still validate.**
- Exit criterion: two independent implementations round-trip the P0 objects and emit conformant OTel
  spans.

**V2 — "Interfaces & governance" (community review → foundation submission).**
- Promote/define the P1 specs: Actor, Capability, Constraint/Policy, Memory-record (generalized from
  Experience), Tool (MCP binding), and the Worker-Interface OpenAPI 3.1 contract.
- Submit the OTel semantic conventions **upstream to OpenTelemetry Semantic Conventions**; submit the
  OEAS object suite + CloudEvents binding to the chosen neutral foundation.
- Stand up the **conformance test suite** (does a runtime accept Missions, stream conformant events,
  return outcome-verified Evaluations?) reusing V1's dependency-free structural validator approach
  from `schemas/README.md`.
- Exit criterion: foundation accepts the specification into its standards process; ≥ 3 runtimes pass
  conformance.

**V3 — "Ratification & certification" (foundation submission → ratification).**
- Ratify OEAS v1 as a foundation specification; publish the P2 additions (Asset, Learning-event,
  Worker-artifact) as ratified.
- Launch **conformance certification** and a public conformance registry; the benchmark
  leaderboard consumes certified runtimes only.
- Begin the OEAS v2 major line under the compatibility window rules (§6.8).

## 6.10 Governance of the standard

- **Neutral home.** Donate OEAS to a vendor-neutral foundation (CNCF is the natural fit given the
  CloudEvents + OpenTelemetry alignment; Linux Foundation / an OpenSSF-style sibling are alternates).
  The specification must not be owned by any single runtime vendor, or scores and conformance become
  meaningless — the MLPerf/SWE-bench lesson from the ontology review (§7).
- **Working-group structure.** A Technical Steering Committee owns the spec; sub-working-groups mirror
  the catalog (Objects, Event/Telemetry, Interfaces). Changes flow through public proposals — the OEAS
  analogue of V1's RFC (contract change) and ADR (invariant change) process, preserving the
  "provenance of change" discipline from `schemas/README.md`.
- **Conformance & certification.** Two levels: **(a) Schema-conformant** — artifacts validate against
  OEAS schemas and events carry the CloudEvents binding; **(b) Runtime-conformant** — implements the
  OpenAPI Worker-Interface, emits OTel cognition spans, and returns outcome-verified Evaluations.
  Certification is self-test + published results against the open conformance suite; the registry is
  public.
- **Separation of powers.** The standard (interfaces/protocol) is governed by the foundation; the
  benchmark/leaderboard (the ruler) is governed neutrally alongside it; runtimes (the players) are
  commercial and compete *on* the open benchmark. OEAS defines only the first.

## 6.11 What must NOT become a standard

Standardizing these would freeze the very things that must compete and improve. They are explicitly
out of scope (consistent with `Enterprise-AI-Ontology.md` §7):

- **Implementation algorithms** — context ranking, memory-graph internals, trust/decay scoring,
  decision optimization, calibration, credit assignment, consolidation ("sleep") heuristics. These
  are where runtimes differentiate on quality/latency/cost; standardize the *inputs and outputs*
  (schemas + spans), never the method.
- **Model choice, prompts, and the reasoning loop internals** — the cognitive architecture is a
  recombination and will be superseded; standardizing it would ossify a transient design.
- **Production operational concerns** — multi-tenancy, SLAs, storage engines, indexing physics,
  autoscaling. Product concerns, not interoperability contracts.
- **Benchmark internals beyond the task/eval format** — the *task specification* and the
  *Evaluation/Outcome schema* are standardized (so results are comparable); the scenario content,
  scoring harness internals, difficulty curation, and held-out sets are governed by the benchmark
  body, not frozen into the wire standard.
- **The reference enterprise (MCG) and illustrative traces** — teaching/seed material, explicitly not
  a normative part of the standard. The MCG-specific ID prefixes in `CANON.md §6` inform the ID
  *grammar* but are not themselves the standard.

## 6.12 Summary

OEAS is not a new framework — it is the **interoperability layer** distilled from EnterpriseSim V1.
Keep JSON Schema 2020-12; keep the eleven V1 objects (Keep/Extend); promote Experience→Memory-record,
the `tool` string→MCP Tool, and Actor/Asset from ID conventions to schemas; invent only the ontology
primitives V1 lacked (Objective, Outcome, Mission, Constraint/Policy, Capability). Envelope everything
in CloudEvents, expose runtimes via OpenAPI 3.1, and — the flagship move — ship **OpenTelemetry
semantic conventions for cognition** so agent reasoning is observable on tooling the world already
runs. Govern it neutrally, certify conformance, and standardize the contract while leaving the
algorithms to compete. That is the durable prize the ontology named: *making Enterprise AI measurable
and interoperable*, which is the only kind of reference architecture that survives a decade.
