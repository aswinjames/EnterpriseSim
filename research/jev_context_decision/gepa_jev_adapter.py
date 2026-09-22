"""X-GEPA-1's GEPAAdapter: lets GEPA optimize JEV's decision-policy text.

GEPA (https://github.com/gepa-ai/gepa, ``pip install gepa``) optimizes any
system with textual parameters against any evaluation metric by having a
reflection LM read execution traces and propose improved text. Plugging in a
custom system means implementing ``gepa.core.adapter.GEPAAdapter``'s two
required methods: ``evaluate()`` and ``make_reflective_dataset()``. This
module implements those two methods against the *existing, unmodified*
``JevProvider`` and ``DecisionCase`` -- it does not add a new provider, a new
transport, or a new scoring function.

This class is written as a plain duck-typed adapter (it does not import or
subclass ``gepa.core.adapter.GEPAAdapter`` directly) so this module -- and
its offline tests -- import and run correctly whether or not the ``gepa``
package is installed. ``gepa.optimize(..., adapter=JevGepaAdapter(...))``
only needs an object with the right two methods; GEPAAdapter is a typed
Protocol, not a required base class. Only ``run_experiment_x_gepa_1.py``'s
``--live`` path needs ``gepa`` actually importable.

What GEPA optimizes here: the three JEV-facing text fields of a
``DecisionCase`` -- ``jev_instructions``, ``jev_criteria_true``,
``jev_criteria_false`` (see ``providers/base.py``). Everything else about
the criterion (``task_statement``, ``task_scope``, the model, the transport)
stays exactly as BC-0101 defined it. KN-101 and KN-047 are never part of the
candidate dict, the trainset, the valset, or the testset -- see
``experiment_x_gepa_1_candidates.py``.

The per-example score GEPA optimizes against is a Brier-score complement
(1 - (p_include - target)^2, in [0, 1], higher is better) over JEV's own
``noul`` probability -- not raw classification accuracy -- so GEPA gets
calibration signal, not just a binary right/wrong.

Every real ``provider.decide()`` call in ``evaluate()`` goes through
``decide_with_retry()``: bounded exponential-backoff retry on transient
network failures only (``TimeoutError``/``socket.timeout``/
``urllib.error.URLError``), resending the exact same request each attempt.
Application-level errors (a real OpenRouter error response, a misconfigured
provider) are never retried -- they propagate on the first attempt, same as
before this was added.
"""

from __future__ import annotations

import socket
import time
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .experiment_x_gepa_1_candidates import GepaDataInst
from .providers.base import BC_0101, DecisionCase
from .providers.jev_provider import JevProvider

#: The exact keys GEPA's ``seed_candidate`` / ``candidate`` dicts must use.
#: These map 1:1 onto the corresponding ``DecisionCase`` fields.
COMPONENT_KEYS: tuple[str, ...] = ("jev_instructions", "jev_criteria_true", "jev_criteria_false")

#: Exceptions treated as transient/retryable -- purely network-level failures.
#: Deliberately excludes OpenRouterError (a real non-2xx response, e.g. auth or
#: a bad request) and ProviderNotConfigured -- those are not transient and must
#: propagate immediately, not be retried. socket.timeout is TimeoutError's alias
#: on Python >=3.10 (listed anyway for clarity, matching the exact set specified
#: for this retry policy).
TRANSIENT_EXCEPTIONS: tuple[type[BaseException], ...] = (
    TimeoutError,
    socket.timeout,
    urllib.error.URLError,
)


