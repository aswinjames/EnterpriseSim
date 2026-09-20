"""Tests for the BC-0102 follow-up: a different context-admission criterion
(task-specific necessity) asked under otherwise identical conditions to BC-0101
(same task, candidates, candidate content, ground truth, scorer, models,
provider configuration). No live network access anywhere in this file.

Three things this file exists to verify:
1. BC-0102 actually reaches each provider with the new criterion wording (not
   just a differently-named constant that happens not to be used).
2. BC-0101's own wording, prompt_version, and default behavior are byte-for-byte
   unchanged by the DecisionCase refactor that made BC-0102 possible.
3. The BC-0102 wording itself matches the exact text specified for this
   experiment, and never leaks a ground-truth label (e.g. "KN-101") into the
   decision prompt.
"""

import unittest
from unittest import mock

from research.jev_context_decision.candidates import load_bc_0101_candidates
from research.jev_context_decision.providers import gpt_provider, jev_provider, openai_direct, openrouter
from research.jev_context_decision.providers.base import (
    BC_0101,
    BC_0102,
    DEFAULT_CASE,
    PROMPT_VERSION,
    TASK_STATEMENT,
)
from research.jev_context_decision.providers.gpt_provider import GPTProvider
from research.jev_context_decision.providers.jev_provider import JevProvider
from research.jev_context_decision.providers.mock_provider import MockProvider

_EXACT_BC_0102_QUESTION = (
    "Is this artifact necessary to correctly perform this specific task? "
    "Include it only if omitting it would materially reduce the Worker's "
    "ability to complete the task correctly."
)

_GROUND_TRUTH_LABELS_THAT_MUST_NEVER_APPEAR = (
    "must_include", "must_exclude", "acceptable_optional", "ground_truth", "KN-101",
)


def _candidate(candidate_id: str):
    candidates = {c.id: c for c in load_bc_0101_candidates()}
    return candidates[candidate_id]


class TestDefaultCaseIsUnchangedBC0101(unittest.TestCase):
    """The DecisionCase refactor must not alter BC-0101 in any way."""

    def test_default_case_is_bc_0101(self):
        self.assertIs(DEFAULT_CASE, BC_0101)

    def test_backward_compatible_aliases_match_bc_0101_fields(self):
        self.assertEqual(TASK_STATEMENT, BC_0101.task_statement)
        self.assertEqual(PROMPT_VERSION, BC_0101.prompt_version)

    def test_bc_0101_wording_is_byte_for_byte_the_original(self):
        # Pinned exactly as it existed before BC-0102 was introduced -- any
        # future accidental edit to BC-0101's wording will fail this test.
        self.assertEqual(
            BC_0101.task_statement,
            "Task (CHK-1421, APP-003 Checkout Service): implement guest checkout order "
            "placement. Decide, for this ONE candidate artifact only, whether it should be "
            "included in the Worker's working context for this task. Judge it strictly on "
            "its own content and relevance to guest checkout order placement -- do not "
            "assume information about any other candidate.",
        )
        self.assertEqual(BC_0101.prompt_version, "jev-gpt-openrouter-context-decision-v2")

    def test_gpt_default_request_uses_bc_0101_wording(self):
        candidate = _candidate("KN-045")
        body = gpt_provider._build_request(candidate, DEFAULT_CASE, "gpt-5-mini")
        self.assertIn(BC_0101.task_statement, body["messages"][0]["content"])

    def test_jev_default_request_uses_bc_0101_wording(self):
        candidate = _candidate("KN-045")
        body = jev_provider._build_request(candidate, DEFAULT_CASE, "typesafe/jev-1.13")
        question = body["questions"][jev_provider._QUESTION_KEY]
        self.assertEqual(question["instructions"], BC_0101.jev_instructions)
        self.assertEqual(question["criteria"]["true"], BC_0101.jev_criteria_true)
        self.assertEqual(question["criteria"]["false"], BC_0101.jev_criteria_false)

    def test_provider_decide_defaults_to_bc_0101_prompt_version(self):
        # decide() with no explicit `case` kwarg (the pre-BC-0102 calling
        # convention) must still resolve to BC-0101.
        fake_gpt_response = {
            "model": "gpt-5-mini",
            "choices": [{"message": {"content": '{"verdict": "include", "rationale": "x", "confidence": 0.8}'}}],
            "usage": {},
        }
        with mock.patch.object(openai_direct, "post_json", return_value=fake_gpt_response):
            decision = GPTProvider(api_key="sk-test").decide(_candidate("KN-045"))
        self.assertEqual(decision.prompt_version, BC_0101.prompt_version)


