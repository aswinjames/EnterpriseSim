"""Tests for direct-OpenAI (GPT) and OpenRouter (Jev) request construction/parsing.

These never touch the network: the pure ``_build_request``/``_parse_response``
functions are tested directly against literal fixture payloads (the GPT fixture
mirrors the direct OpenAI chat-completions response shape; the Jev fixture
mirrors the exact example response documented for OpenRouter's alpha Decisions
API), and ``decide()`` end-to-end is tested by monkeypatching each provider's
own transport module's ``post_json`` to a fake that asserts on the outgoing
request and returns a canned response.
"""

import unittest
from unittest import mock

from research.jev_context_decision.candidates import load_bc_0101_candidates
from research.jev_context_decision.providers import gpt_provider, jev_provider, openai_direct, openrouter
from research.jev_context_decision.providers.base import BC_0101, PROMPT_VERSION


def _candidate(candidate_id: str):
    candidates = {c.id: c for c in load_bc_0101_candidates()}
    return candidates[candidate_id]


class TestOpenRouterModule(unittest.TestCase):
    def test_endpoints_and_env_var(self):
        self.assertEqual(openrouter.CHAT_COMPLETIONS_PATH, "/api/v1/chat/completions")
        self.assertEqual(openrouter.DECISIONS_PATH, "/api/alpha/decisions")
        self.assertEqual(openrouter.API_KEY_ENV_VAR, "OPENROUTER_API_KEY")
        self.assertEqual(openrouter.OPENROUTER_BASE, "https://openrouter.ai")

    def test_post_json_sends_bearer_auth_and_raises_on_http_error(self):
        import json
        import urllib.error

        captured = {}

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return json.dumps({"ok": True}).encode("utf-8")

        def fake_urlopen(request, timeout=None):
            captured["url"] = request.full_url
            captured["headers"] = {k.lower(): v for k, v in request.headers.items()}
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse()

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            result = openrouter.post_json("/api/v1/chat/completions", {"a": 1}, "sk-test")

        self.assertEqual(result, {"ok": True})
        self.assertEqual(captured["url"], "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(captured["headers"]["authorization"], "Bearer sk-test")
        self.assertEqual(captured["body"], {"a": 1})

        def raise_http_error(request, timeout=None):
            import io

            raise urllib.error.HTTPError(
                request.full_url, 401, "unauthorized", {}, io.BytesIO(b'{"error": "bad key"}')
            )

        with mock.patch("urllib.request.urlopen", raise_http_error):
            with self.assertRaises(openrouter.OpenRouterError):
                openrouter.post_json("/api/v1/chat/completions", {"a": 1}, "sk-bad")


class TestGPTProviderDirectOpenAI(unittest.TestCase):
    def test_default_model_is_gpt_5_mini(self):
        self.assertEqual(gpt_provider.DEFAULT_MODEL, "gpt-5-mini")

    def test_build_request_shape(self):
        candidate = _candidate("KN-045")
        body = gpt_provider._build_request(candidate, BC_0101, "gpt-5-mini")
        self.assertEqual(body["model"], "gpt-5-mini")
        self.assertEqual(body["response_format"]["type"], "json_schema")
        self.assertEqual(body["response_format"]["json_schema"]["name"], "context_decision")
        self.assertIn(candidate.body, body["messages"][0]["content"])
        self.assertIn("KN-045", body["messages"][0]["content"])
        # Direct OpenAI's Chat Completions API rejects max_tokens for reasoning
        # models -- must be max_completion_tokens instead (same value).
        self.assertEqual(body["max_completion_tokens"], gpt_provider.MAX_OUTPUT_TOKENS)
        self.assertNotIn("max_tokens", body)
        self.assertLess(body["max_completion_tokens"], 65536, "must not leave the cap unset/unbounded")
        # Flat reasoning_effort, not OpenRouter's nested reasoning:{"effort":...}.
        self.assertEqual(body["reasoning_effort"], gpt_provider.REASONING_EFFORT)
        self.assertNotIn("reasoning", body)

    def test_parse_response_raises_clear_error_on_truncation(self):
        # A reasoning model can spend part of the token budget on hidden
        # reasoning and cut off the JSON mid-string; this must surface as an
        # actionable error, not an opaque JSONDecodeError (reproduces a real
        # live-call failure seen against OpenRouter; finish_reason=="length"
        # is OpenAI's own field name, unchanged on the direct API).
        raw = {
            "model": "gpt-5-mini",
            "choices": [{"finish_reason": "length", "message": {"content": '{"verdict": "incl'}}],
            "usage": {"prompt_tokens": 500, "completion_tokens": 400},
        }
        with self.assertRaisesRegex(RuntimeError, "truncated"):
            gpt_provider._parse_response(raw)

    def test_parse_response_extracts_normalized_fields(self):
        raw = {
            "model": "gpt-5-mini",
            "choices": [
                {"message": {"content": '{"verdict": "include", "rationale": "relevant", "confidence": 0.87}'}}
            ],
            "usage": {"prompt_tokens": 512, "completion_tokens": 24},
        }
        parsed = gpt_provider._parse_response(raw)
        self.assertEqual(parsed["verdict"], "include")
        self.assertEqual(parsed["rationale"], "relevant")
        self.assertAlmostEqual(parsed["confidence"], 0.87)
        self.assertEqual(parsed["model"], "gpt-5-mini")
        self.assertEqual(parsed["input_tokens"], 512)
        self.assertEqual(parsed["output_tokens"], 24)
        # Direct OpenAI responses have no usage.cost field (that's an
        # OpenRouter-only addition) -- must come back as None, not KeyError.
        self.assertIsNone(parsed["cost_usd"])

    def test_decide_end_to_end_with_mocked_transport(self):
        candidate = _candidate("KN-101")
        fake_response = {
            "model": "gpt-5-mini",
            "choices": [
                {"message": {"content": '{"verdict": "exclude", "rationale": "out of scope", "confidence": 0.9}'}}
            ],
            "usage": {"prompt_tokens": 300, "completion_tokens": 15},
        }
        with mock.patch.object(openai_direct, "post_json", return_value=fake_response) as mock_post:
            provider = gpt_provider.GPTProvider(api_key="sk-test")
            decision = provider.decide(candidate)

        mock_post.assert_called_once()
        called_path, called_body, called_key = mock_post.call_args[0]
        self.assertEqual(called_path, openai_direct.CHAT_COMPLETIONS_PATH)
        self.assertEqual(called_body["model"], gpt_provider.DEFAULT_MODEL)
        self.assertEqual(called_key, "sk-test")

        self.assertEqual(decision.candidate_id, "KN-101")
        self.assertEqual(decision.verdict, "exclude")
        self.assertEqual(decision.provider, "gpt")
        self.assertEqual(decision.prompt_version, PROMPT_VERSION)
        self.assertEqual(decision.input_tokens, 300)
        self.assertIsNone(decision.cost_usd)

    def test_decide_never_touches_openrouter(self):
        # Regression guard for the exact bug this migration risked: GPTProvider
        # must not call OpenRouter's transport at all after the swap.
        candidate = _candidate("KN-045")
        fake_response = {
            "model": "gpt-5-mini",
            "choices": [{"message": {"content": '{"verdict": "include", "rationale": "x", "confidence": 0.6}'}}],
            "usage": {},
        }
        with mock.patch.object(openai_direct, "post_json", return_value=fake_response):
            with mock.patch.object(openrouter, "post_json") as mock_openrouter_post:
                gpt_provider.GPTProvider(api_key="sk-test").decide(candidate)
        mock_openrouter_post.assert_not_called()


class TestJevProviderOpenRouter(unittest.TestCase):
    def test_default_model_is_pinned_typesafe_slug(self):
        self.assertEqual(jev_provider.DEFAULT_MODEL, "typesafe/jev-1.13")

    def test_build_request_uses_noul_question_type(self):
        candidate = _candidate("EXP-090")
        body = jev_provider._build_request(candidate, BC_0101, "typesafe/jev-1.13")
        self.assertEqual(body["model"], "typesafe/jev-1.13")
        question = body["questions"][jev_provider._QUESTION_KEY]
        self.assertEqual(question["type"], "noul")
        self.assertIn("true", question["criteria"])
        self.assertIn("false", question["criteria"])
        self.assertEqual(body["state"]["candidate_id"], "EXP-090")
        self.assertEqual(body["state"]["candidate_content"], candidate.body)

    def test_parse_response_maps_probability_to_verdict_include(self):
        raw = {
            "model": "typesafe/jev-1.13-20260917",
            "answers": {jev_provider._QUESTION_KEY: {"type": "noul", "noul": 0.93}},
            "usage": {"input_tokens": 120, "output_tokens": 4, "cost": 0.000006},
        }
        parsed = jev_provider._parse_response(raw)
        self.assertEqual(parsed["verdict"], "include")
        self.assertAlmostEqual(parsed["confidence"], 0.93)
        self.assertEqual(parsed["model"], "typesafe/jev-1.13-20260917")
        self.assertEqual(parsed["input_tokens"], 120)

    def test_parse_response_maps_probability_to_verdict_exclude(self):
        raw = {
            "model": "typesafe/jev-1.13",
            "answers": {jev_provider._QUESTION_KEY: {"type": "noul", "noul": 0.08}},
            "usage": {"input_tokens": 100, "output_tokens": 4, "cost": 0.000005},
        }
        parsed = jev_provider._parse_response(raw)
        self.assertEqual(parsed["verdict"], "exclude")
        self.assertAlmostEqual(parsed["confidence"], 0.92)  # 1 - 0.08

    def test_parse_response_boundary_at_one_half_is_include(self):
        raw = {"model": "typesafe/jev-1.13", "answers": {jev_provider._QUESTION_KEY: {"type": "noul", "noul": 0.5}}}
        parsed = jev_provider._parse_response(raw)
        self.assertEqual(parsed["verdict"], "include")
        self.assertAlmostEqual(parsed["confidence"], 0.5)

    def test_decide_end_to_end_with_mocked_transport(self):
        candidate = _candidate("KN-047")
        fake_response = {
            "id": "gen-dec-test",
            "model": "typesafe/jev-1.13-20260917",
            "provider": "TypeSafe",
            "answers": {jev_provider._QUESTION_KEY: {"type": "noul", "noul": 0.2}},
            "usage": {"input_tokens": 90, "output_tokens": 4, "cost": 0.000004},
        }
        with mock.patch.object(openrouter, "post_json", return_value=fake_response) as mock_post:
            provider = jev_provider.JevProvider(api_key="sk-test")
            decision = provider.decide(candidate)

        mock_post.assert_called_once()
        called_path, called_body, called_key = mock_post.call_args[0]
        self.assertEqual(called_path, openrouter.DECISIONS_PATH)
        self.assertEqual(called_body["model"], jev_provider.DEFAULT_MODEL)
        self.assertEqual(called_key, "sk-test")

        self.assertEqual(decision.candidate_id, "KN-047")
        self.assertEqual(decision.verdict, "exclude")
        self.assertEqual(decision.provider, "jev")
        self.assertEqual(decision.prompt_version, PROMPT_VERSION)
        self.assertAlmostEqual(decision.confidence, 0.8)
        self.assertEqual(decision.model, "typesafe/jev-1.13-20260917")
        self.assertEqual(decision.raw_output, fake_response)


if __name__ == "__main__":
    unittest.main()
