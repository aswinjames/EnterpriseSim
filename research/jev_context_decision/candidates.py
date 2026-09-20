"""Loads the seven real BC-0101 candidate artifacts with their full content.

BC-0101 (suite BENCH-01, see ``benchmarks/specs/BENCH-01.md`` and
``benchmarks/examples/benchmark_case.example.json``) offers the Worker a candidate
corpus of seven items for the guest-checkout task (CHK-1421):

    knowledge:  KN-045, KN-052, KN-063, KN-047, KN-101
    experience: EXP-090, EXP-055

This module resolves each ID to its *real* body text as it actually exists elsewhere
in this repository (``enterprise/knowledge/*.json``, ``schemas/examples/*.json``,
``corpus/experience_store.json``) rather than passing opaque IDs to a decision-maker.

One item, KN-047, has no body anywhere in the repo -- every reference to it (in
``corpus/executions/*.json`` and ``schemas/examples/context_object.example.json``) is
provenance-only ("dropped for budget; flagged"). That is the truth on disk, not a
gap in this loader, so KN-047 resolves to an explicit ``CONTENT_UNAVAILABLE`` stub.
Do not invent a body for it -- the case's own ground truth treats it as a defensible
drop specifically *because* a Worker cannot fully evaluate it (see
``ground_truth.notes`` in the benchmark case).

Nothing here modifies benchmark data or ground truth; it only reads it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
CASE_PATH = REPO_ROOT / "benchmarks" / "examples" / "benchmark_case.example.json"

KNOWLEDGE_SOURCES = (
    REPO_ROOT / "schemas" / "examples" / "knowledge_object.example.json",
    REPO_ROOT / "enterprise" / "knowledge" / "business-rules.json",
    REPO_ROOT / "enterprise" / "knowledge" / "architecture-docs.json",
    REPO_ROOT / "enterprise" / "knowledge" / "api-specs.json",
    REPO_ROOT / "enterprise" / "knowledge" / "runbooks.json",
    REPO_ROOT / "enterprise" / "knowledge" / "postmortems.json",
)
EXPERIENCE_SOURCE = REPO_ROOT / "corpus" / "experience_store.json"

#: Sentinel body used only for candidates whose real content is not present
#: anywhere in the repository. Never used as a substitute for real content that
#: does exist -- see module docstring.
CONTENT_UNAVAILABLE = (
    "[CONTENT UNAVAILABLE] No knowledge body for this ID exists anywhere in the "
    "EnterpriseSim corpus. Every occurrence of this ID in the repository is "
    "provenance-only (an inclusion/exclusion record with a reason and score, "
    "never a title or body). Ground truth (benchmarks/examples/"
    "benchmark_case.example.json) identifies it as 'legacy monolith checkout' "
    "and treats it as a defensible budget drop, not a required item -- a Worker "
    "with only this stub cannot verify that characterization and must decide "
    "under that uncertainty rather than have content invented for it."
)

#: IDs known, from repo-wide search, to have no resolvable body.
KNOWN_CONTENT_UNAVAILABLE_IDS = frozenset({"KN-047"})


@dataclass(frozen=True)
class Candidate:
    """One BC-0101 candidate artifact, with real content resolved from the repo."""

    id: str
    kind: str  # "knowledge" | "experience"
    title: str
    body: str
    content_available: bool
    source_file: str | None
    raw: Mapping[str, object] | None


def _load_json(path: Path) -> object:
    return json.loads(path.read_text())


def _find_knowledge_object(kn_id: str) -> tuple[Mapping[str, object], str] | None:
    for path in KNOWLEDGE_SOURCES:
        if not path.exists():
            continue
        data = _load_json(path)
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("id") == kn_id and "body" in item:
                return item, str(path.relative_to(REPO_ROOT))
    return None


def _find_experience_object(exp_id: str) -> tuple[Mapping[str, object], str] | None:
    if not EXPERIENCE_SOURCE.exists():
        return None
    data = _load_json(EXPERIENCE_SOURCE)
    for item in data:
        if isinstance(item, dict) and item.get("id") == exp_id:
            return item, str(EXPERIENCE_SOURCE.relative_to(REPO_ROOT))
    return None


def load_candidate(candidate_id: str, kind: str) -> Candidate:
    """Resolve one candidate ID to its real content, or the content-unavailable stub."""
    if candidate_id in KNOWN_CONTENT_UNAVAILABLE_IDS:
        return Candidate(
            id=candidate_id,
            kind=kind,
            title=f"{candidate_id} (content unavailable)",
            body=CONTENT_UNAVAILABLE,
            content_available=False,
            source_file=None,
            raw=None,
        )

    if kind == "knowledge":
        found = _find_knowledge_object(candidate_id)
    elif kind == "experience":
        found = _find_experience_object(candidate_id)
    else:
        raise ValueError(f"unknown candidate kind: {kind!r}")

    if found is None:
        raise LookupError(
            f"no real content found anywhere in the repo for {candidate_id} "
            f"({kind}); refusing to invent content. If this ID genuinely has no "
            f"body on disk, add it to KNOWN_CONTENT_UNAVAILABLE_IDS instead."
        )

    obj, source_file = found
    if kind == "experience":
        title = str(obj.get("title", candidate_id))
        body = str(obj.get("lesson", ""))
    else:
        title = str(obj.get("title", candidate_id))
        body = str(obj.get("body", ""))

    return Candidate(
        id=candidate_id,
        kind=kind,
        title=title,
        body=body,
        content_available=True,
        source_file=source_file,
        raw=obj,
    )


def load_bc_0101_candidates() -> list[Candidate]:
    """Load the seven BC-0101 candidates in the order declared on the case."""
    case = json.loads(CASE_PATH.read_text())
    corpus = case["inputs"]["available_corpus"]
    candidates: list[Candidate] = []
    for kn_id in corpus["knowledge"]:
        candidates.append(load_candidate(kn_id, "knowledge"))
    for exp_id in corpus["experience"]:
        candidates.append(load_candidate(exp_id, "experience"))
    return candidates


def load_bc_0101_case() -> dict:
    """Load the frozen BC-0101 benchmark case verbatim (never modified)."""
    return json.loads(CASE_PATH.read_text())


if __name__ == "__main__":
    for c in load_bc_0101_candidates():
        flag = "OK" if c.content_available else "STUB"
        print(f"[{flag}] {c.id} ({c.kind}) <- {c.source_file}: {c.title!r}")
