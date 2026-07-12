# Ecosystem — The Open Enterprise AI Blueprint (V2+)

> Forward-looking strategy for evolving **EnterpriseSim V1** (frozen) into a neutral,
> foundation-hosted **Open Enterprise AI ecosystem**. These are **new planning artifacts**;
> no frozen V1 artifact is modified. Prime directive: **evolution over replacement**, backward
> compatibility first-class. Grounded in [`../review/Enterprise-AI-Ontology.md`](../review/Enterprise-AI-Ontology.md)
> and [`../review/EnterpriseSim-Architecture-Review.md`](../review/EnterpriseSim-Architecture-Review.md).

## The five blueprints

| # | Document | Covers |
|---|---|---|
| 1 | [`ENTERPRISE_AI_ECOSYSTEM.md`](ENTERPRISE_AI_ECOSYSTEM.md) | Ecosystem vision, core projects, canonical ontology, stable APIs, community strategy, ten-year vision, critical self-review (Parts 1–3, 5, 9–11) |
| 2 | [`ENTERPRISESIM_V2_MIGRATION.md`](ENTERPRISESIM_V2_MIGRATION.md) | The complete V1→V2 migration matrix, repo/folder/artifact mappings, compatibility matrix, SemVer, tooling, adapters, deprecation timeline, V1→V1.5→V2→V3 roadmap (Part 4) |
| 3 | [`ENTERPRISE_WORKER_SDK_CHARTER.md`](ENTERPRISE_WORKER_SDK_CHARTER.md) | Charter for the Enterprise Worker SDK (Part 7) |
| 4 | [`REFERENCE_RUNTIME_CHARTER.md`](REFERENCE_RUNTIME_CHARTER.md) | Charter for the open, educational Reference Runtime (Part 8) |
| 5 | [`OPEN_STANDARDS_ROADMAP.md`](OPEN_STANDARDS_ROADMAP.md) | Which specs become standards, aligned to JSON Schema / CloudEvents / OpenTelemetry / OpenAPI / MCP (Part 6) |

## The shape in one picture

A neutral **foundation** hosts five artifacts: **OEAS** (the specification/standard),
**EnterpriseSim** (the simulation environment + benchmark), the **Enterprise Worker SDK**
(build workers), the **Reference Runtime** (run workers — simple, educational), and a
**Conformance & Certification** suite. The ecosystem owns the *world, the ruler, and the
contract*; commercial runtimes own the *engine* and compete on the open benchmark.

## The migration promise

Every V1 artifact has a destination and a disposition (Keep / Extend / Move / Promote / …);
there are **zero hard deletions** and only two *amendments* (ADR-0003 scope; corpus framing),
both handled as supersede-with-pointer. V1 → **V1.5** is purely additive (no breaking changes);
the repo split to polyrepo happens at **V2** with history preserved and adapters in place; **V3**
standardizes and certifies. See document 2 for the full matrix.
