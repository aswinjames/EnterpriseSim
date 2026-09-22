"""Offline tests for X-GEPA-1's dataset module, GEPAAdapter, and the
checkpointing/retry/resume logic in run_experiment_x_gepa_1.py.

No network access, no gepa package required -- these exercise
experiment_x_gepa_1_candidates.py and gepa_jev_adapter.py's own logic
directly, using a tiny deterministic fake in place of a live JevProvider.
The resume/skip tests exercise main() itself with Phase 1 pre-marked
complete, so they never need 'gepa' importable -- deliberately, so this
resume path is verified in this repo's normal (gepa-less) test environment,
not just asserted by hand.
"""

from __future__ import annotations

import json
import os
import socket
import tempfile
import time
import unittest
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from unittest import mock

from .. import experiment_x_gepa_1_candidates as gepa_candidates
from .. import run_experiment_x_gepa_1 as runner
from ..experiment_3_candidates import (
    CONTESTED_CANDIDATE_IDS,
    EXPERIMENT_3_CANDIDATE_IDS,
    MUST_INCLUDE_IDS,
)
from ..gepa_jev_adapter import (
    COMPONENT_KEYS,
    TRANSIENT_EXCEPTIONS,
    JevGepaAdapter,
    case_from_candidate_dict,
    decide_with_retry,
    seed_candidate_from_bc_0101,
)
from ..providers.base import BC_0101


@dataclass
class _FakeDecision:
    verdict: str
    confidence: float
    rationale: str = "fake"
    candidate_id: str = ""
    candidate_kind: str = "knowledge"

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "confidence": self.confidence, "rationale": self.rationale,
                "candidate_id": self.candidate_id, "candidate_kind": self.candidate_kind}


class _FakeJevProvider:
    """Deterministic, offline stand-in for JevProvider.decide().

    Ignores the actual instruction text (unlike the real Jev call) -- this
    exists purely to exercise the adapter's own plumbing (score computation,
    EvaluationBatch/trajectory shape, reflective-dataset shape), not to
    simulate what a real model would decide. Verdict is keyed off the
    candidate id so tests are fully deterministic.
    """

    def __init__(self, include_ids: set[str]):
        self._include_ids = include_ids

    def decide(self, candidate, *, case):
        if candidate.id in self._include_ids:
            return _FakeDecision(verdict="include", confidence=0.9)
        return _FakeDecision(verdict="exclude", confidence=0.8)


class TestGepaDataset(unittest.TestCase):
    def test_kn101_never_labeled(self):
        labeled_ids = {d.candidate_id for d in gepa_candidates.ALL_LABELED}
        for cid in CONTESTED_CANDIDATE_IDS:
            self.assertNotIn(cid, labeled_ids, f"{cid} is CONTESTED and must never be a GEPA label")

    def test_kn047_never_labeled(self):
        labeled_ids = {d.candidate_id for d in gepa_candidates.ALL_LABELED}
        self.assertNotIn("KN-047", labeled_ids)

    def test_all_labeled_are_from_experiment_3_pool(self):
        labeled_ids = {d.candidate_id for d in gepa_candidates.ALL_LABELED}
        self.assertTrue(labeled_ids.issubset(set(EXPERIMENT_3_CANDIDATE_IDS)))

    def test_total_labeled_count(self):
        self.assertEqual(len(gepa_candidates.ALL_LABELED), 13)

    def test_splits_partition_all_labeled_with_no_overlap(self):
        train = gepa_candidates.load_split("train")
        val = gepa_candidates.load_split("val")
        test = gepa_candidates.load_split("test")
        train_ids = {d.candidate_id for d in train}
        val_ids = {d.candidate_id for d in val}
        test_ids = {d.candidate_id for d in test}
        self.assertEqual(len(train_ids & val_ids), 0)
        self.assertEqual(len(train_ids & test_ids), 0)
        self.assertEqual(len(val_ids & test_ids), 0)
        self.assertEqual(train_ids | val_ids | test_ids, {d.candidate_id for d in gepa_candidates.ALL_LABELED})

    def test_train_and_test_each_cover_all_four_categories(self):
        for split in ("train", "test"):
            categories = {d.category for d in gepa_candidates.load_split(split)}
            self.assertEqual(
                categories,
                {"must_include", "acceptable_optional", "related_but_unnecessary", "must_exclude"},
                f"{split} split should represent all 4 categories",
            )

    def test_target_verdict_mapping(self):
        for d in gepa_candidates.ALL_LABELED:
            if d.category in ("must_include", "acceptable_optional"):
                self.assertEqual(d.target_verdict, "include")
            else:
                self.assertEqual(d.target_verdict, "exclude")

    def test_load_resolves_real_candidate_content(self):
        example = gepa_candidates.load_split("train")[0]
        artifact = example.load()
        self.assertEqual(artifact.id, example.candidate_id)


