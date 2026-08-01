#!/usr/bin/env python3
"""
EnterpriseSim — 10-minute quickstart.

Runs a tiny reference Worker against a real benchmark case (BC-0101, suite BENCH-01:
context assembly for guest checkout CHK-1421) and prints an objective-first score —
using the *actual* scoring recipe declared on the case.

No dependencies. No API key. Fully deterministic — the stub Worker uses a fixed
relevance heuristic, so the same score prints every run (that's the point: a
reproducible baseline you can beat).

Usage:
    python examples/quickstart/run_quickstart.py

What this demonstrates:
    - loading a frozen BenchmarkCase from the repo
    - a Worker producing a ContextObject (included / excluded working set)
    - scoring it with the case's own objective metrics (recall, precision, gate)
    - a per-case verdict against the case's pass/partial thresholds

The Worker here is deliberately dumb. Replace `StubContextWorker.assemble()` with
your own model-backed logic (see the SDK contracts in ../../sdk/) and re-run to see
whether your agent beats this baseline.
"""

from __future__ import annotations

import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CASE_PATH = REPO_ROOT / "benchmarks" / "examples" / "benchmark_case.example.json"

# A tiny synthetic "corpus catalog": what each candidate item is about. In the real
# repo these are full KN-###/EXP-### objects; here we only need a topic tag so the
# stub Worker can do keyword relevance. Kept local so the quickstart has zero deps.
ITEM_TOPICS = {
    "KN-045": "checkout order placement domain rules",
    "KN-052": "guest checkout session payment",
    "KN-063": "checkout pricing tax",
    "KN-047": "legacy monolith checkout",
    "KN-101": "marketplace seller onboarding",   # out-of-scope distractor
    "EXP-090": "guest cart must not create loyalty account checkout",
    "EXP-055": "checkout retry idempotency",
}


class StubContextWorker:
    """A baseline Worker: keyword-overlap relevance against the task, with a budget cap.

    Deliberately simple. It reads the trigger/task words and keeps candidate corpus
    items whose topic overlaps — a naive but honest baseline for context assembly.
    """

    def __init__(self, max_items: int = 4) -> None:
        self.max_items = max_items

    def assemble(self, case: dict) -> dict:
        task_text = f"{case['title']} {case['description']}".lower()
        task_words = {w.strip('.,()') for w in task_text.split() if len(w) > 3}

        candidates = (
            case["inputs"]["available_corpus"]["knowledge"]
            + case["inputs"]["available_corpus"]["experience"]
        )

        scored = []
        for item in candidates:
            topic_words = set(ITEM_TOPICS.get(item, "").split())
            overlap = len(task_words & topic_words)
            scored.append((item, overlap))

        # Keep the most relevant items within the (tiny) budget.
        scored.sort(key=lambda x: (-x[1], x[0]))
        included = [item for item, ov in scored if ov > 0][: self.max_items]
        excluded = [item for item, _ in scored if item not in included]

        # A minimal ContextObject (see sdk/objects.py ContextObject Protocol).
        return {
            "id": "CTX-QS01",
            "schema_version": case["schema_version"],
            "task": {"ref": case["task_ref"]},
            "included": [{"source": i, "kind": "corpus", "reason": "keyword-relevant"} for i in included],
            "excluded": [{"source": i, "kind": "corpus", "reason": "low relevance / budget"} for i in excluded],
        }


def score(case: dict, context: dict) -> dict:
    """Score a ContextObject with the case's own objective metrics (objective_first)."""
    gt = case["ground_truth"]
    must_include = set(gt["must_include"])
    must_exclude = set(gt["must_exclude"])
    optional = set(gt["expected"].get("acceptable_optional", []))
    relevant = must_include | optional            # the ground-truth-relevant set

    included = {p["source"] for p in context["included"]}

    # Hard gate: all required present AND all forbidden absent.
    gate_pass = must_include.issubset(included) and not (must_exclude & included)

    # retrieval_recall = fraction of relevant items retrieved
    recall = len(included & relevant) / len(relevant) if relevant else 1.0
    # retrieval_precision = fraction of retrieved items that are relevant
    precision = len(included & relevant) / len(included) if included else 0.0

    weights = {m["name"]: m["weight"] for m in case["scoring"]["metrics"]}
    # Gated weighted sum: if the hard gate fails, the objective score collapses.
    objective = (
        weights["required_items_present"] * (1.0 if gate_pass else 0.0)
        + weights["retrieval_recall"] * recall
        + weights["retrieval_precision"] * precision
    )
    # composition_quality is a model-assisted rubric item — out of scope for a
    # zero-dep stub, so we simply omit its weight (report objective-only).

    total = objective if gate_pass else min(objective, 0.4)

    th = case["thresholds"]
    verdict = "pass" if total >= th["pass"] else "partial" if total >= th["partial"] else "fail"

    return {
        "gate_pass": gate_pass,
        "recall": round(recall, 3),
        "precision": round(precision, 3),
        "objective_score": round(total, 3),
        "verdict": verdict,
        "included": sorted(included),
        "missing_required": sorted(must_include - included),
        "leaked_forbidden": sorted(must_exclude & included),
    }


def main() -> None:
    case = json.loads(CASE_PATH.read_text())
    worker = StubContextWorker()
    context = worker.assemble(case)
    result = score(case, context)

    print("=" * 66)
    print(f"EnterpriseSim quickstart — {case['id']} ({case['suite']})")
    print(f"  {case['title']}")
    print("=" * 66)
    print(f"Worker included : {result['included']}")
    if result["missing_required"]:
        print(f"  MISSING required: {result['missing_required']}")
    if result["leaked_forbidden"]:
        print(f"  LEAKED forbidden: {result['leaked_forbidden']}")
    print("-" * 66)
    print(f"  hard gate        : {'PASS' if result['gate_pass'] else 'FAIL'}")
    print(f"  retrieval recall : {result['recall']}")
    print(f"  retrieval precis.: {result['precision']}")
    print(f"  objective score  : {result['objective_score']}  "
          f"(pass ≥ {case['thresholds']['pass']}, partial ≥ {case['thresholds']['partial']})")
    print(f"  VERDICT          : {result['verdict'].upper()}")
    print("=" * 66)
    print("This is a baseline. Beat it: swap StubContextWorker.assemble() for your")
    print("own model-backed Worker (see ../../sdk/) and re-run.")


if __name__ == "__main__":
    main()
