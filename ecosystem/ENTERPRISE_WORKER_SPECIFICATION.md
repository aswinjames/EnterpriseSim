# Enterprise Worker Specification (EWS)

> **Status:** Specification, v0.9 Draft (targets EWS 1.0 at ecosystem V2). **Stability
> target:** ≥ 10 years (the ecosystem's slowest-moving, most-stable contract). **Keywords:**
> MUST / SHOULD / MAY per RFC-2119. **Supersedes working title:** "OEAS" → EWS
> (see `TERMINOLOGY.md`). **Grounding:** the V1 JSON Schemas (`schemas/`, frozen) are EWS's
> byte-compatible baseline; `review/Enterprise-AI-Ontology.md` is the conceptual basis.

## Part 4.0 — Purpose

The Enterprise Worker Specification is the **contract every Enterprise AI Worker follows**,
independent of vendor, model, language or runtime. It defines *what the objects are*, *how a
Worker behaves over its lifecycle*, and *what it means to be conformant* — so that any
conformant Worker can run in any conformant runtime against any conformant environment
(including EnterpriseSim) and be evaluated comparably.

EWS is a **contract, not an implementation.** It specifies interfaces and object shapes; it
never mandates algorithms (ranking, memory scoring, decision optimization, learning) — those
are where runtimes compete.

## Part 4.1 — Scope

**In scope (normative):** the core object schemas; the Worker, Mission and Objective
lifecycles; the capability interfaces a Worker exposes; extension points; versioning and
compatibility rules; conformance levels and certification requirements.

**Out of scope (non-normative / other artifacts):** algorithms and heuristics; the benchmark
task content (EnterpriseSim); the SDK's ergonomics (EWSDK charter); deployment/ops.

## Part 4.2 — Core objects

All objects are JSON documents validating against EWS JSON Schemas (Draft 2020-12), each
carrying `id`, `schema_version` and `created_at` (the `eclObjectBase` from V1
`schemas/common.schema.json`, retained). IDs follow `CANON-001` §6 conventions
(`RUN`/`DEC`/`EXE` added by `ADR-0051`). Unknown fields MUST be ignored (forward
compatibility); the `metadata` object is the sanctioned extension escape hatch.

| Object | EWS status | V1 schema (baseline) | Normative summary |
|---|---|---|---|
| **Event** | New (P0) | *(none — new)* | Immutable, timestamped fact. MUST be append-only; MUST carry `actor`, `type`, `occurred_at`, `mission`. Enterprise Events SHOULD be CloudEvents-enveloped. The substrate all other records derive from. |
| **Actor** | New (P0) | *(none — new)* | An agent (human · AI · system). MUST carry `kind ∈ {human, ai_worker, system}` and identity. A **Worker** is an Actor with `kind: ai_worker`. |
| **Objective** | New (P0) | *(free text in `planning_object.intent`)* | A desired outcome. MUST carry `metric`, `target`, `direction ∈ {increase, decrease, maintain}`; SHOULD carry `baseline`, `weight`, `horizon`. Absorbs Goal (=measurable Objective) and Intent (=`reason`). |
| **Mission** | New (P0) | *(none — new)* | Actor(s) pursuing Objective(s) under Constraints over time. MUST carry `objectives[]`, `constraints[]`, `state`, `actors[]`, `intent`. The unit of accountable work. |
| **Constraint / Policy** | New (P1) | *(implicit: risk tiers, approvals)* | A boundary. MUST carry `hardness ∈ {hard, soft}`; hard constraints MUST be enforced before Action; soft constraints SHOULD enter the objective as penalties. |
| **Capability** | New (P1) | *(implicit: `WorkerSpec`)* | A repeatable competence. MUST carry `name`, `interface`, `version`. |
| **Worker** | Extend | `sdk.workers.WorkerSpec` | A `WorkerProfile` binding knowledge domains, tools, rubrics, policies (composition, not inheritance — `ADR-0024/0025`). MUST declare supported EWS version range. |
| **Knowledge** | Keep | `knowledge_object.schema.json` (`KN-###`) | Curated, versioned, fallible truth. Unchanged from V1. |
| **Memory record** | Extend | `experience_object.schema.json` | Generalized: MUST carry `memory_type ∈ {semantic, episodic, procedural, experiential, temporal, organizational, policy, execution}`. **V1 `experience_object` instances are valid EWS memory records with `memory_type: experiential`.** |
| **Context** | Keep | `context_object.schema.json` (`CTX-###`) | Ephemeral working set. Unchanged; MAY add `objectives`/`intent` conditioning (additive). |
| **Plan** | Keep | `planning_object.schema.json` (`PLAN-###`) | The committed Intention. MUST reference the Objectives each step advances (additive field). |
| **Decision** | Keep | `decision_object` / `worker_decision` | A recorded selection (an Event). Unchanged. |
| **Execution** | Keep | `execution_object` / `worker_execution` | A record of Action via Tools. Unchanged. |
| **Evaluation** | Extend | `evaluation_object.schema.json` (`EVAL-###`) | MUST score **Outcome vs Objective** (new) in addition to process/standards (V1). MUST link evidence (`ADR-0016`) and report dual confidence (`ADR-0017`). |
| **Outcome** | New (P0) | *(none — new)* | Observed world-delta attributable to Actions, measured against Objectives. MUST be **verified** (computed from Events), not asserted. |
| **Reflection** | Keep | `reflection_object.schema.json` (`REF-###`) | Root-cause reasoning (an Event). Unchanged. |
| **Learning event** | Keep | `learning_event.schema.json` | A governed change to Memory/Knowledge/Policy/Capability/calibration. Unchanged; learning MUST be recorded and reversible (`ADR-0034`; two-speed per `ADR-0052`). |
| **Tool** | Keep | `sdk.execution.ToolSpec` | External-action interface. SHOULD align with MCP. MUST declare `side_effects` and `least_privilege_scope` (`ADR-0042`). |

## Part 4.3 — Lifecycles

### Worker lifecycle (a run)
`bound → perceiving → retrieving → deliberating → deciding → (acting | collaborating |
re-retrieving | replanning) → evaluating → reflecting → proposing → done|escalated|aborted`.
A conformant Worker MUST emit an Event for each cognition step and MUST produce a decision
trace (`ADR-0021`). Re-entrancy and interruption MUST be supported (not a fixed linear pipeline).

### Mission lifecycle
`proposed → scoped (objectives+constraints) → active → (blocked ↔ active) → review → fulfilled |
superseded`. Fulfillment MUST be gated on **verified Outcome** vs Objectives, not on
process-completion alone.

### Objective lifecycle
`declared → measured (baseline) → pursued → (attained | shortfall) → closed`. An Objective
MUST be measurable; an unmeasurable "objective" is non-conformant.

## Part 4.4 — Extension points

Conformant extensions MUST be additive and MUST NOT break readers. Extension mechanisms:
capability plugins (entry points, `RFC-0027`); tool plugins (MCP); rubric packs; policy packs;
memory-type backends; the `metadata` field on any object. New object *kinds* MUST be introduced
via the EWS change process (foundation RFC + ADR), never ad hoc.

## Part 4.5 — Versioning

- **SemVer** on EWS. `schema_version` on every object embeds the spec line
  (`2020-12.v1` = V1 baseline; `2020-12.v2` = EWS 1.0 additive primitives).
- **Additive-only within a major** (expand-contract, `ADR-0033`): new optional fields/objects
  are MINOR; required-field or type changes are MAJOR and require adapters + ≥ 12-month notice.
- EWS 1.0 MUST be a strict superset of the frozen V1 schemas.

## Part 4.6 — Compliance rules (normative)

A Worker/runtime claiming EWS conformance MUST:
1. Accept and emit objects valid against its advertised EWS version range; ignore unknown fields.
2. Bind to a Mission and honor its Objectives and **hard** Constraints (hard-constraint
   violations are automatic non-conformance).
3. Enforce Policy **before** Action (`ADR-0041`).
4. Emit a complete, immutable decision trace and an Event per cognition step.
5. Produce Evaluations that measure **verified Outcomes** vs Objectives with linked evidence.
6. Record Learning as reversible, governed events; MUST NOT silently mutate governed stores.
7. Advertise supported EWS versions and capabilities via a capability descriptor (extends V1
   `sdk.models.CapabilityDescriptor`).

## Part 4.7 — Certification requirements

Two independent levels (see `COMMUNITY_AND_GOVERNANCE.md`):
- **EWS-Conformant (schema + protocol):** passes the conformance suite — all objects validate,
  lifecycles and compliance rules (§4.6) hold, version negotiation works. Self-attested +
  audited; grants the **"EWS-Conformant"** mark.
- **EnterpriseSim-Benchmarked (capability):** runs the EnterpriseSim benchmark under the
  reproducibility + contamination rules and publishes outcome-verified scores. Conformance is a
  prerequisite for a benchmark listing.

## Part 4.8 — Compatibility rules

Backward: a version MUST read all objects from the previous MAJOR (via adapter if needed).
Forward: unknown fields/objects MUST be tolerated, never rejected. Cross-runtime: any
EWS-conformant object MUST be portable between conformant runtimes without loss of required
semantics.

## Part 4.9 — Non-goals

EWS does **not**: mandate any algorithm; define the benchmark tasks (EnterpriseSim);
specify SDK ergonomics or CLIs (EWSDK); define deployment/scaling/ops; require a specific model
provider; or dictate storage engines for Memory/Knowledge. It specifies *contracts*, not
*engines*.

## Part 4.10 — Relationships

- **To EnterpriseSim:** EnterpriseSim is the reference **environment** that produces Missions,
  supplies Knowledge/Memory content and Events, and hosts the **benchmark** that scores
  EWS-conformant Workers. EnterpriseSim consumes EWS; EWS does not depend on EnterpriseSim.
- **To the Enterprise Worker SDK:** the SDK provides the language-level interfaces, base classes,
  CLI and testing tools that make EWS *buildable*. The SDK implements EWS contracts; EWS is the
  source of truth for shapes and rules. The V1 `sdk/` interfaces are the SDK's realization of
  this spec.
- **To the Enterprise Reference Runtime:** the canonical, simple, open implementation of EWS —
  the conformance oracle and teaching runtime.
