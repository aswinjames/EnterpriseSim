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

CHECKPOINTING / CRASH RESILIENCE
---------------------------------
A prior live attempt lost ~50 minutes of real GEPA optimization progress to
a single transient OpenRouter socket timeout, because nothing was persisted
until the very end of the script. This runner now persists incrementally:

- A **configuration manifest** (``xgepa1_<run_id>_manifest.json``) captures
  the immutable configuration this run depends on: experiment id, installed
  ``gepa`` version, the JEV model string, the train/val candidate-id split,
  the full candidate-pool id list, the criterion id, ``max_metric_calls``,
  the reflection-LM string, and the optimized component keys. ``run_id`` is
  a deterministic hash of this manifest, so the *same* configuration always
  maps to the *same* checkpoint files -- resuming needs no extra bookkeeping,
  and a **different** configuration never collides with or silently resumes
  a mismatched prior run. On every invocation, the freshly computed manifest
  is compared field-by-field against any existing one; any difference is a
  hard error (see ``ConfigMismatchError``), not a silent resume.

- **GEPA's own native ``run_dir`` checkpointing**
  (``xgepa1_<run_id>_gepa_state/``) persists optimization state after every
  iteration; GEPA itself resumes from it automatically on the next
  ``gepa.optimize()`` call with the same ``run_dir``, re-running nothing
  already completed.

- A **JSONL iteration log** (``xgepa1_<run_id>_iterations.jsonl``), written
  via a small ``GEPACallback`` (``_CheckpointCallback``) using GEPA's own
  callback hooks (``on_candidate_accepted``/``on_candidate_rejected``/
  ``on_proposal_end``/``on_optimization_end``) -- one record per iteration,
  independent of GEPA's own internal format, for easy inspection.

- A **Phase-2 progress file** (``xgepa1_<run_id>.json``, the actual output
  file) is rewritten after every phase-2 step (the GEPA-complete marker, the
  baseline budget run, the baseline test-split eval, the optimized budget
  run, the optimized test-split eval), tracked via ``completed_steps``.
  ``"complete": true`` is written once, only after every step has completed
  -- never speculatively.

- Phase 2 never starts unless Phase 1's GEPA-complete marker has been
  written **and read back successfully** from the progress file first.

- Every live ``provider.decide()`` call (inside the adapter's ``evaluate()``
  and in this file's own budget-run/test-split-eval loops) goes through
  ``gepa_jev_adapter.decide_with_retry()``: up to 3 attempts, exponential
  backoff, transient network failures only
  (``TimeoutError``/``socket.timeout``/``urllib.error.URLError``) -- never
  retrying a real application/provider error, and never altering the
  request between attempts.

- On an unrecovered failure (retries exhausted), the process exits non-zero,
  prints exactly which step it reached, and leaves every checkpoint file
  exactly as last written -- ``complete`` stays ``false``, nothing is
  fabricated as done.

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
import hashlib
import importlib.metadata
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    COMPONENT_KEYS,
    JevGepaAdapter,
    case_from_candidate_dict,
    decide_with_retry,
    seed_candidate_from_bc_0101,
)
from .providers import ProviderNotConfigured
from .providers.base import BC_0101
from .providers.jev_provider import DEFAULT_MODEL as JEV_DEFAULT_MODEL
from .providers.jev_provider import JevProvider
from .providers.openrouter import API_KEY_ENV_VAR as OPENROUTER_API_KEY_ENV_VAR
from .run_experiment_x_rich_3 import BUDGET, _build_scored_context, apply_budget
from .scoring import score as score_context

RESULTS_DIR = Path(__file__).resolve().parent / "results"
EXPERIMENT_ID = "X-GEPA-1"

#: Ordered phase-2 steps. A step is "complete" once its name is in the
#: progress file's completed_steps list AND, for the two eval steps, its
#: result payload is present. Order matters: each step's code assumes every
#: earlier step already ran (either this invocation or a prior one).
PHASE1_STEP = "phase1_gepa_optimization"
PHASE2_STEPS = ("baseline_budget_run", "baseline_test_split", "optimized_budget_run", "optimized_test_split")
ALL_STEPS = (PHASE1_STEP,) + PHASE2_STEPS


