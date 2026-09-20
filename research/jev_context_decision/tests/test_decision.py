import unittest

from research.jev_context_decision.decision import ContextDecision, aggregate


def _decision(candidate_id: str, verdict: str, kind: str = "knowledge") -> ContextDecision:
    return ContextDecision(
        candidate_id=candidate_id,
        candidate_kind=kind,
        provider="mock",
        verdict=verdict,
        rationale="test",
        confidence=0.7,
        model="test-model",
        prompt_version="test-v1",
        latency_ms=1.0,
        timestamp="2026-01-01T00:00:00Z",
    )


class TestAggregate(unittest.TestCase):
    def test_splits_include_exclude(self):
        decisions = [
            _decision("KN-045", "include"),
            _decision("KN-101", "exclude"),
            _decision("EXP-090", "include", kind="experience"),
        ]
        agg = aggregate(decisions)
        self.assertEqual(sorted(agg.included), ["EXP-090", "KN-045"])
        self.assertEqual(agg.excluded, ["KN-101"])

    def test_duplicate_candidate_raises(self):
        decisions = [_decision("KN-045", "include"), _decision("KN-045", "exclude")]
        with self.assertRaises(ValueError):
            aggregate(decisions)

    def test_to_context_object_shape(self):
        decisions = [_decision("KN-045", "include"), _decision("KN-101", "exclude")]
        agg = aggregate(decisions)
        ctx = agg.to_context_object(task_ref="CHK-1421")
        self.assertEqual(ctx["task"]["ref"], "CHK-1421")
        included_sources = {i["source"] for i in ctx["included"]}
        excluded_sources = {i["source"] for i in ctx["excluded"]}
        self.assertEqual(included_sources, {"KN-045"})
        self.assertEqual(excluded_sources, {"KN-101"})
        for item in ctx["included"] + ctx["excluded"]:
            self.assertIn("reason", item)
            self.assertIn("score", item)


if __name__ == "__main__":
    unittest.main()