class TestBC0102WordingExact(unittest.TestCase):
    """BC-0102's question text must match the specified wording exactly."""

    def test_task_statement_contains_exact_bc_0102_question(self):
        self.assertIn(_EXACT_BC_0102_QUESTION, BC_0102.task_statement)

    def test_jev_instructions_contain_exact_bc_0102_question(self):
        self.assertIn(_EXACT_BC_0102_QUESTION, BC_0102.jev_instructions)

    def test_bc_0102_id_and_distinct_prompt_version(self):
        self.assertEqual(BC_0102.id, "BC-0102")
        self.assertNotEqual(BC_0102.prompt_version, BC_0101.prompt_version)

    def test_no_ground_truth_label_leaks_into_bc_0102_wording(self):
        combined = " ".join(
            [BC_0102.task_statement, BC_0102.jev_instructions, BC_0102.jev_criteria_true, BC_0102.jev_criteria_false]
        )
        for forbidden in _GROUND_TRUTH_LABELS_THAT_MUST_NEVER_APPEAR:
            self.assertNotIn(forbidden, combined)

    def test_no_ground_truth_label_leaks_into_bc_0101_wording_either(self):
        # Same control applies to BC-0101 -- neither criterion should ever
        # reference ground truth or specific candidate IDs by name.
        combined = " ".join(
            [BC_0101.task_statement, BC_0101.jev_instructions, BC_0101.jev_criteria_true, BC_0101.jev_criteria_false]
        )
        for forbidden in _GROUND_TRUTH_LABELS_THAT_MUST_NEVER_APPEAR:
            self.assertNotIn(forbidden, combined)


