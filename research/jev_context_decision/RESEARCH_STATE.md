# Research State: Context Assembly as a Selection Problem

**What this document is.** The single, canonical summary of what this research
has actually done and actually found, as of X-RICH-3. It is not the blog post
— it is the source of truth a blog post would be written from. Every number
here is read from a result file or reconciled cost document already in this
repository; nothing here is estimated or invented. Where evidence is thin,
that is stated explicitly rather than smoothed over.

This document does not replace the per-experiment documents (`RESULTS.md` for
BC-0101, `../EXPERIMENT_3_PROPOSAL.md` for X-RICH-1's design,
`GPT_COST_RECONCILIATION.md` for cost detail) — it summarizes and links to
them. For full per-run detail, read the underlying JSON files in `results/`.

## 1. Business problem

An enterprise AI Worker can potentially access a very large amount of
organizational knowledge — knowledge base articles, past incident write-ups,
prior experience records, application metadata, dependency graphs. As that
pool grows, the problem is not "does the Worker have access to enough
information" but **deciding what information actually deserves a place in the
Worker's working context for one specific task.** Every additional artifact in
context costs tokens, costs latency, and risks distracting the model with
content that is topically related but not actually necessary to do the task
correctly.

## 2. Technical problem

Restated precisely: **context assembly is a selection/prioritization problem,
not a retrieval-completeness problem.** Given a task and a pool of candidate
artifacts, a context-assembly system must decide, per candidate, whether it
belongs in the Worker's working context — and, when the pool or the budget
changes, whether that decision is driven by genuine task-specific necessity or
by something weaker (topical relevance, structural/dependency proximity,
"this seems related").

## 3. EnterpriseSim

EnterpriseSim (this repository) provides a synthetic-but-realistic enterprise
substrate for testing that problem: real interconnected knowledge base
entries, experience records, and an application-dependency registry
(`enterprise/registry/applications.json`, 12 applications with declared
dependency edges), plus a benchmark harness (`score()` in
`examples/quickstart/run_quickstart.py`) that grades a selected context set
against a fixed ground truth (`must_include` / `acceptable_optional` /
`must_exclude`) for a specific benchmark case. `research/jev_context_decision/`
uses this substrate to compare how two different models — Jev and GPT — make
per-candidate include/exclude decisions for one fixed task, across a
progression of experiments that each change exactly one variable.

The task under study throughout is `CHK-1421` (guest checkout order
placement, `APP-003`), from benchmark case `BC-0101`. Every experiment below
reuses this same task.

## 4. Experiment progression

| Experiment | Candidates | Criterion | What changed | Status |
|---|---|---|---|---|
| BC-0101 | 7 | Relevance ("should this be included?") | Baseline | Complete, 5×5 |
| BC-0102 | Same 7 | Necessity ("is this necessary to correctly perform this task?") | Criterion wording only | Complete, 5×5 |
| X-RICH-1 | 15 (7 + 8 new) | BC-0101's criterion, reused by identity | Candidate pool enriched; KN-101 reclassified CONTESTED | Complete, 5×5 |
| X-RICH-2 | Same 15 | Same as X-RICH-1 | Complete, unfiltered application-dependency registry added to every prompt | Complete, 5×5 |
| X-RICH-3 | Same 15 | Same as X-RICH-1 | Hard cap of 5 selected candidates, enforced post-hoc by confidence ranking | Complete, 5×5 |

