"""Minimal, zero-dependency HTTP client for the direct OpenAI API.

Structurally identical to ``providers/openrouter.py`` (same POST-JSON/Bearer-auth/
error-handling shape), pointed at ``api.openai.com`` instead of ``openrouter.ai``.
Exists so ``GPTProvider`` can call OpenAI directly -- bypassing OpenRouter, whose
BC-0102 batches repeatedly failed on truncation and account/key credit limits --
without adding a dependency on the ``openai`` package or changing the
zero-dependency style already used for the OpenRouter client.

Used ONLY by ``gpt_provider.py``. ``JevProvider`` is untouched and continues to
use ``providers/openrouter.py`` exclusively.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Mapping

OPENAI_BASE = "https://api.openai.com"

#: Standard OpenAI chat completions endpoint.
CHAT_COMPLETIONS_PATH = "/v1/chat/completions"

#: Env var read by GPTProvider when calling OpenAI directly. Distinct from
#: OPENROUTER_API_KEY -- this is a different account/gateway entirely.
API_KEY_ENV_VAR = "OPENAI_API_KEY"


class OpenAIError(RuntimeError):
    """A non-2xx response from the direct OpenAI API, with status and raw body attached."""

    def __init__(self, status: int, body: str) -> None:
        super().__init__(f"OpenAI API returned HTTP {status}: {body}")
        self.status = status
        self.body = body


def post_json(path: str, payload: Mapping[str, Any], api_key: str, timeout: float = 30.0) -> dict:
    """POST ``payload`` as JSON to ``OPENAI_BASE + path`` and return the parsed JSON body.

    Raises ``OpenAIError`` on any non-2xx response. This is the only function in
    this module that touches the network.
    """
    url = f"{OPENAI_BASE}{path}"
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise OpenAIError(exc.code, body) from exc
