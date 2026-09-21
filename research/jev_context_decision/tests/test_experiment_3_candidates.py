"""Tests for Experiment 3 (X-RICH-1): the expanded 15-candidate pool.

Covers the 22 requirements for this phase: exact candidate set, KN-101's
CONTESTED (not MUST_INCLUDE/MUST_EXCLUDE) treatment, the 5 held-out
candidates' absence, RELATED_BUT_UNNECESSARY as a separate tier, and proof
that BC-0101/BC-0102/TaskScope/score()/provider behavior are all unaffected
by Experiment 3's existence. No live network access anywhere in this file.
"""

import unittest
from unittest import mock

from research.jev_context_decision.candidates import load_bc_0101_candidates, load_bc_0101_case
from research.jev_context_decision.decision import ContextDecision
from research.jev_context_decision.experiment_3_candidates import (
    ACCEPTABLE_OPTIONAL_IDS,
    CLASSIFICATIONS,
    CONTESTED,
    CONTESTED_CANDIDATE_IDS,
    EXPERIMENT_3_CANDIDATE_IDS,
    EXPERIMENT_ID,
    HELD_OUT_CANDIDATE_IDS,
    MUST_EXCLUDE,
    MUST_EXCLUDE_IDS,
    MUST_INCLUDE,
    MUST_INCLUDE_IDS,
    RELATED_BUT_UNNECESSARY,
    RELATED_BUT_UNNECESSARY_IDS,
    build_experiment_3_case,
    load_experiment_3_candidates,
)
from research.jev_context_decision.providers.base import BC_0101, BC_0102
from research.jev_context_decision.providers.mock_provider import MockProvider
from research.jev_context_decision.run_experiment_3 import _build_scored_context
from research.jev_context_decision.scoring import score as score_context
from research.jev_context_decision.task_scope import TaskScope

_EXPECTED_15 = (
    "KN-045", "KN-052", "EXP-090", "KN-063", "EXP-055", "KN-047", "KN-101",
    "KN-128", "KN-146", "KN-411", "KN-313", "EXP-209", "EXP-206", "KN-122", "KN-311",
)
_EXPECTED_HELD_OUT = ("KN-126", "KN-127", "KN-144", "KN-140", "KN-136")
_EXPECTED_NEW_CLASSIFICATIONS = {
    "KN-128": RELATED_BUT_UNNECESSARY,
    "KN-146": RELATED_BUT_UNNECESSARY,
    "KN-411": RELATED_BUT_UNNECESSARY,
    "KN-313": RELATED_BUT_UNNECESSARY,
    "EXP-209": RELATED_BUT_UNNECESSARY,
    "EXP-206": RELATED_BUT_UNNECESSARY,
    "KN-122": MUST_EXCLUDE,
    "KN-311": MUST_EXCLUDE,
}


class TestExactCandidateSet(unittest.TestCase):
    """Requirements 1-8."""

    def test_exactly_15_candidates(self):
        self.assertEqual(len(EXPERIMENT_3_CANDIDATE_IDS), 15)

    def test_ids_match_exactly_in_order(self):
        self.assertEqual(EXPERIMENT_3_CANDIDATE_IDS, _EXPECTED_15)

    def test_kn101_present(self):
        self.assertIn("KN-101", EXPERIMENT_3_CANDIDATE_IDS)

    def test_kn126_absent(self):
        self.assertNotIn("KN-126", EXPERIMENT_3_CANDIDATE_IDS)

    def test_kn127_absent(self):
        self.assertNotIn("KN-127", EXPERIMENT_3_CANDIDATE_IDS)

    def test_kn144_absent(self):
        self.assertNotIn("KN-144", EXPERIMENT_3_CANDIDATE_IDS)

    def test_kn140_absent(self):
        self.assertNotIn("KN-140", EXPERIMENT_3_CANDIDATE_IDS)

    def test_kn136_absent(self):
        self.assertNotIn("KN-136", EXPERIMENT_3_CANDIDATE_IDS)

    def test_held_out_ids_documented_and_disjoint(self):
        self.assertEqual(set(HELD_OUT_CANDIDATE_IDS), set(_EXPECTED_HELD_OUT))
        self.assertEqual(set(HELD_OUT_CANDIDATE_IDS) & set(EXPERIMENT_3_CANDIDATE_IDS), set())


