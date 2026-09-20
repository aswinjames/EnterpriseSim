"""Explicit representation of TASK SCOPE for the Context Layer.

This is deliberately one of five concepts this codebase keeps separate (see
``research/jev_context_decision/README.md`` for the full explanation):

1. ARTIFACT CONTENT    -- what a candidate actually says (``candidates.py``)
2. ARTIFACT METADATA   -- app/type/id/title/relationships (``Candidate.raw``)
3. TASK SCOPE          -- what the task explicitly declares (this module)
4. DECISION CRITERION  -- why to include/exclude an artifact (``providers/base.py::DecisionCase``)
5. GROUND TRUTH        -- the benchmark's expected answer (``benchmark_case["ground_truth"]``)

``TaskScope`` exists so a future decision provider can be handed explicit,
structured information about the task's boundaries (which apps are declared in
scope, what the task is titled/described as, what code it targets) instead of
inferring that only from candidate title/body text. It is derived, read-only,
from fields that already exist on the frozen benchmark case -- no new
enterprise metadata is invented here.

Critically, ``TaskScope`` carries no decision logic and no candidate-specific
information whatsoever. It does not know that ``KN-101`` exists, does not know
``KN-101`` is ``must_exclude``, and does not encode a rule like "exclude every
artifact from an app not in declared_apps" (such a rule would incorrectly
exclude ``KN-063``, which belongs to APP-008 but is `acceptable_optional`
precisely because it explicitly touches the declared task). ``TaskScope`` is
pure data about the task; what a provider does with it is out of scope for
this module entirely, and nothing in this codebase currently threads it into
any live BC-0101/BC-0102 prompt (see ``providers/base.py::DecisionCase.task_scope``
docstring for why that's true today and how it could change in a future,
separately-versioned experiment).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskScope:
    """What a task explicitly declares about itself, and nothing more.

    Every field here is copied verbatim from the frozen benchmark case (see
    ``from_benchmark_case``) -- this class does not compute, infer, or rank
    anything about any candidate artifact.
    """

    task_id: str
    title: str
    description: str
    declared_apps: tuple[str, ...]
    code_target: str | None = None
    trigger_type: str | None = None

    @classmethod
    def from_benchmark_case(cls, case: dict) -> "TaskScope":
        """Derive a TaskScope from a loaded benchmark case dict, read-only.

        Reuses existing top-level case fields only: ``task_ref``, ``title``,
        ``description``, ``apps``, the first entry of
        ``ground_truth.expected.code`` (there is currently exactly one), and
        ``inputs.trigger.type`` (the closest existing analogue to a
        "task_type" field -- the benchmark schema has no dedicated
        ``task_type``/``task_domain`` field, so none is invented here; see
        the module docstring in ``research/jev_context_decision/README.md``
        for why ``trigger_type`` is named for what it actually is rather than
        overclaiming a general task-type taxonomy).

        Never reads ``ground_truth.must_include``/``must_exclude``/
        ``acceptable_optional`` or any candidate ID -- this constructor has no
        access to candidate-specific ground truth by construction, not just
        by convention.
        """
        expected_code = case.get("ground_truth", {}).get("expected", {}).get("code") or []
        return cls(
            task_id=case["task_ref"],
            title=case["title"],
            description=case["description"],
            declared_apps=tuple(case["apps"]),
            code_target=expected_code[0] if expected_code else None,
            trigger_type=case.get("inputs", {}).get("trigger", {}).get("type"),
        )
