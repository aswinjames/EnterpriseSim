# EnterpriseSim Connectors

> Designs for ingesting **external engineering signal** into EnterpriseSim's ECL objects —
> **metadata only, never proprietary content**.

Connectors turn observable, public engineering metadata into schema-valid
`KnowledgeObject` / `ContextObject` / `ExperienceObject` instances so Enterprise AI Workers
can be built and benchmarked against patterns drawn from real practice, while keeping the
project original, synthetic-in-composition, public and commercially usable (`ADR-0049`).

| Connector | Status | Design |
|---|---|---|
| **GitHub** | Design only (no implementation) | [`github/`](github/) — `GitHubConnector`, `RepositoryScanner`, `ArtifactExtractor`, `EnterpriseNormalizer` |

All connectors share a strict compliance boundary: **public sources only, engineering
metadata only, free text reduced to facts, license + provenance recorded on every object.**
See [`github/README.md`](github/README.md) for the full design.
