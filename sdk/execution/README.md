# `sdk.execution` — Execution Runtime

Interfaces for acting on the enterprise through real tools. Realizes **Execution**
(`CANON-001` §9, Stage 4). No implementation.

## Architecture

Execution is where a Worker *does the work*: it invokes `Tool`s (GitHub, Jira, CI, TestRail,
runbooks) per plan directives, producing concrete, inspectable `WorkerArtifact`s (`PR-####`,
`TR-####`, comments) and `ExecutionObject` records. Tools are declared with a `ToolSpec` that
states side-effects and a **least-privilege scope** (`ADR-0042`); the `ToolRegistry` resolves
only the tools a given Worker is authorized to use. Execution is **idempotent** and every plan
carries a **rollback** strategy (`ADR-0045`). Tool selection and capability negotiation are
specified in `RFC-0012/0013`.

## Python abstract interfaces

See [`interfaces.py`](interfaces.py): `ExecutionRuntime` (execute_step / rollback / artifacts),
`Tool` (Protocol), `ToolRegistry`, and the `ToolSpec` / `ToolResult` value types.

## Extension points

- **Tools.** Implement the `Tool` Protocol for each enterprise capability; register via entry
  points (`RFC-0027`). This is the primary per-Worker specialization axis for *tools*.
- **Runtime.** Subclass `ExecutionRuntime` for different execution backends (local, sandboxed,
  remote).
- **Registry/policy.** Implement `ToolRegistry` to enforce least-privilege scopes.

## Responsibilities

Execute plan steps idempotently via authorized tools, produce artifacts and execution records,
support rollback, and expose the full artifact trail for evaluation and audit.

## Examples

```python
from sdk.execution.interfaces import ExecutionRuntime

def run_step(runtime: ExecutionRuntime, plan) -> None:
    record = runtime.execute_step(plan, step=2)
    if record.status == "failed":
        runtime.rollback(plan)
```

## Future evolution

Sandboxed and remote execution backends, richer tool capability negotiation, and dry-run/plan
simulation ahead of side-effecting actions (see `RFC-0013`).