class TestJevGepaAdapter(unittest.TestCase):
    def test_seed_candidate_matches_bc_0101(self):
        seed = seed_candidate_from_bc_0101()
        self.assertEqual(set(seed.keys()), set(COMPONENT_KEYS))
        self.assertEqual(seed["jev_instructions"], BC_0101.jev_instructions)
        self.assertEqual(seed["jev_criteria_true"], BC_0101.jev_criteria_true)
        self.assertEqual(seed["jev_criteria_false"], BC_0101.jev_criteria_false)

    def test_case_from_candidate_dict_does_not_mutate_bc_0101(self):
        before = (BC_0101.jev_instructions, BC_0101.jev_criteria_true, BC_0101.jev_criteria_false)
        case_from_candidate_dict({
            "jev_instructions": "different",
            "jev_criteria_true": "different true",
            "jev_criteria_false": "different false",
        })
        after = (BC_0101.jev_instructions, BC_0101.jev_criteria_true, BC_0101.jev_criteria_false)
        self.assertEqual(before, after)

    def test_case_reuses_bc_0101_task_statement_and_scope(self):
        case = case_from_candidate_dict(seed_candidate_from_bc_0101())
        self.assertEqual(case.task_statement, BC_0101.task_statement)
        self.assertIs(case.task_scope, BC_0101.task_scope)

    def test_evaluate_returns_correct_shape(self):
        train = gepa_candidates.load_split("train")
        include_ids = {d.candidate_id for d in train if d.target_verdict == "include"}
        adapter = JevGepaAdapter(provider=_FakeJevProvider(include_ids))
        batch = adapter.evaluate(train, seed_candidate_from_bc_0101(), capture_traces=False)
        self.assertEqual(len(batch.outputs), len(train))
        self.assertEqual(len(batch.scores), len(train))
        self.assertIsNone(batch.trajectories)
        for s in batch.scores:
            self.assertGreaterEqual(s, 0.0)
            self.assertLessEqual(s, 1.0)

    def test_evaluate_perfect_policy_scores_high(self):
        """If the fake provider's verdicts exactly match every target, every
        score should be the maximum (1.0), since confidence=0.9/0.8 gives a
        Brier-complement close to, but not exactly, 1.0 -- so we assert 'high'."""
        train = gepa_candidates.load_split("train")
        include_ids = {d.candidate_id for d in train if d.target_verdict == "include"}
        adapter = JevGepaAdapter(provider=_FakeJevProvider(include_ids))
        batch = adapter.evaluate(train, seed_candidate_from_bc_0101(), capture_traces=False)
        for s in batch.scores:
            self.assertGreater(s, 0.5, "a provider that matches every target should score above chance")

    def test_evaluate_wrong_policy_scores_low(self):
        """Fake provider that inverts every verdict should score low."""
        train = gepa_candidates.load_split("train")
        wrong_include_ids = {d.candidate_id for d in train if d.target_verdict == "exclude"}
        adapter = JevGepaAdapter(provider=_FakeJevProvider(wrong_include_ids))
        batch = adapter.evaluate(train, seed_candidate_from_bc_0101(), capture_traces=False)
        for s in batch.scores:
            self.assertLess(s, 0.5, "a provider that inverts every target should score below chance")

    def test_evaluate_capture_traces_populates_trajectories(self):
        train = gepa_candidates.load_split("train")
        adapter = JevGepaAdapter(provider=_FakeJevProvider(set()))
        batch = adapter.evaluate(train, seed_candidate_from_bc_0101(), capture_traces=True)
        self.assertEqual(len(batch.trajectories), len(train))
        for t in batch.trajectories:
            self.assertIn("candidate_id", t)
            self.assertIn("category", t)
            self.assertIn("target_verdict", t)
            self.assertIn("decision_verdict", t)

    def test_make_reflective_dataset_requires_trajectories(self):
        train = gepa_candidates.load_split("train")
        adapter = JevGepaAdapter(provider=_FakeJevProvider(set()))
        batch = adapter.evaluate(train, seed_candidate_from_bc_0101(), capture_traces=False)
        with self.assertRaises(ValueError):
            adapter.make_reflective_dataset(seed_candidate_from_bc_0101(), batch, list(COMPONENT_KEYS))

    def test_make_reflective_dataset_shape(self):
        train = gepa_candidates.load_split("train")
        adapter = JevGepaAdapter(provider=_FakeJevProvider(set()))
        batch = adapter.evaluate(train, seed_candidate_from_bc_0101(), capture_traces=True)
        reflective = adapter.make_reflective_dataset(
            seed_candidate_from_bc_0101(), batch, ["jev_instructions", "jev_criteria_true"]
        )
        self.assertEqual(set(reflective.keys()), {"jev_instructions", "jev_criteria_true"})
        for component, records in reflective.items():
            self.assertEqual(len(records), len(train))
            for r in records:
                self.assertIn("Inputs", r)
                self.assertIn("Generated Outputs", r)
                self.assertIn("Feedback", r)
                self.assertIsInstance(r["Feedback"], str)


