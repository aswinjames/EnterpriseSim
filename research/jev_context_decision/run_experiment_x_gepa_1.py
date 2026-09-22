#!/usr/bin/env python3
"""Runs X-GEPA-1 ("Optimizing Context Selection Under Scarcity"): PILOT.

Research question: can GEPA (https://github.com/gepa-ai/gepa) optimize the
decision-policy text JEV uses to judge one candidate artifact, such that --
when the optimized policy is run through the *exact same* X-RICH-3
hard-budget mechanism -- more of the five-item budget survives for artifacts
that actually matter? This is explicitly NOT an attempt to reproduce
https://praneeth16.github.io/blog/adapting-jev-with-gepa/ (which optimized
JEV for a medical ADE-classification task and measured classification
accuracy/Brier score in isolation) -- here the downstream target is
context-selection behavior under a hard budget, not classification accuracy
on its own. See ``research/X_GEPA_1_PROPOSAL.md`` for the full design and
the honest limitations of the train/val/test split used here (PILOT /
FEASIBILITY scope -- 13 labeled examples, one task, one candidate pool).

Two phases, both required, in this order:

1. GEPA OPTIMIZATION: ``gepa.optimize()`` with
   ``gepa_jev_adapter.JevGepaAdapter`` against the train/val split from
   ``experiment_x_gepa_1_candidates.py`` (13 labeled candidates total, 5
   held out entirely as test). KN-101 (CONTESTED) and KN-047
   (UNRESOLVABLE) are never labeled examples -- see that module.

2. DOWNSTREAM BUDGET COMPARISON: run the *seed* (BC-0101) criterion and the
   *GEPA-optimized* criterion each through the full, unmodified X-RICH-1
   15-candidate pool, JEV only, with the identical X-RICH-3 budget mechanism
   (``run_experiment_x_rich_3.apply_budget``, imported unchanged -- not
   reimplemented here) and the identical, unmodified scorer. This is what
   actually answers the research question; the GEPA optimization step (1) is
   a means to produce the "optimized" criterion tested here, not the result
   itself.

Every one of X-RICH-1/2/3's invariants is preserved unchanged: KN-101 stays
CONTESTED and excluded from the scored set either way; the candidate pool,
order, and bodies are identical to X-RICH-1/2/3; the scorer is imported
unmodified; the model is never told about the budget.

Safety: NO live calls of any kind (JEV decisions during either phase, or
GEPA's own reflection-LM calls during optimization) without --live AND the
required credentials actually present. This runner needs TWO credentials on
top of every other runner in this repo: OPENROUTER_API_KEY for JEV, and
whatever --reflection-lm's provider needs for GEPA's own reflection calls
(e.g. OPENAI_API_KEY for an "openai/..." model string, resolved by GEPA's
own gepa.lm.LM -- not by anything in this repo).
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

from .candidates import load_bc_0101_case
from .experiment_3_candidates import (
    ACCEPTABLE_OPTIONAL_IDS,
    CONTESTED_CANDIDATE_IDS,
    MUST_INCLUDE_IDS,
    RELATED_BUT_UNNECESSARY_IDS,
    build_experiment_3_case,
    load_experiment_3_candidates,
)
from .experiment_x_gepa_1_candidates import load_split
from .gepa_jev_adapter import (
    JevGepaAdapter,
    case_from_candidate_dict,
    seed_candidate_from_bc_0101,
)
from .providers import ProviderNotConfigured
from .providers.jev_provider import JevProvider
from .providers.openrouter import API_KEY_ENV_VAR as OPENROUTER_API_KEY_ENV_VAR
from .run_experiment_x_rich_3 import BUDGET, _build_scored_context, apply_budget
from .scoring import score as score_context

RESULTS_DIR = Path(__file__).resolve().parent / "results"
EXPERIMENT_ID = "X-GEPA-1"


def _budget_run(provider: JevProvider, case, candidates: list) -> dict:
    """One full 15-candidate -> budget-5 -> score pass, for one DecisionCase.

    Identical mechanism to run_experiment_x_rich_3.run_once(), reusing
    apply_budget()/_build_scored_context()/score() unchanged; the only
    difference is which DecisionCase's text is used to ask JEV each
    candidate's question. Always Jev-only -- X-GEPA-1 optimizes JEV's
    policy, not GPT's, matching this experiment's scope.
    """
    base_case = load_bc_0101_case()
    scoring_case = {**build_experiment_3_case(base_case), "id": EXPERIMENT_ID}

    decisions = [provider.decide(c, case=case) for c in candidates]
    raw_included = sorted(d.candidate_id for d in decisions if d.verdict == "include")
    budgeted_included, budgeted_excluded, dropped_for_budget = apply_budget(decisions, BUDGET)

    scored_context = _build_scored_context(
        budgeted_included, budgeted_excluded, decisions, scoring_case["task_ref"],
        exclude_ids=set(CONTESTED_CANDIDATE_IDS),
    )
    result = score_context(scoring_case, scored_context)

    must_include_retained = [c for c in MUST_INCLUDE_IDS if c in budgeted_included]
    optional_retained = [c for c in ACCEPTABLE_OPTIONAL_IDS if c in budgeted_included]
    rbu_retained = [c for c in RELATED_BUT_UNNECESSARY_IDS if c in budgeted_included]
    kn101_selected = any(cid in budgeted_included for cid in CONTESTED_CANDIDATE_IDS)

    return {
        "criterion_id": case.id,
        "prompt_version": case.prompt_version,
        "jev_instructions": case.jev_instructions,
        "jev_criteria_true": case.jev_criteria_true,
        "jev_criteria_false": case.jev_criteria_false,
        "raw_included_pre_budget": raw_included,
        "budgeted_selected": budgeted_included,
        "budgeted_excluded": budgeted_excluded,
        "dropped_for_budget": dropped_for_budget,
        "selected_count": len(budgeted_included),
        "budget_respected": len(budgeted_included) <= BUDGET,
        "must_include_retained": must_include_retained,
        "must_include_retention_rate": len(must_include_retained) / len(MUST_INCLUDE_IDS),
        "acceptable_optional_retained": optional_retained,
        "acceptable_optional_retention_rate": len(optional_retained) / len(ACCEPTABLE_OPTIONAL_IDS),
        "related_but_unnecessary_retained": rbu_retained,
        "related_but_unnecessary_retention_rate": len(rbu_retained) / len(RELATED_BUT_UNNECESSARY_IDS),
        "kn101_selected_post_budget": kn101_selected,
        "recall": result["recall"],
        "precision": result["precision"],
        "score": result["objective_score"],
        "verdict": result["verdict"],
        "gate_pass": result["gate_pass"],
        "required_missing": result["missing_required"],
        "forbidden_selected": result["leaked_forbidden"],
        "raw_decisions": [d.to_dict() for d in decisions],
    }


def _test_split_eval(provider: JevProvider, candidate_dict: dict) -> dict:
    """Held-out per-candidate classification check (Brier-complement mean),
    on the 5-example test split only -- never used during optimization."""
    adapter = JevGepaAdapter(provider=provider)
    test_examples = load_split("test")
    eval_batch = adapter.evaluate(test_examples, candidate_dict, capture_traces=True)
    return {
        "n_test_examples": len(test_examples),
        "mean_score": statistics.fmean(eval_batch.scores),
        "per_example": eval_batch.trajectories,
    }


def run_gepa_optimization(reflection_lm: str, max_metric_calls: int):
    """Phase 1: gepa.optimize() against the train/val split. Live -- makes
    real JEV calls (train/val evaluation) and real reflection-LM calls."""
    import gepa  # imported here, not at module level, so this file stays

    adapter = JevGepaAdapter(provider=JevProvider())
    seed = seed_candidate_from_bc_0101()
    trainset = load_split("train")
    valset = load_split("val")

    result = gepa.optimize(
        seed_candidate=seed,
        trainset=trainset,
        valset=valset,
        adapter=adapter,
        reflection_lm=reflection_lm,
        max_metric_calls=max_metric_calls,
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--live", action="store_true", help="Required for any live call (JEV or GEPA reflection).")
    parser.add_argument("--reflection-lm", default="openai/gpt-5-mini",
                         help="Model string passed to gepa.optimize(reflection_lm=...). Its provider's "
                              "credential (e.g. OPENAI_API_KEY) must be set for --live runs.")
    parser.add_argument("--max-metric-calls", type=int, default=60,
                         help="GEPA's own budget on evaluate() calls during optimization -- kept small for a pilot.")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.live:
        if not os.environ.get(OPENROUTER_API_KEY_ENV_VAR):
            print(f"Refusing --live: {OPENROUTER_API_KEY_ENV_VAR} is not set (needed for JEV calls).",
                  file=sys.stderr)
            return 2
        try:
            import gepa  # noqa: F401
        except ImportError:
            print("Refusing --live: the 'gepa' package is not importable in this environment "
                  "(requires Python >=3.10; pip install gepa). See X_GEPA_1_PROPOSAL.md.",
                  file=sys.stderr)
            return 2
    else:
        print("Refusing to run without --live -- this experiment makes real JEV and GEPA "
              "reflection-LM calls, both billed, and requires OPENROUTER_API_KEY plus the "
              "reflection model's own credential. Nothing was called.", file=sys.stderr)
        return 2

    provider = JevProvider()
    try:
        provider._require_key()
    except ProviderNotConfigured as exc:
        print(f"JEV not configured: {exc}", file=sys.stderr)
        return 3

    base_case = load_bc_0101_case()
    full_case = {**build_experiment_3_case(base_case), "id": EXPERIMENT_ID}
    candidates = load_experiment_3_candidates()

    seed_dict = seed_candidate_from_bc_0101()
    seed_case = case_from_candidate_dict(seed_dict, id_suffix="seed")

    print("Phase 1/2: baseline (seed = BC-0101 criterion) budget run...", file=sys.stderr)
    baseline_result = _budget_run(provider, seed_case, candidates)
    baseline_test = _test_split_eval(provider, seed_dict)

    print(f"Phase 1/2 (real): GEPA optimization (max_metric_calls={args.max_metric_calls}, "
          f"reflection_lm={args.reflection_lm!r})...", file=sys.stderr)
    gepa_result = run_gepa_optimization(args.reflection_lm, args.max_metric_calls)
    optimized_dict = gepa_result.best_candidate

    print("Phase 2/2: optimized-criterion budget run...", file=sys.stderr)
    optimized_case = case_from_candidate_dict(optimized_dict, id_suffix="optimized")
    optimized_result = _budget_run(provider, optimized_case, candidates)
    optimized_test = _test_split_eval(provider, optimized_dict)

    out = {
        "experiment_id": EXPERIMENT_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reflection_lm": args.reflection_lm,
        "max_metric_calls": args.max_metric_calls,
        "seed_candidate": seed_dict,
        "optimized_candidate": optimized_dict,
        "baseline": baseline_result,
        "baseline_test_split": baseline_test,
        "optimized": optimized_result,
        "optimized_test_split": optimized_test,
    }

    out_path = args.out
    if out_path is None:
        RESULTS_DIR.mkdir(exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"xgepa1_jev_{ts}.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Wrote {out_path}", file=sys.stderr)
    print(json.dumps({
        "baseline_score": baseline_result["score"],
        "optimized_score": optimized_result["score"],
        "baseline_must_include_retention": baseline_result["must_include_retention_rate"],
        "optimized_must_include_retention": optimized_result["must_include_retention_rate"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
