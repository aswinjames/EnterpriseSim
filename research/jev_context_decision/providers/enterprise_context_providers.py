"""GPT/Jev provider variants for X-RICH-2: identical to GPTProvider/JevProvider
except the complete, unfiltered enterprise application registry is added to
every request.

Model, token cap, reasoning effort, transport modules, the noul question
type, criteria wording, and response parsing are all reused UNMODIFIED from
``gpt_provider.py`` / ``jev_provider.py`` (imported, not copied) -- the only
addition is one extra section of the GPT prompt / one extra field in Jev's
``state`` payload, and it is the exact same registry content for every
candidate (no per-candidate filtering anywhere in this file).

These are new classes in a new file specifically so that ``GPTProvider`` and
``JevProvider`` (used by BC-0101, BC-0102, and X-RICH-1) are provably
untouched by X-RICH-2's existence.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from ..candidates import Candidate
from ..decision import ContextDecision
from ..enterprise_context import ENTERPRISE_CONTEXT_TRAILER, format_enterprise_context_block
from . import gpt_provider, jev_provider, openai_direct, openrouter
from .base import DecisionCase, DEFAULT_CASE, ContextDecisionProvider, ProviderNotConfigured


class GPTProviderWithEnterpriseContext(ContextDecisionProvider):
    """GPTProvider + the complete application registry appended to the prompt."""

    name = "gpt"

    def __init__(
        self,
        enterprise_registry: list[dict],
        model: str = gpt_provider.DEFAULT_MODEL,
        api_key: str | None = None,
    ) -> None:
        self.enterprise_registry = enterprise_registry
        self.model = model
        self._api_key = api_key or os.environ.get(openai_direct.API_KEY_ENV_VAR)

    def _require_key(self) -> str:
        if not self._api_key:
            raise ProviderNotConfigured(
                f"{openai_direct.API_KEY_ENV_VAR} is not set. Export it in your shell "
                "environment before running a live GPT decision -- never hardcode it in a file."
            )
        return self._api_key

    def decide(self, candidate: Candidate, *, case: DecisionCase = DEFAULT_CASE) -> ContextDecision:
        api_key = self._require_key()
        base_prompt = gpt_provider._build_prompt(candidate, case.task_statement)
        context_block = format_enterprise_context_block(self.enterprise_registry)
        prompt = f"{base_prompt}\n\n{context_block}"

        request_body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_schema", "json_schema": gpt_provider._DECISION_SCHEMA},
            "max_completion_tokens": gpt_provider.MAX_OUTPUT_TOKENS,
            "reasoning_effort": gpt_provider.REASONING_EFFORT,
        }

        start = time.monotonic()
        response = openai_direct.post_json(openai_direct.CHAT_COMPLETIONS_PATH, request_body, api_key)
        latency_ms = (time.monotonic() - start) * 1000

        parsed = gpt_provider._parse_response(response)

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


class JevProviderWithEnterpriseContext(ContextDecisionProvider):
    """JevProvider + the complete application registry added to ``state``."""

    name = "jev"

    def __init__(
        self,
        enterprise_registry: list[dict],
        model: str = jev_provider.DEFAULT_MODEL,
        api_key: str | None = None,
    ) -> None:
        self.enterprise_registry = enterprise_registry
        self.model = model
        self._api_key = api_key or os.environ.get(openrouter.API_KEY_ENV_VAR)

    def _require_key(self) -> str:
        if not self._api_key:
            raise ProviderNotConfigured(
                f"{openrouter.API_KEY_ENV_VAR} is not set. Export it in your shell "
                "environment before running a live Jev decision -- never hardcode it in a file."
            )
        return self._api_key

    def decide(self, candidate: Candidate, *, case: DecisionCase = DEFAULT_CASE) -> ContextDecision:
        api_key = self._require_key()
        base_request = jev_provider._build_request(candidate, case, self.model)
        request_body = {
            **base_request,
            "state": {
                **base_request["state"],
                "enterprise_application_registry": self.enterprise_registry,
                "enterprise_application_registry_note": ENTERPRISE_CONTEXT_TRAILER,
            },
        }

        start = time.monotonic()
        response = openrouter.post_json(openrouter.DECISIONS_PATH, request_body, api_key)
        latency_ms = (time.monotonic() - start) * 1000

        parsed = jev_provider._parse_response(response)

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
