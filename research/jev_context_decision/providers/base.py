"""Provider-independent contract for making one INCLUDE/EXCLUDE decision.

Both concrete providers (``jev_provider.JevProvider``, ``gpt_provider.GPTProvider``)
and the offline ``mock_provider.MockProvider`` implement this. The runner and tests
only depend on this interface, never on a specific provider's SDK.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..candidates import Candidate, load_bc_0101_case
from ..decision import ContextDecision
from ..task_scope import TaskScope

#: Derived once, read-only, from the frozen benchmark case -- the same
#: TaskScope is attached to both BC_0101 and BC_0102 below, since both run
#: against the identical underlying task (CHK-1421). See task_scope.py for
#: what this does and does not contain.
_CHK_1421_SCOPE = TaskScope.from_benchmark_case(load_bc_0101_case())


@dataclass(frozen=True)
class DecisionCase:
    """One fully-specified context-admission criterion.

    BC-0101 and BC-0102 are identical in every other respect (task, candidates,
    candidate content, ground truth, scorer, models, provider configuration,
    structured output shape) -- the only thing a ``DecisionCase`` varies is the
    wording of the question asked of every provider for every candidate.

    Two fields exist per provider family because GPT and Jev structurally split
    "the question" differently: GPT gets one flat prompt, so ``task_statement``
    alone fully specifies it. Jev's Decisions API separates a question's
    ``instructions`` and per-choice ``criteria`` from the ``state`` payload, so
    the same criterion has to be expressed in those three parts independently
    to have Jev actually asking the intended question rather than only seeing
    it echoed back in ``state``.

    ``task_scope`` is a separate concept from ``task_statement``: the latter
    is free-text prompt wording that already existed and is sent to providers
    exactly as before; ``task_scope`` is new, structured data (see
    ``task_scope.py``) that is NOT threaded into any live BC-0101/BC-0102
    request -- ``gpt_provider.py``/``jev_provider.py`` build their requests
    from ``task_statement``/``jev_instructions``/``jev_criteria_*`` only, so
    adding this field changes nothing about what was previously sent over the
    wire for either case. It exists so a future ``DecisionCase`` (a new
    criterion, not BC-0101 or BC-0102) could choose to have its provider
    reference ``case.task_scope`` when building a prompt, without requiring
    any change to the ``decide(candidate, case=...)`` interface.
    """

    id: str
    prompt_version: str
    task_statement: str
    jev_instructions: str
    jev_criteria_true: str
    jev_criteria_false: str
    task_scope: TaskScope


#: BC-0101's criterion: broad relevance/inclusion. Wording unchanged from the
#: original (pre-BC-0102) implementation.
BC_0101 = DecisionCase(
    id="BC-0101",
    prompt_version="jev-gpt-openrouter-context-decision-v2",
    task_statement=(
        "Task (CHK-1421, APP-003 Checkout Service): implement guest checkout order "
        "placement. Decide, for this ONE candidate artifact only, whether it should be "
        "included in the Worker's working context for this task. Judge it strictly on "
        "its own content and relevance to guest checkout order placement -- do not "
        "assume information about any other candidate."
    ),
    jev_instructions=(
        "Should this ONE candidate artifact be included in the Worker's "
        "working context for this task? Judge it strictly on its own "
        "content -- do not assume information about any other candidate."
    ),
    jev_criteria_true=(
        "This candidate artifact should be included in the Worker's working context "
        "for this task: its content is relevant to guest checkout order placement "
        "(CHK-1421, APP-003) and materially helps complete it correctly."
    ),
    jev_criteria_false=(
        "This candidate artifact should be excluded from the Worker's working context "
        "for this task: it is out of scope, a distractor, or its content is not "
        "resolvable/available to judge."
    ),
    task_scope=_CHK_1421_SCOPE,
)

#: BC-0102's criterion: task-specific necessity, not broad relevance. Question
#: wording is used verbatim as specified for this experiment; no ground-truth
#: labels or specific candidate IDs (e.g. KN-101) are referenced anywhere in it.
BC_0102 = DecisionCase(
    id="BC-0102",
    prompt_version="jev-gpt-openrouter-context-decision-bc0102-v1",
    task_statement=(
        "Task (CHK-1421, APP-003 Checkout Service): implement guest checkout order "
        "placement. Is this artifact necessary to correctly perform this specific "
        "task? Include it only if omitting it would materially reduce the Worker's "
        "ability to complete the task correctly. Judge this ONE candidate artifact "
        "strictly on its own content -- do not assume information about any other "
        "candidate."
    ),
    jev_instructions=(
        "Is this artifact necessary to correctly perform this specific task? "
        "Include it only if omitting it would materially reduce the Worker's "
        "ability to complete the task correctly. Judge this ONE candidate artifact "
        "strictly on its own content -- do not assume information about any other "
        "candidate."
    ),
    jev_criteria_true=(
        "This candidate artifact is necessary to correctly perform this specific "
        "task: omitting it would materially reduce the Worker's ability to "
        "complete the task correctly."
    ),
    jev_criteria_false=(
        "This candidate artifact is not necessary to correctly perform this "
        "specific task: omitting it would not materially reduce the Worker's "
        "ability to complete the task correctly."
    ),
    task_scope=_CHK_1421_SCOPE,
)

#: The default criterion, used whenever a caller doesn't specify one. This is
#: BC-0101's criterion -- identical behavior to before ``DecisionCase`` existed.
DEFAULT_CASE = BC_0101

#: Backward-compatible aliases for the pre-BC-0102 module-level constants. Their
#: values are unchanged; new code should prefer ``BC_0101.task_statement`` /
#: ``BC_0101.prompt_version`` directly.
TASK_STATEMENT = BC_0101.task_statement
PROMPT_VERSION = BC_0101.prompt_version


class ContextDecisionProvider(ABC):
    """Makes one independent INCLUDE/EXCLUDE decision for one candidate artifact."""

    name: str

    @abstractmethod
    def decide(self, candidate: Candidate, *, case: DecisionCase = DEFAULT_CASE) -> ContextDecision:
        """Return a single ContextDecision for ``candidate`` under ``case``'s criterion.

        Implementations must not consult or mutate any other candidate's state --
        each candidate is decided independently, by design.
        """
        raise NotImplementedError

    def decide_all(self, candidates: list[Candidate], *, case: DecisionCase = DEFAULT_CASE) -> list[ContextDecision]:
        """Convenience: decide each candidate in turn (still independently)."""
        return [self.decide(c, case=case) for c in candidates]


class ProviderNotConfigured(RuntimeError):
    """Raised when a live provider is asked to decide without required setup.

    Distinguishes "you forgot to set an API key" from a real decision failure so
    the runner can fail fast and loudly instead of silently falling back.
    """
