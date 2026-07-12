# Bytesurge Confidence Engine — Algorithm Research

> **Proprietary — Bytesurge Runtime research. Not part of EnterpriseSim; not Apache-2.0.**
>
> © Bytesurge. Commercial runtime research. This document designs proprietary algorithms; it
> is not part of the open-source, Apache-2.0 EnterpriseSim project and is not governed by its
> license.

**EnterpriseSim interface satisfied:** `sdk.decision.ConfidencePolicy` — the `fuse(...)` and
`control_for(...)` methods (`ARCH-06` Decision Intelligence; `ARCH-04` Evaluation Layer;
normatively owned by `RFC-0009`). Honors `ADR-0013` (composable confidence), `ADR-0014`
(autonomy gated on confidence), `ADR-0017` (dual outcome/judgment confidence).

---

## 1. Problem statement

`sdk.decision.ConfidencePolicy` is the safety backbone of the Enterprise Cognitive Layer. It
exposes two methods:

```python
def fuse(self, inputs: Mapping[str, Confidence]) -> Confidence: ...
def control_for(self, fused: Confidence, risk_tier: int) -> Control: ...
```

`fuse` collapses the four per-layer confidences that `ARCH-06` §Confidence enumerates —
**context coverage** (`ARCH-01`, surfaced as `ContextObject.coverage_confidence`), **knowledge
authority** (`ARCH-02`), **experience applicability** (`ARCH-03`), and **evaluation judgment
confidence** (`ARCH-04`, *not* outcome confidence, per `ADR-0017`) — into a single scalar in the
closed interval `[0.0, 1.0]`. `control_for` maps that scalar plus a change's risk tier to a
`Control` (`PROCEED`, `RE_RETRIEVE`, `REPLAN`, `RETRY`, `ESCALATE`, `ABORT`).

The Bytesurge engineering problem is not "produce a number" — it is to produce an **honest,
calibrated, composable** number under an adversarial reality: the number gates autonomous action
on Tier 0 production systems, and every incentive in the loop pushes toward inflating it.
`RFC-0009 §4.3` binds any conforming `fuse` to five properties: **bounded**, **monotone**,
**weakest-link-sensitive**, **honesty-preserving** (no laundering a starved context into a high
score), and **degenerate-input-honest** (a missing input lowers confidence, it is not dropped).
Beyond conformance, Bytesurge must deliver **calibration**: decisions issued at fused 0.90 must
succeed ~90% of the time, measured continuously against realized `EVAL-###` outcomes. A
`ConfidencePolicy` that satisfies the algebra but is miscalibrated silently re-creates `ARCH-06`'s
overconfident-autonomy failure mode while nominally "gating."

This document designs the fusion combiner, the outcome-vs-judgment separation, the calibration
machinery (ECE / reliability diagrams / temperature scaling), and the risk-adaptive threshold map.

---

## 2. Approaches considered

Five concrete, named approaches. Approaches A–E are combiners for `fuse`; the calibration layer
(§2.F) is orthogonal and composes with any of them.

### A. Heuristic weakest-link combiner (weighted noisy-AND)
A closed-form combiner with per-input weights `wᵢ` and a conjunctive backbone. Candidate form:
`fused = min_i(cᵢ) · (1−λ) + λ · Πᵢ cᵢ^{wᵢ}`, where the `min` term guarantees weakest-link
sensitivity and the weighted geometric mean supplies smoothness and monotonicity. Weights start
uniform and are later tuned per task type by the Learning Engine (`RFC-0009 §8`). No training data
required to start; every term is inspectable.

### B. Bayesian fusion (Beta–Bernoulli posterior)
Treat each layer confidence as evidence about a latent "this decision will succeed" Bernoulli
variable. Maintain a Beta prior per (task-type, risk-tier) cell; each layer input contributes
pseudo-counts weighted by that layer's historically observed reliability. The fused value is the
posterior mean, and its variance yields a *confidence-on-the-confidence* (the `RFC-0009 §9`
"confidently medium vs. unsure" wish). Principled, naturally calibrated as counts accumulate, but
requires an accumulating outcome history and independence assumptions that rarely hold.

### C. Conformal prediction
Wrap the whole decision in a conformal layer: from a calibration set of past (inputs → outcome)
records, compute nonconformity scores and emit a fused value with a **distribution-free coverage
guarantee** — "at target error α, decisions issued above threshold τ fail at most α of the time,"
with finite-sample validity and no distributional assumptions. Strongest formal honesty guarantee
available; but it yields set/threshold semantics rather than a smooth composable scalar, and needs
an exchangeable calibration set that enterprise task drift violates.

