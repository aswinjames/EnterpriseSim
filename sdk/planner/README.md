# `sdk.planner` — Planning

Interfaces that turn intent + context into explicit, testable plans. Realizes **Planning**
(`CANON-001` §9, Stage 3), a responsibility of Decision Intelligence
([`ARCH-06`](../../docs/architecture/06_decision_intelligence.md)). No implementation.

## Architecture

A `PlanningObject` (`PLAN-###`) is a *commitment*: ordered steps, success criteria, the tests
to run, a rollback strategy, a risk tier and the experiences applied. It is what Execution
carries out and what Evaluation scores against (`ARCH-04`). A `PlanValidator` enforces CANON
standards *before* execution — rollback present, risk-tier approvals (`CANON-001` §7),
dependency direction respected (§3), coverage adequate (§4). Plans are revisable via
`replan()`, preserving lineage. The Planner API is specified in `RFC-0008`.

## Python abstract interfaces

See [`interfaces.py`](interfaces.py): `Planner` (plan / replan), `PlanValidator` (validate /
required_approvals), and the `PlanCheck` result type.

## Extension points

- **Planning strategy.** Subclass `Planner`; the Learning Engine supplies improved planning
  heuristics per task type (`RFC-0017`).
- **Validation rules.** Implement `PlanValidator` to encode additional org standards.

## Responsibilities

Produce ordered, testable plans consistent with CANON; validate against standards; revise on
invalidation with lineage; surface required approvals by risk tier.

## Examples

```python
from sdk.planner.interfaces import Planner, PlanValidator

def make_plan(planner: Planner, validator: PlanValidator, intent, context) -> None:
    plan = planner.plan(intent, context)
    check = validator.validate(plan)
    if not check.ok:
        plan = planner.replan(plan, reason="; ".join(check.violations), context=context)
```

## Future evolution

Learned planners specialized per task type, playbook invocation for recurring situations, and
cost-aware reasoning budgets that plan the reasoning itself (see `ARCH-06` §Future Evolution).
