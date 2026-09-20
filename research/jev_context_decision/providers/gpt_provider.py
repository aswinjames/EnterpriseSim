"""GPT provider: structured INCLUDE/EXCLUDE decision via OpenRouter (pinned GPT model).

Routed through OpenRouter's standard, OpenAI-compatible chat-completions endpoint
using structured-output mode (JSON schema response format), so the decision comes
back as validated ``{"verdict", "rationale", "confidence"}`` rather than free text
that needs parsing. The API key is read from ``OPENROUTER_API_KEY`` -- the same
gateway key used by ``JevProvider`` -- never hardcoded, never logged.

Request-building and response-parsing are pure functions (``_build_request``,
``_parse_response``) so they are unit-testable without any network access; only
``decide()`` itself calls out to ``openrouter.post_json``.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone

from ..candidates import Candidate
from ..decision import ContextDecision
from . import openrouter
from .base import PROMPT_VERSION, TASK_STATEMENT, ContextDecisionProvider, ProviderNotConfigured

#: Pinned OpenRouter model slug for the GPT side of this experiment. Confirmed
#: current on OpenRouter's openai model listing (openrouter.ai/openai) alongside
#: openai/gpt-4.1 / gpt-4o family; gpt-5-mini supports response_format
#: json_schema and function calling for structured output. Override only via the
#: env var below -- never hardcode a different model in code.
DEFAULT_MODEL = os.environ.get("GPT_CONTEXT_DECISION_MODEL", "openai/gpt-5-mini")

_DECISION_SCHEMA = {
    "name": "context_decision",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["include", "exclude"]},
            "rationale": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        },
        "required": ["verdict", "rationale", "confidence"],
        "additionalProperties": False,
    },
}


def _build_prompt(candidate: Candidate, task_statement: str) -> str:
    return (
        f"{task_statement}\n\n"
        f"Candidate ID: {candidate.id}\n"
        f"Candidate kind: {candidate.kind}\n"
        f"Candidate title: {candidate.title}\n"
        f"Candidate content:\n{candidate.body}\n\n"
        "Respond with your INCLUDE/EXCLUDE decision for this candidate only."
    )


#: Capped explicitly because OpenRouter reserves credit against a request's
#: max_tokens *before* the call executes; leaving it unset defaults to the
#: pinned model's full output ceiling (65536 for openai/gpt-5-mini) and gets a
#: 402 Payment Required against any balance that can't cover reserving the
#: whole thing, independent of what the call actually ends up costing.
#:
#: gpt-5-mini is a reasoning model: hidden reasoning tokens are drawn from the
#: SAME max_tokens budget as the visible answer, and reasoning-token usage
#: varies per input and per call -- confirmed live twice: a 400-token cap
#: truncated the JSON mid-string for one candidate, and later, even with
#: reasoning.effort="minimal" and a 1500-token cap, a different call in a
#: 5-repeat batch still hit finish_reason=length (OpenRouter's own docs note
#: some providers vary reasoning-token spend independent of the requested
#: effort level). Raised well past both observed failures so this is a safety
#: margin against truncation, not a change to what's being asked or decided.
MAX_OUTPUT_TOKENS = 4000
REASONING_EFFORT = "minimal"


def _build_request(candidate: Candidate, task_statement: str, model: str) -> dict:
    """Pure: build the OpenRouter chat-completions request body. No network."""
    return {
        "model": model,
        "messages": [{"role": "user", "content": _build_prompt(candidate, task_statement)}],
        "response_format": {"type": "json_schema", "json_schema": _DECISION_SCHEMA},
        "max_tokens": MAX_OUTPUT_TOKENS,
        "reasoning": {"effort": REASONING_EFFORT},
    }


def _parse_response(response: dict) -> dict:
    """Pure: extract the normalized decision fields from a raw API response body.

    Returns a dict with keys verdict/rationale/confidence/model/input_tokens/
    output_tokens/cost_usd/raw_payload. No network, no side effects.
    """
    choice = response["choices"][0]
    if choice.get("finish_reason") == "length":
        raise RuntimeError(
            "GPT response was truncated (finish_reason=length) before completing "
            f"the JSON decision -- raise gpt_provider.MAX_OUTPUT_TOKENS "
            f"(currently {MAX_OUTPUT_TOKENS}) rather than treating this as a parse bug."
        )
    payload = json.loads(choice["message"]["content"])
    usage = response.get("usage") or {}
    return {
        "verdict": payload["verdict"],
        "rationale": payload["rationale"],
        "confidence": float(payload["confidence"]),
        "model": response.get("model"),
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
        "cost_usd": usage.get("cost"),
        "raw_payload": payload,
    }


class GPTProvider(ContextDecisionProvider):
    """Structured-output GPT decision-maker, via OpenRouter. Live call happens in ``decide()``."""

    name = "gpt"

    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None) -> None:
        self.model = model
        self._api_key = api_key or os.environ.get(openrouter.API_KEY_ENV_VAR)

    def _require_key(self) -> str:
        if not self._api_key:
            raise ProviderNotConfigured(
                f"{openrouter.API_KEY_ENV_VAR} is not set. Export it in your shell "
                "environment before running a live GPT decision -- never hardcode "
                "it in a file. This is the same key used by JevProvider."
            )
        return self._api_key

    def decide(self, candidate: Candidate, *, task_statement: str = TASK_STATEMENT) -> ContextDecision:
        api_key = self._require_key()
        request_body = _build_request(candidate, task_statement, self.model)

        start = time.monotonic()
        response = openrouter.post_json(openrouter.CHAT_COMPLETIONS_PATH, request_body, api_key)
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