class _FlakyProvider:
    """Fails with a configurable transient exception for the first N calls,
    then succeeds; or always fails, to test exhaustion. Records every
    (candidate, case) pair it was called with, so tests can assert retries
    resend the identical request."""

    def __init__(self, fail_times: int, exc_factory=lambda: TimeoutError("simulated timeout")):
        self.fail_times = fail_times
        self.exc_factory = exc_factory
        self.calls: list[tuple] = []

    def decide(self, candidate, *, case):
        self.calls.append((candidate, case))
        if len(self.calls) <= self.fail_times:
            raise self.exc_factory()
        return _FakeDecision(verdict="include", confidence=0.9)


class _AlwaysRaises:
    def __init__(self, exc):
        self.exc = exc
        self.calls = 0

    def decide(self, candidate, *, case):
        self.calls += 1
        raise self.exc


class TestDecideWithRetry(unittest.TestCase):
    """decide_with_retry: bounded exponential backoff on transient network
    failures only; identical request resent every attempt; non-transient
    errors propagate immediately, unretried."""

    def setUp(self):
        # Never actually sleep in tests.
        self._sleep_patcher = mock.patch("research.jev_context_decision.gepa_jev_adapter.time.sleep")
        self.mock_sleep = self._sleep_patcher.start()
        self.addCleanup(self._sleep_patcher.stop)

    def test_succeeds_without_retry_when_first_call_succeeds(self):
        provider = _FlakyProvider(fail_times=0)
        candidate = gepa_candidates.load_split("train")[0].load()
        case = case_from_candidate_dict(seed_candidate_from_bc_0101())
        result = decide_with_retry(provider, candidate, case)
        self.assertEqual(result.verdict, "include")
        self.assertEqual(len(provider.calls), 1)
        self.mock_sleep.assert_not_called()

    def test_retries_on_transient_timeout_then_succeeds(self):
        provider = _FlakyProvider(fail_times=2)
        candidate = gepa_candidates.load_split("train")[0].load()
        case = case_from_candidate_dict(seed_candidate_from_bc_0101())
        result = decide_with_retry(provider, candidate, case, max_attempts=3, base_delay=0.01)
        self.assertEqual(result.verdict, "include")
        self.assertEqual(len(provider.calls), 3)
        self.assertEqual(self.mock_sleep.call_count, 2)

    def test_retries_use_exponential_backoff(self):
        provider = _FlakyProvider(fail_times=2)
        candidate = gepa_candidates.load_split("train")[0].load()
        case = case_from_candidate_dict(seed_candidate_from_bc_0101())
        decide_with_retry(provider, candidate, case, max_attempts=3, base_delay=2.0)
        delays = [call.args[0] for call in self.mock_sleep.call_args_list]
        self.assertEqual(delays, [2.0, 4.0])

    def test_identical_request_resent_every_attempt(self):
        provider = _FlakyProvider(fail_times=2)
        candidate = gepa_candidates.load_split("train")[0].load()
        case = case_from_candidate_dict(seed_candidate_from_bc_0101())
        decide_with_retry(provider, candidate, case, max_attempts=3, base_delay=0.01)
        for called_candidate, called_case in provider.calls:
            self.assertIs(called_candidate, candidate)
            self.assertIs(called_case, case)

    def test_exhausts_retries_and_reraises(self):
        provider = _AlwaysRaises(TimeoutError("always times out"))
        candidate = gepa_candidates.load_split("train")[0].load()
        case = case_from_candidate_dict(seed_candidate_from_bc_0101())
        with self.assertRaises(TimeoutError):
            decide_with_retry(provider, candidate, case, max_attempts=3, base_delay=0.01)
        self.assertEqual(provider.calls, 3)

    def test_socket_timeout_is_transient(self):
        provider = _AlwaysRaises(socket.timeout("socket timeout"))
        candidate = gepa_candidates.load_split("train")[0].load()
        case = case_from_candidate_dict(seed_candidate_from_bc_0101())
        with self.assertRaises(socket.timeout):
            decide_with_retry(provider, candidate, case, max_attempts=2, base_delay=0.01)
        self.assertEqual(provider.calls, 2)

    def test_url_error_is_transient(self):
        provider = _AlwaysRaises(urllib.error.URLError("connection refused"))
        candidate = gepa_candidates.load_split("train")[0].load()
        case = case_from_candidate_dict(seed_candidate_from_bc_0101())
        with self.assertRaises(urllib.error.URLError):
            decide_with_retry(provider, candidate, case, max_attempts=2, base_delay=0.01)
        self.assertEqual(provider.calls, 2)

    def test_non_transient_error_is_never_retried(self):
        provider = _AlwaysRaises(ValueError("a real application error, not a network issue"))
        candidate = gepa_candidates.load_split("train")[0].load()
        case = case_from_candidate_dict(seed_candidate_from_bc_0101())
        with self.assertRaises(ValueError):
            decide_with_retry(provider, candidate, case, max_attempts=3, base_delay=0.01)
        self.assertEqual(provider.calls, 1, "a non-transient error must not be retried at all")
        self.mock_sleep.assert_not_called()


