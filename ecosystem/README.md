# Ecosystem — The Open Enterprise AI Blueprint (V2+)

> Forward-looking strategy + the **architecture→engineering bridge** for evolving
> **EnterpriseSim V1** (frozen) into a neutral, foundation-hosted **Open Enterprise AI
> ecosystem**. These are **planning artifacts**; no frozen V1 artifact is modified. Prime
> directive: **evolution over replacement**, backward compatibility first-class. Grounded in
> [`../review/`](../review/) (ontology + architecture studies).

## Read order

**Start here:** [`TERMINOLOGY.md`](TERMINOLOGY.md) — the canonical names (resolves every naming
collision; governs all new work). Then the bridge documents below.

## Documents

| Document | Role | Brief covers |
|---|---|---|
| [`TERMINOLOGY.md`](TERMINOLOGY.md) | **Canonical terminology** (source of truth for names) | Part 1 |
| [`ENTERPRISE_AI_ECOSYSTEM.md`](ENTERPRISE_AI_ECOSYSTEM.md) | Ecosystem vision, project structure, stable APIs, 10-year vision, self-review | Parts 2, 5, 9(vision), 11(vision) |
| [`ENTERPRISE_WORKER_SPECIFICATION.md`](ENTERPRISE_WORKER_SPECIFICATION.md) | **The normative contract (EWS)** every Worker follows | Part 4 |
| [`ENTERPRISE_WORKER_SDK_CHARTER.md`](ENTERPRISE_WORKER_SDK_CHARTER.md) | The developer framework charter | Part 5 |
| [`ENTERPRISE_REFERENCE_RUNTIME_CHARTER.md`](ENTERPRISE_REFERENCE_RUNTIME_CHARTER.md) | The open, educational reference executor charter | Part 6 |
| [`OPEN_STANDARDS_ROADMAP.md`](OPEN_STANDARDS_ROADMAP.md) | Which specs become standards (JSON Schema/CloudEvents/OTel/OpenAPI/MCP) | Part 7 |
| [`ENTERPRISESIM_V2_MIGRATION.md`](ENTERPRISESIM_V2_MIGRATION.md) | The complete V1→V2 migration matrix + roadmap | Part 3 |
| [`COMMUNITY_AND_GOVERNANCE.md`](COMMUNITY_AND_GOVERNANCE.md) | Foundation, TSC, WGs, contribution/release/certification | Part 10 |
| [`IMPLEMENTATION_READINESS.md`](IMPLEMENTATION_READINESS.md) | **DX + 5-sprint backlog + readiness verdict** | Parts 8, 9, 11 |

## The shape in one picture

A neutral **foundation** hosts five artifacts: the **Enterprise Worker Specification (EWS)** —
the standard (formerly working-titled "OEAS"; see `TERMINOLOGY.md`); **EnterpriseSim** (the
simulation environment + benchmark); the **Enterprise Worker SDK** (build Workers); the
**Enterprise Reference Runtime** (run Workers — simple, educational); and a **Conformance &
Certification** suite. The ecosystem owns the *world, the ruler, and the contract*; commercial
runtimes own the *engine* and compete on the open benchmark.

## Bottom line for engineers

The architecture phase is **complete** (see `IMPLEMENTATION_READINESS.md`). Engineering starts
with the **`ews` repo** (spec + schemas + `ews-validate`), milestone **M1 "Build & Validate a
Worker"** (Sprints 1–2), first release **EWS 0.9**. Every V1 artifact has a destination
(`ENTERPRISESIM_V2_MIGRATION.md`); zero hard deletions; V1→V1.5 is purely additive.

> **Terminology note:** documents authored before `TERMINOLOGY.md` may use the working title
> "OEAS" and the mark "OEAS-Conformant"; the canonical name is **Enterprise Worker
> Specification (EWS)** / **EWS-Conformant**. These aliases are reconciled at V1.5.
