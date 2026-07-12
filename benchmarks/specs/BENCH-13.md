# BENCH-13 — Cost

| Field | Value |
|---|---|
| Suite | `BENCH-13` |
| Name | Cost |
| Primarily exercises | operational — whole loop (`ARCH-07`) |
| Canon / Arch | `CANON-001` §2.3 (you build it/run it: cost ownership), `ARCH-06` (reasoning budget), `ARCH-04` (efficiency scoring) |
| Owner | Platform Engineering (`PLAT`) + AI Engineering (`TEAM-070`) |

---

## Purpose

Measure the **reasoning cost** a Worker incurs to do the work — model calls, tokens and dollars —
and whether that spend is proportionate to task difficulty. MCG runs a strict "you build it, you
run it" model where squads own service cost (`CANON-001` §2.3); an accurate but ruinously
expensive Worker fails that bar. BENCH-13 makes cost a first-class, comparable output.

## What it measures

- **Absolute cost** — model calls, input/output tokens, and estimated USD per task.
- **Cost proportionality** — is spend scaled to difficulty (cheap models / few calls for easy
  tasks, more for hard ones), reflecting Decision Intelligence routing (`ARCH-06`)?
- **Cost efficiency (quality per dollar)** — passing outcome per unit spend; a cheap *wrong*
  answer earns nothing.
- **Budget adherence** — staying within the per-task reasoning budget without runaway loops
  (`ARCH-06` "runaway cost" failure mode).

## Task design

Cost is captured on the *same executions* as BENCH-01…09 (the harness records
`cost.{model_calls,input_tokens,output_tokens,usd}` on every `BenchmarkResult`), plus dedicated
**budget** cases with an explicit spend cap and a **routing** case that should be solved by a
cheap model (over-routing to a premium model on a trivial task is penalized). Grounded in the
`CHK-1421` loop where a Tier-0 change justifies a high-reasoning model but a lookup does not.

## Inputs

- `inputs.workload_ref` — the run whose costs are scored (e.g. `BR-0101`).
- `inputs.budget` — per-task cost cap `{max_calls, max_tokens, max_usd}`.
- `inputs.difficulty_expectation` — the model class the task *should* warrant.
- `inputs.pair_with_quality` — the quality result that must be `pass` for cost credit.

## Ground truth

`type: numeric` against the budget (`source`: the run's `BenchmarkResult.cost`):

- `expected.max_usd`, `expected.max_calls`, `expected.max_tokens`.
- `expected.appropriate_model_class` — for the routing case.
- gating: cost credit applies **only** when the paired quality verdict is `pass`.

## Scoring (objective-first)

| Metric | Kind | Weight | Notes |
|---|---|---|---|
| `within_budget` | objective | 0.30 | Spend within the per-task cap. |
| `cost_efficiency` | objective | 0.30 | Quality-per-dollar vs a reference frontier. |
| `routing_appropriateness` | objective | 0.20 | Model class matched to difficulty (no premium model on trivial work). |
| `quality_gated` | objective | 0.20 | Paired quality verdict is `pass` (hard gate). |

Objective share = 1.00 (fully measured). `aggregation: gated_weighted_sum`; a non-`pass` paired
outcome → score voided; exceeding a hard spend cap → `fail`.

## Confidence handling

Token and call counts are exact (high judgment confidence); USD is estimated from a published,
versioned price table stored in `metadata` so figures are reproducible even as vendor prices
change. Provider prices are anonymized in public releases (`RFC-0026`).

## Pass/fail thresholds

`pass ≥ 0.80`, `partial ≥ 0.60`. A runaway loop that blows the hard cap → `fail` even if it would
eventually have produced correct work (unbounded cost is itself a defect, `ARCH-06`).

## Model-independence notes

Cost is reported in provider-neutral **token/call** units *and* in normalized USD against a
reference price table, so a Worker on an expensive premium model and one on a cheap local SLM are
compared on efficiency, not sticker price (`RFC-0026` §6). This is essential to the project's
premise: model choice is an economic decision the framework must quantify (`ARCH-07` Example B —
benchmarks quantify the quality/cost/latency difference of a model swap).

## Failure modes / anti-gaming

- **Cheap-but-wrong** — the `quality_gated` hard gate voids cost credit on failed work.
- **Over-routing** — `routing_appropriateness` penalizes a premium model on trivial tasks.
- **Token stuffing** — pairing with BENCH-01 precision: flooding context both hurts quality and
  raises cost, penalized twice.
- **Hidden retries** — all model calls in the loop are counted, including silent re-retrieval and
  self-repair, so cost cannot be hidden off-ledger.

## Example case

```json
{
  "id": "BC-1301",
  "suite": "BENCH-13",
  "schema_version": "2020-12.v1",
  "created_at": "2026-07-05T09:00:00Z",
  "title": "Reasoning cost of guest-checkout context assembly",
  "ecl_layer": "ARCH-07",
  "task_ref": "CHK-1421",
  "apps": ["APP-003"],
  "inputs": {
    "workload_ref": "BR-0101",
    "budget": { "max_calls": 6, "max_tokens": 80000, "max_usd": 0.50 },
    "difficulty_expectation": "high-reasoning",
    "pair_with_quality": "BRES-0101"
  },
  "ground_truth": {
    "type": "numeric",
    "expected": { "max_usd": 0.50, "max_calls": 6, "max_tokens": 80000, "appropriate_model_class": "high-reasoning", "require_quality": "pass" },
    "tolerance": 0.05,
    "source": "BRES-0101",
    "notes": "BRES-0101 recorded 3 calls / ~50k tokens with verdict pass; Tier-0 change justifies the high-reasoning class."
  },
  "rubric": { "id": "RUBRIC-cost", "version": 1 },
  "scoring": { "objective_first": true, "aggregation": "gated_weighted_sum",
    "metrics": [
      { "name": "within_budget", "kind": "objective", "weight": 0.30 },
      { "name": "cost_efficiency", "kind": "objective", "weight": 0.30 },
      { "name": "routing_appropriateness", "kind": "objective", "weight": 0.20 },
      { "name": "quality_gated", "kind": "objective", "weight": 0.20 }
    ] },
  "thresholds": { "pass": 0.80, "partial": 0.60 },
  "repeats": 10,
  "references": ["BR-0101","BRES-0101","CHK-1421","APP-003"]
}
```

## Relationship to ECL layers

Cross-cutting operational measurement over the whole loop (`ARCH-07`), tied to Decision
Intelligence model routing (`ARCH-06`) and the reasoning-budget control that prevents runaway
loops. With BENCH-12 (Latency) it forms the deployability axis: the competency suites answer "is
the work good?"; BENCH-13 answers "can MCG afford to run this Worker at scale?" — and, via
normalized cost, "which provider gives the best quality per dollar?"