### D. Learned calibration on a fused feature (Platt / isotonic / temperature scaling)
Keep a simple combiner (e.g., A) to produce a *raw* score, then learn a monotone calibration map
`g: raw → calibrated` from held-out (score, outcome) pairs. **Platt scaling** fits a logistic
`σ(a·s+b)`; **isotonic regression** fits a free monotone step function; **temperature scaling**
fits a single scalar `T` (the minimal, least-overfitting option). This is the standard fix for the
exact pathology `RFC-0009 §4.6` names — miscalibration — and directly optimizes the metric
Bytesurge is judged on (ECE). It is a *post-hoc* layer, not a combiner: it needs a combiner beneath.

### E. Ensemble disagreement / Dempster–Shafer
Two variance-based families. **Ensemble disagreement**: run K diverse retrieval/plan variants
(or K judge prompts) and treat their spread as inverse confidence — high agreement → high
confidence. **Dempster–Shafer**: model each layer as a mass function over
{success, failure, uncertain} and combine via Dempster's rule, explicitly representing *ignorance*
(unassigned mass) distinct from *conflict*. Both capture epistemic uncertainty that a point
combiner cannot, at the cost of K× compute (disagreement) or notorious counter-intuitive behavior
under high conflict (DS rule normalization).

### F. Calibration & measurement substrate (orthogonal, adopted regardless)
Independent of the combiner: maintain **reliability diagrams** (bin decisions by fused value, plot
predicted vs. realized success), report **Expected Calibration Error** (ECE), **Maximum
Calibration Error** (MCE), and **Brier score**, sliced by risk tier and task type. Fed by the
`ARCH-06` control-decision-accuracy signal ("were proceed/escalate calls vindicated?"), consumed by
the Learning Engine (`ARCH-05`) to re-fit thresholds. This is the honesty audit; it turns
calibration from an aspiration into a monitored SLO.

### Dual confidence (cross-cutting, `ADR-0017`)
Whatever combiner is chosen, the **evaluation input to `fuse` is the judgment confidence, never
the outcome confidence**. DI's question each turn is "how much can I trust this verdict enough to
act on it?" — reliability of the judgment, not quality of the work. A `partial` at high judgment
confidence is trustworthy negative information (replan); a `pass` at low judgment confidence is not
yet actionable (raise confidence first). Feeding outcome confidence would let a shaky-but-flattering
verdict authorize a high-stakes action — the laundering `RFC-0009 §4.3` forbids.

---

## 3. Trade-offs

| Approach | Honesty / weakest-link | Calibration | Cold-start | Compute | Explainability | Conformance to `RFC-0009 §4.3` |
|---|---|---|---|---|---|---|
| A. Heuristic weakest-link | Strong (min backbone) | Manual, drifts | Excellent (no data) | O(k) trivial | High (closed form) | Yes, by construction |
| B. Bayesian Beta | Moderate (mean can mask) | Good as counts grow | Poor (needs history) | O(k) + store | Moderate (posterior) | Needs min-guard added |
| C. Conformal | Strong (coverage proof) | Guaranteed under exchangeability | Poor (needs calib set) | O(n log n) calib | Moderate (threshold) | Partial (set semantics) |
| D. Learned calibration (on A) | Inherits A | **Best** (optimizes ECE) | Good (A works pre-fit) | O(k) + tiny fit | High if isotonic/temp | Yes (A backbone preserved) |
| E. Disagreement / DS | Strong (variance-aware) | Indirect | Good | **K× or heavy** | Low (DS opaque) | Yes (disagreement caps) |

Key tensions: **A** is the only approach that is honest and conformant on day one with zero data,
but its calibration is a human's guess. **D** is the only approach whose *objective* is the metric
Bytesurge is graded on, but it needs a combiner beneath and a steady stream of labeled outcomes. **B**
and **C** are the most principled but the most cold-start-hostile and the least aligned with the
smooth-composable-scalar contract. **E** buys epistemic honesty at real cost and, for DS, real
opacity.

---

## 4. Advantages

