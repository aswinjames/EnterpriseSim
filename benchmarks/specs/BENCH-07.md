# BENCH-07 — Evaluation (evaluating the evaluator)

| Field | Value |
|---|---|
| Suite | `BENCH-07` |
| Name | Evaluation / Self-assessment quality |
| Primarily exercises | Evaluation Layer (`ARCH-04`) |
| Canon / Arch | `CANON-001` §9 (Stage 5), `ARCH-04`, `ARCH-07` |
| Owner | Quality Engineering (`TEAM-050`) + Architecture Office (`TEAM-090`) |

---

## Purpose

Measure whether the Worker can **judge work correctly** — its own or another's — producing a
scored, evidence-linked, objective-first verdict that matches a gold `EVAL-###` (`ARCH-04`). A
Worker that cannot evaluate cannot safely self-correct or feed the learning loop, so this suite
"evaluates the evaluator."

## What it measures

- **Verdict accuracy** — pass/partial/fail matches the gold verdict.
- **Objective-first discipline** — deterministic gates weighted above rubric items; does the
  Worker catch a standards violation that passing tests would hide (`ARCH-04` Example B)?
- **Evidence linkage** — every score line cites the artifact that justifies it (no unsupported
  claims).
- **Dual-confidence honesty** — outcome vs judgment confidence correctly separated; low-certainty
  qualitative items flagged provisional, not laundered.

## Task design

Given an execution bundle (a `PR-####` diff, `TR-####` results, the `PLAN-###`, and standards)
and a rubric, the Worker produces an `EVAL-###`-shaped verdict. The reference is a gold evaluation
(`EVAL-0061`). Cases include: **green-but-wrong** (tests pass yet a reverse dependency
`APP-012`→`APP-003` is introduced → correct verdict is `fail`), **false-fail** (a flaky test that
should not fail the work), **evidence-gap** (a claim with no linked artifact must be marked low
judgment confidence), and **regression** (reintroduces a defect covered by `EXP-090`).

## Inputs

- `inputs.execution` — `{pr, diff, test_runs, plan_ref}`.
- `inputs.standards` and `inputs.rubric` — the bar and the versioned rubric.

## Ground truth

`type: verdict` + objective sub-checks (`source: EVAL-0061`):

- `expected.outcome` — the gold verdict.
- gold `objective[]` gate results (which gates should pass/fail) and required evidence links.
- for the green-but-wrong case, `expected.outcome: fail` with `dependency_rule: fail` as the
  deciding gate.

## Scoring (objective-first)

| Metric | Kind | Weight | Notes |
|---|---|---|---|
| `verdict_match` | objective | 0.30 | Matches gold pass/partial/fail. |
| `gate_result_match` | objective | 0.30 | Per-gate pass/fail matches gold (catches the deciding gate). |
| `evidence_linkage` | objective | 0.20 | Every scored line has a valid evidence ref (hard gate). |
| `standards_violation_caught` | objective | 0.10 | Detects reverse-dependency / rollback / PCI breaches. |
| `confidence_separation` | rubric | 0.10 | Outcome vs judgment confidence correctly distinguished. |

Objective share = 0.90. `aggregation: gated_weighted_sum`; **missing the standards violation on
the green-but-wrong case → `fail`** (a false pass is the cardinal evaluation error).

## Confidence handling

The suite scores the Worker's *use* of dual confidence: a verdict asserting high judgment
confidence on an evidence-free qualitative claim is penalized even if the outcome label is
correct. Judge for the `confidence_separation` rubric item is independent and blind.

## Pass/fail thresholds

`pass ≥ 0.80`, `partial ≥ 0.60`. A false pass (missing a real standards violation) → `fail`.

## Model-independence notes

Gold verdicts are anchored to deterministic gate results over MCG artifacts, so the *correct*
evaluation is provider-invariant. A model that is a lenient or harsh grader is exactly the
variance this suite exposes; BENCH-11 confirms a Worker's evaluation behavior is stable across
providers (`ADR-0010`).

## Failure modes / anti-gaming

- **Rubber-stamping** — always-pass defeated by the green-but-wrong and regression cases.
- **Harsh-grading** — always-fail defeated by the false-fail (flaky) case.
- **Evidence-free scoring** — hard-gated; mirrors `ARCH-04` "no score without evidence."
- **Judge collusion** — the model evaluating must differ from the model that produced the
  execution under test.

## Example case

```json
{
  "id": "BC-0701",
  "suite": "BENCH-07",
  "schema_version": "2020-12.v1",
  "created_at": "2026-07-05T09:00:00Z",
  "title": "Evaluate a green PR that introduces a reverse dependency",
  "ecl_layer": "ARCH-04",
  "task_ref": "CHK-1421",
  "apps": ["APP-003","APP-012"],
  "difficulty": "hard",
  "inputs": {
    "execution": { "pr": "PR-0312", "test_runs": ["TR-0442","TR-0443"], "plan_ref": "PLAN-0072",
      "diff_note": "All tests pass, but adds a call from APP-012 into APP-003." },
    "rubric": { "id": "RUBRIC-feature-change", "version": 3 },
    "standards": ["CANON-001#3"]
  },
  "ground_truth": {
    "type": "verdict",
    "expected": { "outcome": "fail", "deciding_gate": "dependency_rule" },
    "must_include": ["PR-0312"],
    "source": "EVAL-0061",
    "notes": "Green tests do not save a forbidden reverse dependency (CANON-001 §3); verdict = fail."
  },
  "rubric": { "id": "RUBRIC-feature-change", "version": 3 },
  "scoring": { "objective_first": true, "aggregation": "gated_weighted_sum",
    "metrics": [
      { "name": "verdict_match", "kind": "objective", "weight": 0.30 },
      { "name": "gate_result_match", "kind": "objective", "weight": 0.30 },
      { "name": "evidence_linkage", "kind": "objective", "weight": 0.20 },
      { "name": "standards_violation_caught", "kind": "objective", "weight": 0.10 },
      { "name": "confidence_separation", "kind": "rubric", "weight": 0.10 }
    ] },
  "thresholds": { "pass": 0.80, "partial": 0.60 },
  "repeats": 5,
  "references": ["EVAL-0061","PR-0312","PLAN-0072","CHK-1421","APP-003","APP-012"]
}
```

## Relationship to ECL layers

Scores the **Evaluation Layer** (`ARCH-04`) competency directly — the layer this whole framework
is built on. Because Reflection (BENCH-08) and Continuous Learning (BENCH-09) are grounded in
evaluation output, a low BENCH-07 score propagates: "feedback poisoning" (`ARCH-05`) means bad
evaluations produce bad lessons. BENCH-07 therefore gates trust in the learning suites.
