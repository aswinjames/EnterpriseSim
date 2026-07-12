# EnterpriseSim Architecture — The Enterprise Cognitive Layer (ECL)

This folder defines the **permanent architecture of EnterpriseSim**: the **Enterprise
Cognitive Layer (ECL)**, the reusable intelligence architecture that every Enterprise AI
Worker runs on.

> EnterpriseSim provides the **enterprise** (Meridian Commerce Group, see [`../../CANON.md`](../../CANON.md)).
> The ECL provides the **intelligence**.

The founding constraint: **the LLM is stateless**. All knowledge, memory, learning and
orchestration therefore live *outside the model*, in the ECL — which is what makes the
architecture both **model-agnostic** (OpenAI, Anthropic, Gemini, open-source, local SLMs, and
future providers) and **domain-agnostic** (QA, Finance, Privacy, Security, Recruitment,
Support, and future Workers).

## Reading order

Start with the master document, then read the layers.

| # | Document | Component | Concept(s) from `CANON-001` §9 |
|---|---|---|---|
| — | [`07_architecture.md`](07_architecture.md) | **Master architecture** (read first) | Whole system + diagrams |
| 01 | [`01_context_layer.md`](01_context_layer.md) | Context Layer | Context |
| 02 | [`02_knowledge_layer.md`](02_knowledge_layer.md) | Knowledge Layer | Knowledge |
| 03 | [`03_experience_layer.md`](03_experience_layer.md) | Experience Layer | Experience |
| 04 | [`04_evaluation_layer.md`](04_evaluation_layer.md) | Evaluation Layer | Evaluation |
| 05 | [`05_learning_engine.md`](05_learning_engine.md) | Learning Engine | Reflection, Learning |
| 06 | [`06_decision_intelligence.md`](06_decision_intelligence.md) | Decision Intelligence | Planning, Decision Intelligence, (Execution orchestration) |

## The ECL loop

```
Knowledge → Context → Planning → Decision Intelligence → Execution
     ↑                                                        │
     └── Learning ← Experience ← Reflection ← Evaluation ←────┘
```

Every task traverses this loop, and every loop leaves the durable memory (Knowledge +
Experience) richer than it found it — so the next task starts from a higher baseline, **with
the same stateless model**. This is CANON's continuous-improvement flywheel, realized.

## Document conventions

Each layer document follows the same structure: **Purpose · Responsibilities · Inputs ·
Outputs · Signals · Lifecycle · Relationships · Confidence · Failure Modes · Future Evolution
· Best Practices · Examples**, with Mermaid diagrams (component, sequence, lifecycle, and —
in `07` — deployment).

All documents are consistent with, and subordinate to, [`CANON-001`](../../CANON.md). Any
change that would contradict canon requires a formal Architecture Decision Record (ADR).
