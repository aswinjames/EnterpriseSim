# BENCH-09 — Continuous Learning

| Field | Value |
|---|---|
| Suite | `BENCH-09` |
| Name | Continuous Learning (loop closure) |
| Primarily exercises | Learning Engine (`ARCH-05`) |
| Canon / Arch | `CANON-001` §9 (Stage 8), `ARCH-05`, `ARCH-07`, `ADR-0034` |
| Owner | AI Engineering (`TEAM-070`) + Architecture Office (`TEAM-090`) |

---

## Purpose

Measure the single claim EnterpriseSim exists to prove: **does the Worker measurably improve
across repeated tasks because the ECL learned — with the same stateless model?** This is
**loop closure** (`ADR-0034`): a lesson counts only when it changes a later execution
(`ARCH-05` terminal state `LoopClosed`).

## What it measures

- **Score lift** — on a second attempt at a task type, does the `EVAL-###` score rise versus the
  first (the canonical `EVAL-0044` fail → `EVAL-0061` = 0.91 pass on guest checkout)?
- **Loop-closure rate** — fraction of captured lessons that demonstrably alter a later run.
- **Regression prevention** — does an applied experience (`EXP-090`) stop a re-introduced defect?
- **No cheating via weights** — improvement must come from ECL data (knowledge/experience/policy),
  never model fine-tuning (the whole thesis, `ARCH-07`).

## Task design

A **longitudinal** suite: each case is a *pair (or sequence) of runs* on the same task family
with durable memory carried between them. Run 1 executes cold (or with a seeded gap); the Learning
Engine reflects (BENCH-08) and writes experience/policy; Run 2 executes the *next* task in the
family. The score is the **delta and its attribution**. The reference trajectory is the canonical
`PR-0207`(fail) → `PR-0312`(pass) arc closed by `EXP-090`. Variants: **lift** (expect improvement),
**no-regression** (a later task must not reintroduce the fixed defect), **transfer** (a lesson from
one app improves a structurally-similar task on another), **negative control** (memory disabled →
expect *no* lift, proving the lift was real).

## Inputs

- `inputs.run_sequence` — ordered task family with shared durable memory between runs.
- `inputs.memory_mode` — `enabled | disabled` (disabled = negative control).
- `inputs.prior_run` — the `BR-####` this run is compared against.

## Ground truth

`type: numeric` (delta) + `verdict` (loop-closed):

- `expected.min_lift` — minimum `EVAL` score improvement attributable to a specific `EXP-###`.
- `expected.loop_closed_by` — the artifact that must show the lesson applied (`PR-0312`).
- negative control: `expected.min_lift: 0` (memory-off must **not** improve).

## Scoring (objective-first)

| Metric | Kind | Weight | Notes |
|---|---|---|---|
| `score_lift` | objective | 0.35 | Run-2 EVAL minus Run-1 EVAL ≥ `min_lift`. |
| `loop_closure_attributed` | objective | 0.30 | The lift is traceable to a named applied `EXP-###`/policy (hard gate). |
| `regression_prevented` | objective | 0.20 | The previously-fixed defect does not recur. |
| `negative_control_holds` | objective | 0.15 | With memory disabled, no lift (proves it was learning, not noise). |

Objective share = 1.00 (fully deterministic given fixed seeds). `aggregation: gated_weighted_sum`;
**lift with no attributable lesson → cap** (unattributed improvement is treated as noise/luck, not
learning). Fine-tuning the model between runs is a protocol violation that voids the case.

## Confidence handling

Loop closure is measured over `repeats: 10` per run with CIs; a "lift" counts only if Run-2's CI
lies above Run-1's at the 95% level (§5 of `methodology.md`). This prevents celebrating noise as
learning. Judgment confidence is high because attribution is via explicit lineage.

## Pass/fail thresholds

`pass ≥ 0.80`, `partial ≥ 0.60`. A significant lift that is *not attributable* to a lesson, or a
negative control that spuriously improves, fails the case.

## Model-independence notes

The decisive test: hold the model fixed and vary only ECL memory — lift must appear. Then, per
BENCH-11, swap the model and confirm the *same accumulated experience still produces lift* — the
deepest form of vendor independence (`ARCH-07`: "change providers on Monday and every lesson still
applies on Tuesday"). A Worker whose "learning" evaporates on a model swap has learned in the
weights, not the ECL, and fails the intent (`ADR-0010`).

## Failure modes / anti-gaming

- **Unattributed lift** — hard-gated: improvement must trace to a specific lesson, not vibes.
- **Noise-as-learning** — CI-separation requirement filters random fluctuation.
- **Overfitting the family** — held-out task variants in the family detect memorized answers.
- **Weight cheating** — model fine-tuning between runs voids the case (improvement must be data).

## Example case

```json
{
  "id": "BC-0901",
  "suite": "BENCH-09",
  "schema_version": "2020-12.v1",
  "created_at": "2026-07-05T09:00:00Z",
  "title": "Guest-checkout family: fail -> reflect -> pass (loop closure)",
  "ecl_layer": "ARCH-05",
  "task_ref": "CHK-1421",
  "apps": ["APP-003","APP-015"],
  "difficulty": "hard",
  "inputs": {
    "run_sequence": [
      { "task": "guest-flow-v1", "reference_run": "PR-0207", "reference_eval": "EVAL-0044" },
      { "task": "CHK-1421", "reference_run": "PR-0312", "reference_eval": "EVAL-0061" }
    ],
    "memory_mode": "enabled",
    "prior_run": "BR-0207"
  },
  "ground_truth": {
    "type": "numeric",
    "expected": { "min_lift": 0.25, "loop_closed_by": "PR-0312", "attributed_to": "EXP-090" },
    "tolerance": 0.05,
    "source": "REF-0019",
    "notes": "EVAL-0044 (fail) -> EVAL-0061 (0.91) attributable to EXP-090 + the negative-assertion policy update; memory-off control must show no lift."
  },
  "rubric": { "id": "RUBRIC-continuous-learning", "version": 1 },
  "scoring": { "objective_first": true, "aggregation": "gated_weighted_sum",
    "metrics": [
      { "name": "score_lift", "kind": "objective", "weight": 0.35 },
      { "name": "loop_closure_attributed", "kind": "objective", "weight": 0.30 },
      { "name": "regression_prevented", "kind": "objective", "weight": 0.20 },
      { "name": "negative_control_holds", "kind": "objective", "weight": 0.15 }
    ] },
  "thresholds": { "pass": 0.80, "partial": 0.60 },
  "repeats": 10,
  "references": ["REF-0019","EXP-090","EVAL-0044","EVAL-0061","PR-0207","PR-0312","CHK-1421"]
}
```

## Relationship to ECL layers

Scores the learning half of the **Learning Engine** (`ARCH-05`, Stage 8) and, through it, the
whole flywheel: better Reflection (BENCH-08) → richer Experience (BENCH-03) and Knowledge
(BENCH-02) → better Context (BENCH-01) and Planning (BENCH-04) → higher Evaluation (BENCH-07). It
is the integrative suite: a rising BENCH-09 trend is the direct measurement of CANON's
continuous-improvement flywheel (`ARCH-07` improvement signals).
