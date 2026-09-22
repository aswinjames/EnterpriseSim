"""Offline tests for X-GEPA-1's dataset module and GEPAAdapter.

No network access, no gepa package required -- these exercise
experiment_x_gepa_1_candidates.py and gepa_jev_adapter.py's own logic
directly, using a tiny deterministic fake in place of a live JevProvider.
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass

from .. import experiment_x_gepa_1_candidates as gepa_candidates
from ..experiment_3_candidates import CONTESTED_CANDIDATE_IDS, EXPERIMENT_3_CANDIDATE_IDS
from ..gepa_jev_adapter import (
    COMPONENT_KEYS,
    JevGepaAdapter,
    case_from_candidate_dict,
    seed_candidate_from_bc_0101,
)
from ..providers.base import BC_0101


@dataclass
class _FakeDecision:
    verdict: str
    confidence: float
    rationale: str = "fake"


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


if __name__ == "__main__":
    unittest.main()