class TestConfigManifest(unittest.TestCase):
    """Configuration manifest + deterministic run_id + resume validation."""

    def test_manifest_has_all_required_fields(self):
        manifest = runner.build_config_manifest("openai/gpt-5-mini", 60)
        for key in ("experiment_id", "gepa_version", "jev_model", "train_ids", "val_ids",
                    "candidate_pool_ids", "criterion_id", "max_metric_calls",
                    "reflection_lm", "component_keys"):
            self.assertIn(key, manifest)
        self.assertEqual(manifest["experiment_id"], "X-GEPA-1")
        self.assertEqual(manifest["criterion_id"], BC_0101.id)
        self.assertEqual(manifest["max_metric_calls"], 60)
        self.assertEqual(manifest["reflection_lm"], "openai/gpt-5-mini")

    def test_run_id_is_deterministic_for_same_config(self):
        m1 = runner.build_config_manifest("openai/gpt-5-mini", 60)
        m2 = runner.build_config_manifest("openai/gpt-5-mini", 60)
        self.assertEqual(runner.compute_run_id(m1), runner.compute_run_id(m2))

    def test_run_id_differs_for_different_config(self):
        m1 = runner.build_config_manifest("openai/gpt-5-mini", 60)
        m2 = runner.build_config_manifest("openai/gpt-5-mini", 30)
        self.assertNotEqual(runner.compute_run_id(m1), runner.compute_run_id(m2))

    def test_fresh_manifest_is_written_and_reads_back_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            manifest = runner.build_config_manifest("openai/gpt-5-mini", 60)
            is_fresh = runner.validate_or_write_manifest(path, manifest)
            self.assertTrue(is_fresh)
            self.assertTrue(path.exists())
            self.assertEqual(json.loads(path.read_text()), manifest)

    def test_matching_manifest_resumes_without_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            manifest = runner.build_config_manifest("openai/gpt-5-mini", 60)
            runner.validate_or_write_manifest(path, manifest)
            is_fresh = runner.validate_or_write_manifest(path, manifest)
            self.assertFalse(is_fresh, "an identical manifest on the second call should be a resume, not fresh")

    def test_mismatched_manifest_raises_and_does_not_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            m1 = runner.build_config_manifest("openai/gpt-5-mini", 60)
            m2 = runner.build_config_manifest("openai/gpt-5-mini", 30)  # max_metric_calls differs
            runner.validate_or_write_manifest(path, m1)
            with self.assertRaises(runner.ConfigMismatchError) as ctx:
                runner.validate_or_write_manifest(path, m2)
            self.assertIn("max_metric_calls", str(ctx.exception))
            # The stored manifest must be untouched by the rejected attempt.
            self.assertEqual(json.loads(path.read_text()), m1)


