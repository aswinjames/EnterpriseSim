"""Deterministic offline provider used for wiring tests and dry runs.

This is NOT a stand-in for either Jev or GPT's judgment -- it exists only so the
candidate loader, decision schema, aggregator and scoring pipeline can be tested
end-to-end without any network access or API key, per "no live API calls yet".
Its verdicts are a simple, fully-explained heuristic (content-availability plus a
keyword check against the task), not a claim about what a real model would decide.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from ..candidates import Candidate
from ..decision import ContextDecision
from .base import DecisionCase, DEFAULT_CASE, ContextDecisionProvider

_TASK_KEYWORDS = {
    "checkout", "guest", "order", "idempotency", "loyalty", "payment", "cart",
}


class MockProvider(ContextDecisionProvider):
    """Offline heuristic decider: keyword overlap with the task, content-available only."""

    name = "mock"

    def __init__(self, model: str = "mock-heuristic-v1") -> None:
        self.model = model

    def decide(self, candidate: Candidate, *, case: DecisionCase = DEFAULT_CASE) -> ContextDecision:
        start = time.monotonic()

        if not candidate.content_available:
            verdict = "exclude"
            rationale = (
                "Content unavailable for this candidate; cannot verify relevance, "
                "so it is excluded rather than guessed into the working set."
            )
            confidence = 0.5
        else:
            text = f"{candidate.title} {candidate.body}".lower()
            hits = {w for w in _TASK_KEYWORDS if w in text}
            verdict = "include" if hits else "exclude"
            rationale = (
                f"Keyword overlap with task ({sorted(hits)}) found in body."
                if hits
                else "No overlap between candidate content and task keywords."
            )
            confidence = min(0.5 + 0.1 * len(hits), 0.95)

        latency_ms = (time.monotonic() - start) * 1000
        return ContextDecision(
            candidate_id=candidate.id,
            candidate_kind=candidate.kind,
            provider=self.name,
            verdict=verdict,
            rationale=rationale,
            confidence=confidence,
            model=self.model,
            prompt_version=case.prompt_version,
            latency_ms=latency_ms,
            input_tokens=None,
            output_tokens=None,
            cost_usd=0.0,
            timestamp=datetime.now(timezone.utc).isoformat(),
            raw_output={"heuristic": "keyword-overlap", "candidate_id": candidate.id},
        )
