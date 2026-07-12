# `sdk.context` — Context Layer

Interfaces for ephemeral, per-task working memory. Realizes **Context** (`CANON-001` §9,
Stage 2) per [`ARCH-01`](../../docs/architecture/01_context_layer.md). No implementation.

## Architecture

The Context Layer assembles the *right, minimal, sufficient* working set (`ContextObject`,
`CTX-###`) for a single task and holds it **only for that task** (`ADR-0006`: ephemeral). It
pulls from composable `Retriever`s (knowledge, experience, live state), ranks and selects
within the model's token budget (`BudgetPolicy`, enforced *before* the Gateway — never rely on
provider truncation), and records full provenance including a **dropped-candidate log** that
reflection later inspects. Context assembly is *iterative*: `enrich()` supports the Active
self-loop when reasoning surfaces new needs (`RFC-0002`).

## Python abstract interfaces

See [`interfaces.py`](interfaces.py): `ContextAssembler` (assemble / enrich /
coverage_confidence / expire), `Retriever` (Protocol), `BudgetPolicy`, and the `TaskIntent`
and `Candidate` value types.

## Extension points

- **Retrievers.** Implement `Retriever` per source; the assembler composes any set of them.
- **Budgeting.** Implement `BudgetPolicy` to change eviction/hysteresis strategy.
- **Ranking.** Subclass `ContextAssembler` to change selection; the Learning Engine tunes
  retrieval policy over time (`RFC-0017`).

## Responsibilities

Interpret intent, retrieve candidates, rank/select, compose within budget, maintain
provenance, track budget, emit coverage confidence, expire cleanly.

## Examples

```python
from sdk.context.interfaces import ContextAssembler, Retriever, TaskIntent

def build(asm: ContextAssembler, retrievers: list[Retriever]) -> None:
    intent = TaskIntent(task_ref="CHK-1421", goal="support guest checkout",
                        constraints=["no APP-015 side effect"],
                        success_criteria=["guest can place order"], apps=["APP-003"])
    ctx = asm.assemble(intent, retrievers)
    print(ctx.id, asm.coverage_confidence(ctx))
```

## Future evolution

Learned retrieval policies, predictive pre-fetch, hierarchical/streaming context, cross-Worker
context reuse, and confidence-calibrated budgets (see `ARCH-01` §Future Evolution).