class TestProgressFile(unittest.TestCase):
    """Phase-2 progress file: incremental persistence, completed_steps,
    and the complete=true gate."""

    def test_missing_progress_file_yields_default_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            progress = runner._load_progress(path)
            self.assertEqual(progress["completed_steps"], [])
            self.assertFalse(progress["complete"])

    def test_mark_step_complete_persists_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            runner._mark_step_complete(path, "baseline_budget_run", {"score": 0.5})
            reloaded = runner._load_progress(path)
            self.assertIn("baseline_budget_run", reloaded["completed_steps"])
            self.assertEqual(reloaded["baseline_budget_run"], {"score": 0.5})

    def test_marking_same_step_twice_does_not_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            runner._mark_step_complete(path, "baseline_budget_run", {"score": 0.5})
            runner._mark_step_complete(path, "baseline_budget_run", {"score": 0.5})
            reloaded = runner._load_progress(path)
            self.assertEqual(reloaded["completed_steps"].count("baseline_budget_run"), 1)

    def test_complete_is_false_until_every_step_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            for step in runner.ALL_STEPS[:-1]:
                progress = runner._mark_step_complete(path, step, {"ok": True})
                self.assertFalse(progress["complete"], f"should not be complete with {step} but not all steps done")

    def test_complete_is_true_only_after_every_step_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            progress = None
            for step in runner.ALL_STEPS:
                progress = runner._mark_step_complete(path, step, {"ok": True})
            self.assertTrue(progress["complete"])


class _FakeProviderForMain:
    """Stand-in for JevProvider inside main(): no network, no real key
    needed. Deterministic verdicts keyed off MUST_INCLUDE_IDS so the
    downstream budget run produces a sensible, checkable result."""

    def __init__(self, *args, **kwargs):
        self.model = "fake/jev-for-main-test"

    def _require_key(self):
        return "fake-key"

    def decide(self, candidate, *, case):
        verdict = "include" if candidate.id in MUST_INCLUDE_IDS else "exclude"
        return _FakeDecision(verdict=verdict, confidence=0.9,
                              candidate_id=candidate.id, candidate_kind=candidate.kind)


