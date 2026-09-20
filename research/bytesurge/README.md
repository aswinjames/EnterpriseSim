# Reference Runtime — Algorithm Research

This directory contains design-only algorithm research for a reference runtime
implementing EnterpriseSim's ECL interfaces. It is part of the EnterpriseSim
project, under the same terms as the rest of this repository. See
[`NOTICE.md`](NOTICE.md).

## What this is

EnterpriseSim provides the **synthetic enterprise, the ECL architecture, the SDK
contracts, the schemas, the benchmarks and the learning corpus**. It deliberately
ships **interfaces, not algorithms** — the *how* behind each ECL layer is left
open.

This research designs the core algorithms a runtime would use to satisfy the
ECL contracts at enterprise scale. Each algorithm targets a specific
EnterpriseSim SDK interface:

| # | Algorithm | Satisfies (EnterpriseSim contract) |
|---|---|---|
| 01 | [Adaptive Context Ranking](01_adaptive_context_ranking.md) | `sdk.context.ContextAssembler` ranking/selection (`ARCH-01`, `RFC-0002`) |
| 02 | [Semantic Experience Similarity](02_semantic_experience_similarity.md) | `sdk.experience.ExperienceRetriever` (`ARCH-03`, `RFC-0004`) |
| 03 | [Decision Intelligence](03_decision_intelligence.md) | `sdk.decision.Orchestrator` control loop (`ARCH-06`, `RFC-0007`) |
| 04 | [Confidence Engine](04_confidence_engine.md) | `sdk.decision.ConfidencePolicy` (`ARCH-06`, `RFC-0009`) |
| 05 | [Reflection Engine](05_reflection_engine.md) | `sdk.learning.Reflector` (`ARCH-05`, `RFC-0016`) |
| 06 | [Learning Engine](06_learning_engine.md) | `sdk.learning.LearningEngine` (`ARCH-05`, `RFC-0017`) |

## Design-only

Every document is **design and analysis, no implementation.** Each follows the same
structure so approaches can be compared consistently:

1. Problem statement (and the EnterpriseSim interface it must satisfy)
2. Multiple approaches
3. Trade-offs
4. Advantages
5. Weaknesses
6. Computational complexity
7. Enterprise scalability
8. Explainability
9. **Recommendation** (the approach a runtime should adopt, and why)

## Relationship to the rest of EnterpriseSim

- This research **depends on** EnterpriseSim's open contracts (schemas, SDK
  interfaces) — never the reverse. No other part of EnterpriseSim depends on
  this directory.
- A runtime built from this research remains **model-agnostic** by honoring
  `sdk.models.ModelGateway` (`ADR-0009/0010`) and **learns outside the model**
  (`ADR-0003`).
- Runtime quality is measured by EnterpriseSim's benchmark suites
  ([`../../benchmarks/`](../../benchmarks/)) — the same open benchmark any
  runtime, reference or third-party, is scored on.
