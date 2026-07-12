# Bytesurge Learning Engine — Algorithm Research

> **Proprietary — Bytesurge Runtime research. Not part of EnterpriseSim; not Apache-2.0.**
>
> © Bytesurge. Commercial runtime research. This document designs proprietary algorithms; it
> is not part of the open-source, Apache-2.0 EnterpriseSim project and is not governed by its
> license.

**EnterpriseSim interface satisfied:** `sdk.learning.LearningEngine` — `distill(...)`, `emit(...)`,
`loop_closed(...)`, `systemic_patterns(...)`, and the associated `PromotionPolicy.ready(...)`
(`ARCH-05` Learning Engine; normatively owned by `RFC-0017`, with promotion in `RFC-0018`). Honors
**`ADR-0003` (learning lives outside the model — no fine-tuning)**, `ADR-0034` (loop closure defines
learning), and `ADR-0036` (corroboration before promotion).

---

## 1. Problem statement

`sdk.learning.LearningEngine` is the second half of the Learning Engine and the hinge of CANON's
continuous-improvement flywheel. Its contract:

```python
def distill(self, reflection: ReflectionObject) -> ExperienceObject: ...
def emit(self, reflection: ReflectionObject) -> Sequence[LearningEvent]: ...
def loop_closed(self, learning_event: CanonicalId) -> bool: ...
def systemic_patterns(self, window: Mapping[str, object]) -> Sequence[LearningEvent]: ...
```

