"""Tests for the TaskScope abstraction (research/jev_context_decision/task_scope.py).

Covers, per the task-scope infrastructure change:
1. TaskScope for CHK-1421 is correctly derived from the existing benchmark source.
2. It contains the expected task_id/title/description/apps/code_target.
3. BC-0101 remains unchanged by the addition.
4. BC-0102 remains unchanged by the addition.
5. No candidate-specific decision is encoded in task scope.
6. KN-101 is not special-cased by the abstraction.
7. KN-063 is not special-cased by the abstraction.

No live network access anywhere in this file.
"""

import unittest

from research.jev_context_decision.candidates import load_bc_0101_case
from research.jev_context_decision.providers.base import BC_0101, BC_0102
from research.jev_context_decision.task_scope import TaskScope

_ALL_CANDIDATE_IDS = ("KN-045", "KN-052", "KN-063", "KN-047", "KN-101", "EXP-090", "EXP-055")

# Ground-truth schema identifiers that must never leak into a purely
# descriptive scope object. Deliberately narrow (snake_case schema field
# names only) -- ordinary English words like "excludes" legitimately appear
# in the task description's own prose ("...surfaces the decisive facts and
# excludes distractors...") without encoding any candidate-specific decision.
_DECISION_VOCABULARY = (
    "must_include", "must_exclude", "acceptable_optional", "ground_truth",
)


class TestTaskScopeDerivation(unittest.TestCase):
    """Requirement 1 & 2: correctly derived, contains the expected fields."""

    def setUp(self):
        self.case = load_bc_0101_case()
        self.scope = TaskScope.from_benchmark_case(self.case)

    def test_task_id(self):
        self.assertEqual(self.scope.task_id, "CHK-1421")

    def test_title_contains_expected_text(self):
        self.assertIn("Context assembly for guest checkout", self.scope.title)

    def test_description_contains_expected_text(self):
        self.assertIn(
            "the Worker's Context Layer (ARCH-01) must assemble a working set that "
            "surfaces the decisive facts and excludes distractors, within the model budget.",
            self.scope.description,
        )

    def test_declared_apps(self):
        self.assertEqual(self.scope.declared_apps, ("APP-003", "APP-015", "APP-012"))

    def test_code_target(self):
        self.assertEqual(self.scope.code_target, "mcg-checkout-service/src/checkout/PlaceOrder.java")

    def test_trigger_type_reuses_existing_field_not_invented(self):
        # Not part of the explicit requirement list, but documents where this
        # optional field comes from: inputs.trigger.type, verbatim.
        self.assertEqual(self.scope.trigger_type, self.case["inputs"]["trigger"]["type"])

    def test_task_scope_is_frozen(self):
        with self.assertRaises(Exception):
            self.scope.task_id = "CHANGED"  # type: ignore[misc]


class TestBC0101UnchangedByTaskScope(unittest.TestCase):
    """Requirement 3: BC-0101 remains unchanged."""

    def test_task_statement_byte_for_byte(self):
        self.assertEqual(
            BC_0101.task_statement,
            "Task (CHK-1421, APP-003 Checkout Service): implement guest checkout order "
            "placement. Decide, for this ONE candidate artifact only, whether it should be "
            "included in the Worker's working context for this task. Judge it strictly on "
            "its own content and relevance to guest checkout order placement -- do not "
            "assume information about any other candidate.",
        )

    def test_prompt_version_unchanged(self):
        self.assertEqual(BC_0101.prompt_version, "jev-gpt-openrouter-context-decision-v2")

    def test_jev_wording_unchanged(self):
        self.assertEqual(
            BC_0101.jev_criteria_true,
            "This candidate artifact should be included in the Worker's working context "
            "for this task: its content is relevant to guest checkout order placement "
            "(CHK-1421, APP-003) and materially helps complete it correctly.",
        )

    def test_has_task_scope_attached(self):
        self.assertIsInstance(BC_0101.task_scope, TaskScope)
        self.assertEqual(BC_0101.task_scope.task_id, "CHK-1421")