- **A (Heuristic weakest-link):** Conforms to all five `RFC-0009 §4.3` properties *by
  construction* — no training run can violate boundedness or monotonicity. Zero cold-start. Every
  digit traceable to a named layer input, which is exactly the `ADR-0013` composability mandate and
  makes the number defensible in an audit.
- **D (Learned calibration over A):** Directly attacks miscalibration, the first-class concern of
  `RFC-0009 §4.6`. Temperature scaling adds exactly one parameter — negligible overfitting risk and
  fully explainable ("we globally sharpened/softened by T=1.3"). Isotonic gives the best empirical
  ECE when data is plentiful. Post-hoc, so it never touches the honest combiner's algebra.
- **B (Bayesian):** Confidence *intervals*, not just points (`RFC-0009 §9` future). Naturally
  incorporates per-layer reliability as learned pseudo-counts.
- **E (Disagreement):** Surfaces epistemic uncertainty invisible to point combiners — the case
  where every layer is individually confident but they *disagree* about the same fact.

---

## 5. Weaknesses

- **A:** Weights are hand-set until the Learning Engine tunes them; a wrong weight is a silent
  miscalibration. The `λ` blend between `min` and geometric mean is itself a magic number.
- **B:** Independence between layer confidences is assumed and false (context coverage and
  experience applicability co-vary). Cold cells (rare task-type × Tier-0 combinations) stay at the
  prior for a long time, i.e. exactly where stakes are highest.
- **C:** Exchangeability breaks under enterprise drift (a new service, a new standard); the coverage
  guarantee then quietly voids. Set-valued output is an impedance mismatch with a scalar contract.
- **D:** Needs a labeled outcome stream; on brand-new task types it has nothing to fit and must fall
  back to raw A. Isotonic overfits on small samples (mitigate with binning / monotone smoothing).
- **E:** K× inference cost collides with the reasoning budget (`RFC-0029`); Dempster's rule is
  famously counter-intuitive under high conflict and hard to explain to an auditor.

---

## 6. Computational complexity

Let `k` = number of layer inputs (fixed, ~4–6), `n` = size of the calibration history, `K` =
ensemble breadth.

- **`fuse` (A, B):** O(k) per call — a handful of multiplies/comparisons. Negligible against the LLM
  reasoning call it gates.
- **`fuse` (D = A + calibration map):** O(k) at inference (evaluate a logistic or step lookup);
  calibration *fit* is O(n) for temperature (1-D line search), O(n log n) for isotonic (PAVA sort),
  run **offline/asynchronously** by the Learning Engine, never on the hot path.
- **`fuse` (C):** O(n log n) to build the calibration quantiles offline; O(log n) per decision for
  the threshold lookup.
- **`fuse` (E, disagreement):** dominated by K parallel reasoning variants — K× the LLM cost, the
  single most expensive option. DS combination itself is O(k · |frame|), trivial.
- **`control_for`:** O(1) — a table lookup over `(band, risk_tier)`.
- **Calibration monitoring (F):** O(n) to bin and compute ECE/Brier per reporting window; batched.

The hot path is O(k) for every viable choice. The only complexity that matters lives **off** the
decision path, which is the correct place for it.

---

## 7. Enterprise scalability

- **Per-decision cost is constant** and dwarfed by the model call, so `fuse`/`control_for` add no
  meaningful latency at any throughput. This is the decisive scalability fact.
- **Calibration state is small and shardable:** reliability histograms and calibration maps are
  keyed by (task-type, risk-tier); millions of decisions compress to a few thousand histogram cells.
  Fits in memory; refit on a schedule, not per request.
- **Multi-tenant calibration:** each Worker fleet / tenant can carry its own calibration map while
  sharing the combiner and the code path. `RFC-0009 §9` cross-Worker calibration lets a new Worker
  type warm-start from a sibling's curve since the confidence model is domain-agnostic (`ARCH-07`).
- **Drift management at scale:** enterprise reality is non-stationary (new services, new CANON
  standards). Calibration must be **windowed / decayed**, and drift alarms (rising ECE in a slice)
  must trigger refit. Approach C's exchangeability assumption is the least scalable under this drift;
  D with a rolling window is the most operationally robust.
- **Ensemble (E) does not scale** as a default: K× reasoning cost per decision is untenable fleet-wide.
  It is viable only as a *targeted* escalation tool on the highest-stakes Tier 0 decisions.

---

## 8. Explainability

