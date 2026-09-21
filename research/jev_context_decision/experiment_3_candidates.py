"""Experiment 3 (identifier: X-RICH-1) candidate pool and classification metadata.

Experiment 3 tests whether context selection changes when the enterprise
context grows in volume and interconnectedness, using the SAME task (CHK-1421)
and the SAME BC-0101 decision criterion as before -- only the candidate pool
changes. See ``research/EXPERIMENT_3_PROPOSAL.md`` for the full research
design and the adjudication evidence behind every classification below.

This module is purely additive: it does not modify ``candidates.py``,
``decision.py``, ``scoring.py``, ``providers/base.py``, or ``run_experiment.py``.
It reuses ``candidates.load_candidate()`` unchanged for every ID -- every new
candidate's real content already resolves through the existing knowledge-file
search path (``enterprise/knowledge/business-rules.json``,
``enterprise/knowledge/runbooks.json``, ``enterprise/knowledge/postmortems.json``)
and the existing experience store (``corpus/experience_store.json``); nothing
new needed to be added to those search lists.

BC-0101 and BC-0102 are completely unaffected by this module -- it is never
imported by them, and nothing here writes to any of their files.
"""

from __future__ import annotations

from .candidates import Candidate, load_candidate

#: Local identifier for this experiment/candidate-pool version. Deliberately
#: NOT "BC-0103" -- there is no established repository convention requiring
#: sequential BC-01xx numbering for a candidate-pool expansion (as opposed to
#: BC-0102, which varied only the criterion wording against the same 7
#: candidates). This is a candidate-environment version tag, not a new
#: frozen benchmark case.
EXPERIMENT_ID = "X-RICH-1"

#: The 15 executable candidates, in the exact order specified for this
#: experiment: the original 7 (BC-0101/BC-0102 lineage, unchanged) followed by
#: the 8 newly-adjudicated high-confidence additions. (id, kind) pairs so
#: candidates.load_candidate() can be called directly -- no new lookup logic.
EXPERIMENT_3_CANDIDATE_SPECS: tuple[tuple[str, str], ...] = (
    # --- Original 7 (BC-0101 / BC-0102 lineage; retained, unchanged) ---
    ("KN-045", "knowledge"),
    ("KN-052", "knowledge"),
    ("EXP-090", "experience"),
    ("KN-063", "knowledge"),
    ("EXP-055", "experience"),
    ("KN-047", "knowledge"),
    ("KN-101", "knowledge"),
    # --- 8 new, high-confidence additions (see EXPERIMENT_3_PROPOSAL.md) ---
    ("KN-128", "knowledge"),
    ("KN-146", "knowledge"),
    ("KN-411", "knowledge"),
    ("KN-313", "knowledge"),
    ("EXP-209", "experience"),
    ("EXP-206", "experience"),
    ("KN-122", "knowledge"),
    ("KN-311", "knowledge"),
)

EXPERIMENT_3_CANDIDATE_IDS: tuple[str, ...] = tuple(cid for cid, _ in EXPERIMENT_3_CANDIDATE_SPECS)

#: Candidates deliberately held OUT of the executable pool for this phase --
#: their evidence was judged insufficient for a confident classification in
#: the adjudication report (KN-126, KN-127, KN-144, KN-140) or, for KN-136,
#: judged lower-confidence than the other MUST_EXCLUDE candidates. None of
#: these are silently dropped: they remain documented as a contested/held-out
#: tranche for a later, separate adjudication -- this tuple exists so tests
#: can assert their absence is intentional, not an oversight.
HELD_OUT_CANDIDATE_IDS: tuple[str, ...] = ("KN-126", "KN-127", "KN-144", "KN-140", "KN-136")

#: Classification labels used by this experiment. "contested" is new relative
#: to BC-0101/BC-0102's vocabulary (must_include/acceptable_optional/
#: must_exclude/unresolvable) -- it exists specifically for KN-101, whose
#: historical MUST_EXCLUDE label is NOT inherited here (see KN-101 note
#: below). "related_but_unnecessary" is also new: see the module docstring in
#: EXPERIMENT_3_PROPOSAL.md for why it is deliberately excluded from the
#: scorer's must_include/acceptable_optional/must_exclude sets.
MUST_INCLUDE = "must_include"
ACCEPTABLE_OPTIONAL = "acceptable_optional"
UNRESOLVABLE = "unresolvable"
CONTESTED = "contested"
RELATED_BUT_UNNECESSARY = "related_but_unnecessary"
MUST_EXCLUDE = "must_exclude"

#: Per-candidate classification for Experiment 3. KN-101 is CONTESTED, not
#: MUST_INCLUDE and not MUST_EXCLUDE -- its historical BC-0101/BC-0102
#: MUST_EXCLUDE label is a fact about those frozen cases, not something this
#: module inherits, converts, or hardcodes as this experiment's answer. See
#: the KN-101 note below and EXPERIMENT_3_PROPOSAL.md for the full analysis
#: (structural relationship YES, semantic relevance plausible, task-specific
#: necessity UNRESOLVED).
CLASSIFICATIONS: dict[str, str] = {
    "KN-045": MUST_INCLUDE,
    "KN-052": MUST_INCLUDE,
    "EXP-090": MUST_INCLUDE,
    "KN-063": ACCEPTABLE_OPTIONAL,
    "EXP-055": ACCEPTABLE_OPTIONAL,
    "KN-047": UNRESOLVABLE,
    "KN-101": CONTESTED,
    "KN-128": RELATED_BUT_UNNECESSARY,
    "KN-146": RELATED_BUT_UNNECESSARY,
    "KN-411": RELATED_BUT_UNNECESSARY,
    "KN-313": RELATED_BUT_UNNECESSARY,
    "EXP-209": RELATED_BUT_UNNECESSARY,
    "EXP-206": RELATED_BUT_UNNECESSARY,
    "KN-122": MUST_EXCLUDE,
    "KN-311": MUST_EXCLUDE,
}

