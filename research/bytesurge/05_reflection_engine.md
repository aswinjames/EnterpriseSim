# Bytesurge Reflection Engine — Algorithm Research

> **Proprietary — Bytesurge Runtime research. Not part of EnterpriseSim; not Apache-2.0.**
>
> © Bytesurge. Commercial runtime research. This document designs proprietary algorithms; it
> is not part of the open-source, Apache-2.0 EnterpriseSim project and is not governed by its
> license.

**EnterpriseSim interface satisfied:** `sdk.learning.Reflector` — the `reflect(...)` and
`diagnose(...)` methods returning `ReflectionObject` and `RootCause` (`ARCH-05` Learning Engine;
`ARCH-04` Evaluation Layer; normatively owned by `RFC-0016`). Honors `ADR-0035` (root cause, not
symptom) and `ADR-0034` (loop closure defines learning).

---

## 1. Problem statement

`sdk.learning.Reflector` is the first half of the Learning Engine. Its contract:

```python
def reflect(self, evaluation: EvaluationObject, plan: PlanningObject,
            context: ContextObject) -> ReflectionObject: ...
def diagnose(self, reflection: ReflectionObject) -> RootCause: ...
```

Given an evaluated (often failed) execution, the Reflector must explain **why** the outcome
occurred — the *root cause*, not the surface symptom — and emit a `ReflectionObject` (`REF-###`)
carrying a factual `what_happened` narrative, a `root_cause` classified into the bounded taxonomy
of `RFC-0016 §4.3` (`missing_knowledge`, `dropped_context`, `flawed_plan`, `tool_error`,
`model_error`, `standards_gap`, `evaluation_defect`), transferable `lessons[]`, and proposed
`policy_updates[]`. `diagnose` surfaces the dominant `RootCause` with a `Confidence`.

The engineering difficulty is that the LLM is **stateless** — it cannot remember the failure it
must explain. The Reflector must *reconstruct causation from durable evidence*: the plan, the
`ExecutionObject` artifacts, the `EvaluationObject` with its evidence links, and — most decisively —
the `ContextObject` provenance, especially `excluded[]`, the dropped-candidate log. `ARCH-05` Best
Practice 5 and `RFC-0016 §4.4` both insist: the single most common true cause is a context item that
was *available but excluded for budget*, so the pipeline must inspect `excluded[]` before ever
concluding `missing_knowledge`.

Two failure modes are named enemies (`ARCH-05` Failure Modes; `RFC-0016 §2`):

- **Hindsight bias** — the reflection narrates the known outcome and rationalizes it, rather than
  finding the cause that was *actually operative before* the outcome was known.
- **Symptom fixation** — it fixes the visible error (a failing test) instead of the systemic origin
  (a planning heuristic that never asked for a negative assertion), guaranteeing recurrence.

