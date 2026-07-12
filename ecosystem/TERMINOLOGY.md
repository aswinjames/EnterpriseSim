# Canonical Terminology — The Open Enterprise AI Ecosystem

> **Status:** Normative terminology guide (Lead Maintainer, Draft-for-adoption).
> **Purpose:** end naming drift. One concept → one canonical name. This guide governs *future*
> work and documentation; it does **not** modify frozen V1 artifacts (V1 keeps its historical
> names; adapters/aliases bridge them). When any ecosystem document disagrees with this guide,
> **this guide wins going forward.**

## How to read this

Each entry gives: **Canonical name** · **Deprecated / alternative names** (do not use in new
work) · **Definition** · **Purpose** · **Repository owner** · **Lifecycle** (persistence &
mutability class from the ontology).

Ontology grounding: `review/Enterprise-AI-Ontology.md`. Project map: `ecosystem/README.md`.

---

## 1. The naming collisions, resolved

| Collision | Canonical | Ruling |
|---|---|---|
| Experience **vs** Memory | **Memory** (Enterprise Memory) | *Memory* is the concept; **Experience is one memory type** (experiential). "Experience Layer" is retired in new work. |
| Mission **vs** Objective | **both, distinct** | Not synonyms. **Mission** = the unit of accountable work; **Objective** = the desired outcome a Mission pursues. A Mission *has* Objectives. |
| Worker **vs** Actor | **Actor** (superset); **Worker** = AI Actor | An *Actor* is any agent (human · AI · system). A *Worker* is specifically an autonomous AI Actor. Use "Actor" when humans are included. |
| Enterprise Cognitive Layer (ECL) **vs** Enterprise Worker SDK | **both, distinct** | **ECL** = the *concept*: a Worker's inner cognitive cycle. **Enterprise Worker SDK** = the *project* that specifies/implements it. ECL is not a separate deliverable; it lives inside the SDK. |
| Reference Runtime **vs** Runtime | **Enterprise Reference Runtime** (the specific one) | "runtime" (lowercase, generic) = any spec-conformant executor. **Enterprise Reference Runtime** = the one open, educational reference implementation. |
| Enterprise State **vs** Context | **both, distinct** | **Enterprise State** = durable world state in the environment. **Context** = the *ephemeral* per-task working set a Worker assembles. Never interchange. |
| Learning Corpus **vs** Benchmark Dataset | **split into two** | **Reference Execution Traces** (the V1 `corpus/`, *illustrative*, not results) **and** the **Benchmark Dataset** (outcome-verified tasks). "Learning Corpus" is retired to avoid implying proven learning. |
| Specification: OEAS **vs** Enterprise Worker Specification | **Enterprise Worker Specification (EWS)** | The specification/standard is the **Enterprise Worker Specification (EWS)**. "OEAS / Open Enterprise AI Specification" was a working title in the ecosystem drafts → **treat as a deprecated alias of EWS**; the standards roadmap will be reconciled to "EWS" at V1.5. |
| Reference Enterprise **vs** EnterpriseSim | **both, distinct** | **Reference Enterprise** (Meridian Commerce Group / MCG) = the *content*; **EnterpriseSim** = the *project* (environment + benchmark) that contains it. |
| ECL "Layers" **vs** services/capabilities | **Platform Services** and **Worker Capabilities** | The V1 "layers" split: durable shared concerns are *Platform Services*; per-run cognition is *Worker Capabilities* (see ontology / SDK charter). "Layer" is retired as an architectural noun. |

---

## 2. Canonical glossary

### Primitives (ontology fundamentals)

