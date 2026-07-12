# Architecture Decision Records

> The decision record for the **Enterprise Cognitive Layer (ECL)** and EnterpriseSim.

Architecture Decision Records (ADRs) capture *significant* architecture decisions and the
trade-offs behind them. They are written in the strict **Michael Nygard format** — **Context /
Decision / Consequences** — one decision per file at `ADR-000N.md`, zero-padded to four digits,
numbered globally and never reused (`ADR-0022`). ADRs are authored and owned by the
**Architecture Office (`TEAM-090`)** and are subordinate to `CANON-001` and the frozen ECL
architecture (`ARCH-01`…`ARCH-07`).

**ADRs are immutable once Accepted.** A decision is never edited in place; it is changed only by
a new ADR that supersedes it, preserving the full decision history (`ADR-0001`). Any change that
would contradict canon requires an ADR, and canon supremacy is itself recorded as `ADR-0050`.

## How to read an ADR

Each ADR states the **Context** (the forces at play and why a decision was needed), the
**Decision** (stated in active voice — "We will …"), and the **Consequences** (positive,
negative and neutral trade-offs). ADRs cross-reference the `CANON-`, `ARCH-`, `RFC-` and prior
`ADR-` IDs they depend on, so the decision graph is navigable.

## Catalog

All 50 ADRs. ADRs `0001`–`0025` are published in this folder; `0026`–`0050` complete the
catalog and are cross-referenced throughout.

| # | Title | Status |
|---|---|---|
| ADR-0001 | Record Architecture Decisions | Accepted |
| ADR-0002 | The LLM Is Stateless | Accepted |
| ADR-0003 | Learning Lives Outside the Model (No Fine-Tuning) | Accepted |
| ADR-0004 | Knowledge Objects Are Immutable Once Published | Accepted |
| ADR-0005 | Experience Is Append-Only | Accepted |
| ADR-0006 | Context Is Ephemeral | Accepted |
| ADR-0007 | Knowledge Is the Only Source of Enterprise Truth | Accepted |
| ADR-0008 | Decision Intelligence Is the Sole Orchestrator | Accepted |
| ADR-0009 | Single Model Gateway for All Provider Access | Accepted |
| ADR-0010 | Model-Agnostic by Structural Invariant | Accepted |
| ADR-0011 | Store Structured Context Objects, Not Prompt Strings | Accepted |
| ADR-0012 | Capability Negotiation Over Provider Assumptions | Accepted |
| ADR-0013 | Confidence Is Composable and Honest | Accepted |
| ADR-0014 | Autonomy Is Gated on Fused Confidence | Accepted |
| ADR-0015 | Objective-First Evaluation | Accepted |
| ADR-0016 | No Score Without Evidence | Accepted |
| ADR-0017 | Separate Outcome Confidence From Judgment Confidence | Accepted |
| ADR-0018 | Versioned Rubrics for Reproducible Benchmarks | Accepted |
| ADR-0019 | Hybrid Retrieval (Semantic + Keyword + Graph) | Accepted |
| ADR-0020 | Provenance Is Mandatory | Accepted |
| ADR-0021 | Decision Traces Are Mandatory | Accepted |
| ADR-0022 | Globally Unique, Never-Reused IDs | Accepted |
| ADR-0023 | Referential Integrity Across Artifacts | Accepted |
| ADR-0024 | Workers Are Domain-Agnostic | Accepted |
| ADR-0025 | Four Specialization Axes (Knowledge, Tools, Rubrics, Policies) | Accepted |
| ADR-0026 | Open Standards Over Proprietary Formats | Accepted |
| ADR-0027 | JSON Schema Draft 2020-12 as Contract Language | Accepted |
| ADR-0028 | Python as SDK Reference Language | Accepted |
| ADR-0029 | Abstract Interfaces Over Concrete Coupling | Accepted |
| ADR-0030 | Plugin Architecture via Entry Points | Accepted |
| ADR-0031 | Trunk-Based Development | Accepted |
| ADR-0032 | Semantic Versioning for SDK and Schemas | Accepted |
| ADR-0033 | Schema Evolution via Expand-Contract | Accepted |
| ADR-0034 | Loop Closure as the Definition of Learning | Accepted |
| ADR-0035 | Root-Cause Reflection Over Symptom Fixing | Accepted |
| ADR-0036 | Governed Promotion of Experience to Knowledge | Accepted |
| ADR-0037 | Deterministic Replay | Accepted |
| ADR-0038 | Signals Bus for Cross-Layer Observability | Accepted |
| ADR-0039 | Reasoning-Cost Budgets Are First-Class | Accepted |
| ADR-0040 | Human-in-the-Loop on Low Confidence / High Risk | Accepted |
| ADR-0041 | Policy Enforcement Before Execution | Accepted |
| ADR-0042 | Least-Privilege Tool Access | Accepted |
| ADR-0043 | Sensitivity Classification Travels With Data | Accepted |
| ADR-0044 | Local SLM as Availability Floor | Accepted |
| ADR-0045 | Idempotent Execution and Rollback Plans Required | Accepted |
| ADR-0046 | Freshness SLAs for Knowledge | Accepted |
| ADR-0047 | Experience Decay via Down-Weighting Not Deletion | Accepted |
| ADR-0048 | Benchmark Reproducibility Is Mandatory | Accepted |
| ADR-0049 | Apache-2.0 License and Synthetic-Only Content | Accepted |
| ADR-0050 | Canon Supremacy — Changes via ADR Only | Accepted |
| ADR-0051 | Extend ID Namespaces for the Reference Learning Corpus (RUN, DEC, EXE) | Accepted |

## Related

- `CANON-001` — [`../../CANON.md`](../../CANON.md) — authoritative enterprise + project canon.
- `ARCH-01`…`ARCH-07` — [`../architecture/`](../architecture/) — the frozen ECL architecture.
- RFCs — cross-team proposals (`RFC-###`), e.g. `RFC-0021` (schema versioning), `RFC-0027`
  (plugin entry points), referenced by the SDK and schema decisions.
