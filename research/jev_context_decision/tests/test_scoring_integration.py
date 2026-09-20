import unittest

from research.jev_context_decision.candidates import load_bc_0101_case
from research.jev_context_decision.decision import ContextDecision, aggregate
from research.jev_context_decision.scoring import score


def _decision(candidate_id: str, verdict: str, kind: str) -> ContextDecision:
    return ContextDecision(
        candidate_id=candidate_id,
        candidate_kind=kind,
        provider="mock",
        verdict=verdict,
        rationale="test",
        confidence=0.9,
        model="test-model",
        prompt_version="test-v1",
        latency_ms=1.0,
        timestamp="2026-01-01T00:00:00Z",
    )


class TestScoringIntegration(unittest.TestCase):
    """Verifies the reused score() evaluator behaves correctly against decisions
    aggregated by this experiment's own pipeline (not against hand-built dicts)."""

    def setUp(self):
        self.case = load_bc_0101_case()

    def test_ground_truth_optimal_selection_passes(self):
        # ground_truth.expected.acceptable_optional is exactly ["KN-063", "EXP-055"]
        # (KN-047 is only called a "defensible budget drop" in ground_truth.notes;
        # it is NOT in acceptable_optional, so it does not count toward the
        # "relevant" set the scorer uses for recall/precision). The best any
        # provider can score is must_include ∪ acceptable_optional included,
        # both must_exclude and KN-047 dropped.
        decisions = [
            _decision("KN-045", "include", "knowledge"),
            _decision("KN-052", "include", "knowledge"),
            _decision("KN-063", "include", "knowledge"),  # acceptable_optional
            _decision("KN-047", "exclude", "knowledge"),  # defensible drop, not "relevant"
            _decision("KN-101", "exclude", "knowledge"),  # must_exclude
            _decision("EXP-090", "include", "experience"),
            _decision("EXP-055", "include", "experience"),  # acceptable_optional
        ]
        ctx = aggregate(decisions).to_context_object(task_ref=self.case["task_ref"])
        result = score(self.case, ctx)
        self.assertTrue(result["gate_pass"])
        self.assertEqual(result["missing_required"], [])
        self.assertEqual(result["leaked_forbidden"], [])
        self.assertGreaterEqual(result["objective_score"], self.case["thresholds"]["pass"])
        self.assertEqual(result["verdict"], "pass")

    def test_missing_required_item_fails_gate(self):
        decisions = [
            _decision("KN-045", "include", "knowledge"),
            _decision("KN-052", "exclude", "knowledge"),  # required, wrongly dropped
            _decision("KN-063", "exclude", "knowledge"),
            _decision("KN-047", "exclude", "knowledge"),
            _decision("KN-101", "exclude", "knowledge"),
            _decision("EXP-090", "include", "experience"),
            _decision("EXP-055", "exclude", "experience"),
        ]
        ctx = aggregate(decisions).to_context_object(task_ref=self.case["task_ref"])
        result = score(self.case, ctx)
        self.assertFalse(result["gate_pass"])
        self.assertIn("KN-052", result["missing_required"])
        self.assertLessEqual(result["objective_score"], 0.40)

    def test_leaked_forbidden_item_caps_score(self):
        decisions = [
            _decision("KN-045", "include", "knowledge"),
            _decision("KN-052", "include", "knowledge"),
            _decision("KN-063", "include", "knowledge"),
            _decision("KN-047", "exclude", "knowledge"),
            _decision("KN-101", "include", "knowledge"),  # forbidden distractor leaked
            _decision("EXP-090", "include", "experience"),
            _decision("EXP-055", "exclude", "experience"),
        ]
        ctx = aggregate(decisions).to_context_object(task_ref=self.case["task_ref"])
        result = score(self.case, ctx)
        self.assertFalse(result["gate_pass"])
        self.assertIn("KN-101", result["leaked_forbidden"])
        self.assertLessEqual(result["objective_score"], 0.40)
        self.assertEqual(result["verdict"], "fail")

    def test_including_forbidden_distractor_hurts_precision_and_gate(self):
        # KN-101 is the only must_exclude item; the "relevant" set (must_include ∪
        # acceptable_optional) is everything else. Including KN-101 alongside the
        # rest is the literal corpus-dump case: it both leaks the forbidden gate
        # and is the one item that drags precision below 1.0.
        dump_decisions = [
            _decision(cid, "include", "knowledge" if cid.startswith("KN") else "experience")
            for cid in ["KN-045", "KN-052", "KN-063", "KN-047", "KN-101", "EXP-090", "EXP-055"]
        ]
        dump_ctx = aggregate(dump_decisions).to_context_object(task_ref=self.case["task_ref"])
        dump_result = score(self.case, dump_ctx)
        self.assertFalse(dump_result["gate_pass"])
        self.assertLess(dump_result["precision"], 1.0)

    def test_under_inclusion_of_optional_items_reduces_recall_not_precision(self):
        # Dropping acceptable_optional items is a defensible budget choice: it
        # should cost recall but must not be penalized on precision.
        tight_decisions = [
            _decision("KN-045", "include", "knowledge"),
            _decision("KN-052", "include", "knowledge"),
            _decision("KN-063", "exclude", "knowledge"),
            _decision("KN-047", "exclude", "knowledge"),
            _decision("KN-101", "exclude", "knowledge"),
            _decision("EXP-090", "include", "experience"),
            _decision("EXP-055", "exclude", "experience"),
        ]
        ctx = aggregate(tight_decisions).to_context_object(task_ref=self.case["task_ref"])
        result = score(self.case, ctx)
        self.assertTrue(result["gate_pass"])
        self.assertEqual(result["precision"], 1.0)
        self.assertLess(result["recall"], 1.0)


if __name__ == "__main__":
    unittest.main()
