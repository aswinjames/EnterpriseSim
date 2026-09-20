"""Jev provider: native TypeSafe INCLUDE/EXCLUDE decision via OpenRouter's Decisions API.

Routed through OpenRouter's alpha Decisions endpoint (``/api/alpha/decisions``,
deliberately outside the standard ``/api/v1`` chat-completions prefix -- see
``openrouter.DECISIONS_PATH``), pinned to ``typesafe/jev-1.13``. This replaces the
earlier, unverified native ``noul`` SDK client -- OpenRouter is now the one
gateway for both Jev and GPT in this experiment, and the Decisions API's own
``"type": "noul"`` question is a *verified, documented* boolean decision type
(confirmed via OpenRouter's own API reference for
``alphadecisions/submit-a-decisions-questions-and-answers-request``), which is
exactly the "typed choice with an attached probability" semantics `noul` was
always meant to express -- so nothing about the intended decision shape changes,
only the transport.

The API key is read from ``OPENROUTER_API_KEY`` -- the same gateway key used by
``GPTProvider`` -- never hardcoded, never logged.

Request-building and response-parsing are pure functions (``_build_request``,
``_parse_response``) so they are unit-testable without any network access; only
``decide()`` itself calls out to ``openrouter.post_json``.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from ..candidates import Candidate
from ..decision import ContextDecision
from . import openrouter
from .base import PROMPT_VERSION, TASK_STATEMENT, ContextDecisionProvider, ProviderNotConfigured

#: Pinned OpenRouter model slug for the Jev side of this experiment. Confirmed via
#: OpenRouter's own model page (openrouter.ai/typesafe/jev-1.13) and cookbook
#: example request bodies. Override only via the env var below -- never hardcode
#: a different model (e.g. the unpinned "typesafe/jev-latest") in code.
DEFAULT_MODEL = os.environ.get("JEV_CONTEXT_DECISION_MODEL", "typesafe/jev-1.13")

#: The single Decisions-API question asked per candidate: a "noul" (boolean) type,
#: which returns a probability rather than free text -- the closest match on
#: OpenRouter to native noul-style binary INCLUDE/EXCLUDE semantics.
_QUESTION_KEY = "include_in_context"

_INCLUDE_CRITERIA_TRUE = (
    "This candidate artifact should be included in the Worker's working context "
    "for this task: its content is relevant to guest checkout order placement "
    "(CHK-1421, APP-003) and materially helps complete it correctly."
)
_INCLUDE_CRITERIA_FALSE = (
    "This candidate artifact should be excluded from the Worker's working context "
    "for this task: it is out of scope, a distractor, or its content is not "
    "resolvable/available to judge."
)


def _build_request(candidate: Candidate, task_statement: str, model: str) -> dict:
    """Pure: build the OpenRouter Decisions API request body. No network."""
    return {
        "model": model,
        "state": {
            "task": task_statement,
            "candidate_id": candidate.id,
            "candidate_kind": candidate.kind,
            "candidate_title": candidate.title,
            "candidate_content": candidate.body,
        },
        "questions": {
            _QUESTION_KEY: {
                "type": "noul",
                "instructions": (
                    "Should this ONE candidate artifact be included in the Worker's "
                    "working context for this task? Judge it strictly on its own "
                    "content -- do not assume information about any other candidate."
                ),
                "criteria": {
                    "true": _INCLUDE_CRITERIA_TRUE,
                    "false": _INCLUDE_CRITERIA_FALSE,
                },
            }
        },
    }


def _parse_response(response: dict) -> dict:
    """Pure: extract the normalized decision fields from a raw API response body.

    The Decisions API returns a bare probability (``noul: 0.0-1.0``) for a noul
    question, no rationale field -- so the rationale here is synthesized from the
    probability itself, and confidence is the probability of whichever verdict
    was chosen (>= 0.5 -> include with confidence == p; < 0.5 -> exclude with
    confidence == 1 - p).
    """
    answer = response["answers"][_QUESTION_KEY]
    p_include = float(answer["noul"])
    verdict = "include" if p_include >= 0.5 else "exclude"
    confidence = p_include if verdict == "include" else 1.0 - p_include
    rationale = (
        f"Jev noul decision: P(include)={p_include:.3f} "
        f"-> {verdict} (confidence in verdict: {confidence:.3f})"
    )
    usage = response.get("usage") or {}
    return {
        "verdict": verdict,
        "rationale": rationale,
        "confidence": confidence,
        "model": response.get("model"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "cost_usd": usage.get("cost"),
    }


class JevProvider(ContextDecisionProvider):
    """Structured noul-type decision-maker, via OpenRouter. Live call happens in ``decide()``."""

    name = "jev"

    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None) -> None:
        self.model = model
        self._api_key = api_key or os.environ.get(openrouter.API_KEY_ENV_VAR)

    def _require_key(self) -> str:
        if not self._api_key:
            raise ProviderNotConfigured(
                f"{openrouter.API_KEY_ENV_VAR} is not set. Export it in your shell "
                "environment before running a live Jev decision -- never hardcode "
                "it in a file. This is the same key used by GPTProvider."
            )
        return self._api_key

    def decide(self, candidate: Candidate, *, task_statement: str = TASK_STATEMENT) -> ContextDecision:
        api_key = self._require_key()
        request_body = _build_request(candidate, task_statement, self.model)

        start = time.monotonic()
        response = openrouter.post_json(openrouter.DECISIONS_PATH, request_body, api_key)
        latency_ms = (time.monotonic() - start) * 1000

        parsed = _parse_response(response)

        return ContextDecision(
            candidate_id=candidate.id,
            candidate_kind=candidate.kind,
            provider=self.name,
            verdict=parsed["verdict"],
            rationale=parsed["rationale"],
            confidence=parsed["confidence"],
            model=parsed["model"] or self.model,
            prompt_version=PROMPT_VERSION,
            latency_ms=latency_ms,
            input_tokens=parsed["input_tokens"],
            output_tokens=parsed["output_tokens"],
            cost_usd=parsed["cost_usd"],
            timestamp=datetime.now(timezone.utc).isoformat(),
            raw_output=response,
        )
