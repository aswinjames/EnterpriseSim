"""Documents known benchmark-quality issues in the frozen BC-0101/BC-0102 cases.

This module records a real discrepancy; it does not fix, resolve, or paper
over it. BC-0101 and BC-0102 are frozen historical experiments -- their
ground truth, candidate content, and results must remain byte-for-byte
reproducible (see ``research/jev_context_decision/README.md``). Recording a
known issue here, with a test (``tests/test_benchmark_quality.py``) asserting
it still holds, means any future accidental "fix" to either side is caught
and made a deliberate, visible decision rather than silent drift in either
direction.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GroundTruthDiscrepancy:
    """A known mismatch between a ground-truth note's description of a
    candidate artifact and that artifact's actual, independently-resolved
    content.

    Recording this is not the same as resolving it. A decision provider
    reasoning only from the real artifact content (as ``candidates.py``
    resolves it) has no way to reconstruct a rationale that exists only in a
    ground-truth note describing a different subject -- that gap is real,
    and is exactly the kind of benchmark-validity issue this class exists to
    make explicit rather than silently absorbed into "the model got it
    wrong."
    """

    candidate_id: str
    ground_truth_claim: str
    ground_truth_source: str
    actual_content_summary: str
    actual_content_source: str
    note: str


#: benchmarks/examples/benchmark_case.example.json's ground_truth.notes
#: describes KN-101 as being about "marketplace seller onboarding". KN-101's
#: real, resolvable content (enterprise/knowledge/business-rules.json,
#: resolved via candidates.py) is titled "Regional price resolution and
#: currency binding" and concerns per-market currency binding, price-fallback
#: order, and FX policy -- a different subject. Both strings below are
#: quoted verbatim from their respective sources; neither has been altered.
KN_101_DISCREPANCY = GroundTruthDiscrepancy(
    candidate_id="KN-101",
    ground_truth_claim="marketplace seller onboarding",
    ground_truth_source="benchmarks/examples/benchmark_case.example.json:ground_truth.notes",
    actual_content_summary="Regional price resolution and currency binding",
    actual_content_source="enterprise/knowledge/business-rules.json (KN-101.title / KN-101.body)",
    note=(
        "ground_truth.notes characterizes KN-101 as 'marketplace seller onboarding', "
        "an out-of-scope distractor topic. KN-101's actual, independently resolvable "
        "content is about per-market price/currency resolution for the Pricing "
        "Service (APP-007) -- not marketplace seller onboarding. This is documented "
        "here, not corrected: BC-0101 and BC-0102 are frozen historical experiments "
        "and neither the ground truth note nor KN-101's content has been changed. "
        "For future benchmark validity: a model deciding from real artifact content "
        "alone cannot be expected to reconstruct a benchmark rationale that is only "
        "present in a ground-truth note describing a different, unrelated subject -- "
        "any interpretation of why KN-101 is must_exclude that relies on the "
        "'marketplace seller onboarding' framing is not verifiable against what a "
        "Worker actually sees."
    ),
)
