# EnterpriseSim RFCs

> **Request-for-Comments series for the Enterprise Cognitive Layer (ECL).** Owned by the
> Architecture Office (`TEAM-090`). Governed by [`../../CANON.md`](../../CANON.md) (`CANON-001`)
> and subordinate to the frozen architecture in [`../architecture/`](../architecture/)
> (`ARCH-01`…`ARCH-07`).

An RFC is the **design document** that realises an architectural invariant (recorded as an ADR)
as a concrete, reviewable contract against the `sdk/` interfaces and `schemas/` objects. The RFC
process, mandatory document structure, lifecycle, and referential-integrity rules are defined in
[`RFC-0001`](RFC-0001.md).

Hierarchy of authority: **`CANON-001` > ADR > RFC**. If an RFC and canon disagree, canon wins
(`ADR-0050`); the RFC is defective and must be revised.

## Index

All Foundation-phase RFCs are **Accepted**. IDs are zero-padded, immutable, and never reused
(`CANON-001` §6).

| RFC | Title | Status |
|---|---|---|
| [RFC-0001](RFC-0001.md) | ECL Architecture Overview & RFC Process | Accepted |
| [RFC-0002](RFC-0002.md) | Context Assembly Protocol | Accepted |
| [RFC-0003](RFC-0003.md) | Knowledge Retrieval Interface | Accepted |
| [RFC-0004](RFC-0004.md) | Experience Retrieval Interface | Accepted |
| [RFC-0005](RFC-0005.md) | Semantic Search & Hybrid Retrieval | Accepted |
| [RFC-0006](RFC-0006.md) | Knowledge Graph Model | Accepted |
| [RFC-0007](RFC-0007.md) | Decision Intelligence Control Loop | Accepted |
| [RFC-0008](RFC-0008.md) | Planner API | Accepted |
| [RFC-0009](RFC-0009.md) | Confidence Scoring Model | Accepted |
| [RFC-0010](RFC-0010.md) | Model Router | Accepted |
| [RFC-0011](RFC-0011.md) | Model Gateway & Provider Adapter Contract | Accepted |
| [RFC-0012](RFC-0012.md) | Execution Runtime & Tool Invocation Protocol | Accepted |
| [RFC-0013](RFC-0013.md) | Tool Selection & Capability Negotiation | Accepted |
| [RFC-0014](RFC-0014.md) | Evaluation Framework | Accepted |
| [RFC-0015](RFC-0015.md) | Rubric Definition Language | Accepted |
| RFC-0016 | Reflection Pipeline | Accepted |
| RFC-0017 | Learning Event Propagation & Policy Update | Accepted |
| RFC-0018 | Experience Promotion to Knowledge (Governance) | Accepted |
| RFC-0019 | Worker Lifecycle | Accepted |
| RFC-0020 | Worker Specialization Model | Accepted |
| RFC-0021 | Schema Versioning & Compatibility | Accepted |
| RFC-0022 | Object Identity & Referential Integrity | Accepted |
| RFC-0023 | Provenance & Decision Trace | Accepted |
| RFC-0024 | Replay Engine | Accepted |
| RFC-0025 | Benchmarking Harness | Accepted |
| RFC-0026 | Benchmark Scoring & Leaderboards | Accepted |
| RFC-0027 | Plugin Architecture & Extension Points | Accepted |
| RFC-0028 | Signals Bus & Observability | Accepted |
| RFC-0029 | Cost & Latency Budgeting | Accepted |
| RFC-0030 | Security, Policy Enforcement & Guardrails | Accepted |

## Normative contract ownership

Each `sdk.*` interface and each `schemas/*` object is normatively owned by exactly one RFC;
others may cite but not redefine it (`RFC-0001` §4.5). The map for the contract-defining band:

| RFC | Owns (normative) | Frozen source |
|---|---|---|
| RFC-0002 | `sdk.context.ContextAssembler`; `context_object.schema.json` | `ARCH-01` |
| RFC-0003 | `sdk.knowledge.KnowledgeRetriever`/`KnowledgeStore`; `knowledge_object.schema.json` | `ARCH-02` |
| RFC-0004 | `sdk.experience.ExperienceRetriever`/`ExperienceStore`; `experience_object.schema.json` | `ARCH-03` |
| RFC-0005 | `sdk.knowledge.KnowledgeIndex` (hybrid retrieval) | `ARCH-02` |
| RFC-0006 | Knowledge-graph relations of `knowledge_object.schema.json` | `ARCH-02` |
| RFC-0007 | `sdk.decision.Orchestrator`; `worker_decision.schema.json` | `ARCH-06` |
| RFC-0008 | `sdk.planner.Planner`/`PlanValidator`; `planning_object.schema.json` | `ARCH-06` |
| RFC-0009 | `sdk.decision.ConfidencePolicy`; the `Confidence` alias | `ARCH-06` |
| RFC-0010 | `sdk.models.ModelRouter` | `ARCH-07` |
| RFC-0011 | `sdk.models.ModelGateway`/`ModelProvider`/`CapabilityDescriptor` | `ARCH-07` |
| RFC-0012 | `sdk.execution.ExecutionRuntime`; `execution_object.schema.json`; `worker_artifact.schema.json` | `ARCH-07` |
| RFC-0013 | `sdk.execution.Tool`/`ToolRegistry`/`ToolSpec` | `ARCH-07` |
| RFC-0014 | `sdk.evaluation.Evaluator`/`ObjectiveGate`; `evaluation_object.schema.json` | `ARCH-04` |
| RFC-0015 | `sdk.evaluation.Rubric` (rubric definition language) | `ARCH-04` |

## Related ADRs

`ADR-0003` Learning Lives Outside the Model · `ADR-0004` Knowledge Immutable Once Published ·
`ADR-0005` Experience Append-Only · `ADR-0006` Context Ephemeral · `ADR-0008` DI Sole
Orchestrator · `ADR-0009` Single Model Gateway · `ADR-0010` Model-Agnostic by Invariant ·
`ADR-0011` Structured Context Not Prompt Strings · `ADR-0012` Capability Negotiation ·
`ADR-0013` Confidence Composable · `ADR-0014` Autonomy Gated on Confidence · `ADR-0015`
Objective-First Evaluation · `ADR-0016` No Score Without Evidence · `ADR-0017` Dual Confidence ·
`ADR-0018` Versioned Rubrics · `ADR-0019` Hybrid Retrieval · `ADR-0021` Decision Traces
Mandatory · `ADR-0042` Least-Privilege Tools · `ADR-0044` Local SLM Fallback.

---

*This index is consistent with `CANON-001` and lists all thirty EnterpriseSim RFCs.*
