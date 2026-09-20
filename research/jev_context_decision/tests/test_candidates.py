import unittest

from research.jev_context_decision.candidates import (
    CONTENT_UNAVAILABLE,
    load_bc_0101_candidates,
    load_bc_0101_case,
)


class TestCandidateLoading(unittest.TestCase):
    def test_case_is_bc_0101(self):
        case = load_bc_0101_case()
        self.assertEqual(case["id"], "BC-0101")
        self.assertEqual(case["suite"], "BENCH-01")

    def test_exactly_seven_candidates(self):
        candidates = load_bc_0101_candidates()
        self.assertEqual(len(candidates), 7)
        self.assertEqual(
            sorted(c.id for c in candidates),
            sorted(["KN-045", "KN-052", "KN-063", "KN-047", "KN-101", "EXP-090", "EXP-055"]),
        )

    def test_six_candidates_have_real_content(self):
        candidates = {c.id: c for c in load_bc_0101_candidates()}
        for cid in ["KN-045", "KN-052", "KN-063", "KN-101", "EXP-090", "EXP-055"]:
            with self.subTest(candidate=cid):
                c = candidates[cid]
                self.assertTrue(c.content_available)
                self.assertIsNotNone(c.source_file)
                self.assertGreater(len(c.body), 40, "expected substantial real body text")
                self.assertNotEqual(c.body, CONTENT_UNAVAILABLE)

    def test_kn_047_is_explicit_stub_not_invented(self):
        candidates = {c.id: c for c in load_bc_0101_candidates()}
        kn047 = candidates["KN-047"]
        self.assertFalse(kn047.content_available)
        self.assertIsNone(kn047.source_file)
        self.assertEqual(kn047.body, CONTENT_UNAVAILABLE)

    def test_specific_real_content_matches_repo(self):
        candidates = {c.id: c for c in load_bc_0101_candidates()}
        self.assertIn("idempotency", candidates["KN-052"].body.lower())
        self.assertIn("loyalty", candidates["EXP-090"].body.lower())
        self.assertIn("cache", candidates["KN-063"].body.lower())

    def test_unknown_candidate_id_raises_instead_of_inventing(self):
        from research.jev_context_decision.candidates import load_candidate

        with self.assertRaises(LookupError):
            load_candidate("KN-999999", "knowledge")


if __name__ == "__main__":
    unittest.main()