class ConfigMismatchError(RuntimeError):
    """Raised when a checkpoint's stored configuration manifest doesn't match
    the configuration this invocation is about to run with. Never silently
    resumed -- the caller must fix the mismatch or start a fresh run_id."""


# --------------------------------------------------------------------------
# Configuration manifest -- what must match, byte-for-byte, to resume.
# --------------------------------------------------------------------------

def _gepa_version() -> str:
    try:
        return importlib.metadata.version("gepa")
    except importlib.metadata.PackageNotFoundError:  # pragma: no cover - gepa always installed for --live
        return "unknown"


def build_config_manifest(reflection_lm: str, max_metric_calls: int) -> dict[str, Any]:
    """The immutable configuration this run depends on. Anything not listed
    here (wall-clock timestamps, latency, etc.) is free to differ across
    resumes; anything listed here must match exactly or resume is refused.
    """
    train_ids = sorted(d.candidate_id for d in load_split("train"))
    val_ids = sorted(d.candidate_id for d in load_split("val"))
    pool_ids = sorted(c.id for c in load_experiment_3_candidates())
    return {
        "experiment_id": EXPERIMENT_ID,
        "gepa_version": _gepa_version(),
        "jev_model": JEV_DEFAULT_MODEL,
        "train_ids": train_ids,
        "val_ids": val_ids,
        "candidate_pool_ids": pool_ids,
        "criterion_id": BC_0101.id,
        "max_metric_calls": max_metric_calls,
        "reflection_lm": reflection_lm,
        "component_keys": sorted(COMPONENT_KEYS),
    }


def compute_run_id(manifest: dict[str, Any]) -> str:
    """Deterministic id from the manifest -- same configuration always maps
    to the same checkpoint files; a changed configuration always maps
    elsewhere, so it can never silently collide with/resume the wrong run."""
    canonical = json.dumps(manifest, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:12]


def validate_or_write_manifest(manifest_path: Path, manifest: dict[str, Any]) -> bool:
    """Returns True if this is a fresh run (manifest just written), False if
    resuming an existing, matching run. Raises ConfigMismatchError if a
    manifest already exists and differs from ``manifest`` in any field.
    """
    if not manifest_path.exists():
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
        # Read back to confirm the write actually landed before anyone
        # treats this manifest as authoritative.
        reloaded = json.loads(manifest_path.read_text())
        if reloaded != manifest:
            raise RuntimeError(f"Manifest write at {manifest_path} did not read back correctly.")
        return True

    existing = json.loads(manifest_path.read_text())
    if existing != manifest:
        diffs = {
            key: {"checkpoint": existing.get(key), "current": manifest.get(key)}
            for key in sorted(set(existing) | set(manifest))
            if existing.get(key) != manifest.get(key)
        }
        raise ConfigMismatchError(
            f"Checkpoint at {manifest_path} was created with a different configuration. "
            f"Refusing to resume. Differing fields: {json.dumps(diffs, indent=2, sort_keys=True)}"
        )
    return False


# --------------------------------------------------------------------------
# Phase-2 progress file: read/update helpers.
# --------------------------------------------------------------------------

def _load_progress(progress_path: Path) -> dict[str, Any]:
    if progress_path.exists():
        return json.loads(progress_path.read_text())
    return {"experiment_id": EXPERIMENT_ID, "completed_steps": [], "complete": False}


def _save_progress(progress_path: Path, progress: dict[str, Any]) -> None:
    progress_path.write_text(json.dumps(progress, indent=2))
    # Read back before returning -- callers gate subsequent phases on this
    # write having actually landed, not merely having been attempted.
    reloaded = json.loads(progress_path.read_text())
    if reloaded.get("completed_steps") != progress.get("completed_steps"):
        raise RuntimeError(f"Progress write at {progress_path} did not read back correctly.")


