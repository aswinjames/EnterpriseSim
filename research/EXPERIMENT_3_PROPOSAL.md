# Experiment 3 (X-RICH-1) — Context Selection Under a Richer Enterprise Environment

**Update — this experiment has since been run live, 5×5, for both Jev and
GPT.** Results: `research/jev_context_decision/results/experiment3_jev_20260920T192733Z.json`,
`results/experiment3_gpt_20260920T194326Z.json`. See
[`research/jev_context_decision/RESEARCH_STATE.md`](jev_context_decision/RESEARCH_STATE.md)
for the summarized findings, and this same directory's `README.md` for how
X-RICH-2 and X-RICH-3 build on this design. **The rest of this document is
preserved unchanged as the original pre-execution design** — written and
reviewed before any live run, describing the candidate pool, classifications,
and research question as they were designed. Its "not yet run" / "proposed,
not performed" language below describes that design-time state, not the
current state of the experiment.

**Original status note (superseded by the update above): implemented offline,
not yet run live.** This document describes the
design and the evidence behind every candidate classification. Code lives in
`research/jev_context_decision/experiment_3_candidates.py` and
`run_experiment_3.py`. Offline tests: `tests/test_experiment_3_candidates.py`
(30 tests, part of the repo's 115-test offline suite).

## 1. Research question

> When a candidate artifact is structurally connected to the task's domain via
> a real, declared enterprise dependency, does a context-selection system
> distinguish dependency-level relevance from task-level necessity, or does it
> treat structural/semantic connection as sufficient grounds for inclusion?

This is not a question BC-0101 or BC-0102 could answer on their own — both use
the same 7 candidates, none of which (except KN-101, see §3/§5) sits at a real,
documented dependency boundary the way Experiment 3's expanded pool does.

## 2. Why the candidate pool is expanded

BC-0101/BC-0102 use 7 candidates drawn from a much larger, already-existing
enterprise corpus: `enterprise/knowledge/*.json` alone holds 145 knowledge
entries (5 used) and `corpus/experience_store.json` holds 13 experiences (2
used), all already real and already interconnected via explicit
`relations`/`depends_on`/`related` fields. `enterprise/registry/applications.json`
independently encodes a real 12-app dependency graph. Experiment 3 draws 8
additional candidates from this same, unmodified corpus — no new enterprise
schema or data was created or required (see §7 and the inspection note below).

**A note on schema changes:** a prior instruction referenced "changes already
made" to the enterprise schema. `git log --oneline -- enterprise/ schemas/`
shows exactly one commit touching those paths — the repository's own root
commit. No schema change exists in this repository's history. Experiment 3 is
built entirely on the original, unmodified enterprise data model, which turned
out to already be rich enough for this design.

## 3. Why KN-101 remains

KN-101 was part of both BC-0101 and BC-0102. Removing it from Experiment 3
would silently break the experimental lineage those two cases established, and
would also remove the single most informative candidate for this experiment's
own research question. Specifically:

- `enterprise/registry/applications.json` confirms `APP-003.dependencies`
  includes `APP-007` — the app that owns KN-101. **KN-101 is not a
  structurally-unrelated distractor**; a real, declared dependency edge
  connects its owning application to the task's own application.
- Its real content ("Regional price resolution and currency binding") is
  plausibly relevant to computing an order total, unlike an obviously
  off-topic artifact.

Because of this, KN-101 is retained as a **CONTESTED** candidate rather than
either being dropped or having its historical `must_exclude` label silently
carried forward as this experiment's answer.

## 4. Three reasoning axes

Kept explicitly separate throughout the adjudication and in the data model:

| Axis | Question | Evidence source |
|---|---|---|
| **A. Structural enterprise relationship** | Is there a declared dependency/ownership edge to APP-003? | `enterprise/registry/applications.json` |
| **B. Semantic relevance** | Does the content plausibly bear on checkout/order-placement? | The artifact's own body text |
| **C. Task-specific necessity** | Would omitting it materially reduce the ability to correctly implement `PlaceOrder.java`? | Not directly evidenced by any single field — the genuinely hard question |

Structural relationship does not imply necessity (KN-101: A=yes, C=unresolved).
Absence of a direct dependency does not imply irrelevance either — this is why
candidates were adjudicated individually rather than by a blanket
apps-in-scope rule.

## 5. KN-101 ambiguity (documented, not resolved)

| | Value |
|---|---|
| Historical ground truth (BC-0101/BC-0102, frozen) | `must_exclude` |
| Historical `ground_truth.notes` claim | "marketplace seller onboarding" |
| KN-101's actual content | "Regional price resolution and currency binding" |
| Owning app | APP-007 |
| APP-007 vs. APP-003 | Declared dependency (`applications.json`) |
| Experiment 3 classification | **CONTESTED** |

Neither the historical note nor KN-101's content has been changed anywhere.
**Effect on benchmark validity:** the historical `must_exclude` label's own
stated rationale doesn't match what KN-101 actually says, and now that the
real dependency edge is known, a Worker reasoning from real content has a
legitimate, evidence-grounded reason to lean toward *including* it. BC-0101/
BC-0102's result (both providers included KN-101 in most/all runs) may
therefore reflect a defensible read of genuinely ambiguous content rather than
a straightforward failure to spot an obvious distractor. Experiment 3 is built
specifically so this can be observed rather than assumed.

**How KN-101 is handled without inventing a ground-truth answer:**
`experiment_3_candidates.CONTESTED_CANDIDATE_IDS = ("KN-101",)`; every run
captures its decision (verdict, confidence, rationale) in a dedicated
`contested` record, and `run_experiment_3.py::_build_scored_context()` removes
it from the included/excluded sets passed to the unmodified `score()` before
scoring — so it can never affect recall, precision, or the required-items
gate, in either direction. Its selection rate is reported separately
(`kn101_selection_rate`) as an observation, never as a pass/fail judgment.

## 6. Related-but-unnecessary candidates

A new descriptive tier, absent from BC-0101/BC-0102's vocabulary
(`must_include`/`acceptable_optional`/`must_exclude`/unresolvable). These 6
candidates are genuinely connected to the enterprise domain — five share
APP-003 with the task itself, one (`EXP-206`, APP-009) connects via a real
`applications.json` dependency edge — but their content addresses a different
concern (latency SLOs, change-freeze policy, incident postmortems/runbooks,
saga-testing practice) than the guest-checkout order-placement invariants this
task is about:

| ID | App | Why related | Why unnecessary |
|---|---|---|---|
| KN-128 | APP-003 | `depends_on: [KN-052]`, same app | Latency-SLO/circuit-breaking policy |
| KN-146 | APP-003 | `related: [KN-063, KN-128, KN-141]` | Change-freeze/deployment policy |
| KN-411 | APP-003 | Same app, references a real incident | Operational runbook, not implementation guidance |
| KN-313 | APP-003 | Same app, references a real incident | Postmortem about a *different* incident than EXP-090's |
| EXP-209 | APP-003 | Same app | Performance-hardening lesson, not a placement-correctness rule |
| EXP-206 | APP-009 | Real dependency of APP-003 | Saga-compensation testing practice, not a call APP-003 needs to make |

They are deliberately absent from `must_include`/`acceptable_optional`/
`must_exclude` in the Experiment 3 case (`build_experiment_3_case()`) —
exactly like KN-047's existing treatment — so `score()` needs no modification
to handle them correctly. Their inclusion is tracked descriptively
(`related_but_unnecessary_selected`/`_total`/`_inclusion_rate`) to observe
whether a provider over-admits genuinely-connected-but-unneeded material as
the candidate pool grows — the direct test of H3.

## 7. Historical comparability

| | Candidates | Criterion |
|---|---|---|
| BC-0101 | 7 | "Should this artifact be included in the Worker working context for this task?" |
| BC-0102 | Same 7 | "Is this artifact necessary to correctly perform this specific task? ..." |
| Experiment 3 (X-RICH-1) | Same 7 + 8 new = 15 | BC-0101's criterion, byte-for-byte (reused directly, not re-worded) |

The original 7 candidates' content, IDs, and (for the 6 non-contested ones)
classifications are unchanged. Experiment 3 changes candidate-environment
richness, not the original candidates or the criterion — the only variable
under test is the size and interconnectedness of the surrounding context.

## Held-out candidates (not in the executable pool)

`KN-126`, `KN-127`, `KN-144`, `KN-140`, `KN-136` remain outside the 15-candidate
pool. All five have real supporting evidence pointing toward more than one
plausible classification (see the standalone adjudication report from the
prior phase); none were forced to resolve cleanly. They are documented as a
held-out, contested tranche for a separate future adjudication — not silently
dropped, not silently included.

## Context-expansion analysis

| | Original (BC-0101/0102) | Experiment 3 |
|---|---|---|
| Total candidates | 7 | 15 |
| Knowledge / Experience | 5 / 2 | 11 / 4 |
| must_include | 3 | 3 (unchanged) |
| acceptable_optional | 2 | 2 (unchanged) |
| related_but_unnecessary | 0 (tier didn't exist) | 6 |
| must_exclude | 1 | 2 (KN-101 moved to contested; KN-122, KN-311 new) |
| contested | 0 (tier didn't exist) | 1 (KN-101) |
| unresolvable | 1 | 1 (unchanged) |

## Metrics captured (per run and per 5-run batch)

Preserving comparability with BC-0101/BC-0102, from the unmodified `score()`:
required-item recall, retrieval precision, required-items gate, overall
objective score, verdict, per-candidate include/exclude decisions with
confidence — all computed over the KN-101-filtered `scored_selected` context.

New, analysis-only, computed outside `score()`:
- `contested.selected_ids` / `excluded_ids` / full decision records for KN-101
- `kn101_selection_count` / `kn101_selection_rate` (batch-level, e.g. "3/5 runs
  → 60%") — an observation, never a correctness judgment
- `related_but_unnecessary.selected_count` / `total_count` / `inclusion_rate`
  (per run), `related_but_unnecessary_inclusion_rate_mean` (batch-level)

## Threats to validity

- The 8 new candidates' classifications are newly-introduced experimental
  judgments grounded in real artifact content and the real dependency graph —
  not pre-existing benchmark rules. They carry the same authority as
  BC-0101/BC-0102's original curation, no more, no less.
- KN-101's contested status is itself a design choice; a reader could argue
  either historical label should have been kept. This document exists so that
  choice is visible and reviewable rather than silent.
- Same single-task limitation as BC-0101/BC-0102: one task (CHK-1421), one
  domain (guest checkout). Findings should not be generalized beyond this
  case without further work.

## Execution plan (not yet run)

Once approved:
```bash
# Offline wiring check (already passing):
python3 -m research.jev_context_decision.run_experiment_3 --provider mock --repeats 1

# Live sanity check, one provider at a time:
OPENROUTER_API_KEY=... python3 -m research.jev_context_decision.run_experiment_3 --provider jev --repeats 1 --live
OPENAI_API_KEY=...    python3 -m research.jev_context_decision.run_experiment_3 --provider gpt --repeats 1 --live

# Full 5-repeat batches, once sanity checks pass:
OPENROUTER_API_KEY=... python3 -m research.jev_context_decision.run_experiment_3 --provider jev --repeats 5 --live
OPENAI_API_KEY=...    python3 -m research.jev_context_decision.run_experiment_3 --provider gpt --repeats 5 --live
```
No live run had been made as part of this design/implementation phase — see
the status update at the top of this document for what has happened since.
