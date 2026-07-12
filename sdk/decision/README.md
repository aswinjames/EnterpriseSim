# `sdk.decision` — Decision Intelligence

Interfaces for the ECL's orchestrator. Realizes **Decision Intelligence** (`CANON-001` §9)
per [`ARCH-06`](../../docs/architecture/06_decision_intelligence.md). No implementation.

## Architecture

Decision Intelligence is the **only** component with agency (`ADR-0008`): it interprets
intent, drives the Context → Plan → Execute → Evaluate loop, routes models through the Gateway,
and records an immutable **decision trace** (`ADR-0021`). Autonomy is **gated on fused
confidence** (`ADR-0014`, `RFC-0009`): a `ConfidencePolicy` combines per-layer confidences and
maps them (with risk tier) to a `Control` decision — proceed, re-retrieve, replan, retry,
escalate, or abort. A `PolicyGuard` enforces guardrails **before** execution (`ADR-0041`):
approvals, PCI boundaries, segregation-of-duties, fairness. Model routing lives here but never
couples to a provider — all access is via `sdk.models` (`RFC-0010`).

## Python abstract interfaces

See [`interfaces.py`](interfaces.py): `Orchestrator` (interpret / decide / trace),
`ConfidencePolicy` (fuse / control_for), `PolicyGuard` (check), the `Control` enum and
`PolicyVerdict`.

## Extension points

- **Confidence fusion.** Implement `ConfidencePolicy` to change how uncertainty gates autonomy.
- **Guardrails.** Implement `PolicyGuard` per Worker domain (PCI vs. fairness vs. SoD).
- **Orchestration.** Subclass `Orchestrator` for custom control loops; the Learning Engine
  tunes planning heuristics it uses.

## Responsibilities

Interpret intent, plan (via `sdk.planner`), orchestrate the loop, route models, manage
confidence & control, enforce policy, emit the decision trace.

## Examples

```python
from sdk.decision.interfaces import Orchestrator, ConfidencePolicy, Control

def step(orc: Orchestrator, conf: ConfidencePolicy, plan, ctx, evaluation) -> Control:
    decision = orc.decide(plan, ctx, evaluation)
    return conf.control_for(decision.fused_confidence, plan.risk_tier)
```

## Future evolution

Learned planners, playbook invocation, multi-Worker orchestration, risk-adaptive autonomy and
cost-aware reasoning budgets (see `ARCH-06` §Future Evolution and `RFC-0007`).