It consumes the `ReflectionObject`s produced by the Reflector (algorithm 05) and converts them into
**durable improvement that lives entirely outside the model** (`ADR-0003`, `ARCH-05` "Learning exists
outside the model"). The LLM's weights never change. A better Worker tomorrow is *the same stateless
model given a better Context* assembled from a richer Experience and Knowledge base and tuned
retrieval/planning/routing policies. The engine must:

1. **Distill** reflections into reusable, `situation`-linked `ExperienceObject`s (`EXP-###`),
   append-only, carrying a `value` map (`application_frequency`, `outcome_lift`, …).
2. **Emit** typed, immutable `LearningEvent`s (`experience_written`, `promotion_proposed`,
   `policy_updated`, `pattern_detected`) onto the Signals Bus and their targets (`RFC-0017 §3`).
3. **Update policies** — versioned retrieval/planning/routing records read by `ARCH-01` and `ARCH-06`
   on the *next* task, applied with **no redeploy** because policies are data, not code (`RFC-0017
   §4.2`).
4. **Propose governed promotion** of repeatedly-corroborated experiences to Knowledge (`ARCH-02` via
   `RFC-0018`, gated by `PromotionPolicy.ready`).
5. **Measure loop closure** (`ADR-0034`): a lesson is *learned* only when a later execution
   measurably reflects it — the *only* definition of learning the ECL accepts. Volume of lessons is
   not progress.
6. **Detect systemic patterns** across many reflections (`RFC-0017 §4.5`).

The defining constraint, and the thesis this document must defend, is **`ADR-0003`: improvement is
data and policy, never fine-tuning.** The design must therefore also solve the problems fine-tuning
*cannot*: **catastrophic-forgetting avoidance**, **auditability**, and **reversibility**, while
proving improvement via **loop-closure metrics** rather than asserting it.

---

## 2. Approaches considered

### A. Experience-store accretion with value scoring
The baseline mandated by the contract. `distill` writes an append-only `EXP-###` keyed by `situation`
(task_type, apps, failure_class); each experience carries a `value` map updated over time —
`application_frequency` (how often retrieved), `outcome_lift` (mean `EVAL-###` delta when applied vs.
not), and corroboration count. Value scoring is what lets `PromotionPolicy.ready` (`ADR-0036`) fire
only on repeated, measured success and what ranks experiences for retrieval (`ARCH-03`). Append-only +
value decay is the core memory model.

### B. Offline policy search / bandits over retrieval & planning parameters
Treat retrieval and planning **policies** as tunable parameters and search them *offline* against the
recorded outcome history: retrieval priorities (which apps' rules to raise for which task types),
budget allocations (`BudgetPolicy`), planning heuristics (require-negative-assertion), routing hints.
Model each policy variant as a **contextual bandit** arm; the reward is realized `EVAL-###` lift;
select variants with proven lift and keep them as new policy versions (`RFC-0017 §9`, `ARCH-05`
"automated policy search"). Crucially **offline and evidence-grounded — never a weight update.**

### C. Prompt / context-template optimization
Optimize the *templates* that assemble what the model sees — context layout, instruction phrasing,
few-shot exemplar selection, ordering — rather than the model. Search template variants against
outcome history (or held-out replays) and keep those with lift. This is "learning" in the
literal sense the ECL means: changing the model's *inputs*. Composes with B (a template is a kind of
context policy) and is fully model-agnostic and portable across providers (`ARCH-07`).

### D. Memory consolidation / clustering
Periodically consolidate the growing experience store: cluster near-duplicate `EXP-###` by
`situation` embedding, merge them into stronger consolidated lessons (summing corroboration), retire
stale or contradicted ones, and abstract specific lessons into more general ones only when breadth is
*earned* by cross-situation corroboration. This is the analogue of sleep-time memory consolidation and
the direct defense against **policy sprawl** (`RFC-0017 §5`) and experience-store bloat.

### E. Promotion governance (corroboration-gated, human-in-the-loop)
The `PromotionPolicy` and `promotion_proposed` machinery. An experience is proposed for promotion to
Knowledge only after crossing a **corroboration bar** (`ADR-0036`, `RFC-0018`): N independent
loop-closed applications with positive `outcome_lift`, no contradicting evidence. High-stakes
promotions route to human governance (`ARCH-05` future). Contradictory lessons targeting the same
Knowledge raise a `pattern_detected` for governance rather than silently overwriting (`RFC-0017 §4.4`).

### F. Fine-tuning the model on outcomes — **the rejected baseline**
The industry-default alternative: periodically fine-tune (or LoRA/RLHF) the LLM on successful
trajectories. Explicitly **rejected** by `ADR-0003`, `RFC-0017 §6`, and `ARCH-07`. Included here only
to be contrasted, because the design's entire architecture is a rebuttal of it (§4/§5).

---

## 3. Trade-offs

| Approach | Model-agnostic | Reversible / auditable | Forgetting risk | Cold-start | Compute | Loop-closure measurable |
|---|---|---|---|---|---|---|
| A. Experience accretion | Yes | **Yes** (append-only lineage) | None (additive) | Excellent | Cheap writes | Yes (per `EXP-###`) |
| B. Offline policy search | Yes | Yes (versioned policies) | None | Poor (needs history) | Heavy (offline) | Yes (A/B lift) |
| C. Template optimization | Yes | Yes (versioned templates) | None | Moderate | Moderate (offline) | Yes (lift) |
| D. Consolidation/clustering | Yes | Yes (merge lineage kept) | Low (if lineage kept) | N/A | Periodic batch | Indirect |
| E. Promotion governance | Yes | **Yes** (governed, staged) | None | N/A | Cheap | Yes (post-promotion) |
| **F. Fine-tuning** | **No** | **No** (opaque weights) | **High** (catastrophic) | Poor | **Very heavy** (GPU) | **No** (can't attribute) |

The table is the argument for `ADR-0003` in one view: every outside-the-model approach (A–E) is
model-agnostic, reversible, auditable, forgetting-free, and loop-closure-measurable; fine-tuning (F)
fails on *every one of those axes*. The internal tension among A–E is only cold-start and compute:
A/E work from the first reflection; B/C need an accumulated outcome history to search over.

---

## 4. Advantages

- **A (Experience accretion):** Additive and reversible by construction (`ARCH-05` Best Practice 7) —
  a bad lesson is retired, never "unlearned" from weights. Full lineage (reflection → experience →
  knowledge) is traceable end to end (`RFC-0017 §4.1`). Works from the very first reflection.
- **B (Offline policy search):** Turns improvement into a *measured* optimization — keep only variants
  with proven `EVAL-###` lift — and because policies are data, applying a winner needs **no redeploy**
  and is instantly reversible (`RFC-0017 §4.2`). Directly realizes the `ARCH-05` automated-policy-search
  future without touching weights.
- **C (Template optimization):** The purest expression of `ADR-0003` — it improves *what the model
  sees*, is portable across any provider via the Gateway (`ARCH-07`), and often yields the largest
  lift per unit effort.
- **D (Consolidation):** Keeps the store dense and retrieval sharp as it grows; the standing answer to
  `RFC-0017 §5` policy sprawl.
- **E (Promotion governance):** Prevents one-off luck from becoming enterprise truth (`ADR-0036`);
  staged, governed, and reversible, with contradiction handling that escalates rather than overwrites.
- **Contrast with F:** because learning is *data*, the organization gets properties fine-tuning cannot
  offer at any price — audit ("which reflection produced this active policy, and what lift did it
  yield?"), rollback (delete a policy version), and provider portability. This is the whole `ARCH-07`
  thesis: **model-agnostic and improves anyway.**

---

## 5. Weaknesses

- **A:** Store grows without bound and retrieval degrades without D. Value scores (`outcome_lift`) need
  enough applications to be statistically meaningful; early scores are noisy.
- **B:** Cold-start-hostile — nothing to search until an outcome history exists. **Attribution
  ambiguity** (`RFC-0017 §5`): when several policies change between two executions, crediting the lift
  to one is imperfect; needs controlled/A-B trials to be rigorous. Offline search is compute-heavy.
- **C:** Template search space is large and easy to overfit to a replay set that no longer matches live
  drift; a template win on stale data can regress live.
- **D:** Over-aggressive merging can abstract a lesson beyond its valid `situation` (the
  over-generalization failure of `ARCH-05`); must keep merge lineage to stay reversible.
- **E:** Corroboration bar trades safety for speed — too high and good lessons never promote (open
  loops), too low and luck promotes. **Delayed confirmation** (`RFC-0017 §5`): loop closure can lag many
  tasks, so near-term improvement is invisible until the open-loop window elapses.
- **F (why rejected):** **Catastrophic forgetting** — fine-tuning on new trajectories degrades unrelated
  prior capability, and there is no lineage to audit or roll back; opaque weight deltas cannot be
  attributed to a lesson, so **loop closure is unmeasurable**; and it *couples the runtime to one
  model*, breaking `ARCH-07`. Every one of these is a first-class violation of `ADR-0003`.

---

## 6. Computational complexity

Let `R` = reflections per period, `E` = experience-store size, `P` = policy-variant search space,
`H` = outcome-history size, `c` = clusters.

- **`distill` (A):** O(1) amortized append + O(log E) index insert per reflection. `emit` (`RFC-0017`)
  is O(events) with idempotency keyed on `(source_reflection, kind, target)` — O(1) dedup lookup.
- **`loop_closed` (A/E):** O(1) — flips a flag when a later reflection sets `loop_closed_by`; the
  detection happens inside reflection (algorithm 05), not here.
- **Policy search (B):** the heavy term. Naïve grid over P variants each evaluated on H history = O(P·H);
  bandit/Bayesian-optimization search reduces effective P by orders of magnitude. **Runs offline**, never
  on any task's critical path.
- **Template search (C):** same shape as B, O(variants · replay-set).
- **Consolidation (D):** O(E log E) clustering per batch (ANN + agglomeration over `situation`
  embeddings), scheduled (e.g., nightly), not per task.
- **`systemic_patterns` (E):** O(R) aggregation of `root_cause.category` counts over the window, plus
  threshold checks — cheap, batched.

Everything on the **task hot path is O(1)–O(log E)** (a policy read, an experience write); everything
expensive (B, C, D) is **offline and batched** — the architecturally correct placement, and the reason
outside-the-model learning imposes *no* per-task latency, unlike fine-tuning's GPU-bound retrain cycles.

---

## 7. Enterprise scalability

- **Reads are trivial, writes are append-only.** The next task reads one active policy version (O(1))
  and retrieves ranked experiences (O(log E), shared with algorithm 02). No global lock, no redeploy —
  policies are versioned data (`RFC-0017 §4.2`), so a fleet of thousands of Workers applies new lessons
  the moment the version flips.
- **Learning compute is decoupled from serving.** Policy/template search and consolidation run on a
  separate offline cadence; they scale independently of task throughput and never contend with the
  serving path — a structural advantage over fine-tuning, whose retrain cost scales with data *and*
  blocks release of the updated model.
- **Multi-tenant / cross-Worker curriculum:** experiences and policies are `situation`-keyed and
  domain-agnostic (`ARCH-07`), so a new Worker type can **warm-start** from a sibling's promoted
  Knowledge and policies (`RFC-0017 §9`, `RFC-0020`) — accumulated organizational memory transfers
  without any model surgery.
- **Sprawl is bounded operationally:** consolidation (D) + `outcome_lift`-based retirement + the
  open-loop signal (surfacing lessons whose loop never closes within the window, `RFC-0017 §4.3`) keep
  the active policy/experience set dense as volume grows into the millions.
- **Governed promotion scales trust:** the corroboration bar and contradiction-escalation (`RFC-0017
  §4.4`) mean the *Knowledge* base grows slowly and safely even as the *Experience* base grows fast —
  the right asymmetry for enterprise durability.

---

## 8. Explainability

Outside-the-model learning is **explainable precisely because it is data**, which is the core safety
argument against fine-tuning:

- **Full lineage (`RFC-0017 §4.1`, `ARCH-05` BP 6):** every improvement traces reflection → `EXP-###`
  → `promotion_proposed` → `KN-###`, and every active policy references the prior version and the
  `source_reflection` that produced it. "Why does the Worker now retrieve `APP-015` rules for `APP-003`
  changes?" resolves to a specific `REF-###` and its measured lift — a query, not a mystery.
- **Append-only, immutable `LearningEvent`s** (`RFC-0017 §4.1`, `ADR-0022`): a correction is a new
  event, never an edit, so the entire history of *what changed, why, and whether it worked* is a
  replayable ledger. Fine-tuning offers no equivalent — a weight delta explains nothing.
- **Loop closure is the honest success metric:** `LearningEvent.loop_closed` flips only when a later
  execution demonstrably applied the lesson and did not regress (`ADR-0034`, `RFC-0017 §4.3`). The
  engine reports *measured* improvement, not asserted volume.
- **Reversibility is a form of explainability:** because any policy version can be diffed and rolled
  back, the effect of a lesson can be isolated and demonstrated (turn it off, watch lift disappear) —
  impossible with entangled weights.
- **Systemic patterns are auditable aggregates:** a `pattern_detected` event carries the supporting
  `REF-###`/`INC-####` set (`RFC-0017 §4.5`), so an organization-level lesson is backed by its evidence,
  not a hunch.

---

## 9. Recommendation

**Adopt the full outside-the-model stack — A (experience accretion + value scoring) and E
(corroboration-gated promotion governance) as the always-on spine, D (consolidation) as a scheduled
hygiene process, and B (offline policy/bandit search) + C (template optimization) as the offline
improvement engines that fire once sufficient outcome history exists — and categorically reject F
(fine-tuning) per `ADR-0003`.**

Staging and rationale:

1. **Day one: A + E.** `distill` writes append-only, `situation`-keyed `EXP-###` with a `value` map;
   `emit` produces immutable, idempotent `LearningEvent`s onto the Signals Bus and the versioned policy
   stores; `PromotionPolicy.ready` gates promotion on the `ADR-0036` corroboration bar. This is fully
   functional from the first reflection, needs no history, and is reversible and auditable by
   construction. **Loop closure (`loop_closed`) is wired in from the start** as the sole success metric
   (`ADR-0034`) — the engine measures itself on lessons that *changed a later execution*, never on
   lessons written.

2. **Continuous hygiene: D.** Scheduled consolidation clusters near-duplicate experiences, retires
   stale/contradicted ones by `outcome_lift`, and keeps merge lineage so every consolidation stays
   reversible. This is the standing defense against policy sprawl (`RFC-0017 §5`) and the
   over-generalization failure (`ARCH-05`), abstracting a lesson's `situation` only when breadth is
   *earned* by cross-situation corroboration.

3. **As history accrues: B + C, offline.** Once enough loop-closed outcomes exist, run contextual-bandit
   policy search (B) and template optimization (C) *offline* against that history, keeping only variants
   with proven `EVAL-###` lift and shipping them as new **policy/template versions** — no redeploy, no
   weight change, instantly reversible (`RFC-0017 §4.2/§9`). Use A/B-style controlled policy trials to
   defeat the attribution-ambiguity weakness (`RFC-0017 §5/§8`).

4. **Always: `systemic_patterns`.** Aggregate `root_cause.category` across the reflection window and
   raise `pattern_detected` (with supporting `REF-###`/`INC-####`) when same-category failures recur —
   turning per-task lessons into organization-level ones for the Architecture Office (`RFC-0017 §4.5`,
   `ARCH-05` Example C).

**Why not F, restated as the design's thesis:** fine-tuning is rejected not merely by fiat but because
it fails every property this engine must guarantee. It is **not model-agnostic** (couples the runtime to
one provider, breaking `ARCH-07`); it is **not reversible or auditable** (opaque weight deltas with no
lineage — loop closure becomes unmeasurable, so `ADR-0034` cannot even be evaluated); and it invites
**catastrophic forgetting** (new trajectories degrade unrelated prior capability). The recommended stack
delivers durable improvement with the exact opposite properties — additive, reversible, auditable,
provider-portable, and measured by loop closure. **The same stateless model gets better every day
because the ECL around it learned — which is the entire thesis of EnterpriseSim, implemented by
Bytesurge without ever touching a weight.**