Both providers, throughout: **Jev** (`typesafe/jev-1.13`, via OpenRouter's
alpha Decisions API, `noul` question type) and **GPT** (`openai/gpt-5-mini`,
via the direct OpenAI Chat Completions API starting with BC-0102; BC-0101 used
OpenRouter for both — see `README.md`'s gateway note).

## 5. Key observations, by experiment

### 5.1 BC-0101 (relevance criterion, 7 candidates)

Both providers selected the identical 5-item set in all 5 runs each
(`EXP-090, KN-045, KN-052, KN-063, KN-101`), scored 0.400 (fail) every run.
Both included `KN-101` — the sole `must_exclude` item — in every run. Full
detail: [`RESULTS.md`](RESULTS.md).

### 5.2 BC-0102 (necessity criterion, same 7 candidates)

Reframing the criterion from relevance to necessity changed `KN-101`'s
selection rate, but did not eliminate it, and did so differently per provider:

| Provider | Score mean | Verdicts | KN-101 selected (forbidden) |
|---|---|---|---|
| GPT | 0.3868 | fail, fail, fail, fail, fail (5/5) | 5/5 runs |
| Jev | 0.5848 | partial, partial, fail, partial, fail | 2/5 runs |

GPT selected `KN-101` in every BC-0102 run despite the necessity framing —
identical to its BC-0101 behavior. Jev's inclusion rate dropped from BC-0101's
implicit 5/5 to 2/5 under the necessity criterion. This is a single
before/after comparison on one task with 5 repeats per provider; it shows
that criterion wording alone did not resolve `KN-101`'s inclusion for GPT, and
partially — not fully — reduced it for Jev. It does not establish which
provider "understood necessity better," only that their responses to the same
wording change differed.

### 5.3 The KN-101 discovery (why X-RICH-1 changed how KN-101 is treated)

While reviewing BC-0101/BC-0102, a real inconsistency was found
(`benchmark_quality.py::KN_101_DISCREPANCY`, `tests/test_benchmark_quality.py`):

| | Says |
|---|---|
| `benchmark_case.example.json`'s `ground_truth.notes` | "marketplace seller onboarding" |
| `KN-101`'s actual, resolvable content (`enterprise/knowledge/business-rules.json`) | "Regional price resolution and currency binding" |

These describe different subjects. Both models, reasoning from KN-101's real
content (not the ground-truth note, which they never see), gave rationales
about price/currency resolution being relevant to computing an order total —
a plausible read of what KN-101 actually says. Separately,
`enterprise/registry/applications.json` confirms a real, declared dependency:
`APP-003.dependencies` includes `APP-007`, the application that owns KN-101.
So KN-101 sits at a genuine structural dependency boundary, with content that
is plausibly semantically relevant, and unresolved task-specific necessity —
three axes that BC-0101/BC-0102 do not distinguish (`../EXPERIMENT_3_PROPOSAL.md`
§4).

**This is a benchmark-quality finding, not a resolved question.** Nothing in
this research concludes that KN-101 is objectively necessary or objectively
unnecessary for `CHK-1421`. Neither BC-0101's `must_exclude` label nor its
`ground_truth.notes` rationale has been altered — they remain frozen, exactly
as originally written. Starting with X-RICH-1, KN-101 is instead classified
**CONTESTED**: its decision is fully captured and reported every run, but it
is removed from the scored included/excluded sets before `score()` runs, so
it can never affect recall, precision, or the required-items gate in either
direction (`run_experiment_3.py::_build_scored_context`,
`experiment_3_candidates.CONTESTED_CANDIDATE_IDS`). Its selection rate is
reported as an observation, never as a pass/fail judgment.

### 5.4 X-RICH-1 (15 candidates, richer environment, KN-101 CONTESTED)

| Provider | Score mean | Recall mean | Precision mean | KN-101 selection rate | Related-but-unnecessary inclusion rate mean |
|---|---|---|---|---|---|
| Jev | 0.683 (flat, 0 stddev) | 0.800 | 0.571 | 5/5 | 0.500 |
| GPT | 0.6794 | 0.800 | 0.5568 | 5/5 | 0.5333 |

Both providers retained all 3 `must_include` items every run and produced
close, broadly similar aggregate scores. Both selected KN-101 in every run
under this criterion — richer candidate pool and CONTESTED treatment did not,
by itself, change KN-101's selection rate relative to BC-0101/BC-0102's GPT
behavior. Roughly half of the genuinely-connected-but-unnecessary candidates
(the `RELATED_BUT_UNNECESSARY` tier — six candidates sharing `APP-003` or a
real dependency edge, but addressing a different concern than order
placement) were admitted by both providers. This experiment does not
establish that "richer context improved or worsened results" as a general
claim — it establishes these specific numbers, on this one task, for this one
candidate pool. Design detail: [`../EXPERIMENT_3_PROPOSAL.md`](../EXPERIMENT_3_PROPOSAL.md).

### 5.5 X-RICH-2 (X-RICH-1 + complete application-dependency registry)

Testing H1: *"Explicit enterprise application-dependency context will change
candidate selection when structural relationships are relevant to determining
task-specific necessity."* Treatment: the complete, unfiltered
`enterprise/registry/applications.json` (all 12 applications, every field,
schema excluded) appended to every one of the 75 per-provider requests — the
only change from X-RICH-1.

| Provider | Score mean (X-RICH-1 → X-RICH-2) | Precision mean (X-RICH-1 → X-RICH-2) | Related-but-unnecessary inclusion rate mean (X-RICH-1 → X-RICH-2) | KN-101 selection rate |
|---|---|---|---|---|
| Jev | 0.683 → 0.683 (unchanged) | 0.571 → 0.571 (unchanged) | 0.500 → 0.500 (unchanged) | 5/5 → 5/5 |
| GPT | 0.6794 → 0.6594 | 0.5568 → 0.4776 | 0.5333 → 0.7333 | 5/5 → 5/5 |

Jev's scored metrics were completely unchanged by the added registry — same
score, same recall/precision, same RBU rate, to the same decimal. GPT's
precision decreased and its related-but-unnecessary inclusion rate increased
with the registry present; recall was unchanged at 0.8 for both providers in
both experiments. KN-101 remained selected in every run for both providers
either way.

**This experiment is consistent with the hypothesis that explicit
dependency context affects GPT's selection behavior — it does not establish
that the registry caused the change, and it does not generalize beyond this
one task, this one registry, and these two models.** A single before/after
comparison with 5 repeats per provider cannot rule out other explanations
(e.g., run-to-run variance in a non-deterministic model), though the
direction and size of GPT's shift (precision down ~14%, RBU inclusion up ~38%
relative) is larger than the run-to-run stddev observed within either
experiment alone.

