"""Per-candidate INCLUDE/EXCLUDE decision schema and aggregation into a context set.

BC-0101 gives a Worker seven candidates. This experiment asks the *decision* to be
made independently, per candidate, rather than as one "pick the working set" call --
each of the seven gets its own INCLUDE/EXCLUDE judgment, from Jev (native TypeSafe
`noul` schema call) and separately from GPT (structured INCLUDE/EXCLUDE output).
This module defines the common shape both providers produce, and the aggregation
step that turns seven independent decisions into one selected context set.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Literal, Mapping, Sequence

Verdict = Literal["include", "exclude"]


@dataclass(frozen=True)
class ContextDecision:
    """One provider's INCLUDE/EXCLUDE judgment for one candidate artifact.

    This is the common, provider-independent record. Both the Jev provider (native
    `noul` TypeSafe schema) and the GPT provider (structured JSON/tool-call output)
    must normalize into this shape so the aggregator and the capture log never need
    to know which provider produced a given decision.
    """

    candidate_id: str
    candidate_kind: str  # "knowledge" | "experience"
    provider: str  # "jev" | "gpt" | "mock"
    verdict: Verdict
    rationale: str
    confidence: float | None  # None if the provider does not expose one
    model: str
    prompt_version: str
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    timestamp: str = ""  # ISO-8601 UTC, set by the provider at call time
    raw_output: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AggregatedContext:
    """The selected working set assembled from seven independent decisions."""

    included: list[str]
    excluded: list[str]
    decisions: list[ContextDecision]

    def to_context_object(self, task_ref: str = "CHK-1421") -> dict:
        """Render as a minimal ContextObject shape (see sdk/objects.py Protocol),
        compatible with the ``score()`` evaluator's expected input."""
        return {
            "task": {"ref": task_ref},
            "included": [
                {
                    "source": d.candidate_id,
                    "kind": d.candidate_kind,
                    "reason": d.rationale,
                    "score": d.confidence if d.confidence is not None else 0.5,
                }
                for d in self.decisions
                if d.verdict == "include"
            ],
            "excluded": [
                {
                    "source": d.candidate_id,
                    "kind": d.candidate_kind,
                    "reason": d.rationale,
                    "score": d.confidence if d.confidence is not None else 0.5,
                }
                for d in self.decisions
                if d.verdict == "exclude"
            ],
        }


def aggregate(decisions: Sequence[ContextDecision]) -> AggregatedContext:
    """Combine independent per-candidate decisions into one selected context set.

    Each candidate must appear exactly once. This is intentionally a pure fold --
    no re-ranking, no re-scoring, no budget re-evaluation -- because BC-0101 asks
    each of the seven candidates to be judged independently; the aggregate is just
    the union of "include" verdicts.
    """
    seen: set[str] = set()
    included: list[str] = []
    excluded: list[str] = []
    for d in decisions:
        if d.candidate_id in seen:
            raise ValueError(f"duplicate decision for candidate {d.candidate_id!r}")
        seen.add(d.candidate_id)
        (included if d.verdict == "include" else excluded).append(d.candidate_id)
    return AggregatedContext(included=included, excluded=excluded, decisions=list(decisions))
