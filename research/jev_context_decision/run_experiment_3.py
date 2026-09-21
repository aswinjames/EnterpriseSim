#!/usr/bin/env python3
"""Runs Experiment 3 (X-RICH-1) for one provider, N times.

Experiment 3 tests H3: as enterprise context grows in volume and
interconnectedness, does context selection still track task-specific
necessity, or does it admit artifacts merely because they are related? Same
task (CHK-1421), same BC-0101 decision criterion (byte-for-byte, reused
directly from ``providers.base.BC_0101`` -- not copied, not re-worded), same
TaskScope, same scorer. Only the candidate pool changes: 15 candidates
instead of 7 (see ``experiment_3_candidates.py``).

This is a SEPARATE file from ``run_experiment.py`` specifically so that
BC-0101/BC-0102's runner, candidate loading, and CLI behavior are provably
untouched by Experiment 3's existence -- nothing in this file is imported by
``run_experiment.py`` or vice versa, and this file never calls
``load_bc_0101_candidates()``/``load_bc_0101_case()`` for anything other than
reading the frozen task fields to build the Experiment 3 case (see
``experiment_3_candidates.build_experiment_3_case``, which reads a fresh dict
and never writes back to the source file).

KN-101 is retained in the full 15-candidate pool and every provider decision
about it is fully captured, but it is excluded from the score()'s
included/excluded context before scoring -- so it never affects recall,
precision, or the required-items gate. This is a context-filtering step done
here, in this file; ``scoring.py``/``score()`` itself is imported and called
completely unmodified. Likewise, RELATED_BUT_UNNECESSARY candidates are
absent from the Experiment 3 case's must_include/acceptable_optional/
must_exclude sets (exactly like KN-047's existing treatment), so their
inclusion/exclusion is captured and reported separately but never scored as
right or wrong by the frozen scorer.

Safety: this phase makes NO live API calls. Same double-gate as
run_experiment.py: a live provider requires BOTH --live AND
OPENAI_API_KEY/OPENROUTER_API_KEY set.

Usage:
    # Offline wiring check (no network, no key needed):
    python3 -m research.jev_context_decision.run_experiment_3 --provider mock --repeats 1

    # Live sanity/batch runs (NOT executed in this phase):
    OPENROUTER_API_KEY=... python3 -m research.jev_context_decision.run_experiment_3 --provider jev --repeats 5 --live
    OPENAI_API_KEY=...    python3 -m research.jev_context_decision.run_experiment_3 --provider gpt --repeats 5 --live
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
    CONTESTED_CANDIDATE_IDS,
    EXPERIMENT_ID,
    RELATED_BUT_UNNECESSARY_IDS,
    build_experiment_3_case,
    load_experiment_3_candidates,
)
from .providers import PROVIDERS, ProviderNotConfigured
from .providers.base import BC_0101
from .scoring import score as score_context

RESULTS_DIR = Path(__file__).resolve().parent / "results"
LIVE_PROVIDERS = {"jev", "gpt"}

#: Experiment 3 uses BC-0101's criterion byte-for-byte -- imported directly,
#: never copied or re-worded. This is not a configurable choice in this
#: runner: Experiment 3 is specifically designed to hold the criterion
#: constant while the candidate pool changes.
CRITERION = BC_0101


def _build_scored_context(decisions: list[ContextDecision], task_ref: str, exclude_ids: set[str]) -> dict:
    """Build the context object passed to score(), omitting ``exclude_ids``.

    Mirrors decision.py::AggregatedContext.to_context_object()'s shape
    exactly, but skips any decision whose candidate_id is in ``exclude_ids``
    (i.e. CONTESTED_CANDIDATE_IDS) -- so those candidates never reach the
    scorer's included/excluded sets and cannot affect recall, precision, or
    the required-items gate, while still being fully present in ``decisions``
    for separate reporting.
    """
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
        # Full 15-candidate selection, unfiltered -- transparency over
        # everything the provider actually decided.
        "selected_full": {"included": full_included, "excluded": full_excluded},
        # The context actually passed to score() -- CONTESTED candidates
        # (KN-101) removed before scoring, per experiment design.
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
    kn101_selected_count = sum(
        1 for r in repeats_result if "KN-101" in r["contested"]["selected_ids"]
    )
    rbu_rates = [r["related_but_unnecessary"]["inclusion_rate"] for r in repeats_result
                 if r["related_but_unnecessary"]["inclusion_rate"] is not None]
    return {
        "n_repeats": n,
        "score_mean": round(statistics.fmean(scores), 4),
        "score_stddev": round(statistics.pstdev(scores), 4) if n > 1 else 0.0,
        "verdicts": [r["verdict"] for r in repeats_result],
        "gate_pass_all": all(r["gate_pass"] for r in repeats_result),
        # Observational only -- NOT a correctness metric. KN-101 is contested;
        # this reports what the provider did, not whether it was "right."
        "kn101_selection_count": kn101_selected_count,
        "kn101_selection_rate": (kn101_selected_count / n) if n else None,
        "related_but_unnecessary_inclusion_rate_mean": (
            round(statistics.fmean(rbu_rates), 4) if rbu_rates else None
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--live", action="store_true", help="Required to actually call jev/gpt; mock ignores this.")
    parser.add_argument("--out", type=Path, default=None, help="Output JSON path; default: results/experiment3_<provider>_<ts>.json")
    args = parser.parse_args(argv)

    if args.provider in LIVE_PROVIDERS and not args.live:
        print(
            f"Refusing to run provider={args.provider!r} without --live. "
            "This phase makes no live API calls by design.",
            file=sys.stderr,
        )
        return 2

    provider_cls = PROVIDERS[args.provider]
    provider = provider_cls()

    base_case = load_bc_0101_case()
    case = build_experiment_3_case(base_case)
    candidates = load_experiment_3_candidates()

    out_path = args.out
    if out_path is None:
        RESULTS_DIR.mkdir(exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"experiment3_{args.provider}_{ts}.json"

    def write_partial(repeats_result: list[dict], complete: bool) -> None:
        output = {
            "experiment_id": EXPERIMENT_ID,
            "provider": args.provider,
            "criterion_id": CRITERION.id,
            "candidate_count": len(candidates),
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