def _mark_step_complete(progress_path: Path, step: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    progress = _load_progress(progress_path)
    if step not in progress["completed_steps"]:
        progress["completed_steps"].append(step)
    if payload is not None:
        progress[step] = payload
    progress["complete"] = set(ALL_STEPS).issubset(progress["completed_steps"])
    _save_progress(progress_path, progress)
    return progress


# --------------------------------------------------------------------------
# GEPA callback: our own supplementary iteration log (JSONL), independent of
# GEPA's own run_dir state. Implements only the hooks it needs -- GEPACallback
# is a Protocol and GEPA's dispatcher skips any method a callback lacks.
# --------------------------------------------------------------------------

class _CheckpointCallback:
    """Appends one JSON record per notable event to a JSONL log. Never
    raises -- GEPA's dispatcher already isolates callback failures, but this
    also guards defensively against any event-field assumption being wrong,
    so a logging hiccup can never take down a real optimization run."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path

    def _append(self, record: dict[str, Any]) -> None:
        record["timestamp"] = datetime.now(timezone.utc).isoformat()
        try:
            with self.log_path.open("a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as exc:  # pragma: no cover - defensive only
            print(f"[_CheckpointCallback] failed to write log record: {exc}", file=sys.stderr)

    def on_optimization_start(self, event: Any) -> None:
        self._append({
            "event": "optimization_start",
            "trainset_size": event.get("trainset_size"),
            "valset_size": event.get("valset_size"),
        })

    def on_proposal_end(self, event: Any) -> None:
        self._append({
            "event": "proposal_end",
            "iteration": event.get("iteration"),
            "new_instructions": event.get("new_instructions"),
            "raw_lm_outputs": event.get("raw_lm_outputs"),
        })

    def on_candidate_accepted(self, event: Any) -> None:
        self._append({
            "event": "candidate_accepted",
            "iteration": event.get("iteration"),
            "new_candidate_idx": event.get("new_candidate_idx"),
            "new_score": event.get("new_score"),
        })

    def on_candidate_rejected(self, event: Any) -> None:
        self._append({
            "event": "candidate_rejected",
            "iteration": event.get("iteration"),
            "old_score": event.get("old_score"),
        })

    def on_optimization_end(self, event: Any) -> None:
        self._append({
            "event": "optimization_end",
            "best_candidate_idx": event.get("best_candidate_idx"),
            "total_iterations": event.get("total_iterations"),
            "total_metric_calls": event.get("total_metric_calls"),
        })


# --------------------------------------------------------------------------
# The two phases.
# --------------------------------------------------------------------------

def _budget_run(provider: JevProvider, case, candidates: list) -> dict:
    """One full 15-candidate -> budget-5 -> score pass, for one DecisionCase.

    Identical mechanism to run_experiment_x_rich_3.run_once(), reusing
    apply_budget()/_build_scored_context()/score() unchanged; the only
    difference is which DecisionCase's text is used to ask JEV each
    candidate's question. Always Jev-only -- X-GEPA-1 optimizes JEV's
    policy, not GPT's, matching this experiment's scope. Every decide()
    call goes through decide_with_retry() for transient-failure resilience.
    """
    base_case = load_bc_0101_case()
    scoring_case = {**build_experiment_3_case(base_case), "id": EXPERIMENT_ID}

    decisions = [decide_with_retry(provider, c, case) for c in candidates]
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
    on the 5-example test split only -- never used during optimization.
    Uses the adapter's evaluate(), which already retries transient failures.
    """
    adapter = JevGepaAdapter(provider=provider)
    test_examples = load_split("test")
    eval_batch = adapter.evaluate(test_examples, candidate_dict, capture_traces=True)
    return {
        "n_test_examples": len(test_examples),
        "mean_score": statistics.fmean(eval_batch.scores),
        "per_example": eval_batch.trajectories,
    }


def run_gepa_optimization(reflection_lm: str, max_metric_calls: int, run_dir: Path, callback: _CheckpointCallback):
    """Phase 1: gepa.optimize() against the train/val split. Live -- makes
    real JEV calls (train/val evaluation) and real reflection-LM calls.

    ``run_dir`` is GEPA's own native checkpoint directory: if it already has
    state from a prior attempt, GEPA resumes from the last saved iteration
    instead of starting over. Every per-candidate JEV call the adapter makes
    is retried on transient failure (see gepa_jev_adapter.decide_with_retry);
    GEPA itself is not wrapped in a retry -- if optimize() still raises after
    the adapter's own retries are exhausted, that's a real, unrecovered
    failure and it propagates, leaving whatever run_dir/log state already
    exists on disk untouched for the next attempt to resume from.
    """
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
        run_dir=str(run_dir),
        callbacks=[callback],
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
    parser.add_argument("--out", type=Path, default=None,
                         help="Override the progress/output file path. Defaults to a deterministic "
                              "path derived from the run's configuration, so reruns with the same "
                              "configuration resume the same checkpoint automatically.")
    args = parser.parse_args(argv)

    if args.live:
        if not os.environ.get(OPENROUTER_API_KEY_ENV_VAR):
            print(f"Refusing --live: {OPENROUTER_API_KEY_ENV_VAR} is not set (needed for JEV calls).",
                  file=sys.stderr)
            return 2
        # 'gepa' is only actually needed if Phase 1 hasn't completed yet --
        # checked lazily, right before it would be used, not here. A resume
        # that only needs to finish Phase 2 must work in any environment with
        # JEV credentials, even one without gepa/Python>=3.10 installed.
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

    RESULTS_DIR.mkdir(exist_ok=True)
    manifest = build_config_manifest(args.reflection_lm, args.max_metric_calls)
    run_id = compute_run_id(manifest)
    manifest_path = RESULTS_DIR / f"xgepa1_{run_id}_manifest.json"
    gepa_run_dir = RESULTS_DIR / f"xgepa1_{run_id}_gepa_state"
    iteration_log_path = RESULTS_DIR / f"xgepa1_{run_id}_iterations.jsonl"
    progress_path = args.out or (RESULTS_DIR / f"xgepa1_{run_id}.json")

    try:
        is_fresh = validate_or_write_manifest(manifest_path, manifest)
    except ConfigMismatchError as exc:
        print(f"CONFIGURATION MISMATCH -- refusing to resume: {exc}", file=sys.stderr)
        return 4
    print(f"{'Fresh run' if is_fresh else 'Resuming'}: run_id={run_id}, manifest={manifest_path}", file=sys.stderr)

    progress = _load_progress(progress_path)
    completed = set(progress["completed_steps"])

    base_case = load_bc_0101_case()
    full_case = {**build_experiment_3_case(base_case), "id": EXPERIMENT_ID}
    candidates = load_experiment_3_candidates()
    seed_dict = seed_candidate_from_bc_0101()
    seed_case = case_from_candidate_dict(seed_dict, id_suffix="seed")

    # ---- Phase 1: GEPA optimization (gated: must persist before Phase 2) ----
    if PHASE1_STEP not in completed:
        try:
            import gepa  # noqa: F401
        except ImportError:
            print("Refusing to run Phase 1: the 'gepa' package is not importable in this "
                  "environment (requires Python >=3.10; pip install gepa). See "
                  "X_GEPA_1_PROPOSAL.md. If Phase 1 already completed in another environment, "
                  "make sure its checkpoint files are present here instead of retrying it.",
                  file=sys.stderr)
            return 2
        print("Phase 1/2 (real): GEPA optimization "
              f"(max_metric_calls={args.max_metric_calls}, reflection_lm={args.reflection_lm!r}, "
              f"run_dir={gepa_run_dir})...", file=sys.stderr)
        callback = _CheckpointCallback(iteration_log_path)
        try:
            gepa_result = run_gepa_optimization(args.reflection_lm, args.max_metric_calls, gepa_run_dir, callback)
        except Exception as exc:
            print(f"Phase 1 (GEPA optimization) failed, unrecovered: {exc}", file=sys.stderr)
            print(f"Nothing was lost beyond this attempt: GEPA's own state is checkpointed at "
                  f"{gepa_run_dir}; rerun the identical command to resume from there.", file=sys.stderr)
            return 5
        optimized_dict = gepa_result.best_candidate
        phase1_payload = {
            "optimized_candidate": optimized_dict,
            "val_aggregate_scores": list(gepa_result.val_aggregate_scores),
            "best_idx": gepa_result.best_idx,
            "total_metric_calls": gepa_result.total_metric_calls,
        }
        progress = _mark_step_complete(progress_path, PHASE1_STEP, phase1_payload)
        completed = set(progress["completed_steps"])
        print(f"Phase 1 complete and checkpointed at {progress_path}.", file=sys.stderr)
    else:
        print(f"Phase 1 already complete (resumed from {progress_path}); skipping GEPA optimization.",
              file=sys.stderr)

    # Hard gate: never proceed to phase 2 unless phase 1's checkpoint is
    # confirmed present in a freshly reloaded copy of the progress file.
    progress = _load_progress(progress_path)
    if PHASE1_STEP not in progress["completed_steps"] or "optimized_candidate" not in progress.get(PHASE1_STEP, {}):
        print("Phase 1 checkpoint missing or incomplete after supposedly completing -- refusing "
              "to start Phase 2.", file=sys.stderr)
        return 6
    optimized_dict = progress[PHASE1_STEP]["optimized_candidate"]
    optimized_case = case_from_candidate_dict(optimized_dict, id_suffix="optimized")

    # ---- Phase 2: downstream comparison, one step at a time, persisted after each ----
    print("Phase 2/2: downstream budget comparison...", file=sys.stderr)

    if "baseline_budget_run" not in completed:
        baseline_result = _budget_run(provider, seed_case, candidates)
        progress = _mark_step_complete(progress_path, "baseline_budget_run", baseline_result)
        completed = set(progress["completed_steps"])
    else:
        baseline_result = progress["baseline_budget_run"]
        print("baseline_budget_run already complete; skipping.", file=sys.stderr)

    if "baseline_test_split" not in completed:
        baseline_test = _test_split_eval(provider, seed_dict)
        progress = _mark_step_complete(progress_path, "baseline_test_split", baseline_test)
        completed = set(progress["completed_steps"])
    else:
        baseline_test = progress["baseline_test_split"]
        print("baseline_test_split already complete; skipping.", file=sys.stderr)

    if "optimized_budget_run" not in completed:
        optimized_result = _budget_run(provider, optimized_case, candidates)
        progress = _mark_step_complete(progress_path, "optimized_budget_run", optimized_result)
        completed = set(progress["completed_steps"])
    else:
        optimized_result = progress["optimized_budget_run"]
        print("optimized_budget_run already complete; skipping.", file=sys.stderr)

    if "optimized_test_split" not in completed:
        optimized_test = _test_split_eval(provider, optimized_dict)
        progress = _mark_step_complete(progress_path, "optimized_test_split", optimized_test)
        completed = set(progress["completed_steps"])
    else:
        optimized_test = progress["optimized_test_split"]
        print("optimized_test_split already complete; skipping.", file=sys.stderr)

    # Final metadata pass -- does not gate completeness (that's ALL_STEPS
    # already being a subset of completed_steps, set by _mark_step_complete).
    progress["experiment_id"] = EXPERIMENT_ID
    progress["run_id"] = run_id
    progress["reflection_lm"] = args.reflection_lm
    progress["max_metric_calls"] = args.max_metric_calls
    progress["seed_candidate"] = seed_dict
    progress["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_progress(progress_path, progress)

    print(f"Wrote {progress_path} (complete={progress['complete']})", file=sys.stderr)
    print(json.dumps({
        "complete": progress["complete"],
        "baseline_score": baseline_result["score"],
        "optimized_score": optimized_result["score"],
        "baseline_must_include_retention": baseline_result["must_include_retention_rate"],
        "optimized_must_include_retention": optimized_result["must_include_retention_rate"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
