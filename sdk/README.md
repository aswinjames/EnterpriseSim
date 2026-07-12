# EnterpriseSim SDK

> The **abstract contract layer** for the Enterprise Cognitive Layer (ECL). Interfaces
> only — **no implementation**. This is what a team of senior Python engineers builds
> against.

The SDK translates the architecture in [`../docs/architecture/`](../docs/architecture/)
into precise, typed Python interfaces (`abc.ABC` and `typing.Protocol`) and the object
contracts they exchange. It is governed by [`../CANON.md`](../CANON.md) (`CANON-001`) and
subordinate to the frozen ECL architecture (`ARCH-01`…`ARCH-07`).

## Principles

- **No implementation.** Every method body is `...`. The SDK defines *what*, never *how*.
- **Model-agnostic.** Only `sdk.models` touches providers; everything else is provider-free.
- **Domain-agnostic.** `sdk.workers` specializes the shared core at four edges: knowledge
  domains, tools, rubrics, policies. New Worker types add specializations, not architecture.
- **Contract-first.** In-code object Protocols in [`objects.py`](objects.py) mirror the JSON
  Schemas in [`../schemas/`](../schemas/). The schema is the source of truth for shape; the
  Protocols are the typing surface.

## Module map

| Module | Component (ECL doc) | Produces / owns | Key interfaces |
|---|---|---|---|
| [`knowledge/`](knowledge/) | Knowledge Layer (`ARCH-02`) | `KnowledgeObject` | `KnowledgeStore`, `KnowledgeRetriever`, `KnowledgeIndex` |
| [`context/`](context/) | Context Layer (`ARCH-01`) | `ContextObject` | `ContextAssembler`, `Retriever`, `BudgetPolicy` |
| [`planner/`](planner/) | Decision Intelligence (`ARCH-06`) | `PlanningObject` | `Planner`, `PlanValidator` |
| [`decision/`](decision/) | Decision Intelligence (`ARCH-06`) | `DecisionObject`, `WorkerDecision` | `Orchestrator`, `ConfidencePolicy`, `PolicyGuard` |
| [`execution/`](execution/) | Execution Runtime | `ExecutionObject`, `WorkerArtifact` | `ExecutionRuntime`, `Tool`, `ToolRegistry` |
| [`evaluation/`](evaluation/) | Evaluation Layer (`ARCH-04`) | `EvaluationObject` | `Evaluator`, `Rubric`, `ObjectiveGate` |
| [`experience/`](experience/) | Experience Layer (`ARCH-03`) | `ExperienceObject` | `ExperienceStore`, `ExperienceRetriever` |
| [`learning/`](learning/) | Learning Engine (`ARCH-05`) | `ReflectionObject`, `LearningEvent` | `Reflector`, `LearningEngine`, `PromotionPolicy` |
| [`models/`](models/) | Model Gateway (`ARCH-07`) | model calls | `ModelGateway`, `ModelProvider`, `ModelRouter`, `CapabilityDescriptor` |
| [`workers/`](workers/) | Enterprise AI Worker | Worker runs | `Worker`, `WorkerSpec`, `WorkerRuntime` |

Shared object contracts live in [`objects.py`](objects.py); package metadata in
[`__init__.py`](__init__.py).

## How the modules compose (one task)

```
workers.Worker.run(trigger)
   └─ decision.Orchestrator          # interpret intent, drive the loop
        ├─ context.ContextAssembler  # assemble CTX-### from knowledge + experience + state
        │     ├─ knowledge.KnowledgeRetriever
        │     └─ experience.ExperienceRetriever
        ├─ planner.Planner           # produce PLAN-###
        ├─ models.ModelGateway       # route reasoning to a provider (agnostic)
        ├─ execution.ExecutionRuntime# act via tools -> WorkerArtifact(s)
        ├─ evaluation.Evaluator      # score -> EVAL-###
        └─ learning.LearningEngine   # reflect -> REF-###, EXP-###, LearningEvent(s)
```

## Extension points (summary)

Every module documents its extension points in its own README. The recurring pattern:
implement the module's abstract interface, register it (via plugin entry points, see
`RFC-0027`), and the ECL runtime wires it in. Workers additionally supply a `WorkerSpec`
that binds knowledge domains, tools, rubrics and policies.

## Status

Foundation Phase artifact. Interfaces are versioned (`sdk.__version__`) and target a
schema version (`sdk.SCHEMA_VERSION`). Breaking changes follow `RFC-0021` (schema
versioning) and the SemVer policy in `ADR-0032`.
