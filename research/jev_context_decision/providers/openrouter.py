"""Minimal, zero-dependency HTTP client for OpenRouter, shared by both providers.

Both the standard chat-completions endpoint (``GPTProvider``) and TypeSafe's alpha
Decisions endpoint (``JevProvider``) live under the same ``openrouter.ai`` host and
use the same bearer-token auth, so the POST/JSON/error-handling plumbing is
factored out here; only the path, request body shape and response shape differ
per provider. Uses only ``urllib`` (stdlib) -- no SDK dependency, matching this
repo's zero-dep quickstart convention.

Both providers read the SAME environment variable, ``OPENROUTER_API_KEY`` --
OpenRouter is the one gateway for both Jev and GPT in this experiment.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Mapping

OPENROUTER_BASE = "https://openrouter.ai"

#: Standard OpenAI-compatible chat completions endpoint. Used by GPTProvider.
CHAT_COMPLETIONS_PATH = "/api/v1/chat/completions"

#: TypeSafe's Decisions endpoint for the Jev model family. Deliberately outside
#: the /api/v1 prefix -- confirmed via OpenRouter's own cookbook
#: ("The Decisions API is at https://openrouter.ai/api/alpha/decisions, outside
#: the /api/v1 prefix"), docs/cookbook/evaluate-and-optimize/jev-verified-cascade.
#: Used by JevProvider.
DECISIONS_PATH = "/api/alpha/decisions"

#: Env var read by both providers. There is intentionally only one -- OpenRouter
#: is the single gateway for both Jev and GPT in this experiment.
API_KEY_ENV_VAR = "OPENROUTER_API_KEY"


class OpenRouterError(RuntimeError):
    """A non-2xx response from OpenRouter, with the status and raw body attached."""

    def __init__(self, status: int, body: str) -> None:
        super().__init__(f"OpenRouter returned HTTP {status}: {body}")
        self.status = status
        self.body = body


def post_json(path: str, payload: Mapping[str, Any], api_key: str, timeout: float = 30.0) -> dict:
    """POST ``payload`` as JSON to ``OPENROUTER_BASE + path`` and return the parsed JSON body.

    Raises ``OpenRouterError`` on any non-2xx response. This is the only function
    in this module that touches the network -- everything else in the providers
    is pure request-building / response-parsing and is unit-testable offline.
    """
    url = f"{OPENROUTER_BASE}{path}"
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            # Recommended (not required) by OpenRouter for attribution/rankings.
            "HTTP-Referer": "https://github.com/aswinjames/EnterpriseSim",
            "X-Title": "EnterpriseSim jev_context_decision experiment",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise OpenRouterError(exc.code, body) from exc
