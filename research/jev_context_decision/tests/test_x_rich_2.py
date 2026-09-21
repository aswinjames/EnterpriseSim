"""Tests for X-RICH-2: same candidates/criterion/scorer as X-RICH-1, with the
complete enterprise application registry as the sole added treatment.

Covers the 6 required proofs:
1. X-RICH-2 candidate pool identical to X-RICH-1.
2. Criterion identical.
3. Registry loaded from the existing repository source.
4. The complete registry is passed to the model.
5. No candidate-specific registry filtering occurs.
6. X-RICH-1 behavior/files remain unchanged.

No live network access anywhere in this file.
"""

import json
import unittest
from unittest import mock

from research.jev_context_decision.candidates import load_bc_0101_case
from research.jev_context_decision.enterprise_context import (
    APPLICATION_REGISTRY_PATH,
    ENTERPRISE_CONTEXT_TRAILER,
    format_enterprise_context_block,
    load_application_registry,
)
from research.jev_context_decision.experiment_3_candidates import (
    EXPERIMENT_3_CANDIDATE_IDS,
    build_experiment_3_case,
    load_experiment_3_candidates,
)
from research.jev_context_decision.providers import gpt_provider, jev_provider, openai_direct, openrouter
from research.jev_context_decision.providers.base import BC_0101
from research.jev_context_decision.providers.enterprise_context_providers import (
    GPTProviderWithEnterpriseContext,
    JevProviderWithEnterpriseContext,
)
from research.jev_context_decision.run_experiment_x_rich_2 import CRITERION, EXPERIMENT_ID


def _candidate(candidate_id: str):
    candidates = {c.id: c for c in load_experiment_3_candidates()}
    return candidates[candidate_id]


class TestCandidatePoolIdenticalToXRich1(unittest.TestCase):
    """Requirement 1."""

    def test_x_rich_2_uses_the_same_candidate_loader_and_ids(self):
        # run_experiment_x_rich_2.py imports load_experiment_3_candidates
        # directly -- there is no separate X-RICH-2 candidate list anywhere.
        candidates = load_experiment_3_candidates()
        self.assertEqual(tuple(c.id for c in candidates), EXPERIMENT_3_CANDIDATE_IDS)
        self.assertEqual(len(candidates), 15)


class TestCriterionIdentical(unittest.TestCase):
    """Requirement 2."""

    def test_criterion_is_bc_0101_by_identity(self):
        self.assertIs(CRITERION, BC_0101)

    def test_experiment_id_is_x_rich_2_not_x_rich_1(self):
        self.assertEqual(EXPERIMENT_ID, "X-RICH-2")


class TestRegistryLoadedFromRepository(unittest.TestCase):
    """Requirement 3."""

    def test_registry_matches_file_on_disk_exactly(self):
        registry = load_application_registry()
        on_disk = json.loads(APPLICATION_REGISTRY_PATH.read_text())
        self.assertEqual(registry, on_disk)

    def test_registry_has_expected_size_and_a_known_fact(self):
        registry = load_application_registry()
        self.assertEqual(len(registry), 12)
        by_id = {a["id"]: a for a in registry}
        self.assertIn("APP-003", by_id)
        self.assertIn("APP-007", by_id["APP-003"]["dependencies"])

    def test_registry_is_read_fresh_not_hardcoded(self):
        # Two independent loads must be equal in value (not necessarily
        # identity) -- proves it's read from disk each time, not a baked-in
        # module-level constant that could silently drift from the file.
        first = load_application_registry()
        second = load_application_registry()
        self.assertEqual(first, second)
        self.assertIsNot(first, second)


