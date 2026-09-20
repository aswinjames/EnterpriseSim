"""GPT provider: structured INCLUDE/EXCLUDE decision via the direct OpenAI API.

Routed directly to OpenAI's own chat-completions endpoint (``api.openai.com``,
NOT OpenRouter) using structured-output mode (JSON schema response format), so
the decision comes back as validated ``{"verdict", "rationale", "confidence"}``
rather than free text that needs parsing. The API key is read from
``OPENAI_API_KEY`` -- a different key/account than ``JevProvider``'s
``OPENROUTER_API_KEY``; never hardcoded, never logged.

This replaces the OpenRouter transport this provider used previously (see
``providers/openrouter.py``, still used unchanged by ``JevProvider``).
OpenRouter's BC-0102 batches repeatedly failed on GPT-side response truncation
and, separately, on account/key credit-limit errors (402); this file changes
ONLY the transport and the two request parameters that direct OpenAI naming
requires (``max_tokens``->``max_completion_tokens``, ``reasoning.effort``->
``reasoning_effort``, same values) -- prompt wording, schema, model, and
reasoning effort are unchanged.

Request-building and response-parsing are pure functions (``_build_request``,
``_parse_response``) so they are unit-testable without any network access; only
``decide()`` itself calls out to ``openai_direct.post_json``.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone

from ..candidates import Candidate
from ..decision import ContextDecision
from . import openai_direct
from .base import DecisionCase, DEFAULT_CASE, ContextDecisionProvider, ProviderNotConfigured

#: Direct-OpenAI-API model id for the GPT side of this experiment. Same model as
#: before (OpenRouter's "openai/gpt-5-mini" slug) -- "gpt-5-mini" is the
#: un-prefixed id OpenRouter routes to, and is independently documented as a
#: current OpenAI API model (developers.openai.com/api/docs/models/gpt-5-mini).
#: Override only via the env var below -- never hardcode a different model.
DEFAULT_MODEL = os.environ.get("GPT_CONTEXT_DECISION_MODEL", "gpt-5-mini")

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


#: gpt-5-mini is a reasoning model: hidden reasoning tokens are drawn from the
#: SAME token budget as the visible answer, and reasoning-token usage varies
#: per input and per call -- confirmed live at several cap levels during the
#: OpenRouter-transport attempts (400, 1500, 4000, and 8000 all truncated a
#: call at some point across BC-0101/BC-0102 batches; 12000 was the value
#: OpenRouter's account/key credit limit allowed at the time). Value carried
#: over unchanged for the direct OpenAI transport -- this switch changes only
#: the transport and parameter names below, not this number, the model, or the
#: reasoning effort. It is now sent as ``max_completion_tokens`` (direct
#: OpenAI's Chat Completions API rejects ``max_tokens`` outright for reasoning
#: models such as gpt-5-mini).
MAX_OUTPUT_TOKENS = 12000

#: Unchanged value ("minimal"), sent under direct OpenAI's own flat
#: ``reasoning_effort`` parameter instead of OpenRouter's nested
#: ``reasoning: {"effort": ...}`` wrapper.
REASONING_EFFORT = "minimal"


def _build_request(candidate: Candidate, case: DecisionCase, model: str) -> dict:
    """Pure: build the direct OpenAI chat-completions request body. No network."""
    return {
        "model": model,
        "messages": [{"role": "user", "content": _build_prompt(candidate, case.task_statement)}],
        "response_format": {"type": "json_schema", "json_schema": _DECISION_SCHEMA},
        "max_completion_tokens": MAX_OUTPUT_TOKENS,
        "reasoning_effort": REASONING_EFFORT,
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
    """Structured-output GPT decision-maker, via the direct OpenAI API. Live call happens in ``decide()``."""

    name = "gpt"

    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None) -> None:
        self.model = model
        self._api_key = api_key or os.environ.get(openai_direct.API_KEY_ENV_VAR)

    def _require_key(self) -> str:
        if not self._api_key:
            raise ProviderNotConfigured(
                f"{openai_direct.API_KEY_ENV_VAR} is not set. Export it in your shell "
                "environment before running a live GPT decision -- never hardcode "
                "it in a file. This is a direct OpenAI API key, separate from "
                "OPENROUTER_API_KEY (which JevProvider still uses)."
            )
        return self._api_key

    def decide(self, candidate: Candidate, *, case: DecisionCase = DEFAULT_CASE) -> ContextDecision:
        api_key = self._require_key()
        request_body = _build_request(candidate, case, self.model)

        start = time.monotonic()
        response = openai_direct.post_json(openai_direct.CHAT_COMPLETIONS_PATH, request_body, api_key)
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
            prompt_version=case.prompt_version,
            latency_ms=latency_ms,
            input_tokens=parsed["input_tokens"],
            output_tokens=parsed["output_tokens"],
            cost_usd=parsed["cost_usd"],
            timestamp=datetime.now(timezone.utc).isoformat(),
            raw_output=response,
        )