class TestBC0102ReachesEachProvider(unittest.TestCase):
    """BC-0102 must actually change what each provider is asked, not just exist
    as an unused constant."""

    def test_gpt_request_differs_between_bc_0101_and_bc_0102(self):
        candidate = _candidate("KN-045")
        body_0101 = gpt_provider._build_request(candidate, BC_0101, "gpt-5-mini")
        body_0102 = gpt_provider._build_request(candidate, BC_0102, "gpt-5-mini")
        self.assertNotEqual(body_0101["messages"][0]["content"], body_0102["messages"][0]["content"])
        self.assertIn(_EXACT_BC_0102_QUESTION, body_0102["messages"][0]["content"])
        self.assertNotIn(_EXACT_BC_0102_QUESTION, body_0101["messages"][0]["content"])
        # Everything except the wording is identical: same model, same schema,
        # same token cap, same reasoning effort.
        self.assertEqual(body_0101["model"], body_0102["model"])
        self.assertEqual(body_0101["response_format"], body_0102["response_format"])
        self.assertEqual(body_0101["max_completion_tokens"], body_0102["max_completion_tokens"])
        self.assertEqual(body_0101["reasoning_effort"], body_0102["reasoning_effort"])

    def test_jev_request_differs_between_bc_0101_and_bc_0102(self):
        candidate = _candidate("KN-045")
        body_0101 = jev_provider._build_request(candidate, BC_0101, "typesafe/jev-1.13")
        body_0102 = jev_provider._build_request(candidate, BC_0102, "typesafe/jev-1.13")
        q_0101 = body_0101["questions"][jev_provider._QUESTION_KEY]
        q_0102 = body_0102["questions"][jev_provider._QUESTION_KEY]
        self.assertNotEqual(q_0101["instructions"], q_0102["instructions"])
        self.assertNotEqual(q_0101["criteria"], q_0102["criteria"])
        self.assertEqual(q_0102["instructions"], BC_0102.jev_instructions)
        # Candidate content and identity are identical either way -- only the
        # question changes.
        self.assertEqual(body_0101["state"]["candidate_content"], body_0102["state"]["candidate_content"])
        self.assertEqual(body_0101["state"]["candidate_id"], body_0102["state"]["candidate_id"])
        self.assertEqual(body_0101["model"], body_0102["model"])

    def test_gpt_decide_with_bc_0102_records_bc_0102_prompt_version(self):
        fake_response = {
            "model": "gpt-5-mini",
            "choices": [{"message": {"content": '{"verdict": "exclude", "rationale": "not necessary", "confidence": 0.7}'}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        with mock.patch.object(openai_direct, "post_json", return_value=fake_response) as mock_post:
            decision = GPTProvider(api_key="sk-test").decide(_candidate("KN-101"), case=BC_0102)
        called_body = mock_post.call_args[0][1]
        self.assertIn(_EXACT_BC_0102_QUESTION, called_body["messages"][0]["content"])
        self.assertEqual(decision.prompt_version, BC_0102.prompt_version)

    def test_jev_decide_with_bc_0102_records_bc_0102_prompt_version(self):
        fake_response = {
            "model": "typesafe/jev-1.13",
            "answers": {jev_provider._QUESTION_KEY: {"type": "noul", "noul": 0.3}},
            "usage": {},
        }
        with mock.patch.object(openrouter, "post_json", return_value=fake_response) as mock_post:
            decision = JevProvider(api_key="sk-test").decide(_candidate("KN-101"), case=BC_0102)
        called_body = mock_post.call_args[0][1]
        question = called_body["questions"][jev_provider._QUESTION_KEY]
        self.assertEqual(question["instructions"], BC_0102.jev_instructions)
        self.assertEqual(decision.prompt_version, BC_0102.prompt_version)

    def test_mock_provider_records_requested_case_prompt_version(self):
        # MockProvider's heuristic doesn't read case content, but it must still
        # correctly report which criterion it was run under.
        decision_0101 = MockProvider().decide(_candidate("KN-045"), case=BC_0101)
        decision_0102 = MockProvider().decide(_candidate("KN-045"), case=BC_0102)
        self.assertEqual(decision_0101.prompt_version, BC_0101.prompt_version)
        self.assertEqual(decision_0102.prompt_version, BC_0102.prompt_version)


class TestRunExperimentCriterionSelection(unittest.TestCase):
    """The CLI's --criterion flag must select the matching DecisionCase and
    leave the default (bc-0101) path completely unaffected."""

    def test_criteria_registry_maps_expected_ids(self):
        from research.jev_context_decision.run_experiment import CRITERIA

        self.assertEqual(CRITERIA["bc-0101"], BC_0101)
        self.assertEqual(CRITERIA["bc-0102"], BC_0102)

    def test_offline_dry_run_with_bc_0102_criterion(self):
        import json
        import tempfile
        from pathlib import Path

        from research.jev_context_decision.run_experiment import main

        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "bc0102_mock.json"
            exit_code = main(
                ["--provider", "mock", "--repeats", "1", "--criterion", "bc-0102", "--out", str(out_path)]
            )
            self.assertEqual(exit_code, 0)
            data = json.loads(out_path.read_text())
            self.assertEqual(data["criterion_id"], "BC-0102")
            self.assertEqual(data["case_id"], "BC-0101")  # same underlying benchmark case
            self.assertEqual(data["repeats"][0]["criterion_id"], "BC-0102")
            self.assertEqual(data["repeats"][0]["prompt_version"], BC_0102.prompt_version)

    def test_offline_dry_run_default_criterion_unchanged(self):
        import json
        import tempfile
        from pathlib import Path

        from research.jev_context_decision.run_experiment import main

        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "bc0101_mock.json"
            exit_code = main(["--provider", "mock", "--repeats", "1", "--out", str(out_path)])
            self.assertEqual(exit_code, 0)
            data = json.loads(out_path.read_text())
            self.assertEqual(data["criterion_id"], "BC-0101")
            self.assertEqual(data["repeats"][0]["prompt_version"], BC_0101.prompt_version)


if __name__ == "__main__":
    unittest.main()
