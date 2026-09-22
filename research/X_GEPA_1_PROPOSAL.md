# X-GEPA-1 — Optimizing Context Selection Under Scarcity

**Status: implemented and offline-validated, not yet run live.** This
document describes the design, why it exists, and its honest limitations.
Code lives in `research/jev_context_decision/experiment_x_gepa_1_candidates.py`,
`gepa_jev_adapter.py`, and `run_experiment_x_gepa_1.py`. Offline tests:
`tests/test_x_gepa_1.py` (17 tests, part of the repo's 146-test offline
suite). A real `gepa==0.1.4` engine sanity run (see §7) was performed outside
this repository, against this exact adapter code, with fake offline
providers — it is not part of the committed test suite (it needs Python
≥3.10 and the `gepa` package, neither available in this repo's normal test
environment) but its result is reported here because it materially changed
the adapter code (see §7's bug fix).

## 1. Motivation

A public article, [*"Adapting Jev to Your Domain with
GEPA"*](https://praneeth16.github.io/blog/adapting-jev-with-gepa/) by
Praneeth Paikray (20 Sep 2026), already shows GEPA optimizing JEV's
instruction for a medical-literature classification task (identifying
adverse-drug-event sentences in the ADE Corpus V2), improving F1 from 69.1%
to 79.7% and Brier score from 0.1357 to 0.0747. That article is the reason
this experiment is scoped the way it is: X-GEPA-1 does **not** reproduce
"GEPA optimizes JEV's prompt, classification accuracy improves." It asks a
narrower, EnterpriseSim-specific question that Praneeth's article doesn't
touch at all.

## 2. Research question

> Can GEPA optimize the decision-policy text JEV uses to judge one candidate
> artifact, such that — when the optimized policy is run through the exact
> same X-RICH-3 hard-budget mechanism — more of the five-item budget
> survives for artifacts that actually matter?

More specifically, two nested questions:
1. Does optimizing the policy change *which* enterprise context survives a
   hard context budget (relative to `X-RICH-3`'s unoptimized, BC-0101-seeded
   baseline)?
2. Does an optimized policy protect `MUST_INCLUDE` artifacts more reliably
   than the seed policy did — recall from `RESEARCH_STATE.md` that GPT's
   *unoptimized* confidence ranking in `X-RICH-3` displaced a required
   artifact in 2 of 5 runs.

## 3. Why this is different from Praneeth's article

| | Praneeth's GEPA+JEV experiment | X-GEPA-1 |
|---|---|---|
| Task | Medical ADE sentence classification | Enterprise context selection for guest checkout |
| Optimization target | JEV's classification accuracy/Brier score, standalone | JEV's decision policy — GEPA's own search signal is a per-candidate Brier proxy (same family of metric as Praneeth's); its *downstream effect* on what survives a hard budget is checked separately, after optimization, not fed back into GEPA's search (see §6) |
| Dataset | ADE Corpus V2, 20,895 sentences | This repo's existing 15-candidate `X-RICH-1` pool (13 usable labeled examples after excluding CONTESTED/UNRESOLVABLE — see §5) |
| Final metric | F1, precision, recall, Brier (classification) | `MUST_INCLUDE` retention, required-artifact failures, `X-RICH-3`'s existing objective score/recall/precision, budget compliance, related-but-unnecessary retention, confidence/ranking behavior |
| Scale | Large (100+ training examples, 300 test) | Small — explicitly a pilot (§5) |

The two share GEPA and JEV as tools; they optimize for structurally
different things. "GEPA can improve JEV's classification accuracy" was
already shown by Praneeth. This experiment asks whether that kind of
optimization changes *what a Worker keeps when it can't keep everything* —
a question specific to EnterpriseSim's context-assembly research, not
addressed by the prior article.

## 4. Hypothesis

Optimizing JEV's decision-policy text against labeled category examples
(`MUST_INCLUDE`/`ACCEPTABLE_OPTIONAL` → include, `RELATED_BUT_UNNECESSARY`/
`MUST_EXCLUDE` → exclude) will sharpen the policy's ability to distinguish
"relevant" from "necessary" — the exact distinction `BC-0102` first probed —
and that sharper distinction should show up downstream as fewer
`RELATED_BUT_UNNECESSARY` artifacts surviving the `X-RICH-3` budget cut,
without sacrificing `MUST_INCLUDE` retention. This is a hypothesis to test,
not a result — see §9 for what would actually falsify it.

## 5. Dataset, and why this is a PILOT, not a full experiment

The repository has exactly **one task** (`CHK-1421`) and **one** 15-candidate
pool (`X-RICH-1`'s, reused unchanged through `X-RICH-2`/`X-RICH-3`). There is
no second task to hold out for train/val/test. The only labeled examples
available are the individual candidate artifacts themselves, each carrying
its existing, frozen `experiment_3_candidates.CLASSIFICATIONS` label.

`KN-101` (CONTESTED) and `KN-047` (UNRESOLVABLE — no real content) are
**never** used as labeled examples, in either direction. That leaves 13:

| Category | Count | Target verdict |
|---|---|---|
| `MUST_INCLUDE` | 3 | include |
| `ACCEPTABLE_OPTIONAL` | 2 | include |
| `RELATED_BUT_UNNECESSARY` | 6 | exclude |
| `MUST_EXCLUDE` | 2 | exclude |

**13 examples split three ways is not a statistically defensible
train/val/test split.** The fixed split used (`experiment_x_gepa_1_candidates.py`):

- **Train (5):** `KN-045`(MI), `KN-063`(AO), `KN-128`(RBU), `KN-146`(RBU), `KN-122`(ME)
- **Val (3):** `KN-052`(MI), `KN-411`(RBU), `KN-313`(RBU)
- **Test (5):** `EXP-090`(MI), `EXP-055`(AO), `EXP-209`(RBU), `EXP-206`(RBU), `KN-311`(ME)

Train and test each contain all 4 categories; **val contains zero examples
of `ACCEPTABLE_OPTIONAL` and zero of `MUST_EXCLUDE`**, because only 2 of
each exist in the entire dataset and one was already spent on train, one on
test. This is the honest consequence of a 13-example, single-task dataset —
not a modeling choice. **X-GEPA-1 is explicitly a pilot/feasibility
experiment, not a statistically powered one, because of this**, per the
instruction that produced this design: do not manufacture a
statistically-dressed-up experiment on data too small to support one.

## 6. Design

**What's optimized:** three text fields of a `DecisionCase`
(`jev_instructions`, `jev_criteria_true`, `jev_criteria_false` —
see `providers/base.py`). `task_statement` and `task_scope` stay fixed,
copied unchanged from `BC_0101`. `BC_0101` itself is never mutated — every
GEPA candidate becomes a brand-new `DecisionCase` instance.

**Adapter:** `gepa_jev_adapter.JevGepaAdapter` implements GEPA's two required
methods (`evaluate`, `make_reflective_dataset`) as a plain duck-typed class
(not subclassing `gepa.core.adapter.GEPAAdapter`, which is a `Protocol` —
this keeps the module importable without `gepa` installed; see §7 for the
one place duck typing wasn't quite enough).

**Per-example metric:** a Brier-score complement over JEV's own `noul`
probability — `1 - (p_include - target)^2`, in `[0, 1]`, higher is better —
not raw classification accuracy. `target` is 1.0 for `MUST_INCLUDE`/
`ACCEPTABLE_OPTIONAL`, 0.0 for `RELATED_BUT_UNNECESSARY`/`MUST_EXCLUDE`.

**GEPA optimization (train/val):** `gepa.optimize(seed_candidate=<BC-0101's
current text>, trainset=<5 train examples>, valset=<3 val examples>,
adapter=JevGepaAdapter(provider=JevProvider()), reflection_lm=<configurable,
default "openai/gpt-5-mini">, max_metric_calls=60)`.

**Downstream comparison (the actual research answer):** both the seed
(BC-0101) criterion and `result.best_candidate` (GEPA-optimized) are each
run through the *full, unmodified* 15-candidate `X-RICH-1` pool, JEV only,
through the *identical* `X-RICH-3` budget mechanism
(`run_experiment_x_rich_3.apply_budget`, imported unchanged — not
reimplemented) and the identical, unmodified scorer. **The model is never
told about the budget in either condition** — the cap is imposed
mechanically by `apply_budget()` after independent per-candidate decisions,
exactly as in `X-RICH-3`.

Note this means the full-pool budget run necessarily includes the same
candidates used to *train* the optimized policy (there is only one 15-item
pool). It is not a leakage-free held-out test of the budget outcome — only
the separate, candidate-level test-split evaluation (§5, 5 examples) is
held out from optimization. Both numbers are reported; neither is presented
as the other.

## 7. What was actually validated (offline, before any live call)

1. **146/146 offline tests pass** (129 historical + 17 new in
   `tests/test_x_gepa_1.py`), including: `KN-101`/`KN-047` are provably never
   labeled; the three splits partition the 13 examples with no overlap;
   train and test both cover all 4 categories; `evaluate()` returns
   correctly-shaped output for both a policy that matches every target and
   one that inverts every target (scores land above/below 0.5
   respectively); `make_reflective_dataset()` produces the exact
   `{"Inputs", "Generated Outputs", "Feedback"}` record shape GEPA's default
   instruction proposer expects.
2. **A real `gepa==0.1.4` sanity run**, outside this sandbox's Python 3.9
   (gepa requires Python ≥3.10 — confirmed directly from PyPI's file
   metadata, not assumed): in an isolated Python 3.12 venv, `gepa.optimize()`
   was called against this exact `JevGepaAdapter`, the real 5-example
   train / 3-example val split, a fake deterministic offline JEV stand-in,
   and a fake deterministic reflection LM (no network, no API cost). This
   caught one real bug: GEPA's engine reads `self.adapter.propose_new_texts`
   directly rather than via `getattr`, so the attribute has to exist on the
   adapter even when unused — the fix (a `propose_new_texts: Any = None`
   dataclass field) is in the committed adapter. After the fix, the full
   engine loop ran to completion with zero errors: candidate selection,
   minibatch evaluation, reflective dataset construction, instruction
   parsing (the `` ```...``` `` extraction), and the accept/reject decision
   all executed correctly against real `gepa` internals. No candidate
   improvement was found in that particular sanity run, which is expected —
   the fake reflection LM returns identical text on every call, so after one
   evaluated proposal there is nothing new to accept. That's a property of
   the deliberately non-adaptive fake reflection LM, not the adapter.

## 8. What has NOT been run

No live call of any kind has been made: not a live JEV decision, not a real
GEPA reflection-LM call. `run_experiment_x_gepa_1.py --live` requires
`OPENROUTER_API_KEY` (JEV) and a working reflection-LM credential (e.g.
`OPENAI_API_KEY` for the default `openai/gpt-5-mini` reflection model), plus
`gepa` importable — none of which are available in this sandbox (no API
keys are set, and this sandbox's Python is 3.9.6; `gepa` needs ≥3.10). This
is stated plainly rather than worked around.

## 9. No overclaiming

This experiment does not attempt to show "GEPA is better than JEV" — that
sentence doesn't parse; GEPA optimizes JEV, it isn't a competitor to it. It
also does not attempt to show JEV is better or worse than GPT — GPT isn't
part of this experiment at all (GEPA here only optimizes JEV's policy,
matching this repo's existing Jev-only-optimization scope). The only claim
this experiment is built to support, if the live run confirms it, is
narrower: whether optimizing JEV's decision-policy text against these 13
labeled examples changed what survives a hard five-item budget on this one
task, and whether `MUST_INCLUDE` retention held or slipped in the process.
Given §5's honest limitations, even a positive result here would be a pilot
finding on one task, not a general claim about GEPA, JEV, or context
selection.

## 10. Next step

Two independent blockers, either can be resolved without the other:

1. **Run it live.** Needs `OPENROUTER_API_KEY`, a reflection-LM credential,
   and `gepa` installed in a Python ≥3.10 environment (this sandbox has
   neither the credentials nor a compatible Python — a Python 3.12 venv
   with `gepa==0.1.4` was created and validated for the offline sanity run
   in §7, but no live credentials exist to complete a real optimization run
   in it). Once available: `python3 -m research.jev_context_decision.run_experiment_x_gepa_1 --live`.
   Output is written to `results/xgepa1_jev_<UTC timestamp>.json` (auto-named,
   same convention as every other runner in this directory).
2. **Make the split defensible.** The real fix for §5's small-N problem is
   not a cleverer split of the one existing pool — it's more EnterpriseSim
   task scenarios (plural), so GEPA can train on some tasks and be evaluated
   on genuinely different, held-out ones. That is a larger scope decision
   for this repository (more simulated enterprise use cases, per the
   project's own stated direction in `RESEARCH_STATE.md`), not something
   this experiment should invent unilaterally — flagged here as a
   recommendation, not built.
