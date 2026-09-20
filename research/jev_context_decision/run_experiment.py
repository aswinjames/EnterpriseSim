#!/usr/bin/env python3
"""Runs the BC-0101 context-decision experiment for one provider, N times.

For each repeat: each of the seven BC-0101 candidates is judged independently
(INCLUDE/EXCLUDE) by the chosen provider, the seven decisions are aggregated into
a selected context set, and that set is scored with the repo's own
``examples/quickstart/run_quickstart.py::score()`` (unmodified, no invented
composition-quality term). Nothing here writes to or alters the benchmark case or
its ground truth -- both are read-only inputs.

Both providers go through OpenRouter as the one gateway (pinned
``typesafe/jev-1.13`` via the alpha Decisions API for Jev; pinned
``openai/gpt-5-mini`` via chat completions for GPT) -- see
``providers/jev_provider.py`` and ``providers/gpt_provider.py``.

Safety: this phase makes NO live API calls. A live provider (jev, gpt) requires
BOTH the ``--live`` flag AND ``OPENROUTER_API_KEY`` being set (the same key for
both); omitting ``--live`` always refuses, even if the key happens to be set, so
this script cannot accidentally spend money.

Usage:
    # Offline wiring check (default; no network, no key needed):
    python3 -m research.jev_context_decision.run_experiment --provider mock --repeats 1

    # First live Jev sanity test (single repeat), once OPENROUTER_API_KEY is exported:
    OPENROUTER_API_KEY=... python3 -m research.jev_context_decision.run_experiment \\
        --provider jev --repeats 1 --live

    # First live GPT sanity test (single repeat), once OPENROUTER_API_KEY is exported:
    OPENROUTER_API_KEY=... python3 -m research.jev_context_decision.run_experiment \\
        --provider gpt --repeats 1 --live

    # Full x5 runs, once sanity tests pass:
    OPENROUTER_API_KEY=... python3 -m research.jev_context_decision.run_experiment --provider jev --repeats 5 --live
    OPENROUTER_API_KEY=... python3 -m research.jev_context_decision.run_experiment --provider gpt --repeats 5 --live
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

from .candidates import load_bc_0101_candidates, load_bc_0101_case
from .decision import aggregate
from .providers import PROVIDERS, ProviderNotConfigured
from .scoring import score as score_context

RESULTS_DIR = Path(__file__).resolve().parent / "results"
LIVE_PROVIDERS = {"jev", "gpt"}


def run_once(provider, case: dict, candidates: list) -> dict:
    decisions = provider.decide_all(candidates)
    aggregated = aggregate(decisions)
    context = aggregated.to_context_object(task_ref=case["task_ref"])
    result = score_context(case, context)

    gt = case["ground_truth"]
    must_include = set(gt["must_include"])
    included = set(aggregated.included)

    confidences = [d.confidence for d in decisions if d.confidence is not None]
    input_tokens = [d.input_tokens for d in decisions if d.input_tokens is not None]
    output_tokens = [d.output_tokens for d in decisions if d.output_tokens is not None]
    costs = [d.cost_usd for d in decisions if d.cost_usd is not None]
    models = sorted({d.model for d in decisions})
    prompt_versions = sorted({d.prompt_version for d in decisions})

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider.name,
        "case_id": case["id"],
        "model": models[0] if len(models) == 1 else models,
        "prompt_version": prompt_versions[0] if len(prompt_versions) == 1 else prompt_versions,
        "selected": {"included": sorted(aggregated.included), "excluded": sorted(aggregated.excluded)},
        "required_present": sorted(must_include & included),
        "required_missing": result["missing_required"],
        "forbidden_selected": result["leaked_forbidden"],
        "recall": result["recall"],
        "precision": result["precision"],
        "score": result["objective_score"],
        "verdict": result["verdict"],
        "gate_pass": result["gate_pass"],
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
    return {
        "n_repeats": len(repeats_result),
        "score_mean": round(statistics.fmean(scores), 4),
        "score_stddev": round(statistics.pstdev(scores), 4) if len(scores) > 1 else 0.0,
        "verdicts": [r["verdict"] for r in repeats_result],
        "gate_pass_all": all(r["gate_pass"] for r in repeats_result),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--live", action="store_true", help="Required to actually call jev/gpt; mock ignores this.")
    parser.add_argument("--out", type=Path, default=None, help="Output JSON path; default: results/<provider>_<ts>.json")
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

    case = load_bc_0101_case()
    candidates = load_bc_0101_candidates()

    out_path = args.out
    if out_path is None:
        RESULTS_DIR.mkdir(exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"{args.provider}_{ts}.json"

    def write_partial(repeats_result: list[dict], complete: bool) -> None:
        # Written after every repeat (not just at the end) so a later failure in
        # a long, multi-repeat live batch cannot erase already-completed,
        # already-paid-for decisions -- each repeat's full raw_decisions are
        # preserved as soon as that repeat finishes, regardless of what happens
        # to any repeat after it.
        output = {
            "provider": args.provider,
            "case_id": case["id"],
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
        print(f"  repeat {i + 1}/{args.repeats}: score={repeats_result[-1]['score']} verdict={repeats_result[-1]['verdict']}")

    print(f"Wrote {len(repeats_result)} repeat(s) for provider={args.provider!r} to {out_path}")
    print(json.dumps(summarize(repeats_result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