class TestCandidatesResolveToRealContent(unittest.TestCase):
    """Requirement 9."""

    def test_all_15_resolve_kn047_stub_excepted(self):
        candidates = load_experiment_3_candidates()
        self.assertEqual(len(candidates), 15)
        by_id = {c.id: c for c in candidates}
        self.assertEqual(set(by_id), set(EXPERIMENT_3_CANDIDATE_IDS))
        for cid, c in by_id.items():
            if cid == "KN-047":
                self.assertFalse(c.content_available)
            else:
                self.assertTrue(c.content_available, f"{cid} should have real content")
                self.assertIsNotNone(c.source_file)
                self.assertGreater(len(c.body), 20)


class TestKN101Contested(unittest.TestCase):
    """Requirements 10-13: KN-101 is CONTESTED, not converted, not hardcoded."""

    def test_kn101_classified_contested(self):
        self.assertEqual(CLASSIFICATIONS["KN-101"], CONTESTED)

    def test_kn101_not_must_include(self):
        self.assertNotIn("KN-101", MUST_INCLUDE_IDS)

    def test_kn101_not_must_exclude(self):
        self.assertNotIn("KN-101", MUST_EXCLUDE_IDS)

    def test_kn101_not_acceptable_optional(self):
        self.assertNotIn("KN-101", ACCEPTABLE_OPTIONAL_IDS)

    def test_kn101_absent_from_experiment_3_ground_truth_entirely(self):
        # Not hardcoded as an answer anywhere in the scored ground truth --
        # not in must_include, not in must_exclude, not in acceptable_optional.
        case = build_experiment_3_case(load_bc_0101_case())
        gt = case["ground_truth"]
        self.assertNotIn("KN-101", gt["must_include"])
        self.assertNotIn("KN-101", gt["must_exclude"])
        self.assertNotIn("KN-101", gt["expected"]["acceptable_optional"])

    def test_kn101_excluded_from_scored_context_regardless_of_verdict(self):
        # Functional proof: whether the provider includes or excludes KN-101,
        # it never reaches the context object passed to score().
        for verdict in ("include", "exclude"):
            decisions = [
                ContextDecision(
                    candidate_id=cid, candidate_kind="knowledge", provider="mock",
                    verdict=(verdict if cid == "KN-101" else "include"),
                    rationale="x", confidence=0.9, model="mock", prompt_version="v",
                    latency_ms=1.0, timestamp="2026-01-01T00:00:00Z",
                )
                for cid in ["KN-045", "KN-101"]
            ]
            ctx = _build_scored_context(decisions, "CHK-1421", exclude_ids=set(CONTESTED_CANDIDATE_IDS))
            all_sources = {i["source"] for i in ctx["included"]} | {i["source"] for i in ctx["excluded"]}
            self.assertNotIn("KN-101", all_sources, f"KN-101 leaked into scored context (verdict={verdict})")

    def test_kn101_decision_is_still_fully_captured(self):
        # Not scored, but never silently dropped from the record either.
        candidates = {c.id: c for c in load_experiment_3_candidates()}
        decision = MockProvider().decide(candidates["KN-101"], case=BC_0101)
        self.assertEqual(decision.candidate_id, "KN-101")
        self.assertIn(decision.verdict, ("include", "exclude"))
        self.assertIsNotNone(decision.confidence)


class TestRelatedButUnnecessarySeparateTier(unittest.TestCase):
    """Requirement 14."""

    def test_related_but_unnecessary_ids_match_expected(self):
        self.assertEqual(
            set(RELATED_BUT_UNNECESSARY_IDS),
            {"KN-128", "KN-146", "KN-411", "KN-313", "EXP-209", "EXP-206"},
        )

    def test_related_but_unnecessary_absent_from_all_three_scored_sets(self):
        case = build_experiment_3_case(load_bc_0101_case())
        gt = case["ground_truth"]
        for cid in RELATED_BUT_UNNECESSARY_IDS:
            self.assertNotIn(cid, gt["must_include"])
            self.assertNotIn(cid, gt["must_exclude"])
            self.assertNotIn(cid, gt["expected"]["acceptable_optional"])


class TestNewCandidateClassifications(unittest.TestCase):
    """Requirement 15."""

    def test_eight_new_candidates_have_intended_classifications(self):
        for cid, expected in _EXPECTED_NEW_CLASSIFICATIONS.items():
            self.assertEqual(CLASSIFICATIONS[cid], expected, f"{cid} classification mismatch")


