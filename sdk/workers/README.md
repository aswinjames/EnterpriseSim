# `sdk.workers` — Enterprise AI Worker

Interfaces for domain-agnostic Enterprise AI Workers. Ties the ECL together per
[`ARCH-07`](../../docs/architecture/07_architecture.md). No implementation.

## Architecture

A Worker is **domain-agnostic** (`ADR-0024`): it reuses the entire ECL core unchanged and is
defined only by a `WorkerSpec` binding **four specialization axes** (`ADR-0025`):

1. **Knowledge domains** — which `KN` corpora are in scope.
2. **Tools** — which enterprise capabilities it may act through (least-privilege, `ADR-0042`).
3. **Rubrics** — how its work is evaluated.
4. **Policies** — its guardrails (PCI, fairness, segregation-of-duties, ...).

A `WorkerRuntime.bind()` produces a ready `Orchestrator` from a spec; `Worker.run()` executes
one task end to end through the ECL loop; `Worker.replay()` deterministically re-runs a past
task for debugging and benchmarking (`RFC-0024`). Adding QA / Finance / Privacy / Security /
Recruitment / Support / future Workers requires *zero architectural change* — only a new
`WorkerSpec`. The worker lifecycle is specified in `RFC-0019`.

## Python abstract interfaces

See [`interfaces.py`](interfaces.py): `Worker` (run / replay), `WorkerRuntime` (bind), and the
`WorkerSpec` / `RunResult` value types.

## Extension points

- **New Worker type.** Provide a `WorkerSpec`; optionally subclass `Worker` for bespoke run
  behavior. No changes to the shared core.
- **Runtime.** Implement `WorkerRuntime` to wire the ECL components for your deployment.

## Responsibilities

Bind specializations to the shared core, run tasks through the full ECL loop, produce
`RunResult`s, and support deterministic replay.

## Examples

```python
from sdk.workers.interfaces import Worker, WorkerSpec

spec = WorkerSpec(
    name="privacy-worker",
    knowledge_domains=["privacy-policy", "data-lineage"],
    tools=["identity-service", "dsar-workflow"],
    rubrics=["RUBRIC-dsar"],
    policies=["pii-handling", "data-minimization"],
    default_routing={"difficulty": "medium"},
)

def handle(worker: Worker) -> None:
    result = worker.run(trigger="PRIV-204")   # a data-subject-access request
    print(result.status, result.run_id)
```

## Future evolution

Multi-Worker collaboration orchestrated by Decision Intelligence, shared context fragments
across Worker types, and a marketplace of `WorkerSpec`s and tool plugins (see `ARCH-07`
§Future Evolution, `RFC-0020`, `RFC-0027`).
