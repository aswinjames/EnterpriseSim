"""Tests documenting the known KN-101 ground-truth/content discrepancy.

These tests do not resolve the discrepancy -- they assert that it currently
exists, exactly as documented in benchmark_quality.py. If either side of the
discrepancy is ever changed (the ground truth note, or KN-101's real content),
these tests fail loudly, forcing a deliberate decision rather than silent
drift. Neither value is altered by this file. No live network access.
"""

import unittest

from research.jev_context_decision.benchmark_quality import KN_101_DISCREPANCY
from research.jev_context_decision.candidates import load_bc_0101_case, load_candidate


class TestKN101Discrepancy(unittest.TestCase):
    def test_ground_truth_claim_matches_live_benchmark_case_notes(self):
        # The recorded claim must match what the frozen case's notes actually
        # say today -- proves the documentation isn't stale.
        case = load_bc_0101_case()
        self.assertIn(KN_101_DISCREPANCY.ground_truth_claim, case["ground_truth"]["notes"])

    def test_actual_content_summary_matches_live_kn101_title(self):
        # The recorded "actual content" side must match what candidates.py
        # actually resolves today for KN-101.
        kn101 = load_candidate("KN-101", "knowledge")
        self.assertEqual(KN_101_DISCREPANCY.actual_content_summary, kn101.title)

    def test_ground_truth_claim_terms_do_not_appear_in_actual_content(self):
        # The discrepancy, asserted directly: none of the ground truth's
        # claimed subject terms appear anywhere in KN-101's real content.
        kn101 = load_candidate("KN-101", "knowledge")
        real_text = f"{kn101.title} {kn101.body}".lower()
        for term in ("marketplace", "seller", "onboarding"):
            self.assertNotIn(term, real_text)

    def test_actual_content_terms_do_not_appear_in_ground_truth_claim(self):
        claim = KN_101_DISCREPANCY.ground_truth_claim.lower()
        for term in ("price", "currency", "region"):
            self.assertNotIn(term, claim)

    def test_neither_value_was_invented_by_this_module(self):
        # Both sides trace to a real, named source location -- not asserted
        # in a vacuum.
        self.assertIn("benchmark_case.example.json", KN_101_DISCREPANCY.ground_truth_source)
        self.assertIn("business-rules.json", KN_101_DISCREPANCY.actual_content_source)


if __name__ == "__main__":
    unittest.main()
