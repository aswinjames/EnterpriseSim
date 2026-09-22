"""X-GEPA-1 labeled dataset: per-candidate classification examples for GEPA.

X-GEPA-1 asks a narrower question than X-RICH-1/2/3: can GEPA (a reflective
prompt/text optimizer) improve the *decision policy* JEV uses to judge one
candidate artifact, such that -- when that optimized policy is run through
the exact same X-RICH-3 hard-budget mechanism -- more of the budget survives
for artifacts that actually matter?

To optimize anything, GEPA needs labeled examples to train and validate
against. This repository has exactly ONE task (CHK-1421) and ONE 15-candidate
pool (X-RICH-1's, reused unchanged by X-RICH-2 and X-RICH-3). There is no
second task to hold out. So the only labeled examples available here are the
INDIVIDUAL CANDIDATE ARTIFACTS themselves, each with its existing, frozen
classification from ``experiment_3_candidates.CLASSIFICATIONS`` (imported by
reference -- never copied or re-adjudicated).

This module is purely additive. It does not modify candidates.py,
experiment_3_candidates.py, providers/base.py, scoring.py, or any historical
result file. It reads the frozen classification dict and turns it into a
tiny, explicitly-labeled, explicitly-imperfect train/val/test split -- see
the "HONEST LIMITATION" note below before using this for anything beyond a
pilot/feasibility check.

------------------------------------------------------------------------
HONEST LIMITATION -- read before treating this as a real experiment
------------------------------------------------------------------------
13 usable labeled candidates (see EXCLUDED_FROM_LABELING below) split three
ways, across 4 categories, is NOT a statistically defensible train/val/test
split. It is a single task, single domain, single candidate pool. Two of the
four categories (ACCEPTABLE_OPTIONAL, MUST_EXCLUDE) have only 2 examples
each in the entire dataset, so the validation split necessarily has ZERO
examples of both. This module exists to make that split reproducible and
visible, not to pretend it is adequate. X-GEPA-1's own runner and proposal
doc both label the whole experiment a PILOT / FEASIBILITY CHECK for exactly
this reason. A defensible version of this experiment needs more EnterpriseSim
task scenarios (plural), not a cleverer split of the one pool that already
exists -- see the "Next step" section of X_GEPA_1_PROPOSAL.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from .candidates import Candidate, load_candidate
from .experiment_3_candidates import (
    ACCEPTABLE_OPTIONAL_IDS,
    CONTESTED_CANDIDATE_IDS,
    MUST_EXCLUDE_IDS,
    MUST_INCLUDE_IDS,
    RELATED_BUT_UNNECESSARY_IDS,
)
from .experiment_3_candidates import EXPERIMENT_3_CANDIDATE_SPECS

EXPERIMENT_ID = "X-GEPA-1"

#: Candidates deliberately never given a target label for GEPA optimization:
#: KN-101 is CONTESTED (see experiment_3_candidates.KN_101_CONTESTED_NOTE) --
#: it must never be treated as resolved ground truth, so it is never a
#: labeled training/validation/test example here, in either direction.
#: KN-047 is UNRESOLVABLE (no real content anywhere in the repo -- an
#: explicit content-unavailable stub); labeling it would only test stub
#: handling, not the actual research question.
EXCLUDED_FROM_LABELING: tuple[str, ...] = tuple(CONTESTED_CANDIDATE_IDS) + ("KN-047",)

_KIND_BY_ID: dict[str, str] = {cid: kind for cid, kind in EXPERIMENT_3_CANDIDATE_SPECS}


@dataclass(frozen=True)
class GepaDataInst:
    """One labeled example: a candidate artifact plus its target verdict.

    ``target_verdict`` is derived mechanically from the existing, frozen
    X-RICH-1 classification -- never re-adjudicated here:
      MUST_INCLUDE, ACCEPTABLE_OPTIONAL       -> "include"
      RELATED_BUT_UNNECESSARY, MUST_EXCLUDE   -> "exclude"
    This mapping is the entire point of X-GEPA-1: MUST_INCLUDE and
    ACCEPTABLE_OPTIONAL are both "relevant" under the original scorer, but
    RELATED_BUT_UNNECESSARY is *also* relevant/on-topic and is exactly the
    category a policy needs to learn to say "exclude" to, to protect budget
    for what's actually necessary.
    """

    candidate_id: str
    kind: str
    category: str  # the original experiment_3_candidates classification label
    target_verdict: str  # "include" | "exclude"

    def load(self) -> Candidate:
        return load_candidate(self.candidate_id, self.kind)


def _target_for_category(category: str) -> str:
    if category in ("must_include", "acceptable_optional"):
        return "include"
    if category in ("related_but_unnecessary", "must_exclude"):
        return "exclude"
    raise ValueError(f"category {category!r} has no defined GEPA target label")


_ALL_LABELED_IDS_BY_CATEGORY: dict[str, tuple[str, ...]] = {
    "must_include": MUST_INCLUDE_IDS,
    "acceptable_optional": ACCEPTABLE_OPTIONAL_IDS,
    "related_but_unnecessary": RELATED_BUT_UNNECESSARY_IDS,
    "must_exclude": MUST_EXCLUDE_IDS,
}

#: Every labeled example this module can produce (13 total: 3 MI + 2 AO + 6
#: RBU + 2 ME), built mechanically from the frozen classification dict.
ALL_LABELED: tuple[GepaDataInst, ...] = tuple(
    GepaDataInst(
        candidate_id=cid,
        kind=_KIND_BY_ID[cid],
        category=category,
        target_verdict=_target_for_category(category),
    )
    for category, ids in _ALL_LABELED_IDS_BY_CATEGORY.items()
    for cid in ids
)

assert {d.candidate_id for d in ALL_LABELED}.isdisjoint(EXCLUDED_FROM_LABELING), (
    "KN-101 (contested) and KN-047 (unresolvable) must never receive a GEPA target label"
)

#: The fixed, deterministic (not random-seed-tunable) three-way split. Chosen
#: by hand so TRAIN and TEST each contain at least one example of all four
#: categories; VAL could not also get all four without duplicating an
#: example across splits, given only 2 ACCEPTABLE_OPTIONAL and 2 MUST_EXCLUDE
#: candidates exist in total. This asymmetry is the honest consequence of a
#: 13-example dataset, not a modeling choice -- see the module docstring.
_TRAIN_IDS: tuple[str, ...] = ("KN-045", "KN-063", "KN-128", "KN-146", "KN-122")
_VAL_IDS: tuple[str, ...] = ("KN-052", "KN-411", "KN-313")
_TEST_IDS: tuple[str, ...] = ("EXP-090", "EXP-055", "EXP-209", "EXP-206", "KN-311")

assert set(_TRAIN_IDS) | set(_VAL_IDS) | set(_TEST_IDS) == {d.candidate_id for d in ALL_LABELED}
assert not (set(_TRAIN_IDS) & set(_VAL_IDS) & set(_TEST_IDS))
assert len(set(_TRAIN_IDS) & set(_VAL_IDS)) == 0
assert len(set(_TRAIN_IDS) & set(_TEST_IDS)) == 0
assert len(set(_VAL_IDS) & set(_TEST_IDS)) == 0

_BY_ID: dict[str, GepaDataInst] = {d.candidate_id: d for d in ALL_LABELED}


def load_split(split: str) -> list[GepaDataInst]:
    """Return the labeled examples for ``split`` in ('train', 'val', 'test')."""
    ids = {"train": _TRAIN_IDS, "val": _VAL_IDS, "test": _TEST_IDS}[split]
    return [_BY_ID[cid] for cid in ids]
