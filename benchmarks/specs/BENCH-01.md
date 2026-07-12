# BENCH-01 — Context Assembly

| Field | Value |
|---|---|
| Suite | `BENCH-01` |
| Name | Context Assembly |
| Primarily exercises | Context Layer (`ARCH-01`) |
| Canon / Arch | `CANON-001` §9 (Stage 2), `ARCH-01`, `ARCH-04` |
| Owner | AI Engineering (`TEAM-070`) + Quality Engineering (`TEAM-050`) |

---

## Purpose

Measure how well a Worker performs **Context Engineering**: assembling the *right, minimal,
sufficient* working set for one task and holding it only for that task (`ARCH-01`). This is the
competency that separates a Worker that reasons over the three decisive documents from one that
is drowned in tokens or starved of the fact that would have made it succeed.

## What it measures

- **Recall** of task-relevant knowledge/experience/code (did the decisive item get in?).
- **Precision** — exclusion of distractors and out-of-scope material (no flooding).
- **Budget discipline** — staying within the model window while keeping high-value items.
- **Provenance completeness** — every included item has a source and reason.

## Task design

Given an MCG task trigger and the *full* candidate corpora, the Worker must emit a `CTX-###`
working set: `included[]` and `excluded[]` with provenance, plus a coverage-confidence estimate.
Cases vary the corpus size, the number of distractors, and the tightness of the token budget
(a "budget pressure" variant forces a genuine drop decision). The reference is the canonical
context object for that task (e.g. `CTX-0118` for `CHK-1421`).

## Inputs

- `inputs.trigger` — the task (`CHK-1421`, an incident, a review request).
- `inputs.available_corpus` — the `KN-###`/`EXP-###`/state handles the Worker may retrieve from,
  including plausible distractors (`KN-101`) and defensible-drop items (`KN-047`).
- `inputs.model_budget` — window and reserved-output tokens (varied across cases).

## Ground truth

`type: reference_set`, anchored on the canonical context (`source: CTX-0118`):

- `must_include` — decisive items (`KN-045`, `KN-052`, `EXP-090`) and the primary change site.
- `must_exclude` — out-of-scope distractors (`KN-101`).
- `expected.acceptable_optional` — items that are fine to include or defensibly drop (`KN-063`,
  `EXP-055`, `KN-047`) — neither rewarded nor penalized.

## Scoring (objective-first)

| Metric | Kind | Weight | Notes |
|---|---|---|---|
| `required_items_present` | objective | 0.30 | Hard gate: all `must_include` present AND all `must_exclude` absent. |
| `retrieval_recall` | objective | 0.30 | Relevant items retrieved / relevant items available. |
| `retrieval_precision` | objective | 0.25 | Relevant retrieved / total retrieved (penalizes flooding). |
| `composition_quality` | rubric | 0.15 | Ordering, provenance completeness, budget rationale (model-assisted, evidence-linked). |

Objective share = 0.85. `aggregation: gated_weighted_sum`; a `must_exclude` leak caps the score
at `gate_cap` (0.40) → `fail`.

## Confidence handling

- **Outcome confidence** from set-metric stability across repeats.
- **Judgment confidence** high (objective-dominant, 0.85 objective weight). The Worker's own
  `coverage_confidence` is *not* scored here — that honesty is scored in BENCH-10.

## Pass/fail thresholds

`pass ≥ 0.80`, `partial ≥ 0.60`. A leaked distractor or a missing decisive item → `fail`.

## Model-independence notes

Budgets are expressed relative to the model's advertised window
(`environment.gateway_capability_digest`), so a small-context model competes on *selection
quality* rather than being penalized for the window it was given — except in the explicit
budget-pressure variant, where forcing a good drop decision is the point (`ADR-0010`).

## Failure modes / anti-gaming

- **Corpus dump** → precision term + `must_exclude` gate make "retrieve everything" fail.
- **Provenance-free inclusion** → caps `composition_quality`.
- **Distractor blindness** (`KN-101` included) → hard-gate fail; mirrors the dropped-context
  failure class in `ARCH-01`/`ARCH-05`.
- Held-out corpus variants detect overfitting to the public candidate set.

## Example case

The canonical case is [`../examples/benchmark_case.example.json`](../examples/benchmark_case.example.json)
(`BC-0101`), scored by [`../examples/benchmark_result.example.json`](../examples/benchmark_result.example.json)
(`BRES-0101`). Abbreviated:

```json
{
  "id": "BC-0101",
  "suite": "BENCH-01",
  "schema_version": "2020-12.v1",
  "created_at": "2026-07-05T09:00:00Z",
  "title": "Context assembly for guest checkout (CHK-1421)",
  "ecl_layer": "ARCH-01",
  "task_ref": "CHK-1421",
  "apps": ["APP-003", "APP-015", "APP-012"],
  "inputs": {
    "trigger": { "type": "jira_story", "ref": "CHK-1421" },
    "available_corpus": { "knowledge": ["KN-045","KN-052","KN-063","KN-047","KN-101"], "experience": ["EXP-090","EXP-055"] },
    "model_budget": { "window_tokens": 200000, "reserved_output": 8000 }
  },
  "ground_truth": {
    "type": "reference_set",
    "must_include": ["KN-045","KN-052","EXP-090"],
    "must_exclude": ["KN-101"],
    "source": "CTX-0118"
  },
  "scoring": { "objective_first": true, "aggregation": "gated_weighted_sum",
    "metrics": [
      { "name": "required_items_present", "kind": "objective", "weight": 0.30 },
      { "name": "retrieval_recall", "kind": "objective", "weight": 0.30 },
      { "name": "retrieval_precision", "kind": "objective", "weight": 0.25 },
      { "name": "composition_quality", "kind": "rubric", "weight": 0.15 }
    ] },
  "thresholds": { "pass": 0.80, "partial": 0.60 },
  "repeats": 5
}
```

## Relationship to ECL layers

Directly scores the **Context Layer** (`ARCH-01`). It consumes the outputs of the **Knowledge**
(`ARCH-02`) and **Experience** (`ARCH-03`) layers (whose *retrieval* is scored separately in
BENCH-02/03) and produces the working set the rest of the loop reasons over. A weak BENCH-01
score is the leading indicator of the downstream "context starvation" / "dropped the fix"
failures that BENCH-08 reflection must later diagnose.