class TestCompleteRegistryPassedToModel(unittest.TestCase):
    """Requirement 4."""

    def test_context_block_contains_every_app_id(self):
        registry = load_application_registry()
        block = format_enterprise_context_block(registry)
        for app in registry:
            self.assertIn(app["id"], block)
        self.assertIn(ENTERPRISE_CONTEXT_TRAILER, block)

    def test_gpt_request_contains_full_registry(self):
        registry = load_application_registry()
        candidate = _candidate("KN-045")
        fake_response = {
            "model": "gpt-5-mini",
            "choices": [{"message": {"content": '{"verdict": "include", "rationale": "x", "confidence": 0.7}'}}],
            "usage": {},
        }
        with mock.patch.object(openai_direct, "post_json", return_value=fake_response) as mock_post:
            provider = GPTProviderWithEnterpriseContext(enterprise_registry=registry, api_key="sk-test")
            provider.decide(candidate, case=BC_0101)
        called_body = mock_post.call_args[0][1]
        content = called_body["messages"][0]["content"]
        for app in registry:
            self.assertIn(app["id"], content)
        # Base X-RICH-1 prompt content must still be present, unmodified.
        self.assertIn(candidate.body, content)
        self.assertIn(BC_0101.task_statement, content)

    def test_jev_request_contains_full_registry_verbatim(self):
        registry = load_application_registry()
        candidate = _candidate("KN-101")
        fake_response = {
            "model": "typesafe/jev-1.13",
            "answers": {jev_provider._QUESTION_KEY: {"type": "noul", "noul": 0.6}},
            "usage": {},
        }
        with mock.patch.object(openrouter, "post_json", return_value=fake_response) as mock_post:
            provider = JevProviderWithEnterpriseContext(enterprise_registry=registry, api_key="sk-test")
            provider.decide(candidate, case=BC_0101)
        called_body = mock_post.call_args[0][1]
        self.assertEqual(called_body["state"]["enterprise_application_registry"], registry)
        # Base X-RICH-1 state/question fields must still be present, unmodified.
        self.assertEqual(called_body["state"]["candidate_content"], candidate.body)
        self.assertEqual(
            called_body["questions"][jev_provider._QUESTION_KEY]["instructions"],
            BC_0101.jev_instructions,
        )


class TestNoCandidateSpecificFiltering(unittest.TestCase):
    """Requirement 5."""

    def test_registry_identical_across_different_candidates_gpt(self):
        registry = load_application_registry()
        fake_response = {
            "model": "gpt-5-mini",
            "choices": [{"message": {"content": '{"verdict": "include", "rationale": "x", "confidence": 0.7}'}}],
            "usage": {},
        }
        seen_contents = []
        with mock.patch.object(openai_direct, "post_json", return_value=fake_response) as mock_post:
            provider = GPTProviderWithEnterpriseContext(enterprise_registry=registry, api_key="sk-test")
            for cid in ("KN-045", "KN-101", "KN-311"):
                provider.decide(_candidate(cid), case=BC_0101)
        for call in mock_post.call_args_list:
            body = call.args[1]
            # Extract just the registry JSON portion by re-serializing what
            # was loaded -- it must be byte-identical every call regardless
            # of which candidate was being decided.
            seen_contents.append(json.dumps(registry, indent=2) in body["messages"][0]["content"])
        self.assertTrue(all(seen_contents))

    def test_registry_identical_across_different_candidates_jev(self):
        registry = load_application_registry()
        fake_response = {
            "model": "typesafe/jev-1.13",
            "answers": {jev_provider._QUESTION_KEY: {"type": "noul", "noul": 0.4}},
            "usage": {},
        }
        with mock.patch.object(openrouter, "post_json", return_value=fake_response) as mock_post:
            provider = JevProviderWithEnterpriseContext(enterprise_registry=registry, api_key="sk-test")
            for cid in ("KN-045", "KN-101", "KN-311"):
                provider.decide(_candidate(cid), case=BC_0101)
        registries_sent = [call.args[1]["state"]["enterprise_application_registry"] for call in mock_post.call_args_list]
        self.assertTrue(all(r == registry for r in registries_sent))


class TestXRich1Unaffected(unittest.TestCase):
    """Requirement 6."""

    def test_gpt_provider_module_unchanged_no_registry_field(self):
        candidate = _candidate("KN-045")
        body = gpt_provider._build_request(candidate, BC_0101, "gpt-5-mini")
        self.assertNotIn("enterprise", json.dumps(body).lower())

    def test_jev_provider_module_unchanged_no_registry_field(self):
        candidate = _candidate("KN-045")
        body = jev_provider._build_request(candidate, BC_0101, "typesafe/jev-1.13")
        self.assertNotIn("enterprise_application_registry", body["state"])

    def test_x_rich_1_case_and_candidates_unchanged(self):
        case = build_experiment_3_case(load_bc_0101_case())
        self.assertEqual(case["id"], "X-RICH-1")  # frozen function's own id, untouched
        self.assertEqual(case["ground_truth"]["must_include"], ["KN-045", "KN-052", "EXP-090"])
        self.assertNotIn("KN-101", case["ground_truth"]["must_include"])
        self.assertNotIn("KN-101", case["ground_truth"]["must_exclude"])


if __name__ == "__main__":
    unittest.main()
