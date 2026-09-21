#!/usr/bin/env python3
"""Runs X-RICH-3 (Context Budget) for one provider, N times.

Research question: "When the AI Worker has a hard limit on the number of
artifacts it can place into working context, can it prioritize
task-necessary information over merely related information?"

Control (identical to X-RICH-1): same 15 candidates, same order, same
bodies, same BC-0101 criterion object (imported by identity), same
TaskScope, same ground truth, same GPTProvider/JevProvider (the plain
X-RICH-1 providers -- NOT the enterprise-context variants from X-RICH-2),
same 5-repeat structure. Every provider call in this file is byte-identical
to an X-RICH-1 call: same prompt, same model, same parameters.

Treatment (the ONLY change): a hard budget of BUDGET=5 selected candidates,
enforced as a pure post-hoc aggregation step over the model's own
independent per-candidate decisions -- rank every "include" verdict by the
model's own confidence, keep the top BUDGET, demote the rest to "excluded"
for scoring/reporting. The model is never told about the budget, never asked
a different question, and never sees a different prompt. This isolates the
effect of forcing a cardinality constraint on top of unchanged, independent
per-candidate judgments -- it does not test whether the model can reason
about a budget itself.

KN-101 remains CONTESTED: it is included in the budget ranking like any
other candidate (so we can observe whether it survives budget pressure), but
is removed from the scored included/excluded sets before scoring, exactly as
in X-RICH-1 -- it never affects recall/precision/the gate.

Separate file from run_experiment_3.py / run_experiment_x_rich_2.py --
neither is imported by this file besides the frozen candidate/case
definitions, and neither is modified by this file's existence.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

from .candidates import load_bc_0101_case
from .decision import ContextDecision
from .experiment_3_candidates import (
    ACCEPTABLE_OPTIONAL_IDS,
    CONTESTED_CANDIDATE_IDS,
    MUST_INCLUDE_IDS,
    RELATED_BUT_UNNECESSARY_IDS,
    build_experiment_3_case,
    load_experiment_3_candidates,
)
from .providers import PROVIDERS, ProviderNotConfigured
from .providers.base import BC_0101
from .scoring import score as score_context

RESULTS_DIR = Path(__file__).resolve().parent / "results"
LIVE_PROVIDERS = {"jev", "gpt"}
EXPERIMENT_ID = "X-RICH-3"
CRITERION = BC_0101  # same criterion object as X-RICH-1, unchanged
BUDGET = 5


def apply_budget(decisions: list[ContextDecision], budget: int) -> tuple[list[str], list[str], list[str]]:
    """Pure: enforce the hard budget over the model's own unchanged verdicts.

    Ranks every candidate the model marked "include" by the model's own
    confidence (descending); keeps the top ``budget`` ids as the final
    included set; every other candidate (originally excluded, OR originally
    included but dropped for budget) becomes excluded. Returns
    (final_included_ids, final_excluded_ids, dropped_for_budget_ids).
    """
    included = [d for d in decisions if d.verdict == "include"]
    excluded_ids = {d.candidate_id for d in decisions if d.verdict == "exclude"}
    included_ranked = sorted(included, key=lambda d: (d.confidence if d.confidence is not None else 0.0), reverse=True)
    kept = included_ranked[:budget]
    dropped = included_ranked[budget:]
    final_included = sorted(d.candidate_id for d in kept)
    dropped_ids = sorted(d.candidate_id for d in dropped)
    final_excluded = sorted(excluded_ids | set(dropped_ids))
    return final_included, final_excluded, dropped_ids


def _build_scored_context(included_ids: list[str], excluded_ids: list[str], decisions: list[ContextDecision],
                           task_ref: str, exclude_ids: set[str]) -> dict:
    by_id = {d.candidate_id: d for d in decisions}
    def item(cid):
        d = by_id[cid]
        return {"source": cid, "kind": d.candidate_kind, "reason": d.rationale,
                "score": d.confidence if d.confidence is not None else 0.5}
    return {
        "task": {"ref": task_ref},
        "included": [item(cid) for cid in included_ids if cid not in exclude_ids],
        "excluded": [item(cid) for cid in excluded_ids if cid not in exclude_ids],
    }


def run_once(provider, case: dict, candidates: list) -> dict:
    decisions = provider.decide_all(candidates, case=CRITERION)

    raw_included = sorted(d.candidate_id for d in decisions if d.verdict == "include")
    budgeted_included, budgeted_excluded, dropped_for_budget = apply_budget(decisions, BUDGET)

    scored_context = _build_scored_context(
        budgeted_included, budgeted_excluded, decisions, case["task_ref"], exclude_ids=set(CONTESTED_CANDIDATE_IDS)
    )
    result = score_context(case, scored_context)

    must_include_retained = [c for c in MUST_INCLUDE_IDS if c in budgeted_included]
    optional_retained = [c for c in ACCEPTABLE_OPTIONAL_IDS if c in budgeted_included]
    rbu_retained = [c for c in RELATED_BUT_UNNECESSARY_IDS if c in budgeted_included]
    kn101_selected = any(cid in budgeted_included for cid in CONTESTED_CANDIDATE_IDS)

    confidences = [d.confidence for d in decisions if d.confidence is not None]
    input_tokens = [d.input_tokens for d in decisions if d.input_tokens is not None]
    output_tokens = [d.output_tokens for d in decisions if d.output_tokens is not None]
    costs = [d.cost_usd for d in decisions if d.cost_usd is not None]
    models = sorted({d.model for d in decisions})

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider.name,
        "experiment_id": EXPERIMENT_ID,
        "criterion_id": CRITERION.id,
        "budget": BUDGET,
        "model": models[0] if len(models) == 1 else models,
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
        "latency_ms": {"total": sum(d.latency_ms for d in decisions),
                        "per_candidate": {d.candidate_id: d.latency_ms for d in decisions}},
        "tokens": {"input_total": sum(input_tokens) if input_tokens else None,
                   "output_total": sum(output_tokens) if output_tokens else None},
        "cost_usd_total": sum(costs) if costs else None,
        "confidence": {"per_candidate": {d.candidate_id: d.confidence for d in decisions},
                       "mean": statistics.fmean(confidences) if confidences else None},
        "raw_decisions": [d.to_dict() for d in decisions],
    }


def summarize(repeats_result: list[dict]) -> dict:
    n = len(repeats_result)
    scores = [r["score"] for r in repeats_result]
    return {
        "n_repeats": n,
        "score_mean": round(statistics.fmean(scores), 4),
        "score_stddev": round(statistics.pstdev(scores), 4) if n > 1 else 0.0,
        "verdicts": [r["verdict"] for r in repeats_result],
        "gate_pass_all": all(r["gate_pass"] for r in repeats_result),
        "budget_respected_all": all(r["budget_respected"] for r in repeats_result),
        "must_include_retention_rate_mean": round(statistics.fmean(r["must_include_retention_rate"] for r in repeats_result), 4),
        "acceptable_optional_retention_rate_mean": round(statistics.fmean(r["acceptable_optional_retention_rate"] for r in repeats_result), 4),
        "related_but_unnecessary_retention_rate_mean": round(statistics.fmean(r["related_but_unnecessary_retention_rate"] for r in repeats_result), 4),
        "kn101_selection_count": sum(1 for r in repeats_result if r["kn101_selected_post_budget"]),
        "kn101_selection_rate": sum(1 for r in repeats_result if r["kn101_selected_post_budget"]) / n if n else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.provider in LIVE_PROVIDERS and not args.live:
        print(f"Refusing to run provider={args.provider!r} without --live.", file=sys.stderr)
        return 2

    provider = PROVIDERS[args.provider]()
    base_case = load_bc_0101_case()
    case = {**build_experiment_3_case(base_case), "id": EXPERIMENT_ID}
    candidates = load_experiment_3_candidates()

    out_path = args.out
    if out_path is None:
        RESULTS_DIR.mkdir(exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"xrich3_{args.provider}_{ts}.json"

    def write_partial(repeats_result, complete):
        out_path.write_text(json.dumps({
            "experiment_id": EXPERIMENT_ID, "provider": args.provider, "criterion_id": CRITERION.id,
            "budget": BUDGET, "candidate_count": len(candidates),
            "repeats": repeats_result, "summary": summarize(repeats_result) if repeats_result else None,
            "complete": complete,
        }, indent=2))

    repeats_result: list[dict] = []
    for i in range(args.repeats):
        try:
            repeats_result.append(run_once(provider, case, candidates))
        except ProviderNotConfigured as exc:
            print(f"Provider {args.provider!r} not configured: {exc}", file=sys.stderr)
            if repeats_result:
                write_partial(repeats_result, complete=False)
            return 3
        except Exception as exc:
            print(f"Repeat {i + 1}/{args.repeats} failed: {exc}", file=sys.stderr)
            write_partial(repeats_result, complete=False)
            raise
        write_partial(repeats_result, complete=(i + 1 == args.repeats))
        r = repeats_result[-1]
        print(f"  repeat {i + 1}/{args.repeats}: score={r['score']} verdict={r['verdict']} "
              f"selected={r['selected_count']} kn101={'in' if r['kn101_selected_post_budget'] else 'out'}")

    print(f"Wrote {len(repeats_result)} repeat(s) to {out_path}")
    print(json.dumps(summarize(repeats_result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