Explainability is not optional here — the fused number authorizes autonomous production changes and
must survive audit. Every `DecisionObject` already carries `inputs: Mapping[str, Confidence]` and
`fused_confidence` (`sdk.objects`), so the raw material is on the trace by contract.

- **A** is the most explainable: "fused = 0.62 because context coverage was 0.62 and dominated the
  weakest-link term; knowledge (0.95) and experience (0.88) could not compensate." A single sentence
  fully reconstructs the decision.
- **D** stays explainable with **temperature** ("raw 0.71 → 0.63 after global T=1.2 calibration") and
  **isotonic** (a monotone step chart), but a **Platt** logistic is slightly less legible.
- **B** explains as a posterior with pseudo-counts — moderate; requires the reader to understand Beta
  updating.
- **C** explains as "above the τ that guarantees ≤α error on the calibration set" — a coverage claim,
  not a decomposition of *why this decision*.
- **E / Dempster–Shafer** is the worst: conflict-normalization behavior is counter-intuitive and
  hard to defend to a non-specialist auditor.

Across all combiners, Bytesurge attaches a **confidence rationale** to the trace: the ranked layer
inputs, which input was decisive (bound the fused value), the calibration transform applied, and the
`control_for` band and risk tier that produced the `Control`. This makes both the fusion and the
autonomy decision reconstructable — the `ARCH-06` "trace every decision" best practice.

---

## 9. Recommendation

**Adopt a hybrid: Approach A (heuristic weakest-link combiner) as the always-on backbone, wrapped by
Approach D (learned calibration, temperature-first then isotonic), with Approach F (ECE/reliability
monitoring) as a permanent SLO and Approach E (ensemble disagreement) reserved as a targeted Tier-0
escalation probe.**

Rationale:

1. **Conformance and cold-start come from A.** The five `RFC-0009 §4.3` properties are satisfied by
   construction, on day one, with no training data — critical because the highest-stakes decisions
   (rare Tier 0 task types) are exactly where a data-hungry method (B/C/D-alone) has the least data.
   The `min`-dominated backbone is the algebraic embodiment of `RFC-0009 §4.3`'s weakest-link and
   honesty-preserving rules, so we cannot accidentally launder a starved context.

2. **Calibration comes from D, layered on top.** A's hand-set weights guarantee honest *ordering* but
   not honest *magnitude*; D closes that gap by fitting the raw score to realized outcomes. Start with
   **temperature scaling** (one parameter, minimal overfitting, fully explainable) and graduate a
   slice to **isotonic** only once that slice has enough labeled outcomes to justify it. Because D is
   post-hoc and monotone, it preserves every property A guarantees.

3. **Honesty is monitored, not assumed (F).** ECE, MCE, Brier and reliability diagrams — sliced by
   risk tier and task type, fed by the `ARCH-06` control-decision-accuracy signal — turn `RFC-0009
   §4.6`'s calibration mandate into a live SLO. Rising ECE in a slice triggers a Learning-Engine refit
   (`ARCH-05`), which also owns the per-task-type weight tuning A defers to it.

4. **`control_for` is a risk-adaptive band table** (`RFC-0009 §4.4`): monotone in confidence, tighter
   for Tier 0 / PCI, looser for Tier 2/3, with the hard invariant that a high-stakes change never
   `PROCEED`s at low fused confidence (`ADR-0014`), and always composing with — never overriding — the
   `PolicyGuard` (`RFC-0030`, `ADR-0041`): a policy block forces escalation regardless of the band.
   Bands are tuned/learned; the *shape* is normative.

5. **Dual confidence is wired in (`ADR-0017`):** `fuse` consumes evaluation **judgment** confidence.
   This is a data-plumbing invariant, enforced by a schema check, independent of combiner choice.

6. **E is a scalpel, not a default.** K× ensemble disagreement is too expensive fleet-wide but is the
   right tool to *break ties* on the small population of Tier-0/PCI decisions sitting on a band
   boundary — spend the compute only where the stakes justify it.

**Deferred:** B (Bayesian) and C (conformal) are strong future directions once a rich exchangeable
outcome history exists — B for native confidence *intervals* (`RFC-0009 §9`), C for a formal coverage
guarantee on stable, high-volume task types. Neither is a day-one choice because both are cold-start-
hostile precisely where autonomy matters most. The A+D+F hybrid is honest from the first decision and
gets *calibrated*, not just *ordered*, as outcomes accrue — the correct maturation curve for a safety
backbone.