class TestBC0102UnchangedByTaskScope(unittest.TestCase):
    """Requirement 4: BC-0102 remains unchanged."""

    def test_task_statement_byte_for_byte(self):
        self.assertEqual(
            BC_0102.task_statement,
            "Task (CHK-1421, APP-003 Checkout Service): implement guest checkout order "
            "placement. Is this artifact necessary to correctly perform this specific "
            "task? Include it only if omitting it would materially reduce the Worker's "
            "ability to complete the task correctly. Judge this ONE candidate artifact "
            "strictly on its own content -- do not assume information about any other "
            "candidate.",
        )

    def test_prompt_version_unchanged(self):
        self.assertEqual(BC_0102.prompt_version, "jev-gpt-openrouter-context-decision-bc0102-v1")

    def test_has_task_scope_attached(self):
        self.assertIsInstance(BC_0102.task_scope, TaskScope)

    def test_bc_0101_and_bc_0102_share_identical_task_scope(self):
        # Same underlying task (CHK-1421) -- the criterion differs, the scope does not.
        self.assertEqual(BC_0101.task_scope, BC_0102.task_scope)


class TestTaskScopeNeverThreadedIntoLivePrompts(unittest.TestCase):
    """The historical experiment inputs must remain byte-for-byte equivalent:
    task_scope must not appear anywhere in what's actually sent to a provider."""

    def _candidate(self):
        from research.jev_context_decision.candidates import load_bc_0101_candidates

        return load_bc_0101_candidates()[0]

    def test_gpt_request_does_not_reference_task_scope(self):
        from research.jev_context_decision.providers import gpt_provider

        body = gpt_provider._build_request(self._candidate(), BC_0101, "gpt-5-mini")
        self.assertNotIn("task_scope", body)
        self.assertNotIn("declared_apps", str(body))

    def test_jev_request_does_not_reference_task_scope(self):
        from research.jev_context_decision.providers import jev_provider

        body = jev_provider._build_request(self._candidate(), BC_0101, "typesafe/jev-1.13")
        self.assertNotIn("task_scope", body)
        self.assertNotIn("declared_apps", str(body))


class TestNoCandidateSpecificDecisionInTaskScope(unittest.TestCase):
    """Requirements 5, 6, 7: task scope carries no candidate-specific
    information and has no mechanism to special-case any candidate."""

    def setUp(self):
        self.scope = BC_0101.task_scope

    def test_no_candidate_id_appears_anywhere_in_scope_values(self):
        combined = " ".join(
            str(v) for v in (
                self.scope.task_id, self.scope.title, self.scope.description,
                self.scope.code_target, self.scope.trigger_type,
            )
        ) + " ".join(self.scope.declared_apps)
        for candidate_id in _ALL_CANDIDATE_IDS:
            self.assertNotIn(candidate_id, combined)

    def test_kn101_app_not_referenced_and_not_special_cased(self):
        # KN-101 belongs to APP-007; APP-007 is correctly absent from
        # declared_apps (it's genuinely not one of the task's apps) -- but
        # this must be a neutral fact about the task, not a rule that names
        # or targets KN-101 specifically.
        self.assertNotIn("APP-007", self.scope.declared_apps)
        self.assertNotIn("KN-101", str(self.scope))

    def test_kn063_app_absence_does_not_imply_exclusion_rule(self):
        # KN-063 belongs to APP-008, also absent from declared_apps -- exactly
        # like KN-101. TaskScope must not encode "apps outside declared_apps
        # are excluded" as a rule (that would incorrectly target KN-063, which
        # is acceptable_optional, not excluded). Verified structurally: the
        # dataclass has no method that maps an app or candidate to a verdict.
        self.assertNotIn("APP-008", self.scope.declared_apps)
        self.assertNotIn("KN-063", str(self.scope))

    def test_task_scope_has_no_decision_or_filtering_methods(self):
        # Architectural guarantee: TaskScope is pure data. It cannot compute
        # in/out-of-scope verdicts for any app or candidate, so it cannot be
        # used to special-case KN-101, KN-063, or anything else.
        forbidden_substrings = (
            "include", "exclude", "relevant", "necessary", "decide", "should",
            "verdict", "filter", "score",
        )
        public_attrs = [a for a in dir(TaskScope) if not a.startswith("_")]
        # from_benchmark_case is the only public method; it's a constructor,
        # not a decision function, and is exempted by name here.
        public_attrs = [a for a in public_attrs if a != "from_benchmark_case"]
        for attr in public_attrs:
            for bad in forbidden_substrings:
                self.assertNotIn(
                    bad, attr.lower(),
                    f"TaskScope must not encode decision logic; found suspicious attribute: {attr}",
                )

    def test_ground_truth_and_decision_vocabulary_absent_from_scope_text(self):
        combined = f"{self.scope.title} {self.scope.description}".lower()
        for word in _DECISION_VOCABULARY:
            self.assertNotIn(word, combined)


if __name__ == "__main__":
    unittest.main()