Cost of the added registry: see §8 below and
[`GPT_COST_RECONCILIATION.md`](results/GPT_COST_RECONCILIATION.md).

### 5.6 X-RICH-3 (X-RICH-1 + a hard 5-candidate budget)

Research question: when the Worker has a hard limit on how many artifacts it
can place into working context, does its confidence ranking prioritize
task-necessary information over merely related information? Treatment: a
hard cap of 5 selected candidates, enforced as a pure post-hoc aggregation
over each provider's own, unchanged, independent per-candidate decisions —
rank every "include" verdict by the model's own confidence, keep the top 5.
**The model is never told about the budget or asked a different question; the
budget is mechanically enforced by `apply_budget()`, not "obeyed" by either
model.** The research question is what each provider's own confidence
ranking prioritized once fewer than all "included" items could survive — not
whether either model can reason about a budget.

| Provider | Score mean (X-RICH-1 → X-RICH-3) | Recall mean | Precision mean | Must-include retention mean | KN-101 selection rate | Run-to-run selection variance |
|---|---|---|---|---|---|---|
| Jev | 0.683 → 0.667 | 0.8 → 0.6 | 0.571 → 0.75 | 1.0 (3/3 every run) | 5/5 | None — identical selection every run |
| GPT | 0.6794 → 0.5248 | 0.8 → 0.6 | 0.5568 → 0.66 | 0.8667 (10/12; 2 of 5 runs dropped one) | 2/5 | High — every run's selection differed |

Both providers respected the 5-item cap in all 10 runs (by construction).
Both showed the same qualitative pattern: recall dropped (fewer slots means
fewer "relevant" items retained overall) while precision rose (the smaller
set is more concentrated in scorer-relevant items). Jev's confidence ranking
was fully deterministic across all 5 repeats — identical selected set,
identical dropped set, identical score every time. GPT's ranking varied on
every run: which related-but-unnecessary item survived differed run to run,
and in 2 of 5 runs GPT's own confidence ranking placed a required item
(`EXP-090` in one run, `KN-045` in another) below the cut line, triggering the
scorer's required-items gate and a `fail` verdict (score 0.367 and 0.33
respectively — well below the 0.63–0.667 scores of the "clean" runs).

**The defensible observation: under this specific task and budget mechanism,
Jev's selection was stable across repeats, while GPT displaced a required
artifact in 2 of 5 runs.** This is not a claim that Jev is "better" at context
selection — it is a claim about run-to-run consistency of one specific
confidence-ranking mechanism, on one task, with a five-run sample per
provider. It does not generalize to other tasks, budgets, or model versions.

## 6. KN-101 — cross-experiment summary

| Experiment | KN-101 treatment | Selection rate |
|---|---|---|
| BC-0101 | `must_exclude` (frozen ground truth) | Jev 5/5, GPT 5/5 |
| BC-0102 | `must_exclude` (frozen ground truth, necessity criterion) | Jev 2/5, GPT 5/5 |
| X-RICH-1 | CONTESTED (excluded from scoring either way) | Jev 5/5, GPT 5/5 |
| X-RICH-2 | CONTESTED | Jev 5/5, GPT 5/5 |
| X-RICH-3 | CONTESTED, additionally subject to the 5-item budget | Jev 5/5, GPT 2/5 |

KN-101 has never been given a resolved ground-truth answer in this research.
The historical `must_exclude` label from BC-0101/BC-0102 has not been changed
to agree with KN-101's real content, and no experiment has concluded KN-101
is objectively necessary or unnecessary for `CHK-1421`. What has changed
across experiments is (a) the criterion wording, (b) whether KN-101 affects
the formal score at all, and (c) whether it survives a hard selection budget
— and both providers' responses to those changes differ from each other in
ways this document reports without adjudicating.

## 7. Jev's role in this research

Jev is not framed here as a competitor being "better" or "worse" than GPT at
context selection in general — the sample sizes (5 runs per condition, one
task) do not support that claim for either model. Its practical role in this
research has been:

- **Fast, low-marginal-cost repeated decision generation** — BC-0101's
  measured mean cost was $0.0001859/run for Jev vs. $0.0018767/run for GPT
  (`RESULTS.md` §4), enabling the repeated 5×5 batches this research relies
  on without prohibitive cost.