def decide_with_retry(provider: Any, candidate: Any, case: DecisionCase, *,
                       max_attempts: int = 3, base_delay: float = 2.0) -> Any:
    """``provider.decide(candidate, case=case)`` with bounded exponential-backoff
    retry on transient network failures only.

    Every attempt resends the exact same ``candidate``/``case`` -- nothing about
    the request changes between retries. Non-transient errors (an actual
    OpenRouter error response, a misconfigured provider, etc.) propagate on the
    first attempt, unretried. After ``max_attempts`` transient failures, the
    last exception is re-raised (not swallowed) so the caller's own
    checkpointing can react to a real, unrecovered failure.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return provider.decide(candidate, case=case)
        except TRANSIENT_EXCEPTIONS:
            if attempt >= max_attempts:
                raise
            time.sleep(base_delay * (2 ** (attempt - 1)))


def seed_candidate_from_bc_0101() -> dict[str, str]:
    """The baseline/seed text GEPA starts from: BC-0101's own criterion,
    copied as plain strings (BC_0101 itself is never mutated)."""
    return {
        "jev_instructions": BC_0101.jev_instructions,
        "jev_criteria_true": BC_0101.jev_criteria_true,
        "jev_criteria_false": BC_0101.jev_criteria_false,
    }


def case_from_candidate_dict(component_values: Mapping[str, str], *, id_suffix: str = "seed") -> DecisionCase:
    """Build a DecisionCase for one GEPA candidate's text.

    Everything except the three optimized fields is copied unchanged from
    BC_0101 (task_statement, task_scope) -- BC_0101 itself is never mutated,
    this only reads its fields to construct a brand-new DecisionCase.
    """
    return DecisionCase(
        id=f"X-GEPA-1-{id_suffix}",
        prompt_version=f"x-gepa-1-pilot-v1-{id_suffix}",
        task_statement=BC_0101.task_statement,
        jev_instructions=component_values["jev_instructions"],
        jev_criteria_true=component_values["jev_criteria_true"],
        jev_criteria_false=component_values["jev_criteria_false"],
        task_scope=BC_0101.task_scope,
    )


# --- EvaluationBatch: use gepa's real dataclass when available, else a
# structurally-identical local shim so this module works without gepa installed. ---
try:
    from gepa.core.adapter import EvaluationBatch as _GepaEvaluationBatch  # type: ignore
except ImportError:  # pragma: no cover - exercised only when gepa is not installed
    _GepaEvaluationBatch = None


@dataclass
class _LocalEvaluationBatch:
    outputs: list
    scores: list
    trajectories: list | None = None
    objective_scores: list | None = None
    num_metric_calls: int | None = None


def _evaluation_batch(outputs: list, scores: list, trajectories: list | None) -> Any:
    cls = _GepaEvaluationBatch or _LocalEvaluationBatch
    return cls(outputs=outputs, scores=scores, trajectories=trajectories)


@dataclass
class JevGepaAdapter:
    """GEPAAdapter for optimizing JEV's per-candidate decision-policy text.

    ``provider`` defaults to a real ``JevProvider()`` (requires
    ``OPENROUTER_API_KEY`` and makes live calls) but accepts any object with
    a ``decide(candidate, *, case=...)`` method -- tests pass a fake here so
    the adapter's own logic (score computation, reflective-dataset shape) is
    fully covered without network access.
    """

    provider: Any = field(default_factory=JevProvider)
    #: GEPA's engine reads this attribute directly (``self.adapter.propose_new_texts
    #: is not None``), not via getattr -- it must exist even when unused. None
    #: means "use GEPA's default reflective proposer", which is what we want.
    propose_new_texts: Any = None

    def evaluate(self, batch: Sequence[GepaDataInst], candidate: Mapping[str, str],
                 capture_traces: bool = False) -> Any:
        case = case_from_candidate_dict(candidate, id_suffix="candidate")
        outputs: list[dict] = []
        scores: list[float] = []
        trajectories: list[dict] | None = [] if capture_traces else None

        for data_inst in batch:
            artifact = data_inst.load()
            decision = decide_with_retry(self.provider, artifact, case)
            p_include = decision.confidence if decision.verdict == "include" else 1.0 - (decision.confidence or 0.5)
            target = 1.0 if data_inst.target_verdict == "include" else 0.0
            score = 1.0 - (p_include - target) ** 2  # Brier-complement, higher is better

            output = {
                "candidate_id": data_inst.candidate_id,
                "verdict": decision.verdict,
                "confidence": decision.confidence,
                "p_include": p_include,
                "rationale": decision.rationale,
            }
            outputs.append(output)
            scores.append(score)
            if capture_traces:
                trajectories.append({
                    "candidate_id": data_inst.candidate_id,
                    "candidate_title": artifact.title,
                    "candidate_body": artifact.body,
                    "category": data_inst.category,
                    "target_verdict": data_inst.target_verdict,
                    "decision_verdict": decision.verdict,
                    "p_include": p_include,
                    "confidence": decision.confidence,
                    "rationale": decision.rationale,
                    "score": score,
                })

        return _evaluation_batch(outputs, scores, trajectories)

    def make_reflective_dataset(self, candidate: Mapping[str, str], eval_batch: Any,
                                 components_to_update: Sequence[str]) -> Mapping[str, Sequence[Mapping[str, Any]]]:
        trajectories = eval_batch.trajectories
        if not trajectories:
            raise ValueError(
                "make_reflective_dataset requires eval_batch.trajectories -- "
                "call evaluate(..., capture_traces=True) first"
            )

        records = []
        for t in trajectories:
            correct = t["decision_verdict"] == t["target_verdict"]
            feedback = (
                f"Candidate category (frozen X-RICH-1 classification): {t['category']}. "
                f"Correct verdict for this category: {t['target_verdict']}. "
                f"Policy verdict: {t['decision_verdict']} (P(include)={t['p_include']:.3f}, "
                f"confidence={t['confidence']:.3f}). "
                + ("Correct." if correct else
                   f"Incorrect -- this is a {t['category']} artifact and should have been "
                   f"'{t['target_verdict']}'d. Rationale given: {t['rationale']}")
            )
            records.append({
                "Inputs": {
                    "candidate_id": t["candidate_id"],
                    "candidate_title": t["candidate_title"],
                    "candidate_body": t["candidate_body"],
                },
                "Generated Outputs": {
                    "verdict": t["decision_verdict"],
                    "confidence": t["confidence"],
                },
                "Feedback": feedback,
            })

        # Single per-candidate decision call informed jointly by all three text
        # fields -- there is no separate "stage" per component, so every
        # updated component gets the same reflective evidence.
        return {component: records for component in components_to_update}
