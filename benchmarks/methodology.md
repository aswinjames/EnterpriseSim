# Benchmark Methodology

> How EnterpriseSim scores Enterprise AI Workers: from a frozen task to a comparable,
> reproducible, gaming-resistant leaderboard entry. This document is the authoritative scoring
> methodology referenced by every suite spec (`specs/BENCH-NN.md`) and realized by the schemas
> in [`schemas/`](schemas/).

| Field | Value |
|---|---|
| Governing RFCs | `RFC-0025` (Benchmarking Harness), `RFC-0026` (Scoring & Leaderboards) |
| Governing ADRs | `ADR-0048` (Reproducibility), `ADR-0010` (Model Independence), `ADR-0015`/`0016`/`0017` (objective-first / evidence / dual confidence), `ADR-0034` (Loop Closure) |
| Canon / Arch | `CANON-001`, `ARCH-04`, `ARCH-07` |
| Status | Authoritative for the benchmark framework |

---

## 1. Task suites

A **suite** (`BENCH-NN`) isolates one ECL competency so that a Worker's strengths and
weaknesses are legible rather than blended into a single opaque number. Each suite is a set of
**cases** (`BenchmarkCase`, `BC-####`); each case is one self-contained task with fixed inputs,
machine-checkable ground truth, a versioned rubric and a scoring recipe.

Cases are drawn from the MCG canon (`CANON-001`) and its worked loops — principally the
`CHK-1421` guest-checkout loop that recurs through `ARCH-01`…`ARCH-07`. Reusing canonical
artifacts (`KN-045`, `EXP-090`, `APP-003`, the `APP-012`→`APP-003` dependency rule) keeps
ground truth objective and referentially consistent, and lets a single task be scored from
several angles across suites (its context in BENCH-01, its plan in BENCH-04, its evaluation in
BENCH-07, its learning in BENCH-09).

Case design rules:

- **Deterministic where possible.** Prefer set/exact/numeric/verdict ground truth over prose.
- **One competency per case.** A BENCH-02 case must not silently depend on planning skill.
- **Distractors included.** Every retrieval/selection case ships plausible wrong options
  (`ground_truth.must_exclude`) so that "take everything" scores poorly.
- **Frozen and versioned.** A case is immutable once published; a change is a new case or a new
  `dataset_version` (`ADR-0048`). This preserves comparability of historical results.
- **Balanced difficulty.** Cases are tagged `easy|medium|hard`; suites report per-difficulty
  breakdowns so an aggregate cannot be inflated by easy-case stuffing.

---

## 2. Ground truth

Ground truth is the reference a Worker's output is scored against. Its `type`
(`ground_truth.type`) determines the comparison:

| Type | Used by (e.g.) | Comparison |
|---|---|---|
| `exact_match` | tool name, single ID | string equality |
| `set_match` | selected tools, retrieved IDs | precision / recall / F1 vs a reference set |
| `reference_set` | context assembly | `must_include` ⊆ output, `must_exclude` ∩ output = ∅, plus optional set overlap |
| `ranking` | knowledge/experience retrieval | rank-aware metrics (nDCG, MRR) vs an ideal ordering |
| `numeric` | confidence value, cost, latency | absolute error within `tolerance` |
| `verdict` | evaluation / decision | label match (pass/partial/fail, proceed/escalate/…) |
| `rubric_only` | irreducibly qualitative facets | model-assisted rubric with mandatory evidence |

Every ground truth cites its **`source`** — the canonical artifact that establishes it (e.g.
`CTX-0118` for BENCH-01, `EVAL-0061` for BENCH-07) — so any disputed score is auditable back to
canon. Ground truth is authored by Quality Engineering (`TEAM-050`) with the Architecture
Office (`TEAM-090`) and reviewed like any `KN-###` (`ARCH-02` governance).

**Human-anchored labels.** Where ground truth encodes "senior-MCG-engineer quality" (e.g. plan
adequacy), the label is set by expert consensus and stored as data, never inferred at scoring
time by the same model being tested.

---

## 3. Objective-first scoring

Scoring inherits the Evaluation Layer's discipline verbatim (`ARCH-04`; `ADR-0015`): **weight
deterministic gates above model-assisted judgment**, and never launder a low-confidence guess
as a high-confidence score.

Each case declares `scoring.metrics[]`, each with a `kind` (`objective` | `rubric`) and a
`weight` in `[0,1]`. The rules:

1. **Objective gates dominate.** The sum of `objective` weights must be ≥ 0.70 for any scored
   (non-`rubric_only`) suite. Objective gates are deterministic and reproducible: set overlap,
   test pass/fail, coverage thresholds, dependency-rule checks, numeric error, latency/cost
   budgets.
2. **Rubric items are the minority, and always evidence-linked.** A `rubric` metric may be
   model-assisted, but each `rubric_items[]` result must carry `evidence` and a
   `judgment_confidence` (`ADR-0016`/`0017`).
3. **Hard gates can veto.** Some gates are gating, not weighted: e.g. a dependency-rule
   violation or a `must_exclude` leak forces `verdict = fail` regardless of other credit
   (`aggregation: gated_weighted_sum`). This mirrors `ARCH-04` Example B (green tests but a
   forbidden reverse dependency → fail).

### Aggregation of a single case score

For `aggregation: weighted_sum`:

```
case_score = Σ_i ( weight_i × metric_score_i )      (weights normalized to sum 1)
```

For `aggregation: gated_weighted_sum` (the default):

```
if any hard gate fails:  case_score = min(weighted_sum, gate_cap)   # gate_cap default 0.40
else:                    case_score = weighted_sum
```

`min` aggregation exists for cases where the weakest facet should dominate (e.g. safety).

### Verdict

```
verdict = pass     if case_score ≥ thresholds.pass
        = partial  if thresholds.partial ≤ case_score < thresholds.pass
        = fail      otherwise
```

Suite-standard thresholds are `pass ≥ 0.80`, `partial ≥ 0.60` unless a spec overrides them
(BENCH-05, BENCH-10 use stricter cuts).

---

## 4. Dual confidence

Every `BenchmarkResult` reports **two** confidences, never conflated (`ARCH-04`; `ADR-0017`):

- **`outcome_confidence`** — how good the work is (a property of the score).
- **`judgment_confidence`** — how *certain the scoring is*. Objective-heavy results score high
  judgment confidence; results leaning on model-assisted rubric items score lower and are
  flagged *provisional*, eligible for human spot-audit.

Judgment confidence is computed from the objective-weight share actually exercised and the mean
`judgment_confidence` of the rubric items:

```
judgment_confidence ≈ objective_weight_share
                    + (1 − objective_weight_share) × mean(rubric_item_judgment_confidence)
```

A result whose judgment confidence falls below `0.70` is not admitted to a leaderboard without
review. This is how the framework refuses to "launder a guess" at the benchmark level, not just
the single-evaluation level.

---

## 5. Statistical treatment (repeats, seeds, intervals)

LLM-backed Workers are stochastic. The framework treats that head-on rather than reporting a
single lucky draw.

- **Seeds.** A run fixes a base `seed`; repeat *k* uses a deterministic derived seed
  (`seed + k`). Deterministic gates must reproduce exactly across repeats; only genuinely
  sampled behavior varies.
- **Repeats.** Each case is executed `repeats` times (suite default **5**; **10+** for the
  high-variance BENCH-04/05/08). Per-case results carry `score_mean`, `score_stddev` and a
  `confidence_interval`.
- **Confidence intervals.** The aggregate score reports a **bootstrap** 95% CI over the repeat
  (and case) distribution (`confidence_interval.method: bootstrap`). Wilson intervals are used
  for pure pass-rate metrics.
- **Comparisons need overlap tests.** Two Workers (or two models) are declared *different* on a
  suite only if their CIs separate at the stated level; otherwise the result is "no significant
  difference." Leaderboards render CIs, not just point scores, to prevent over-reading noise.
- **Outlier transparency.** Repeats are never silently dropped; if a repeat is excluded (e.g.
  provider outage), the reason is recorded in `metadata`.

---

## 6. Normalization across models

Raw scores are already model-agnostic in *construction* (ground truth is MCG-artifact-based),
but three normalizations make cross-model and cross-Worker comparison fair (`RFC-0026`):

1. **Capability-fair budgets.** Token/window budgets are expressed relative to the model's
   advertised capability (via the Gateway `gateway_capability_digest`), so a small-context model
   is not penalized for a task that assumes a large window unless the suite is explicitly testing
   that (BENCH-01 budget pressure).
2. **Cost/latency normalized separately.** BENCH-12/13 report *both* absolute figures and figures
   normalized to a reference model, so a cheaper-but-slightly-worse Worker is legible on a
   quality-per-dollar / quality-per-second basis rather than hidden.
