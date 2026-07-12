# `sdk.evaluation` — Evaluation Layer

Interfaces for measuring Worker quality. Realizes **Evaluation** (`CANON-001` §9, Stage 5)
per [`ARCH-04`](../../docs/architecture/04_evaluation_layer.md). No implementation.

## Architecture

Evaluation renders a scored, evidence-linked verdict (`EvaluationObject`, `EVAL-###`) of an
execution against its plan and CANON standards. It is **objective-first** (`ADR-0015`):
deterministic `ObjectiveGate`s (tests, coverage, security scan, dependency-direction rule)
are weighted above model-assisted `rubric_items`. **No score exists without linked evidence**
(`ADR-0016`), and the layer reports **two** confidences — outcome vs. judgment (`ADR-0017`).
`Rubric`s are versioned (`ADR-0018`) so benchmarking is reproducible. This layer is the
substrate for the benchmark framework in [`../../benchmarks/`](../../benchmarks/) (`RFC-0025/0026`).

## Python abstract interfaces

See [`interfaces.py`](interfaces.py): `Evaluator` (evaluate / check_regressions), `Rubric`,
`ObjectiveGate` (Protocol), and the `GateResult` / `RubricItemResult` value types.

## Extension points

- **Rubrics.** Implement `Rubric` per task type — the primary per-Worker specialization axis
  for *rubrics*.
- **Gates.** Implement `ObjectiveGate` for new deterministic checks.
- **Evaluator.** Subclass `Evaluator` for alternative aggregation, incl. model-assisted judges
  (always evidence-linked).

## Responsibilities

Score against plan + standards, aggregate objective signals, apply versioned rubrics, attach
evidence, emit dual-confidence verdicts, feed learning, support benchmarking.

## Examples

```python
from sdk.evaluation.interfaces import Evaluator, Rubric

def score(evaluator: Evaluator, rubric: Rubric, execution, plan) -> float:
    result = evaluator.evaluate(execution, plan, rubric)
    return result.verdict["score"]
```

## Future evolution

Adversarial (red-team) evaluation, comparative benchmarking harness, calibrated model judges,
continuously-ratcheting quality baselines, and cost/latency-aware scoring (see `ARCH-04`).