assert set(CLASSIFICATIONS) == set(EXPERIMENT_3_CANDIDATE_IDS), (
    "every executable candidate must have exactly one classification, and vice versa"
)

MUST_INCLUDE_IDS: tuple[str, ...] = tuple(cid for cid, c in CLASSIFICATIONS.items() if c == MUST_INCLUDE)
ACCEPTABLE_OPTIONAL_IDS: tuple[str, ...] = tuple(cid for cid, c in CLASSIFICATIONS.items() if c == ACCEPTABLE_OPTIONAL)
#: Experiment-3-specific must_exclude set. Deliberately does NOT contain
#: KN-101 -- that is the entire point of treating KN-101 as CONTESTED rather
#: than inheriting BC-0101/BC-0102's historical label.
MUST_EXCLUDE_IDS: tuple[str, ...] = tuple(cid for cid, c in CLASSIFICATIONS.items() if c == MUST_EXCLUDE)
RELATED_BUT_UNNECESSARY_IDS: tuple[str, ...] = tuple(
    cid for cid, c in CLASSIFICATIONS.items() if c == RELATED_BUT_UNNECESSARY
)
CONTESTED_CANDIDATE_IDS: tuple[str, ...] = tuple(cid for cid, c in CLASSIFICATIONS.items() if c == CONTESTED)

#: KN-101's ambiguity, recorded once, in the same shape as
#: benchmark_quality.py's GroundTruthDiscrepancy -- documented, not resolved,
#: and never used to derive a classification. Neither the historical
#: ground_truth.notes text nor KN-101's real content is altered anywhere.
KN_101_CONTESTED_NOTE = (
    "KN-101 (app APP-007, Pricing Service) is retained from the BC-0101/BC-0102 "
    "lineage and classified CONTESTED, not MUST_INCLUDE or MUST_EXCLUDE, for "
    "Experiment 3. Evidence: (A) structural relationship -- APP-007 IS a "
    "declared dependency of APP-003 (enterprise/registry/applications.json), "
    "so KN-101 is not a structurally-unrelated distractor; (B) semantic "
    "relevance -- KN-101's real content ('Regional price resolution and "
    "currency binding') plausibly bears on computing an order total; (C) "
    "task-specific necessity -- UNRESOLVED: KN-045 (must_include) does not "
    "reference KN-101 or any APP-007 pricing artifact, and no incident links "
    "the two, but this absence of a citation is not proof of unnecessity "
    "either. Separately: benchmark_case.example.json's ground_truth.notes "
    "describes KN-101 as 'marketplace seller onboarding', which does not "
    "match its real content -- documented in benchmark_quality.py, neither "
    "value altered here or there."
)


def load_experiment_3_candidates() -> list[Candidate]:
    """Load all 15 Experiment 3 candidates, in the fixed order above.

    Reuses candidates.load_candidate() unchanged -- identical resolution
    behavior to BC-0101's loader, including KN-047's explicit
    content-unavailable stub (never invented content).
    """
    return [load_candidate(cid, kind) for cid, kind in EXPERIMENT_3_CANDIDATE_SPECS]


def build_experiment_3_case(base_case: dict) -> dict:
    """Build the Experiment 3 scoring case from the frozen BC-0101 case dict.

    ``base_case`` is expected to be a freshly-loaded dict from
    ``candidates.load_bc_0101_case()`` (re-read from the frozen JSON file each
    call, so mutating the dict returned here never touches
    ``benchmark_case.example.json`` on disk). Task fields (task_ref, title,
    description, apps, scoring, thresholds, expected.code) are copied
    verbatim -- Experiment 3 uses the identical underlying task. Only
    ``id`` and ``ground_truth`` are replaced:

    - must_include / acceptable_optional: unchanged from the original case.
    - must_exclude: KN-101 is deliberately NOT included (contested, not
      excluded); KN-122 and KN-311 are the new must_exclude set.
    - KN-047 and every RELATED_BUT_UNNECESSARY candidate are absent from
      must_include/acceptable_optional/must_exclude entirely -- exactly like
      KN-047's existing treatment in the original case, so score() (imported
      unmodified) needs no changes to handle them.
    """
    return {
        **base_case,
        "id": EXPERIMENT_ID,
        "ground_truth": {
            "type": "reference_set",
            "must_include": list(MUST_INCLUDE_IDS),
            "must_exclude": list(MUST_EXCLUDE_IDS),
            "expected": {
                "code": base_case["ground_truth"]["expected"]["code"],
                "acceptable_optional": list(ACCEPTABLE_OPTIONAL_IDS),
            },
            "source": base_case["ground_truth"]["source"],
            "notes": (
                "Experiment 3 (X-RICH-1) ground truth. KN-101 is intentionally "
                "excluded from must_include/must_exclude/acceptable_optional -- "
                "it is CONTESTED, tracked and reported separately, not scored. "
                "related_but_unnecessary candidates (see experiment_3_candidates."
                "RELATED_BUT_UNNECESSARY_IDS) are likewise absent from all three "
                "sets by design, tracked separately, and reported descriptively "
                "only. See KN_101_CONTESTED_NOTE for the KN-101 evidence summary."
            ),
        },
    }