- **A structured context-decision workflow** via the `noul` typed-decision
  question, distinct from GPT's free-form-JSON-then-parse approach.
- **A second, independent reasoning path** for the same per-candidate
  question, useful for observing where two differently-built models agree or
  diverge (e.g., §5.2's BC-0102 KN-101 divergence, §5.6's X-RICH-3 stability
  difference).

**Observed:** Jev is fast and cheap enough to be useful for generating large
numbers of independent context-selection decisions in this research context.

**Not yet established:** whether Jev-generated decisions are suitable as
training labels for RLCD (reinforcement learning from contextual decisions)
or any other downstream training use. No experiment in this repository has
tested label quality, inter-model agreement rates as a proxy for
correctness, or any training pipeline. This is a future research direction,
not a current result — it should not be read as one.

## 8. Economics

All GPT cost figures below are **reconciled real costs** from OpenAI's own
usage/cost exports (matched by exact request count against each experiment's
result files), not API-reported figures — the direct OpenAI API does not
return a per-call cost field, so the result JSONs for BC-0102 onward correctly
record `cost_usd_total: null`. Full provenance:
[`GPT_COST_RECONCILIATION.md`](results/GPT_COST_RECONCILIATION.md).

| | BC-0102 GPT (5×5 + validation) | X-RICH-1 GPT (5×5) | X-RICH-2 GPT (5×5) |
|---|---|---|---|
| Requests | 42 | 75 | 75 |
| Input tokens | 10,908 | 19,315 | 165,790 |
| Cached input tokens | 0 | 0 | 117,376 (≈71%) |
| Real cost | $0.011721 | $0.019951 | $0.032514 |
| Per repeat | ≈$0.00234 | ≈$0.00399 | ≈$0.00650 |

X-RICH-2's raw input token volume grew ≈8.6× over X-RICH-1 (adding the full
application registry to every call), but real cost grew only ≈1.63× because
≈71% of that added volume was cache-discounted repeated content. **Raw token
growth should not be read as proportional cost growth** when the added
content is identical across calls.

No reconciled GPT cost figure exists yet for X-RICH-3 (would require the same
CSV-matching exercise against a later billing export). No Jev cost figures
beyond BC-0101's are reported here — BC-0101 is the only experiment where
Jev's cost was directly captured from the API response; extending this to
later experiments has not been done and is not estimated here.

## 9. Limitations

- **One task, one domain, throughout.** Every experiment in this document
  uses `CHK-1421` (guest checkout order placement). No claim here
  generalizes to other tasks, other domains, or the EnterpriseSim Worker
  architecture as a whole.
- **Small samples.** 5 repeats per provider per experiment. Observed
  differences (e.g., GPT's run-to-run variance under budget pressure) are
  reported descriptively; no statistical significance testing has been
  performed, and none is claimed.
- **Two models, two specific pinned versions** (`typesafe/jev-1.13`,
  `openai/gpt-5-mini`). Nothing here claims to characterize either model
  family in general, or any other model.
- **KN-101 is unresolved by design**, not by oversight — see §6.
- **No causal claims.** X-RICH-2 is consistent with H1; it does not prove
  the registry caused GPT's behavior change (§5.5). X-RICH-3 shows Jev was
  more stable under this budget mechanism; it does not show Jev is a better
  context-selection model (§5.6).
- **X-RICH-3 has no dedicated offline test file** — only an ad hoc mock
  smoke test was run before the live batch, per an explicit
  time-boxing decision during that session. `run_experiment_x_rich_3.py` is
  otherwise built on the same, already-tested `apply_budget`/`_build_scored_context`
  patterns as `run_experiment_3.py`/`run_experiment_x_rich_2.py`, both of
  which do have offline test coverage.
- **No consolidated results document exists for BC-0102 or any X-RICH
  experiment** in the style of `RESULTS.md` — this document's §5 summarizes
  them, but full per-run detail lives only in the raw JSON files under
  `results/`.

## 10. Open research questions

- Does the KN-101 pattern (structural dependency + plausible semantic
  relevance + unresolved necessity) generalize to other candidates, other
  tasks, or is it specific to this one artifact?
- Would explicit `TaskScope` information (declared apps, code target —
  designed but never threaded into a live prompt; see `README.md`'s "Task
  Scope" section) change either provider's KN-101 inclusion or its
  related-but-unnecessary/budget-induced behavior, independent of the
  criterion-wording change BC-0101→BC-0102 or the enterprise-context change
  X-RICH-1→X-RICH-2?
- Would GPT's run-to-run selection variance under a budget constraint
  (§5.6) persist at a larger sample size, or shrink toward Jev's observed
  stability?
- Is Jev's decision-generation speed/cost profile (§7) sufficient on its own
  to justify using it for large-scale synthetic-label generation, or does
  that require first validating decision quality against some independent
  standard?