Every claim must be **evidence-grounded** (an unsourced clause is rejected by the validator,
mirroring `ARCH-04`'s "no score without evidence"), diagnoses must carry honest **root-cause
confidence** (diffuse failures yield low-confidence *hypothesis* lessons, never promoted on one
occurrence), and lessons must be **transferable** — indexed by `situation` so `ARCH-03` can retrieve
them. The Reflector writes nothing durable but the `REF-###` itself (`RFC-0016 §4.1`); propagation is
`RFC-0017`'s job.

---

## 2. Approaches considered

### A. LLM-as-analyst with a structured schema
Route the correlated evidence bundle (plan, execution, evaluation, context provenance) to a model via
the Gateway (`ARCH-07`) under a **fixed structured schema** that forces the model to emit
`what_happened`, a taxonomy `category`, per-clause evidence citations, `lessons[]`, and
`policy_updates[]` — never free prose. Run under the replay controls of `RFC-0024` (fixed seed, pinned
model class) so the reflection is regenerable and auditable (`RFC-0016 §4.5`). A deterministic
validator rejects any output whose `detail` lacks an artifact ID. This is the natural reading of
"model-assisted step to phrase `what_happened` or propose lessons" in `RFC-0016 §4.5`.

### B. Causal tracing over the decision trace
Treat the immutable decision trace (`RFC-0023`, the ordered `DecisionObject`s with their
`fused_confidence` and per-layer `inputs`) as a causal chain and walk it backward from the failing
`EVAL-###` line to the earliest decision whose inputs already contained the seed of the failure. The
first point where a decisive layer input was low (e.g., `coverage_confidence` collapsed at retrieval)
is the candidate root cause. Largely deterministic, exploits data the ECL already emits, and directly
attacks hindsight bias by anchoring to *what was known at each step*, not the outcome.

### C. Counterfactual / ablation analysis
Ask the falsifiable question: *what minimal change would have prevented this?* Re-run (or dry-run) the
decision with one variable perturbed — re-inject a specific `excluded[]` candidate, add the missing
negative-assertion step, swap the model class — and observe whether the predicted outcome flips. If
re-injecting the dropped loyalty rule flips the verdict, `dropped_context` is confirmed causally, not
merely correlationally. This is the strongest evidence a diagnosis can carry and feeds directly into
`RFC-0016 §9`'s counterfactual-reflection future.

### D. Retrieval of similar past reflections
Before diagnosing from scratch, retrieve prior `REF-###` whose `situation` (task_type, apps,
failure_class) matches the current one, via the same `sdk.experience.ExperienceRetriever` machinery
(`ARCH-03`, Bytesurge algorithm 02). Prior root causes for near-identical failures are strong priors —
"the last three `APP-003` guest-flow failures were all `dropped_context`." Cheap, warm-starts
diagnosis, and reinforces systemic-pattern detection, but risks anchoring on a stale prior for a
genuinely novel failure.

### E. Rule-based classifiers over signals
Deterministic decision rules over structured signals map directly to the taxonomy without any model
call: `excluded[]` contains a high-relevance item whose content matches the failing assertion →
`dropped_context`; no `KN-###` covers the decisive fact and `excluded[]` is clean → `missing_knowledge`;
`WorkerArtifact.status` shows a tool crash → `tool_error`; a CANON standards line failed that no gate
covered → `standards_gap`; `EVAL-###.judgment_confidence` is low → `evaluation_defect`. Fully
explainable, fully reproducible, zero model cost — but brittle on ambiguous or multi-cause failures.

---

## 3. Trade-offs

| Approach | Root-cause depth | Hindsight-bias resistance | Determinism / replay | Compute cost | Transferable lessons | Handles novel failures |
|---|---|---|---|---|---|---|
| A. LLM-as-analyst | High (semantic) | **Weak** (sees outcome) | Only via seed pinning | 1 model call | Strong (rich phrasing) | Strong |
| B. Causal trace | Moderate–high | **Strong** (per-step knowledge) | High (deterministic walk) | O(trace) cheap | Moderate | Moderate |
| C. Counterfactual | **Highest** (proven) | Strong (falsifiable) | High if dry-run pinned | **High** (re-run) | Strong (minimal fix) | Strong |
| D. Similar-reflection retrieval | Moderate (prior) | Moderate | High | Cheap (ANN lookup) | Reuses proven | **Weak** (anchors) |
| E. Rule-based | Shallow–moderate | Strong (no narration) | **Total** | Trivial | Weak (templated) | **Weak** |

The core tension: the approaches strongest at *depth and transferable phrasing* (A, C) are the ones
most exposed to *hindsight bias* (A) or *cost* (C), while the approaches strongest at *determinism and
bias-resistance* (B, E) are shallow on genuinely novel, multi-cause failures. No single approach both
resists hindsight bias and produces rich, transferable lessons — which is why the recommendation is a
staged pipeline.

---

## 4. Advantages

- **A (LLM-as-analyst):** Only approach that produces genuinely *transferable* natural-language
  lessons ("when adding a guest flow to `APP-003`, guard `APP-015` provisioning, because guest orders
  must not create loyalty accounts") indexable for `ARCH-03` retrieval. Handles novel failures the
  rules never anticipated. Schema-forcing + validator + seed-pinning tame its worst tendencies.
- **B (Causal trace):** The structurally correct antidote to hindsight bias — it reasons over *what
  each `DecisionObject` knew at the time*, using data (`inputs`, `fused_confidence`) the ECL already
  records (`RFC-0023`), so it is nearly free and fully replayable.
- **C (Counterfactual):** Converts a *correlation* ("the loyalty rule was dropped and it failed") into
  a *demonstrated cause* ("re-injecting it flips the outcome"). This is the only approach that can
  raise `root_cause.confidence` on principled grounds rather than assertion.
- **D (Similar-reflection retrieval):** Cheap, warm-starts diagnosis with proven priors, and is the
  raw material for `RFC-0017 §4.5` systemic-pattern detection (same-category recurrence).
- **E (Rule-based):** Total determinism and zero cost make it the ideal *first-pass classifier and
  validator* — it can settle the clear cases and cheaply flag the `dropped_context`-vs-`missing_
  knowledge` distinction that `RFC-0016 §4.4` mandates checking.

---

## 5. Weaknesses

- **A:** Structurally prone to hindsight bias — the model sees the outcome and can rationalize any
  narrative to fit it. Non-deterministic without strict seed/model-class pinning. Can fabricate
  evidence citations (mitigated by the validator rejecting unsourced clauses). Cost per execution
  collides with `RFC-0029` budgets, so it cannot run at full depth on every passing execution.
- **B:** Depends on decision-trace richness; if a layer under-reports its confidence inputs, the walk
  loses signal. Finds *where* confidence collapsed, not always *why* semantically.
- **C:** Expensive — a re-run or high-fidelity dry-run per hypothesis. A dry-run's predicted outcome is
  itself model-estimated and may be wrong. Combinatorial if many variables are perturbed.
- **D:** Anchoring risk — a stale or over-broad prior mislabels a novel failure as a familiar one,
  entrenching a wrong lesson (the over-generalization failure of `ARCH-05`).
- **E:** Brittle. Genuinely novel or multi-cause failures do not fit the rules and get forced into a
  mediocre bucket (the `RFC-0016 §5` taxonomy-rigidity drawback); lessons are templated, not
  transferable.

---

## 6. Computational complexity

Let `t` = decision-trace length, `x` = size of `excluded[]`, `h` = number of counterfactual hypotheses
tried, `N` = corpus of prior reflections.

- **A:** One (bounded, `RFC-0029`) model call — cost dominated by prompt tokens (the evidence bundle),
  O(context-window). Validation is O(clauses).
- **B:** O(t) backward walk over the trace with O(1) work per node (compare layer inputs to a
  threshold) — effectively free.
- **C:** O(h) counterfactual evaluations; each is either a cheap dry-run (one model call) or a full
  re-execution (expensive, tool-invoking). Dominant cost when enabled; bounded by capping `h` to the
  top-ranked hypotheses from B/E.
- **D:** O(log N) approximate-nearest-neighbor lookup over the reflection index (reusing algorithm 02's
  ANN structures) — cheap.
- **E:** O(x + gates) deterministic checks — trivial.

The naturally cheap stages (B, D, E) run always; the expensive stages (A, C) run **selectively**,
gated by outcome severity and remaining reasoning budget (`RFC-0029`), matching `RFC-0016 §5`'s
"depth proportional to outcome and cost budget."

---

## 7. Enterprise scalability

- **Asynchronous by design.** Reflection is off the critical execution path (`ARCH-05` "asynchronous
  but bounded"), so its latency is a *learning-lag* signal, not a task-latency cost. It scales
  horizontally: a queue of `EVAL-###` events fanned out to stateless reflection workers.
- **Tiered depth controls cost at fleet scale.** The cheap deterministic pass (B+D+E) runs on *every*
  execution; the expensive A/C stages run only when the cheap pass is inconclusive or the outcome is
  high-severity. This keeps aggregate model spend sublinear in execution volume — essential when a
  fleet produces millions of executions.
- **Reflection corpus grows without bound** and must be indexed (ANN over `situation`) and periodically
  consolidated (dedup near-identical `REF-###`), sharing infrastructure with algorithm 02 and the
  memory-consolidation work of algorithm 06.
- **Determinism enables replay at scale** (`RFC-0024`): a disputed reflection can be regenerated
  identically for audit, and A/B evaluation of reflection strategies (the `ARCH-05` meta-learning
  future) becomes possible because runs are reproducible.
- **Feedback-poisoning guard scales the trust boundary:** reflections built on low-`judgment_confidence`
  evaluations inherit a discount and are marked provisional (`RFC-0016 §4.4`) — automatic, per-object,
  no manual triage.

---

## 8. Explainability

Explainability is intrinsic to this engine — a reflection *is* an explanation, and its whole value is
being inspectable. The design guarantees it structurally:

- **Evidence-first validator (`RFC-0016 §4.4`):** every clause in `root_cause.detail` cites a concrete
  artifact ID or the reflection is rejected. An auditor can follow each causal claim to the `PR-####`,
  `TR-####`, `CTX-###.excluded[]` entry, or `EVAL-###` line that supports it.
- **Bounded taxonomy** makes root causes *comparable and aggregable* across thousands of reflections
  (the input to systemic-pattern detection); free-text `detail` carries the nuance, the `category`
  carries the structure.
- **Per-approach legibility:** E (rules) and B (causal walk) are fully transparent — the rule that
  fired or the trace node where confidence collapsed *is* the explanation. C (counterfactual) is the
  most *convincing* — "re-injecting `excluded[]` item X flips the verdict" is a demonstration, not an
  assertion. A (LLM) is legible only because the schema + validator force citations and the seed
  pinning makes it replayable; an un-schematized LLM reflection would be the *least* explainable.
- **Root-cause confidence is explicit and honest:** a diffuse failure produces a low-confidence
  *hypothesis* lesson flagged for corroboration, never dressed up as certainty (`RFC-0016 §4.4`),
  which is itself a form of honest explanation.

---

## 9. Recommendation

**Adopt a staged hybrid pipeline: E → B → D as an always-on deterministic core, escalating to A
(schema-forced, validated, seed-pinned LLM-as-analyst) for depth and transferable lessons, with C
(counterfactual confirmation) invoked selectively to raise `root_cause.confidence` on high-severity or
contested diagnoses.** Concretely, the `Reflector` pipeline is:

1. **Ingest & correlate** (`RFC-0016 §3` stage 1): gather plan, execution, evaluation, and — first —
   `ContextObject.excluded[]`.
2. **Deterministic first pass (E):** rule-based classifier over signals. Critically, it enforces the
   `RFC-0016 §4.4` ordering — inspect `excluded[]` and rule out `dropped_context` *before* concluding
   `missing_knowledge`. Clear cases are settled here at zero model cost.
3. **Causal trace walk (B):** anchor the diagnosis to *what was known at each `DecisionObject`*, not to
   the outcome. This is the primary structural defense against **hindsight bias** — it forces the
   Reflector to explain the failure from the pre-outcome knowledge state.
4. **Prior-reflection retrieval (D):** attach matching past `REF-###` as priors and systemic-pattern
   evidence — used as *support*, never as an override, to avoid anchoring on novel failures.
5. **LLM-as-analyst (A):** on inconclusive or high-value cases, synthesize the factual `what_happened`,
   the transferable `lessons[]`, and concrete `policy_updates[]`. The structured schema + evidence
   validator + `RFC-0024` seed/model-class pinning convert A's raw power into an auditable,
   reproducible artifact and neutralize fabrication.
6. **Counterfactual confirmation (C):** for high-severity failures or when `diagnose` confidence sits
   below the promotion-relevant band, run the minimal counterfactual (re-inject the suspected dropped
   item / add the missing step) to *demonstrate* causation and legitimately raise
   `root_cause.confidence`. Cap hypotheses to the top candidates ranked by B/E to bound cost.

Why this composition:

- **It directly answers the two named enemies.** B (per-step knowledge) is the antidote to hindsight
  bias; C (minimal-fix falsification) and the taxonomy discipline are the antidote to symptom fixation —
  a symptom fix would fail the counterfactual test.
- **It respects the budget (`RFC-0029`).** The always-on core (E+B+D) is nearly free; the expensive
  stages (A, C) fire *proportionally to outcome severity and remaining budget* (`RFC-0016 §5`), which
  is exactly how the RFC frames depth-of-reflection.
- **It is honest and reproducible by construction.** Evidence-first validation, bounded taxonomy,
  explicit hypothesis-level confidence, and seed-pinned replay (`RFC-0024`) satisfy every `RFC-0016
  §4.4/§4.5` honesty and determinism rule.
- **It produces *transferable* lessons.** A's schema-forced natural-language lessons, `situation`-tagged
  for `ARCH-03` retrieval and validated against evidence, are what the Learning Engine (algorithm 06)
  distills into durable `EXP-###` — closing the flywheel `RFC-0016 §4.6` depicts.

**Deferred:** full **meta-reflection** (learning which reflection strategies find true root causes,
`RFC-0016 §9`) and **causal incident graphs** (`INC-#### → cause → REF-### → prevention`) are natural
extensions once the reflection corpus and its loop-closure outcomes are large enough to learn over —
they sit on top of, not instead of, the E→B→D→A→C pipeline recommended here.