| Canonical name | Deprecated/alt | Definition | Purpose | Owner | Lifecycle |
|---|---|---|---|---|---|
| **Event** | (none) | An immutable, timestamped fact that something occurred. | The event-sourced substrate of truth, audit, memory and learning. | EWS (schema), EnterpriseSim (log) | persistent · immutable |
| **Actor** | Agent | Any entity that perceives → decides → acts: human, AI, or system. | Unifies human + AI for governance and collaboration. | EWS | persistent · mutable |
| **Worker** | Enterprise Worker, AI Worker | An autonomous **AI Actor** bound to a Mission. | The buildable unit developers create. | EWSDK | ephemeral (run) / persistent (profile) |
| **Objective** | Goal, Intent (as free text) | A desired change in world-state, with a measurable target. Absorbs *Goal* (=measurable Objective) and *Intent* (=an Objective's reason). | The semantic center: source of value, evaluation and learning signal. | EWS | persistent · mutable |
| **Mission** | (new) | An Actor committing to pursue Objective(s) under Constraints over time, accountably. | The operational unit of accountable work. | EWS | persistent · mutable (state) |
| **Constraint** | Policy (when codified) | A boundary on states/actions: permitted, required, forbidden. | Safety/compliance/risk boundary for planning & decisions. | EWS | persistent · mutable |
| **Policy** | — | A governed, codified set of Constraints. | Enforced pre-action by Governance. | EWS | persistent · governed |
| **Knowledge** | (Knowledge Layer) | An Actor's curated, fallible, versioned model of truth. | Durable enterprise truth (business rules, architecture, contracts). | EWS (schema), EnterpriseSim (content) | persistent · versioned |
| **Capability** | Skill | A repeatable competence an Actor can exercise. | The procedural/skill axis; reusable competence. | EWSDK / EWS | persistent · improves |
| **Asset** | Entity | A durable thing with identity and state (system, dataset, artifact). | What Actions operate on. | EnterpriseSim | persistent · mutable |

### Memory (one concept, seven types — all projections over the Event log)

| Canonical name | Deprecated/alt | Definition | Owner | Lifecycle |
|---|---|---|---|---|
| **Memory** (Enterprise Memory) | Experience Layer, Experience Store | A governed, bitemporal, trust-scored **projection** over Events + Beliefs + Capability. | EWS (interface), runtime/commercial (impl) | persistent · index-mutable |
| **Semantic memory** | Knowledge (loosely) | Curated facts/truth. | — | — |
| **Episodic memory** | — | Specific past events (runs, incidents, decisions). | — | — |
| **Procedural memory** | Skills | Reusable playbooks/plans that worked. | — | — |
| **Experiential memory** | **Experience** (V1 first-class) | Distilled lessons. **This is the demoted V1 "Experience."** | — | — |
| **Temporal memory** | — | As-of-time / bitemporal views. | — | — |
| **Organizational memory** | — | Who knows/owns/decides. | — | — |
| **Policy / Execution memory** | — | Constraint history / action-trace (OTel) memory. | — | — |

### Cognition (Worker capabilities — the ECL, reframed)

| Canonical name | Deprecated/alt | Definition | Owner |
|---|---|---|---|
| **Cognitive Cycle** | Enterprise Cognitive Layer (as a standalone deliverable) | A Worker's inner loop: perceive → retrieve → deliberate/plan → decide → act → evaluate → reflect. | EWSDK (spec: EWS) |
| **Context** | Enterprise State (wrongly), Working Set | The ephemeral, per-task working set assembled for a decision. | EWSDK |
| **Plan** | Intention | A committed, revisable structure of intended Actions toward Objectives. | EWSDK |
| **Decision** | — | An Actor's recorded selection among actions (an Event). | EWSDK |
| **Evaluation** | — | A judgment of Outcome vs Objective + standards (an Event). | EWS (schema), EnterpriseSim (benchmark) |
| **Reflection** | — | An Actor's internal action producing lessons/Beliefs (an Event). | EWSDK |
| **Outcome** | — | The observed world-delta attributable to Actions, measured vs Objective. | EWS |
| **Learning** | Learning Engine (as a layer) | The governed process that updates Memory/Knowledge/Policy/Capability/calibration from outcome-verified Events. | EWSDK (hooks), runtime (impl) |
| **Tool** | — | The external-action interface onto Assets (MCP-aligned). | EWSDK / EWS |

### Projects, environment & standards

| Canonical name | Deprecated/alt | Definition | Owner | Release cadence |
|---|---|---|---|---|
| **Enterprise Worker Specification (EWS)** | **OEAS**, Open Enterprise AI Specification | The normative contract every Worker follows: core object schemas + lifecycle + interfaces + compliance/certification rules. | Foundation (Standards WG) | slow / LTS (≥ 10y stability target) |
| **EnterpriseSim** | (project keeps its name) | The simulation environment + reference enterprise + benchmark + datasets + reference connectors. | EnterpriseSim project | env ≥ 3y; benchmark by season |
| **Reference Enterprise** | (the content) | Meridian Commerce Group (MCG) — the synthetic enterprise inside EnterpriseSim. | EnterpriseSim | frozen (V1) + extended |
| **Enterprise Worker SDK (EWSDK)** | (SDK) | The developer framework/contracts to build Workers. | EWSDK project | developer-speed (minors) |
| **Enterprise Reference Runtime** | Reference Runtime, Runtime | The open, simple, educational, spec-conformant executor. | Runtime project | tracks SDK |
| **Conformance & Certification** | — | The neutral suite: "EWS-Conformant" mark + "EnterpriseSim-Benchmarked" leaderboard. | Foundation | tracks EWS |
| **Open Enterprise AI Foundation (OEAF)** | (working name) | The neutral governance host for all of the above. | — | — |
| **Reference Execution Traces** | Learning Corpus | The V1 `corpus/` bundles, *illustrative* (not empirical results). | EnterpriseSim | frozen (V1) |
| **Benchmark Dataset** | Learning Corpus (wrongly) | The outcome-verified benchmark tasks + held-out families. | EnterpriseSim (Benchmark WG) | seasons |

---

## 3. Rules for new work

1. Use only canonical names in new code, docs, schemas and issues. Deprecated names may appear
   only in a "formerly known as" note or in frozen V1 artifacts.
2. `Objective` is one concept — do not reintroduce separate "Goal"/"Intent" objects; they are
   attributes (`metric`/`target`, `reason`) of an Objective.
3. `Memory` is one interface with a `memory_type` discriminator — do not create type-specific
   top-level objects; V1 `experience_object` validates as `memory_type: experiential`.
4. Say **Enterprise Worker Specification (EWS)** for the standard; retire "OEAS" in new work.
5. Reserve "layer" for prose only; architecturally, things are **Platform Services** or
   **Worker Capabilities**.
6. Never conflate **Enterprise State** (durable) with **Context** (ephemeral).
