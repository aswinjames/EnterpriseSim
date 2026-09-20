import os
import unittest
from unittest import mock

from research.jev_context_decision.candidates import load_bc_0101_candidates
from research.jev_context_decision.providers import GPTProvider, JevProvider, MockProvider, ProviderNotConfigured


class TestMockProvider(unittest.TestCase):
    def setUp(self):
        self.candidates = {c.id: c for c in load_bc_0101_candidates()}
        self.provider = MockProvider()

    def test_decides_all_seven_independently(self):
        decisions = self.provider.decide_all(list(self.candidates.values()))
        self.assertEqual(len(decisions), 7)
        self.assertEqual({d.candidate_id for d in decisions}, set(self.candidates))
        for d in decisions:
            self.assertIn(d.verdict, ("include", "exclude"))
            self.assertEqual(d.provider, "mock")
            self.assertTrue(d.rationale)

    def test_content_unavailable_candidate_is_excluded_not_guessed(self):
        decision = self.provider.decide(self.candidates["KN-047"])
        self.assertEqual(decision.verdict, "exclude")
        self.assertIn("unavailable", decision.rationale.lower())


class TestLiveProvidersRefuseWithoutConfig(unittest.TestCase):
    """These must never attempt a network call in this test suite -- only verify
    that the safety gate (missing API key) fires before any request is made."""

    def test_gpt_provider_raises_without_api_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            provider = GPTProvider(api_key=None)
            candidate = load_bc_0101_candidates()[0]
            with self.assertRaises(ProviderNotConfigured):
                provider.decide(candidate)

    def test_jev_provider_raises_without_api_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            provider = JevProvider(api_key=None)
            candidate = load_bc_0101_candidates()[0]
            with self.assertRaises(ProviderNotConfigured):
                provider.decide(candidate)

    def test_gpt_provider_reads_key_from_openrouter_env_var(self):
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test-not-real"}, clear=True):
            provider = GPTProvider()
            self.assertEqual(provider._api_key, "sk-or-test-not-real")

    def test_jev_provider_reads_key_from_openrouter_env_var(self):
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test-not-real"}, clear=True):
            provider = JevProvider()
            self.assertEqual(provider._api_key, "sk-or-test-not-real")

    def test_gpt_and_jev_share_the_same_gateway_key_env_var(self):
        from research.jev_context_decision.providers import openrouter

        self.assertEqual(openrouter.API_KEY_ENV_VAR, "OPENROUTER_API_KEY")


if __name__ == "__main__":
    unittest.main()
