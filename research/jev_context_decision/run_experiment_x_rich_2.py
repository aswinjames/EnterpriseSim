#!/usr/bin/env python3
"""Runs X-RICH-2 for one provider, N times.

X-RICH-2 tests H1: "Explicit enterprise application-dependency context will
change candidate selection when structural relationships are relevant to
determining task-specific necessity." The ONLY change relative to X-RICH-1 is
that the model additionally receives the complete, unfiltered enterprise
application registry (see ``enterprise_context.py``) -- same 15 candidates,
same order, same IDs/bodies/classifications, same BC-0101 criterion object
(imported by identity, not re-worded), same TaskScope, same scorer, same
provider model/token/reasoning configuration.

This is a separate file from ``run_experiment_3.py`` (X-RICH-1) specifically
so X-RICH-1's runner, candidates, and results are provably unaffected --
nothing here is imported by ``run_experiment_3.py`` and nothing there is
imported here except the frozen, unmodified candidate/case/criterion
definitions.

KN-101 remains CONTESTED and is excluded from the scored denominator exactly
as in X-RICH-1 (same filtering logic, same reasoning). RELATED_BUT_UNNECESSARY
candidates remain outside must_include/acceptable_optional/must_exclude,
tracked descriptively only.

Safety: NO live API calls without --live AND the relevant key set
(OPENROUTER_API_KEY for jev, OPENAI_API_KEY for gpt) -- same double-gate as
every other runner in this repo.
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
from .enterprise_context import load_application_registry
from .experiment_3_candidates import (
    CONTESTED_CANDIDATE_IDS,
    RELATED_BUT_UNNECESSARY_IDS,
    build_experiment_3_case,
    load_experiment_3_candidates,
)
from .providers import ProviderNotConfigured
from .providers.base import BC_0101
from .providers.enterprise_context_providers import (
    GPTProviderWithEnterpriseContext,
    JevProviderWithEnterpriseContext,
)
from .providers.mock_provider import MockProvider
from .scoring import score as score_context

RESULTS_DIR = Path(__file__).resolve().parent / "results"
LIVE_PROVIDERS = {"jev", "gpt"}

#: Local identifier for this treatment. Distinct from X-RICH-1's id so
#: results are never confused, even though the underlying case/candidates
#: are the frozen X-RICH-1 definitions reused unchanged.
EXPERIMENT_ID = "X-RICH-2"

#: Same criterion object as X-RICH-1 -- imported by identity, never re-worded.
CRITERION = BC_0101

PROVIDER_CLASSES = {
    "jev": JevProviderWithEnterpriseContext,
    "gpt": GPTProviderWithEnterpriseContext,
}


def _build_scored_context(decisions: list[ContextDecision], task_ref: str, exclude_ids: set[str]) -> dict:
    """Identical logic to run_experiment_3.py::_build_scored_context (KN-101
    excluded from the scored denominator regardless of its verdict)."""
    return {
        "task": {"ref": task_ref},
        "included": [
            {"source": d.candidate_id, "kind": d.candidate_kind, "reason": d.rationale,
             "score": d.confidence if d.confidence is not None else 0.5}
            for d in decisions if d.verdict == "include" and d.candidate_id not in exclude_ids
        ],
        "excluded": [
            {"source": d.candidate_id, "kind": d.candidate_kind, "reason": d.rationale,
             "score": d.confidence if d.confidence is not None else 0.5}
            for d in decisions if d.verdict == "exclude" and d.candidate_id not in exclude_ids
        ],
    }


def run_once(provider, case: dict, candidates: list) -> dict:
    decisions = provider.decide_all(candidates, case=CRITERION)

    full_included = sorted(d.candidate_id for d in decisions if d.verdict == "include")
    full_excluded = sorted(d.candidate_id for d in decisions if d.verdict == "exclude")

    scored_context = _build_scored_context(decisions, case["task_ref"], exclude_ids=set(CONTESTED_CANDIDATE_IDS))
    result = score_context(case, scored_context)

    contested = [d for d in decisions if d.candidate_id in CONTESTED_CANDIDATE_IDS]
    rbu = [d for d in decisions if d.candidate_id in RELATED_BUT_UNNECESSARY_IDS]
    rbu_selected = [d.candidate_id for d in rbu if d.verdict == "include"]

    confidences = [d.confidence for d in decisions if d.confidence is not None]
    input_tokens = [d.input_tokens for d in decisions if d.input_tokens is not None]
    output_tokens = [d.output_tokens for d in decisions if d.output_tokens is not None]
    costs = [d.cost_usd for d in decisions if d.cost_usd is not None]
    models = sorted({d.model for d in decisions})
    prompt_versions = sorted({d.prompt_version for d in decisions})

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider.name,
        "experiment_id": EXPERIMENT_ID,
        "criterion_id": CRITERION.id,
        "model": models[0] if len(models) == 1 else models,
        "prompt_version": prompt_versions[0] if len(prompt_versions) == 1 else prompt_versions,
        "selected_full": {"included": full_included, "excluded": full_excluded},
        "scored_selected": {
            "included": sorted(i["source"] for i in scored_context["included"]),
            "excluded": sorted(i["source"] for i in scored_context["excluded"]),
        },
        "required_present": [c for c in case["ground_truth"]["must_include"] if c in full_included],
        "required_missing": result["missing_required"],
        "forbidden_selected": result["leaked_forbidden"],
        "recall": result["recall"],
        "precision": result["precision"],
        "score": result["objective_score"],
        "verdict": result["verdict"],
        "gate_pass": result["gate_pass"],
        "contested": {
            "candidate_ids": list(CONTESTED_CANDIDATE_IDS),
            "selected_ids": [d.candidate_id for d in contested if d.verdict == "include"],
            "excluded_ids": [d.candidate_id for d in contested if d.verdict == "exclude"],
            "decisions": [d.to_dict() for d in contested],
        },
        "related_but_unnecessary": {
            "candidate_ids": list(RELATED_BUT_UNNECESSARY_IDS),
            "selected_ids": rbu_selected,
            "selected_count": len(rbu_selected),
            "total_count": len(RELATED_BUT_UNNECESSARY_IDS),
            "inclusion_rate": (len(rbu_selected) / len(RELATED_BUT_UNNECESSARY_IDS)) if RELATED_BUT_UNNECESSARY_IDS else None,
            "decisions": [d.to_dict() for d in rbu],
        },
        "latency_ms": {
            "total": sum(d.latency_ms for d in decisions),
            "per_candidate": {d.candidate_id: d.latency_ms for d in decisions},
        },
        "tokens": {
            "input_total": sum(input_tokens) if input_tokens else None,
            "output_total": sum(output_tokens) if output_tokens else None,
        },
        "cost_usd_total": sum(costs) if costs else None,
        "confidence": {
            "per_candidate": {d.candidate_id: d.confidence for d in decisions},
            "mean": statistics.fmean(confidences) if confidences else None,
        },
        "raw_decisions": [d.to_dict() for d in decisions],
    }


def summarize(repeats_result: list[dict]) -> dict:
    scores = [r["score"] for r in repeats_result]
    n = len(repeats_result)
    kn101_selected_count = sum(1 for r in repeats_result if "KN-101" in r["contested"]["selected_ids"])
    rbu_rates = [r["related_but_unnecessary"]["inclusion_rate"] for r in repeats_result
                 if r["related_but_unnecessary"]["inclusion_rate"] is not None]
    return {
        "n_repeats": n,
        "score_mean": round(statistics.fmean(scores), 4),
        "score_stddev": round(statistics.pstdev(scores), 4) if n > 1 else 0.0,
        "verdicts": [r["verdict"] for r in repeats_result],
        "gate_pass_all": all(r["gate_pass"] for r in repeats_result),
        "kn101_selection_count": kn101_selected_count,
        "kn101_selection_rate": (kn101_selected_count / n) if n else None,
        "related_but_unnecessary_inclusion_rate_mean": (
            round(statistics.fmean(rbu_rates), 4) if rbu_rates else None
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", choices=sorted(["mock", "jev", "gpt"]), required=True)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--live", action="store_true", help="Required to actually call jev/gpt; mock ignores this.")
    parser.add_argument("--out", type=Path, default=None, help="Output JSON path; default: results/xrich2_<provider>_<ts>.json")
    args = parser.parse_args(argv)

    if args.provider in LIVE_PROVIDERS and not args.live:
        print(
            f"Refusing to run provider={args.provider!r} without --live. "
            "This phase makes no live API calls by design.",
            file=sys.stderr,
        )
        return 2

    registry = load_application_registry()
    if args.provider == "mock":
        provider = MockProvider()
    else:
        provider = PROVIDER_CLASSES[args.provider](enterprise_registry=registry)

    base_case = load_bc_0101_case()
    # Reuse build_experiment_3_case() (frozen, unmodified) then relabel the id
    # locally so X-RICH-2 results are never confused with X-RICH-1's, without
    # touching experiment_3_candidates.py.
    case = {**build_experiment_3_case(base_case), "id": EXPERIMENT_ID}
    candidates = load_experiment_3_candidates()

    out_path = args.out
    if out_path is None:
        RESULTS_DIR.mkdir(exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"xrich2_{args.provider}_{ts}.json"

    def write_partial(repeats_result: list[dict], complete: bool) -> None:
        output = {
            "experiment_id": EXPERIMENT_ID,
            "provider": args.provider,
            "criterion_id": CRITERION.id,
            "candidate_count": len(candidates),
            "registry_app_count": len(registry),
            "repeats": repeats_result,
            "summary": summarize(repeats_result) if repeats_result else None,
            "complete": complete,
        }
        out_path.write_text(json.dumps(output, indent=2))

    repeats_result: list[dict] = []
    for i in range(args.repeats):
        try:
            repeats_result.append(run_once(provider, case, candidates))
        except ProviderNotConfigured as exc:
            print(f"Provider {args.provider!r} not configured: {exc}", file=sys.stderr)
            if repeats_result:
                write_partial(repeats_result, complete=False)
                print(f"Preserved {len(repeats_result)} completed repeat(s) at {out_path}", file=sys.stderr)
            return 3
        except Exception as exc:
            print(f"Repeat {i + 1}/{args.repeats} failed: {exc}", file=sys.stderr)
            write_partial(repeats_result, complete=False)
            print(f"Preserved {len(repeats_result)} completed repeat(s) at {out_path}", file=sys.stderr)
            raise
        write_partial(repeats_result, complete=(i + 1 == args.repeats))
        print(f"  repeat {i + 1}/{args.repeats}: score={repeats_result[-1]['score']} verdict={repeats_result[-1]['verdict']} "
              f"kn101={'include' if 'KN-101' in repeats_result[-1]['contested']['selected_ids'] else 'exclude'}")

    print(f"Wrote {len(repeats_result)} repeat(s) for provider={args.provider!r} to {out_path}")
    print(json.dumps(summarize(repeats_result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