class TestMainResumeAndSkip(unittest.TestCase):
    """Exercises main() itself with Phase 1 pre-marked complete in the
    progress file -- deliberately never triggers `import gepa`, so this
    passes in this repo's normal (gepa-less) Python environment, which is
    itself part of the proof that the skip path works: if main() tried to
    re-run Phase 1, this test would fail with ImportError.
    """

    def _seeded_run(self, tmp_path: Path, reflection_lm="openai/gpt-5-mini", max_metric_calls=60):
        manifest = runner.build_config_manifest(reflection_lm, max_metric_calls)
        run_id = runner.compute_run_id(manifest)
        manifest_path = tmp_path / f"xgepa1_{run_id}_manifest.json"
        progress_path = tmp_path / f"xgepa1_{run_id}.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
        seed_dict = seed_candidate_from_bc_0101()
        phase1_payload = {
            "optimized_candidate": {**seed_dict, "jev_instructions": seed_dict["jev_instructions"] + " (optimized)"},
            "val_aggregate_scores": [0.95, 0.97, 0.9],
            "best_idx": 1,
            "total_metric_calls": 27,
        }
        progress = {"experiment_id": "X-GEPA-1", "completed_steps": [runner.PHASE1_STEP], "complete": False,
                    runner.PHASE1_STEP: phase1_payload}
        progress_path.write_text(json.dumps(progress, indent=2))
        return run_id, manifest_path, progress_path

    def test_resume_skips_phase1_and_completes_phase2(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_id, manifest_path, progress_path = self._seeded_run(tmp_path)
            with mock.patch.object(runner, "RESULTS_DIR", tmp_path), \
                 mock.patch.object(runner, "JevProvider", _FakeProviderForMain), \
                 mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "fake-key-for-test"}):
                exit_code = runner.main(["--live"])
            self.assertEqual(exit_code, 0)
            final = json.loads(progress_path.read_text())
            self.assertTrue(final["complete"])
            for step in runner.ALL_STEPS:
                self.assertIn(step, final["completed_steps"])
            # Phase 1's payload must be exactly what was seeded, not recomputed.
            self.assertEqual(final[runner.PHASE1_STEP]["total_metric_calls"], 27)

    def test_resume_does_not_recompute_already_completed_phase2_steps(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_id, manifest_path, progress_path = self._seeded_run(tmp_path)
            # Pre-seed baseline_budget_run too, with a sentinel score that the
            # real (fake-provider) computation would never produce.
            progress = json.loads(progress_path.read_text())
            progress["completed_steps"].append("baseline_budget_run")
            progress["baseline_budget_run"] = {"score": -999.0, "must_include_retention_rate": -999.0,
                                                "sentinel": True}
            progress_path.write_text(json.dumps(progress, indent=2))

            with mock.patch.object(runner, "RESULTS_DIR", tmp_path), \
                 mock.patch.object(runner, "JevProvider", _FakeProviderForMain), \
                 mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "fake-key-for-test"}):
                exit_code = runner.main(["--live"])
            self.assertEqual(exit_code, 0)
            final = json.loads(progress_path.read_text())
            self.assertEqual(final["baseline_budget_run"]["score"], -999.0,
                              "an already-completed step must not be recomputed on resume")

    def test_fresh_run_with_mismatched_config_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_id, manifest_path, progress_path = self._seeded_run(tmp_path, max_metric_calls=60)
            # Corrupt the on-disk manifest to simulate a stale/mismatched checkpoint
            # for the run_id this invocation would compute for --max-metric-calls 30.
            # Since run_id is itself derived from the manifest, a real mismatch can
            # only be forced by writing directly under the OTHER run_id's expected
            # path -- so instead we assert the manifest-diff path directly.
            manifest_60 = runner.build_config_manifest("openai/gpt-5-mini", 60)
            manifest_30 = runner.build_config_manifest("openai/gpt-5-mini", 30)
            forced_path = tmp_path / "forced_manifest.json"
            runner.validate_or_write_manifest(forced_path, manifest_60)
            with self.assertRaises(runner.ConfigMismatchError):
                runner.validate_or_write_manifest(forced_path, manifest_30)


if __name__ == "__main__":
    unittest.main()