3. **Z-scored composite (optional).** A cross-suite composite standardizes each suite's scores to
   the cohort mean/stddev before weighting, so a suite with a naturally compressed score range
   does not dominate or vanish. The composite always ships alongside the raw per-suite vector,
   never instead of it.

Normalization never changes ground truth or per-case scoring; it only affects how results are
*presented and ranked*.

---

## 7. Leaderboard construction

A leaderboard is built from `BenchmarkResult` aggregates (`RFC-0026`):

- **Unit of ranking = (Worker implementation, model, dataset_version).** Never a bare model.
- **Per-suite first.** The primary artifact is a 13-column vector (one score + CI per suite),
  because a single number hides the trade-offs the framework exists to expose.
- **Composite second.** An optional weighted or z-scored composite gives a single ordering, with
  the weighting scheme published and versioned.
- **Ties broken by CI, then by cost/latency.** Overlapping CIs are shown as ties; among genuine
  ties the more efficient Worker (BENCH-12/13) ranks higher.
- **Provenance mandatory.** Every leaderboard cell links to the `BR-####`/`BRES-####` that
  produced it and the `dataset_version`, so any entry is reproducible and auditable.
- **Immutable history.** Entries are append-only; a re-run under a new harness or dataset version
  is a new entry, preserving longitudinal trend (the direct measurement of CANON's
  continuous-improvement flywheel, `ARCH-07` signals).

---

## 8. Guarding against metric gaming

The framework assumes the metric *will* be optimized and designs against it (`ARCH-04` failure
mode "Gaming the metric"). Per-case `anti_gaming[]` names the guards; scoring emits
`gaming_flags[]` when a guard trips, which caps or voids the case score.

Cross-cutting defenses:

- **Distractors and `must_exclude`.** Retrieval/selection suites penalize over-inclusion, so
  "return everything" cannot win.
- **Precision alongside recall.** Recall-only metrics reward flooding; every retrieval suite
  pairs recall with precision.
- **Held-out cases.** A rotating hidden slice of each suite (not published) detects overfitting to
  the public set; large public-vs-hidden gaps are flagged.
- **Mutation / negative tests.** Correctness suites require negative assertions (e.g. BENCH-01
  must exclude `KN-101`; a Worker that only maximizes inclusion fails).
- **Trivial-work detection.** Coverage/planning gates check substance, not volume (no credit for
  trivial tests that lift coverage without asserting behavior).
- **Independent judge.** Model-assisted rubric items are scored by a model *different from and
  blind to* the Worker under test, and judge accuracy is itself tracked against human labels.
- **Cost/latency counted.** A Worker cannot buy quality with unbounded calls unnoticed — BENCH-12/13
  make efficiency visible, and a suite may cap reasoning budget.

---

## 9. Reproducibility protocol

Reproducibility is a hard requirement (`ADR-0048`; `ARCH-04` Best Practice 7). A published
result must be replayable by a third party:

1. **Freeze inputs.** The `BenchmarkCase` set and `dataset_version` are immutable.
2. **Capture the environment.** `BenchmarkRun.environment` records `provider`, `model`,
   `model_class`, `seed`, `temperature`, `harness_version`, `gateway_capability_digest` and
   `dataset_version`.
3. **Replay.** `Worker.replay(run_id)` (`RFC-0024`) re-executes the run. Deterministic gates must
   reproduce **exactly**; sampled steps reproduce under the recorded seed. A divergence in a
   deterministic gate is a harness bug, not noise.
4. **Re-derive statistics.** Repeats, means, stddevs and CIs are recomputed from the replay; a
   published aggregate that cannot be re-derived within its CI is rejected.
5. **Provider swap is a config change only.** To benchmark a different provider, only
   `environment.provider`/`model` change (`ADR-0010`); the case set, ground truth and scoring are
   untouched — the structural guarantee that makes BENCH-11 meaningful.
6. **Everything is provenanced.** No score without evidence; no leaderboard cell without a linked
   run and result (`ARCH-07` Best Practice 7).

---

## 10. Roles & governance

- **Quality Engineering (`TEAM-050`)** owns rubrics and ground-truth labels; versions them.
- **AI Engineering (`TEAM-070`)** owns the harness (`RFC-0025`) and the Worker implementations
  under test.
- **Architecture Office (`TEAM-090`)** owns this methodology, the schemas and canon consistency;
  approves new suites and dataset versions.

A change to scoring that alters historical comparability requires an RFC; a change that alters an
invariant (objective-first, evidence-linked, dual-confidence, reproducible) requires an ADR and is
subordinate to `CANON-001`.
