# BENCH-12 — Latency

| Field | Value |
|---|---|
| Suite | `BENCH-12` |
| Name | Latency |
| Primarily exercises | operational — whole loop (`ARCH-07`) |
| Canon / Arch | `CANON-001` §4 (SLOs), `ARCH-06` (loop budget), `ARCH-04` (efficiency scoring) |
| Owner | Platform Engineering (`PLAT`, `TEAM-032` SRE) + AI Engineering (`TEAM-070`) |

---

## Purpose

Measure whether a Worker completes tasks **fast enough to be operationally useful**, and where its
time goes across the ECL loop. A Worker that is correct but far too slow is not deployable on a
Tier-0 change window; BENCH-12 makes wall-clock and per-phase latency first-class, comparable
outputs (`ARCH-04` future evolution: cost/latency-aware scoring).

## What it measures

- **End-to-end latency** — wall-clock from task trigger to finalized artifact, `p50`/`p95`.
- **Per-phase breakdown** — time in context assembly, planning, model reasoning, execution,
  evaluation (localizes the bottleneck).
- **Latency under load** — tail behavior (`p95`/`p99`) across repeats, not just the median.
- **Quality-holding-latency** — latency is only meaningful paired with a passing outcome; a fast
  *wrong* answer scores zero.

## Task design

Latency is captured on the *same executions* used by BENCH-01…09 (measurement, not a separate
workload), plus dedicated **budget** cases with an explicit latency SLO (e.g. an incident-triage
task with a 60-second budget). The harness records `wall_ms`, `p50_ms`, `p95_ms` on every
`BenchmarkResult`; BENCH-12 aggregates and scores them against per-task-class budgets grounded in
MCG service tiers (`CANON-001` §3 tiers → tighter budgets for Tier-0 paths).

## Inputs

- `inputs.workload_ref` — the run whose latencies are scored (e.g. `BR-0101`).
- `inputs.slo` — per-task-class latency budget (`{p50_budget_ms, p95_budget_ms}`).
- `inputs.pair_with_quality` — the quality result that must be `pass` for latency to count.

## Ground truth

`type: numeric` against the SLO (`source`: the run's `BenchmarkResult.latency`):

- `expected.p50_budget_ms`, `expected.p95_budget_ms`.
- gating: latency credit applies **only** when the paired quality verdict is `pass` (a fast fail
  earns nothing).

## Scoring (objective-first)

| Metric | Kind | Weight | Notes |
|---|---|---|---|
| `p50_within_budget` | objective | 0.35 | Median latency within budget. |
| `p95_within_budget` | objective | 0.30 | Tail latency within budget (weighted heavily — tails hurt ops). |
| `quality_gated` | objective | 0.25 | Paired quality verdict is `pass` (hard gate). |
| `phase_balance` | objective | 0.10 | No pathological single-phase stall (e.g. runaway re-retrieval). |

Objective share = 1.00 (fully measured). `aggregation: gated_weighted_sum`; a non-`pass` paired
outcome → score voided (latency of wrong work is not rewarded).

## Confidence handling

Latency is measured with high judgment confidence, but is environment-sensitive; the harness
records hardware/region in `metadata` and reports latency normalized to a reference environment so
cross-run comparison is fair. CIs are reported over repeats (tails are noisy).

## Pass/fail thresholds

`pass ≥ 0.80`, `partial ≥ 0.60`. Budgets scale with MCG tier: Tier-0 interactive paths get the
tightest budgets; batch/reflection tasks get looser ones.

## Model-independence notes

Reported both **absolute** and **normalized to a reference model/environment**, so a slower-but-
better provider is legible on a quality-per-second basis rather than hidden (`RFC-0026` §6). This
keeps BENCH-12 a *Worker* measurement, comparable across providers, rather than a raw model speed
test.

## Failure modes / anti-gaming

- **Fast-but-wrong** — the `quality_gated` hard gate voids speed on failed work.
- **Median gaming** — heavy `p95` weight prevents optimizing the median while tails blow up.
- **Phase hiding** — `phase_balance` + BENCH-13 call counts catch a Worker that offloads latency
  into unbounded background retrieval.
- **Environment shopping** — normalization + recorded environment prevent cherry-picking fast
  hardware.

## Example case

```json
{
  "id": "BC-1201",
  "suite": "BENCH-12",
  "schema_version": "2020-12.v1",
  "created_at": "2026-07-05T09:00:00Z",
  "title": "Latency of guest-checkout context assembly (Tier-0 budget)",
  "ecl_layer": "ARCH-07",
  "task_ref": "CHK-1421",
  "apps": ["APP-003"],
  "inputs": {
    "workload_ref": "BR-0101",
    "slo": { "p50_budget_ms": 10000, "p95_budget_ms": 15000 },
    "pair_with_quality": "BRES-0101"
  },
  "ground_truth": {
    "type": "numeric",
    "expected": { "p50_budget_ms": 10000, "p95_budget_ms": 15000, "require_quality": "pass" },
    "tolerance": 500,
    "source": "BRES-0101",
    "notes": "BRES-0101 recorded p50=8700ms, p95=11200ms with verdict pass -> within Tier-0 budget."
  },
  "rubric": { "id": "RUBRIC-latency", "version": 1 },
  "scoring": { "objective_first": true, "aggregation": "gated_weighted_sum",
    "metrics": [
      { "name": "p50_within_budget", "kind": "objective", "weight": 0.35 },
      { "name": "p95_within_budget", "kind": "objective", "weight": 0.30 },
      { "name": "quality_gated", "kind": "objective", "weight": 0.25 },
      { "name": "phase_balance", "kind": "objective", "weight": 0.10 }
    ] },
  "thresholds": { "pass": 0.80, "partial": 0.60 },
  "repeats": 10,
  "references": ["BR-0101","BRES-0101","CHK-1421","APP-003"]
}
```

## Relationship to ECL layers

Cross-cutting operational measurement over the whole loop (`ARCH-07`). It instruments every layer's
phase timing — heavy context-assembly time points at `ARCH-01`, runaway re-retrieval at `ARCH-06`
loop control. Paired with BENCH-13 (Cost), it turns "is this Worker good?" into "is this Worker
*deployable*?" — the operational complement to the competency suites.
