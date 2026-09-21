"""The X-RICH-2 experimental treatment: the complete enterprise application
registry, exposed to the model verbatim and unfiltered.

This is the ONLY thing X-RICH-2 changes relative to X-RICH-1. Everything else
-- candidates, order, IDs, bodies, classifications, the BC-0101 criterion
object, TaskScope, the scorer, provider model/config -- is reused unchanged
from ``experiment_3_candidates.py`` / ``providers/base.py`` / ``scoring.py``.

Nothing here invents data: ``enterprise/registry/applications.json`` is read
fresh from disk every call and returned/rendered exactly as it exists in the
repository, with no per-candidate filtering, curation, or truncation. Per the
approved treatment, ``enterprise/schemas/application.schema.json`` (the shape
definition, not additional facts) is deliberately NOT included.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APPLICATION_REGISTRY_PATH = REPO_ROOT / "enterprise" / "registry" / "applications.json"

ENTERPRISE_CONTEXT_PREAMBLE = (
    "Additional enterprise context (application registry, from "
    "enterprise/registry/applications.json):"
)
ENTERPRISE_CONTEXT_TRAILER = (
    "This registry describes every declared application, its owning team, its "
    "declared dependencies on other applications, its business unit, and its "
    "criticality tier. Use it only if it helps you judge this candidate -- it "
    "does not tell you which candidates to select."
)


def load_application_registry() -> list[dict]:
    """Return the complete, unfiltered application registry (all 12 apps,
    every field), read fresh from disk every call. Never cached, never
    trimmed, never candidate-specific."""
    return json.loads(APPLICATION_REGISTRY_PATH.read_text())


def format_enterprise_context_block(registry: list[dict]) -> str:
    """Pure: render the complete registry as the shared text block appended
    to every GPT prompt. The same ``registry`` value (untouched) is used
    directly as Jev's ``state.enterprise_application_registry`` field --
    no separate formatting needed there since Jev's state is already JSON.
    """
    return (
        f"{ENTERPRISE_CONTEXT_PREAMBLE}\n\n"
        f"{json.dumps(registry, indent=2)}\n\n"
        f"{ENTERPRISE_CONTEXT_TRAILER}"
    )
