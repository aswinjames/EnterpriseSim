# BENCH-03 — Experience Retrieval

| Field | Value |
|---|---|
| Suite | `BENCH-03` |
| Name | Experience Retrieval |
| Primarily exercises | Experience Layer (`ARCH-03`) |
| Canon / Arch | `CANON-001` §9 (Stage 7), `ARCH-03`, `ARCH-04` |
| Owner | AI Engineering (`TEAM-070`) |

---

## Purpose

Measure whether the Worker retrieves the **right accumulated lesson** for the situation in front
of it — surfacing "when changing guest flows in `APP-003`, do not provision an `APP-015`
account" (`EXP-090`) *before* it repeats the mistake (`ARCH-03`). This is memory of *what worked
and failed*, distinct from governed truth (BENCH-02).

## What it measures

- **Situational recall** — is the applicable `EXP-###` retrieved for a given situation?
- **Structural (not just semantic) matching** — same app + same failure class, not merely
  "sounds similar" (`ARCH-03` overfitting failure mode).
- **Applicability ranking** — are high-value, corroborated, non-contradicted lessons ranked
  above stale or down-weighted ones?
- **Cross-domain transfer** — recognizing a structurally-transferable lesson (`EXP-142` async
  determinism → a Support Worker), the ECL reuse guarantee.

## Task design

Given a **situation descriptor** (`{task_type, apps, failure_class}`) or a task trigger, the
Worker returns ranked `EXP-###` lessons. Cases include: **exact-situation** (guest checkout →
`EXP-090`), **near-miss distractor** (a superficially similar but wrong-app lesson that must be
excluded), **contradiction** (a down-weighted lesson must rank low), and **cold-start** (no
experience exists → the Worker must return empty and defer to Knowledge, not hallucinate a
lesson).

## Inputs

- `inputs.situation` — `{task_type, apps, failure_class}`.
- `inputs.experience_corpus` — `EXP-###` handles with hidden value/contradiction/recency labels.
- `inputs.retrieval_budget` — max lessons to return.

## Ground truth

`type: set_match` / `ranking`, anchored on the canonical experience (`source: EXP-090`):

- `must_include` — the decisive lesson(s) for the situation.
- `must_exclude` — wrong-app near-misses and contradicted lessons.
- cold-start cases: `expected: []` (empty is correct; any returned lesson is a false positive).

## Scoring (objective-first)

| Metric | Kind | Weight | Notes |
|---|---|---|---|
| `situational_recall` | objective | 0.30 | Decisive lesson retrieved. |
| `precision` | objective | 0.25 | Penalizes near-miss / contradicted inclusions. |
| `applicability_ranking` | objective | 0.20 | Value/corroboration-weighted ordering (nDCG). |
| `cold_start_restraint` | objective | 0.10 | Correctly returns empty when no lesson applies. |
| `transfer_recognition` | rubric | 0.15 | Structurally-transferable lesson recognized (model-assisted). |

Objective share = 0.85. `aggregation: gated_weighted_sum`; a contradicted lesson ranked top or a
false positive on a cold-start case → cap.

## Confidence handling

Judgment confidence high on objective metrics; the transfer-recognition rubric item carries its
own `judgment_confidence` and is scored by an independent judge blind to the Worker.

## Pass/fail thresholds

`pass ≥ 0.80`, `partial ≥ 0.60`.

## Model-independence notes

Situation matching is scored over MCG situation descriptors and `EXP-###` IDs, not model prose.
Structural similarity (app + failure class) is provider-neutral; embedding differences surface as
retrieval quality, the intended signal (`ADR-0010`).

## Failure modes / anti-gaming

- **Overfitting to the past** — near-miss distractors penalize applying a narrow lesson to the
  wrong situation (`ARCH-03`).
- **Cold-start hallucination** — inventing a lesson where none exists is a hard-gate fail.
- **Recency gaming** — value-weighted ranking beats "return the newest," per `ARCH-03` Best
  Practice 4.

## Example case

```json
{
  "id": "BC-0301",
  "suite": "BENCH-03",
  "schema_version": "2020-12.v1",
  "created_at": "2026-07-05T09:00:00Z",
  "title": "Retrieve the guest-checkout loyalty side-effect lesson",
  "ecl_layer": "ARCH-03",
  "task_ref": "CHK-1421",
  "apps": ["APP-003", "APP-015"],
  "inputs": {
    "situation": { "task_type": "feature_change", "apps": ["APP-003","APP-015"], "failure_class": "unintended_side_effect" },
    "experience_corpus": ["EXP-090","EXP-055"],
    "retrieval_budget": { "k": 3 }
  },
  "ground_truth": {
    "type": "set_match",
    "expected": ["EXP-090"],
    "must_include": ["EXP-090"],
    "must_exclude": ["EXP-055"],
    "source": "EXP-090",
    "notes": "EXP-055 (promo-window cache flush) is a plausible but wrong-situation distractor."
  },
  "rubric": { "id": "RUBRIC-experience-retrieval", "version": 1 },
  "scoring": { "objective_first": true, "aggregation": "gated_weighted_sum",
    "metrics": [
      { "name": "situational_recall", "kind": "objective", "weight": 0.30 },
      { "name": "precision", "kind": "objective", "weight": 0.25 },
      { "name": "applicability_ranking", "kind": "objective", "weight": 0.20 },
      { "name": "cold_start_restraint", "kind": "objective", "weight": 0.10 },
      { "name": "transfer_recognition", "kind": "rubric", "weight": 0.15 }
    ] },
  "thresholds": { "pass": 0.80, "partial": 0.60 },
  "repeats": 5,
  "references": ["EXP-090","EXP-055","CHK-1421","APP-003","APP-015"]
}
```

## Relationship to ECL layers

Scores the **Experience Layer** (`ARCH-03`) retrieval surface. Retrieved lessons feed the
**Context Layer** (BENCH-01) and steer **Planning** (BENCH-04, e.g. adding the negative test).
Because experience is *produced* by the Learning Engine (`ARCH-05`), BENCH-03 quality is the
downstream payoff of good BENCH-08 reflection, and its improvement over repeated task types is
part of BENCH-09.
