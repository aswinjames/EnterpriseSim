# BENCH-11 — Model Independence

| Field | Value |
|---|---|
| Suite | `BENCH-11` |
| Name | Model Independence |
| Primarily exercises | Model Gateway + whole ECL (`ARCH-07`) |
| Canon / Arch | `CANON-001` §8 (principle 9, open standards), `ARCH-07`, `ADR-0010` |
| Owner | AI Engineering (`TEAM-070`) + Architecture Office (`TEAM-090`) |

---

## Purpose

Measure the ECL's defining structural claim: the **same tasks, cases, ground truth and accumulated
intelligence produce comparable results across interchangeable model providers** (`ARCH-07`,
`ADR-0010`). A Worker's competence must live in the ECL, not in one vendor's weights — BENCH-11
quantifies how true that is for a given Worker.

## What it measures

- **Cross-provider score variance** — how much a Worker's per-suite scores move when only the
  provider/model changes.
- **Ranking stability** — do the Worker's *relative* strengths (its 13-suite shape) hold across
  models?
- **Learning portability** — does experience accumulated under model A still lift performance
  under model B (the "Monday→Tuesday" guarantee)?
- **Graceful degradation** — on a weaker/smaller model, does quality degrade smoothly rather than
  collapse, and does the ECL compensate (larger context, more retrieval)?

## Task design

BENCH-11 is a **differential** suite: it re-runs a fixed subset of BENCH-01…10 cases across ≥3
provider classes (e.g. high-reasoning, balanced, small/local SLM) by changing *only*
`environment.provider`/`model` on otherwise-identical `BenchmarkRun`s. The score is a function of
the *dispersion and portability* of results, not any single provider's absolute score. The
canonical anchor is `ARCH-07` Example B — migrating the high-reasoning class from Provider A to B
with `CTX-0118`, `PLAN-0072`, `EXP-090` and every rubric untouched.

## Inputs

- `inputs.case_subset` — the BENCH-01…10 cases to replicate.
- `inputs.providers` — the set of provider/model classes to run (≥3).
- `inputs.shared_memory` — the durable Knowledge/Experience state, identical across providers.

## Ground truth

`type: numeric` on dispersion/portability statistics (no per-provider "right answer" — the
per-case ground truth comes from the underlying suites):

- `expected.max_cross_provider_stddev` — cap on per-suite score standard deviation across
  providers (e.g. ≤ 0.08).
- `expected.min_ranking_correlation` — Spearman correlation of the 13-suite shape across providers
  (e.g. ≥ 0.85).
- `expected.min_learning_portability` — fraction of BENCH-09 lift retained after the model swap
  (e.g. ≥ 0.90).

## Scoring (objective-first)

| Metric | Kind | Weight | Notes |
|---|---|---|---|
| `score_stability` | objective | 0.35 | 1 − normalized cross-provider stddev per suite. |
| `ranking_stability` | objective | 0.25 | Spearman correlation of suite shapes across providers. |
| `learning_portability` | objective | 0.25 | BENCH-09 lift retained under a swapped model (hard gate). |
| `graceful_degradation` | objective | 0.15 | Monotone, non-cliff degradation on weaker models. |

Objective share = 1.00. `aggregation: gated_weighted_sum`; **learning that does not survive a
model swap → cap** (it means the improvement lived in weights, violating the ECL thesis).

## Confidence handling

Each per-provider score already carries a CI (§5 of `methodology.md`); BENCH-11 propagates those
into the dispersion statistics so "instability" is only claimed when CIs genuinely separate.
Judgment confidence is high (all-objective).

## Pass/fail thresholds

`pass ≥ 0.80`, `partial ≥ 0.60`. A Worker that only works on one provider, or whose learning
evaporates on a swap, fails regardless of how high its single-provider scores are.

## Model-independence notes

This suite is the model-independence guarantee itself, so its own construction is scrupulously
provider-neutral: identical cases, identical ground truth, identical durable memory, only the
Gateway adapter/routing config differs (`ARCH-07` mechanism 1–2). Provider labels are anonymized
(`provider-a`, `provider-b`) in public releases (`RFC-0026`) to keep the framework about *Workers*,
not vendor marketing.

## Failure modes / anti-gaming

- **Single-provider tuning** — a Worker hand-tuned to one model's quirks shows high dispersion and
  fails `score_stability`.
- **Weight-embedded learning** — caught by the `learning_portability` hard gate.
- **Cherry-picking providers** — the provider set is fixed by the harness, not chosen by the
  submitter.
- **Prompt-format coupling** — since the Context Layer stores structured `CTX-###` and the Gateway
  renders prompts (`ARCH-07`), any provider-specific prompt hacking that would break portability
  surfaces as instability.

## Example case

```json
{
  "id": "BC-1101",
  "suite": "BENCH-11",
  "schema_version": "2020-12.v1",
  "created_at": "2026-07-05T09:00:00Z",
  "title": "Cross-provider replication of the CHK-1421 competency subset",
  "ecl_layer": "ARCH-07",
  "task_ref": "CHK-1421",
  "inputs": {
    "case_subset": ["BC-0101","BC-0401","BC-0701","BC-0901"],
    "providers": ["provider-a:high-reasoning","provider-b:high-reasoning","provider-c:small"],
    "shared_memory": { "knowledge": ["KN-045","KN-052"], "experience": ["EXP-090"] }
  },
  "ground_truth": {
    "type": "numeric",
    "expected": { "max_cross_provider_stddev": 0.08, "min_ranking_correlation": 0.85, "min_learning_portability": 0.90 },
    "tolerance": 0.02,
    "source": "EXP-090",
    "notes": "ARCH-07 Example B: swapping the model must leave CTX-0118/PLAN-0072/EXP-090 fully effective."
  },
  "rubric": { "id": "RUBRIC-model-independence", "version": 1 },
  "scoring": { "objective_first": true, "aggregation": "gated_weighted_sum",
    "metrics": [
      { "name": "score_stability", "kind": "objective", "weight": 0.35 },
      { "name": "ranking_stability", "kind": "objective", "weight": 0.25 },
      { "name": "learning_portability", "kind": "objective", "weight": 0.25 },
      { "name": "graceful_degradation", "kind": "objective", "weight": 0.15 }
    ] },
  "thresholds": { "pass": 0.80, "partial": 0.60 },
  "repeats": 10,
  "references": ["CHK-1421","BC-0101","BC-0401","BC-0701","BC-0901","KN-045","KN-052","EXP-090"]
}
```

## Relationship to ECL layers

Scores the **Model Gateway** boundary and, through it, the whole ECL (`ARCH-07`). It presupposes
the other suites (it replicates their cases) and directly tests mechanisms 1–4 of `ARCH-07`'s
vendor-independence argument — single point of contact, stable structured contract, capability
negotiation, and learning-outside-the-weights. A strong BENCH-11 score is the evidence that lets
EnterpriseSim fairly compare providers *through* a Worker, the project's core purpose.
