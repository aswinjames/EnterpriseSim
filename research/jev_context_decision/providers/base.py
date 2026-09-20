"""Provider-independent contract for making one INCLUDE/EXCLUDE decision.

Both concrete providers (``jev_provider.JevProvider``, ``gpt_provider.GPTProvider``)
and the offline ``mock_provider.MockProvider`` implement this. The runner and tests
only depend on this interface, never on a specific provider's SDK.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..candidates import Candidate
from ..decision import ContextDecision

#: Shared task framing given to every provider for every candidate. Kept identical
#: across providers and repeats so the only variable under test is the provider's
#: own INCLUDE/EXCLUDE judgment, not a difference in how the task was described.
TASK_STATEMENT = (
    "Task (CHK-1421, APP-003 Checkout Service): implement guest checkout order "
    "placement. Decide, for this ONE candidate artifact only, whether it should be "
    "included in the Worker's working context for this task. Judge it strictly on "
    "its own content and relevance to guest checkout order placement -- do not "
    "assume information about any other candidate."
)

#: Version tag for TASK_STATEMENT + the provider-specific prompt wrapper around it.
#: Bump this whenever the wording changes, so captured results stay attributable
#: to an exact prompt version. v2: both providers moved to OpenRouter as the one
#: gateway (pinned typesafe/jev-1.13 via the Decisions API; pinned openai/gpt-5-mini
#: via chat completions), replacing the unverified native noul client and the
#: direct OpenAI SDK call.
PROMPT_VERSION = "jev-gpt-openrouter-context-decision-v2"


class ContextDecisionProvider(ABC):
    """Makes one independent INCLUDE/EXCLUDE decision for one candidate artifact."""

    name: str

    @abstractmethod
    def decide(self, candidate: Candidate, *, task_statement: str = TASK_STATEMENT) -> ContextDecision:
        """Return a single ContextDecision for ``candidate``.

        Implementations must not consult or mutate any other candidate's state --
        BC-0101's seven candidates are decided independently, by design.
        """
        raise NotImplementedError

    def decide_all(self, candidates: list[Candidate]) -> list[ContextDecision]:
        """Convenience: decide each candidate in turn (still independently)."""
        return [self.decide(c) for c in candidates]


class ProviderNotConfigured(RuntimeError):
    """Raised when a live provider is asked to decide without required setup.

    Distinguishes "you forgot to set an API key" from a real decision failure so
    the runner can fail fast and loudly instead of silently falling back.
    """
