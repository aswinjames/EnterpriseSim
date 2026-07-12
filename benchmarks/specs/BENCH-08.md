# BENCH-08 — Reflection

| Field | Value |
|---|---|
| Suite | `BENCH-08` |
| Name | Reflection |
| Primarily exercises | Learning Engine (`ARCH-05`) |
| Canon / Arch | `CANON-001` §9 (Stage 6), `ARCH-05`, `ARCH-04` |
| Owner | AI Engineering (`TEAM-070`) |

---

## Purpose

Measure whether the Worker can reason correctly about *why* an outcome occurred and distill a
**reusable, correctly-scoped lesson** (`REF-###` → `EXP-###`), rather than rationalizing the
result or fixing a symptom (`ARCH-05`). Good reflection is the raw material of all improvement.

## What it measures

- **Root-cause accuracy** — identifies the true origin (missing knowledge, dropped context,
  flawed plan, tool error), not a surface symptom.
- **Evidence grounding** — the diagnosis is tied to evaluation evidence and context provenance
  (including the *dropped-candidate* log — the most common real cause).
- **Lesson quality & scope** — distills a lesson that is neither too narrow nor over-generalized,
  correctly linked to the situation.
- **Actionable policy updates** — proposes retrieval/planning changes that would prevent
  recurrence.

## Task design

Given a failed (or partial) execution bundle — the `EVAL-###`, the `PLAN-###`, and the context
provenance including what was *dropped for budget* — the Worker produces a `REF-###`: what
happened, root cause + confidence, distilled lesson, policy updates. The reference is the
canonical reflection (`REF-0019`, the earlier guest-checkout failure that produced `EXP-090`).
Variants: **dropped-context cause** (the fix was in `KN` dropped for budget), **plan-gap cause**
(no negative assertion), **misleading-symptom trap** (an obvious-but-wrong cause is present),
**diffuse-failure** (no single clear cause → must produce a *hypothesis* flagged low-confidence,
not a false certainty).

## Inputs

- `inputs.outcome` — `{evaluation, plan, execution}`.
- `inputs.context_provenance` — `included[]` and critically `excluded[]`/dropped items.

## Ground truth

`type: rubric_only` with objective sub-checks (`source: REF-0019`):

- `expected.root_cause_category` — the gold cause label (e.g.
  `missing_experience_and_test_gap`).
- `must_include` — the decisive dropped/absent artifact the diagnosis must name (e.g. the loyalty
  domain rules absent from `CTX-0091`).
- diffuse cases: `expected` requires `root_cause.confidence` below a ceiling (honest uncertainty).

## Scoring (objective-first)

| Metric | Kind | Weight | Notes |
|---|---|---|---|
| `root_cause_category_match` | objective | 0.30 | Matches gold cause category. |
| `decisive_artifact_named` | objective | 0.25 | Names the dropped/absent item that caused it (hard gate on dropped-context cases). |
| `evidence_grounding` | objective | 0.15 | Diagnosis cites evaluation evidence + provenance. |
| `lesson_scope_correct` | rubric | 0.20 | Lesson neither narrow nor over-generalized (independent judge). |
| `policy_update_actionable` | rubric | 0.10 | Proposed changes would prevent recurrence. |

Objective share = 0.70 (the floor; reflection is inherently more qualitative). `aggregation:
gated_weighted_sum`; naming a confident wrong cause on the misleading-symptom trap → cap.

## Confidence handling

Explicitly scores **root-cause confidence honesty**: on diffuse-failure cases, a high-confidence
diagnosis is *penalized* (over-generalization / hindsight bias, `ARCH-05`). The correct behavior
is a provisional, low-confidence hypothesis flagged for corroboration. High variance →
`repeats: 10`.

## Pass/fail thresholds

`pass ≥ 0.75`, `partial ≥ 0.55` (looser than deterministic suites, reflecting the qualitative
core — but the objective root-cause gate still dominates).

## Model-independence notes

Gold causes are established from the canonical loop and stored as labelled data, so the *correct*
diagnosis is provider-invariant. Reflection quality genuinely varies by model reasoning strength;
that variance is the signal, and BENCH-11 checks it does not swing wildly across providers.

## Failure modes / anti-gaming

- **Hindsight rationalization** — grounding requirement + misleading-symptom trap penalize
  post-hoc stories that ignore the provenance evidence.
- **Symptom fixation** — the gold cause is the *root*, so surface fixes score low; recurrence is
  measured downstream in BENCH-09.
- **Over-generalization** — `lesson_scope_correct` and the diffuse-failure confidence ceiling
  guard against one-off luck becoming broad "truth."

## Example case

```json
{
  "id": "BC-0801",
  "suite": "BENCH-08",
  "schema_version": "2020-12.v1",
  "created_at": "2026-07-05T09:00:00Z",
  "title": "Diagnose the failed guest-checkout attempt (loyalty side effect)",
  "ecl_layer": "ARCH-05",
  "task_ref": "CHK-1421",
  "apps": ["APP-003","APP-015"],
  "difficulty": "hard",
  "inputs": {
    "outcome": { "evaluation": "EVAL-0044", "plan": "PLAN-0051", "execution": "PR-0207" },
    "context_provenance": { "included": ["KN-045"], "dropped_for_budget": ["APP-015 loyalty domain rules"] }
  },
  "ground_truth": {
    "type": "rubric_only",
    "expected": { "root_cause_category": "missing_experience_and_test_gap" },
    "must_include": ["EVAL-0044"],
    "source": "REF-0019",
    "notes": "Root cause: no prior experience warned of APP-003->APP-015 side effect AND the plan lacked a negative assertion; loyalty rules were dropped from context."
  },
  "rubric": { "id": "RUBRIC-reflection", "version": 1 },
  "scoring": { "objective_first": true, "aggregation": "gated_weighted_sum",
    "metrics": [
      { "name": "root_cause_category_match", "kind": "objective", "weight": 0.30 },
      { "name": "decisive_artifact_named", "kind": "objective", "weight": 0.25 },
      { "name": "evidence_grounding", "kind": "objective", "weight": 0.15 },
      { "name": "lesson_scope_correct", "kind": "rubric", "weight": 0.20 },
      { "name": "policy_update_actionable", "kind": "rubric", "weight": 0.10 }
    ] },
  "thresholds": { "pass": 0.75, "partial": 0.55 },
  "repeats": 10,
  "references": ["REF-0019","EVAL-0044","PLAN-0051","PR-0207","EXP-090","CHK-1421","APP-003","APP-015"]
}
```

## Relationship to ECL layers

Scores the reflection half of the **Learning Engine** (`ARCH-05`, Stage 6). Its output (`REF-###`)
becomes the `EXP-###` measured by BENCH-03 retrieval and drives the policy updates whose payoff is
measured by BENCH-09. Reflection depends on trustworthy Evaluation (BENCH-07) and complete Context
provenance (BENCH-01) — so BENCH-08 failures often trace back to those upstream suites.
