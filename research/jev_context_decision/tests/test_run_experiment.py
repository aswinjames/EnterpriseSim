import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from research.jev_context_decision import run_experiment
from research.jev_context_decision.providers.base import ContextDecisionProvider
from research.jev_context_decision.providers.mock_provider import MockProvider
from research.jev_context_decision.run_experiment import main


class _FailsOnSecondRepeatProvider(ContextDecisionProvider):
    """Behaves like MockProvider on its first full pass, then blows up entirely
    on the second repeat -- simulates a live batch crashing partway through
    (e.g. the real GPT truncation failure), to verify completed repeats are
    not lost."""

    name = "flaky"

    def __init__(self) -> None:
        self._delegate = MockProvider()
        self._repeats_started = 0
        self._candidates_seen_this_repeat = 0

    def decide(self, candidate, *, task_statement=None):
        # A "repeat" is 7 decide() calls; fail partway through the second one.
        self._candidates_seen_this_repeat += 1
        if self._candidates_seen_this_repeat == 1:
            self._repeats_started += 1
        if self._repeats_started == 2 and self._candidates_seen_this_repeat == 3:
            raise RuntimeError("simulated mid-batch failure")
        if self._candidates_seen_this_repeat == 7:
            self._candidates_seen_this_repeat = 0
        return self._delegate.decide(candidate)


class TestRunExperimentCLI(unittest.TestCase):
    def test_mock_dry_run_writes_well_formed_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "mock_result.json"
            exit_code = main(["--provider", "mock", "--repeats", "2", "--out", str(out_path)])
            self.assertEqual(exit_code, 0)

            data = json.loads(out_path.read_text())
            self.assertEqual(data["provider"], "mock")
            self.assertEqual(data["case_id"], "BC-0101")
            self.assertEqual(len(data["repeats"]), 2)
            self.assertEqual(data["summary"]["n_repeats"], 2)

            for repeat in data["repeats"]:
                for field in (
                    "timestamp", "provider", "model", "prompt_version", "selected",
                    "required_present", "required_missing", "forbidden_selected",
                    "recall", "precision", "score", "verdict", "latency_ms",
                    "tokens", "confidence", "raw_decisions",
                ):
                    self.assertIn(field, repeat)
                self.assertEqual(len(repeat["raw_decisions"]), 7)

    def test_live_provider_without_flag_is_refused(self):
        exit_code = main(["--provider", "gpt", "--repeats", "1"])
        self.assertEqual(exit_code, 2)

    def test_live_provider_without_key_fails_cleanly(self):
        import os
        from unittest import mock as umock

        with umock.patch.dict(os.environ, {}, clear=True):
            exit_code = main(["--provider", "gpt", "--repeats", "1", "--live"])
        self.assertEqual(exit_code, 3)

    def test_mid_batch_failure_preserves_already_completed_repeats(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "flaky_result.json"
            with mock.patch.dict(run_experiment.PROVIDERS, {"flaky": _FailsOnSecondRepeatProvider}):
                with self.assertRaises(RuntimeError):
                    main(["--provider", "flaky", "--repeats", "3", "--out", str(out_path)])

            self.assertTrue(out_path.exists(), "partial results must be written before the crash propagates")
            data = json.loads(out_path.read_text())
            self.assertEqual(len(data["repeats"]), 1, "only the fully-completed first repeat should be preserved")
            self.assertFalse(data["complete"])
            self.assertEqual(len(data["repeats"][0]["raw_decisions"]), 7)


if __name__ == "__main__":
    unittest.main()