class TestFrozenComponentsUnaffected(unittest.TestCase):
    """Requirements 16-20: score(), BC-0101, BC-0102, providers, TaskScope."""

    def test_score_function_behaves_identically_on_a_known_case(self):
        # Not just "not edited" -- exercise it with a known input/output pair
        # to prove behavior, matching test_scoring_integration.py's pattern.
        case = load_bc_0101_case()
        ctx = {
            "task": {"ref": case["task_ref"]},
            "included": [
                {"source": s, "kind": "knowledge", "reason": "x", "score": 0.9}
                for s in ["KN-045", "KN-052", "EXP-090"]
            ],
            "excluded": [],
        }
        result = score_context(case, ctx)
        self.assertTrue(result["gate_pass"])
        self.assertEqual(result["missing_required"], [])

    def test_bc_0101_candidates_unchanged(self):
        candidates = load_bc_0101_candidates()
        self.assertEqual(
            sorted(c.id for c in candidates),
            sorted(["KN-045", "KN-052", "KN-063", "KN-047", "KN-101", "EXP-090", "EXP-055"]),
        )

    def test_bc_0101_wording_unchanged(self):
        self.assertEqual(
            BC_0101.task_statement,
            "Task (CHK-1421, APP-003 Checkout Service): implement guest checkout order "
            "placement. Decide, for this ONE candidate artifact only, whether it should be "
            "included in the Worker's working context for this task. Judge it strictly on "
            "its own content and relevance to guest checkout order placement -- do not "
            "assume information about any other candidate.",
        )

    def test_bc_0102_wording_unchanged(self):
        self.assertEqual(BC_0102.prompt_version, "jev-gpt-openrouter-context-decision-bc0102-v1")
        self.assertIn("Is this artifact necessary to correctly perform this specific", BC_0102.task_statement)

    def test_task_scope_unchanged(self):
        self.assertIsInstance(BC_0101.task_scope, TaskScope)
        self.assertEqual(BC_0101.task_scope.task_id, "CHK-1421")
        self.assertEqual(BC_0101.task_scope.declared_apps, ("APP-003", "APP-015", "APP-012"))
        self.assertEqual(BC_0101.task_scope, BC_0102.task_scope)

    def test_provider_decide_signature_and_behavior_unchanged(self):
        # Mock provider still works exactly as before for a BC-0101 candidate
        # under BC-0101's own criterion -- Experiment 3's existence changes
        # nothing about existing provider call sites.
        candidate = load_bc_0101_candidates()[0]
        decision = MockProvider().decide(candidate, case=BC_0101)
        self.assertEqual(decision.provider, "mock")


class TestExperiment3CriterionMatchesBC0101(unittest.TestCase):
    """Requirement 21."""

    def test_run_experiment_3_criterion_is_bc_0101_object(self):
        from research.jev_context_decision.run_experiment_3 import CRITERION

        self.assertIs(CRITERION, BC_0101)

    def test_experiment_id_is_x_rich_1(self):
        self.assertEqual(EXPERIMENT_ID, "X-RICH-1")


class TestNoLiveAPICallsInOfflineTests(unittest.TestCase):
    """Requirement 22: this whole file, and the CLI dry run, must be network-free."""

    def test_offline_dry_run_end_to_end_no_network(self):
        import json
        import tempfile
        from pathlib import Path

        from research.jev_context_decision.run_experiment_3 import main

        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "experiment3_mock.json"
            exit_code = main(["--provider", "mock", "--repeats", "1", "--out", str(out_path)])
            self.assertEqual(exit_code, 0)
            data = json.loads(out_path.read_text())
            self.assertEqual(data["experiment_id"], "X-RICH-1")
            self.assertEqual(data["candidate_count"], 15)
            r = data["repeats"][0]
            self.assertEqual(len(r["raw_decisions"]), 15)
            self.assertIn("kn101_selection_rate", data["summary"])
            self.assertIn("related_but_unnecessary_inclusion_rate_mean", data["summary"])
            # KN-101 must never appear in the scored view, regardless of verdict.
            scored_ids = set(r["scored_selected"]["included"]) | set(r["scored_selected"]["excluded"])
            self.assertNotIn("KN-101", scored_ids)
            # ...but must appear in the full, unfiltered view.
            full_ids = set(r["selected_full"]["included"]) | set(r["selected_full"]["excluded"])
            self.assertIn("KN-101", full_ids)

    def test_live_provider_without_flag_is_refused(self):
        from research.jev_context_decision.run_experiment_3 import main

        exit_code = main(["--provider", "gpt", "--repeats", "1"])
        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
