# Semantic Experience Similarity

> This document is part of EnterpriseSim's reference-runtime algorithm research (see
> [`README.md`](README.md) and [`NOTICE.md`](NOTICE.md)).

| Field | Value |
|---|---|
| Satisfies (EnterpriseSim contract) | `sdk.experience.ExperienceRetriever.retrieve` |
| Supporting types | `sdk.experience.SituationDescriptor`, `sdk.experience.ExperienceMatch`, `sdk.experience.ExperienceStore` |
| Architecture reference | `ARCH-03` (Experience Layer) |
| Protocol reference | `RFC-0004` (Experience Retrieval Interface); structural matching per `ADR-0019`; append-only `ADR-0005`, down-weight-not-delete `ADR-0047` |
| Status | Research — design only |

---

## 1. Problem statement

`ARCH-03` makes the Experience Layer the enterprise's memory of *what it learned by doing*, and
`RFC-0004` fixes the retrieval contract: `retrieve(situation: SituationDescriptor, top_k)` returns
`Sequence[ExperienceMatch]`, each wrapping an `ExperienceObject` with **two separate** `Confidence`
scores — `applicability` (how well this lesson fits the situation) and `value` (its demonstrated
worth, dominated by measured outcome lift). `RFC-0004` is emphatic on one point the runtime must
honor above all: matching is **structural, not merely semantic** (`ADR-0019`). "Same app + same
failure class" beats "sounds similar," because pure semantic similarity is precisely what causes a
narrow lesson to be misapplied to a superficially-similar-but-different situation — the
**overfitting** failure mode (`ARCH-03`, `RFC-0004` §2).

The input is a `SituationDescriptor` — `task_type` (e.g. `feature_change`), `apps`
(e.g. `[APP-003, APP-015]`), optional `failure_class` (e.g. `unintended_side_effect`), and an open
`extra` mapping — deliberately **typed and structural**, not a natural-language query. A stored
`ExperienceObject` mirrors this in its required `situation` block, so incoming situation and stored
lesson are compared on the same structural keys.

The runtime must therefore design a similarity function and retrieval index that:

1. compute **structural applicability** dominated by exact/graded agreement on `task_type`, `apps`,
   `failure_class`, with semantic similarity as a *secondary* signal, not the primary one;
2. compute **value** from `application_frequency`, `outcome_lift`, `corroboration`,
   `contradiction_rate` — with recency **decay** (`RFC-0004` §4.5) and down-weighting on
   contradiction while retaining history (`ADR-0047`);
3. enforce an **applicability floor** — below it a superficially similar lesson is *excluded*
   rather than risked (`RFC-0004` §4.2);
4. keep the two scores **unfused** and pass both forward for DI/Context to weigh (`RFC-0009`);
5. scale to millions of append-only experiences with sub-100 ms retrieval.

The `EXP-090` running example is the touchstone: situation `{feature_change, [APP-003, APP-015],
unintended_side_effect}`, applicability 0.91, value `{freq 4, lift 0.23, strong, contradiction 0}`.

---

## 2. Approaches

Five named approaches to the applicability score (value scoring is treated in §2.5 and folded
throughout).

### 2.1 Embedding cosine (semantic-only baseline)

Embed a textual rendering of the situation (or the lesson) and score by cosine over an ANN index.
Simple, high-recall, handles paraphrase. **But this is exactly the approach `RFC-0004` §6 rejects
as the primary matcher** — semantic-only search causes overfitting, retrieving a lesson that
"sounds similar" but shares no structural key. Retained only as a *secondary* tie-breaker signal
and cold-start fallback when structural keys are sparse.

### 2.2 Structural / graph similarity (primary)

Model each situation as a small typed record over a shared ontology and score by structured
agreement:

```
struct_sim(q, e) =  w_task · 1[task_type_q = task_type_e]
                  +  w_fail · 1[failure_class_q = failure_class_e]
                  +  w_app  · Jaccard(apps_q, apps_e)
                  +  w_extra · overlap(extra_q, extra_e)
```

`apps` overlap is graded (Jaccard), not binary, and can be enriched via the Knowledge Layer
**dependency graph** — two apps that are direct dependencies score partial affinity even when not
equal, so a lesson about `APP-003` transfers appropriately to its caller. `task_type` and
`failure_class` agreement dominate. This is the `ADR-0019` "structural similarity" mandate made
concrete and is the primary applicability signal.

### 2.3 Metric learning (learned structural embedding)

Rather than hand-tune `w_*`, learn a distance metric over situation records such that pairs that
**historically transferred well** (a lesson applied to situation B raised its `EVAL-###`) are close
and pairs that transferred poorly are far. Train a Siamese/triplet network or a Mahalanobis metric
on `(situation, situation, transferred?)` triples mined from the corpus. Learns the *right* weights
for structural keys and their interactions — e.g. that `failure_class` agreement matters far more
for `unintended_side_effect` lessons than for `perf_regression` ones. Learning lives outside the
model (`ADR-0003`).

### 2.4 Hybrid structural + semantic scoring (gated)

Combine 2.2 and 2.1 with structure as a **gate**, not an addend:

```
applicability(q, e) = struct_sim(q, e) · [ α + (1 − α) · sem_sim(q, e) ]      if struct_sim ≥ τ
                    =  0 (excluded)                                            otherwise
```

The `struct_sim ≥ τ` gate is the anti-overfitting guard: no amount of semantic similarity can
resurrect a lesson that fails the structural floor. Above the gate, semantic similarity refines the
ordering (distinguishes two `feature_change`/`APP-003` lessons by textual nuance). This directly
encodes `RFC-0004`'s "structural, not merely semantic" while still exploiting semantics where safe.

### 2.5 ANN index + value-weighted retrieval + decay

The serving and ranking machinery:

- **ANN index (HNSW / IVF-PQ)** over a *composite* key: structural keys as a filter (metadata
  pre-filter on `task_type`/`failure_class`, or partitioned indices) plus a semantic vector for the
  within-partition ordering. Structural filtering first, semantic ranking second.
- **Value-weighted retrieval** — final rank multiplies applicability by a value factor so a proven
  lesson outranks a merely-similar unproven one (`RFC-0004` future; `ARCH-03` "score by value, not
  volume"):
  ```
  value(e) = g(outcome_lift) · h(corroboration) · (1 − contradiction_rate) · decay(age_e)
  rank(e)  = applicability(q, e) · value(e)          # BUT the two scores are reported separately
  ```
- **Decay** — `decay(age) = exp(−age / λ_taskclass)` with a per-task-class half-life (fast-moving
  areas forget quickly, stable areas retain longer — `ARCH-03` future). Decay expresses recency;
  **contradiction** is handled by `ExperienceStore.downweight`, which lowers relevance and raises
  `contradiction_rate` while **retaining history** (`ADR-0047`) — a down-weighted lesson can recover
  to `retrievable` on new corroboration.

---

## 3. Trade-offs

| Approach | Overfitting resistance | Handles paraphrase | Training data | Cold-start | Latency | Explainability |
|---|---|---|---|---|---|---|
| Embedding cosine | **Poor** (the failure mode) | **Excellent** | Pretrained | Good | Low (ANN) | Poor |
| Structural / graph | **Excellent** | None | None (hand weights) | **Excellent** | Very low | **Excellent** |
| Metric learning | High | Medium | Needs transfer labels | Poor | Low | Medium |
| Hybrid gated | **Excellent** | Good (above gate) | Optional | Good | Low | High |
| ANN + value + decay | (serving layer) | inherits | Value from EVAL corpus | Value lags | Low | High |

Cross-cutting tensions:

- **Recall vs. overfitting.** Semantic recall is easy; the whole design problem is *suppressing*
  the recall that leads to misapplication. The structural gate deliberately sacrifices recall for
  safety — the correct trade for `ARCH-03`.
- **Value freshness vs. cold start.** `outcome_lift`/`application_frequency` are only meaningful
  after several applications (`RFC-0004` §5). New lessons cannot be value-ranked and lean on
  structural applicability + corroboration until they earn a track record.
- **Decay aggressiveness.** Fast decay keeps the corpus current but risks forgetting a rare-but-
  valid lesson; slow decay risks applying stale ones. Per-task-class half-lives are the compromise.
- **Hand-tuned vs. learned weights.** Structural weights are transparent and cold-start-safe;
  learned metrics are more accurate but need transfer labels and can overfit to majority task types.

---

## 4. Advantages

- **Overfitting-resistant by design.** The structural gate makes "same app + same failure class"
  a precondition, directly implementing `ADR-0019` and neutralizing the `ARCH-03` overfitting
  failure mode that semantic-only retrieval invites.
- **Dual scores preserved.** Applicability and value are computed and reported separately per the
  `ExperienceMatch` contract, so DI/Context weigh them independently (`RFC-0009` §3.1) rather than
  acting on a laundered blend.
- **Value-honest ranking.** Value-weighting + decay realize `ARCH-03`'s "rank by measured outcome
  lift, not recency alone" and "append, never erase" — contradiction down-weights, never deletes.
- **Cross-domain transfer, safely.** The structural ontology lets a QA Worker's async-determinism
  lesson transfer to a Support Worker (`ARCH-03` Example C) *because* it matches on structural facets
  (async + test determinism), not because the prose is similar — transfer without overfitting.
- **Auditable lineage.** Every returned match carries its `evidence` block (origin execution,
  `EVAL-###`, `REF-###`); the retriever refuses lessons whose lineage cannot resolve (`ADR-0022`).

---

## 5. Weaknesses

- **Cold start (value).** A young corpus has lessons with no `outcome_lift`; ranking degenerates to
  structural applicability + corroboration until history accumulates (`RFC-0004` §5 acknowledges
  this). The runtime must capture aggressively to warm it.
- **Structural-block quality dependence.** If Reflection (`RFC-0016`) captures a weak/inconsistent
  `situation` block, structural matching degrades toward the semantic guessing it was meant to avoid
  (`RFC-0004` §5). Garbage structure in, overfitting out.
- **Floor tuning is a knife-edge.** `τ` (structural gate) and the applicability floor: too high
  misses useful transfer, too low readmits overfitting (`RFC-0004` §5, §8).
- **Ontology drift.** As new `task_type`s and `failure_class`es appear, the structural vocabulary
  must evolve without invalidating historical lessons — a governance burden.
- **Append-only growth / lesson sprawl.** The store only grows; near-duplicate low-value lessons
  dilute retrieval unless consolidation happens during reflection and value-ranking suppresses them
  (`ARCH-03` "lesson sprawl"; `RFC-0004` §5).
- **Decay mis-specification.** A wrong per-class half-life either forgets valid lessons or keeps
  stale ones alive; half-lives themselves should eventually be learned.

---

## 6. Computational complexity

Let `M` = total stored experiences, `p` = partition size after structural pre-filter (`p ≪ M`),
`d` = embedding dim, `k` = `top_k`, `F` = structural feature count, `G` = dependency-graph
neighborhood size for graded app affinity.

| Stage | Complexity | Notes |
|---|---|---|
| Structural pre-filter | `O(1)`–`O(log M)` | Metadata index / partition lookup on `task_type`, `failure_class`. |
| Structural similarity | `O(p · (F + G))` | Cheap; Jaccard + graph-affinity per candidate in partition. |
| Semantic refinement (ANN) | `O(log p)` per query within partition | HNSW over the partition's vectors. |
| Metric-learned distance | `O(p · d)` | Forward pass of the learned metric per candidate. |
| Value + decay scoring | `O(p)` | Arithmetic over stored value fields. |
| Top-k selection | `O(p log k)` | Heap. |
| **Query total** | **`O(log M + p·(F+G) + p·d)`** | Structural pre-filter makes it near-constant in `M`. |
| Append (insert) | `O(log M + d)` | HNSW incremental insert + metadata index; append-only. |
| Reinforce / downweight | `O(1)` + re-score | Updates value fields; no reindex of the vector needed. |
| Offline metric training | `O(T · d²)` for `T` triples | Batch, off the hot path. |

The structural pre-filter is the key: it collapses the candidate set from `M` (millions) to `p`
(a partition of structurally-compatible lessons, typically hundreds), so all expensive per-candidate
work is `O(p)`, not `O(M)`.

---

## 7. Enterprise scalability

**Throughput & latency.** Experience corpora at Fortune-500 scale reach `10^6–10^7` lessons across
many task types and apps. Structural pre-filtering keeps retrieval sub-100 ms regardless of corpus
size because the semantic/metric work only ever touches one structural partition. Target: filter
< 5 ms, score < 30 ms, rank < 5 ms.

**Indexing & sharding.** Partition the store by `task_type` (coarse) and index `apps`/`failure_class`
as metadata filters — or maintain per-`task_type` ANN sub-indices. Shard by tenant/domain for
isolation (a payments lesson never surfaces in a privacy Worker's retrieval unless structurally and
policy-appropriate). HNSW graphs are held in memory per shard with disk-backed payloads.

**Incremental update.** Experience is **append-only** (`ADR-0005`), so the index only ever grows via
incremental insert — no full rebuilds. `reinforce`/`downweight` mutate lightweight *value* fields
(and `contradiction_rate`), not the structural key or vector, so they are `O(1)` metadata writes;
ranking picks up the new value on the next query. Decay is applied at query time from stored
timestamps, so no periodic rewrite is needed.

**Cost.** Dominated by embedding at capture time (once per lesson, offline) and by the in-memory ANN
footprint. Value/decay scoring is arithmetic. Because reinforcement is a metadata update, the
"experience accumulates forever" guarantee (`ARCH-03`) is cheap to honor. Consolidation during
reflection (dedup near-identical lessons) bounds long-term index growth and retrieval dilution.

**Multi-tenancy.** Per-tenant partitions, per-tenant decay half-lives, per-tenant metric models.
Cross-domain transfer (`ARCH-03` Example C) is enabled *within* a tenant across Worker types, gated
by structural compatibility — never across tenants.

---

## 8. Explainability

The `ExperienceMatch` and the lesson's mandatory `evidence` lineage are the audit surface.

- **Structural match breakdown.** Each match reports *why it matched*: `{task_type: exact,
  failure_class: exact, apps: Jaccard 0.67 (APP-003 shared, APP-015 shared, APP-012 absent),
  extra: —}`. An auditor sees the lesson applied because it shares the failure class and two of
  three apps — not because prose was similar.
- **Gate transparency.** Excluded-below-floor lessons are logged with the structural score that
  failed the gate (`struct_sim 0.30 < τ 0.45 → excluded`), so it is visible *which* structurally
  dissimilar lessons were deliberately withheld — the anti-overfitting decision is inspectable.
- **Value provenance.** The value score decomposes into `{outcome_lift 0.23, corroboration strong,
  application_frequency 4, contradiction_rate 0.0, decay 0.94}` and links to the `EVAL-###`s that
  produced the lift — value is grounded in measured evidence, not asserted.
- **Lineage trace.** Every match resolves `origin_execution → EVAL-### → REF-###` and, if promoted,
  `promoted_to_knowledge → KN-###`. A lesson whose lineage cannot resolve is never returned
  (`ADR-0022`), so there are no unexplainable recommendations.
- **Applied-vs-outcome record.** When a retrieved lesson is later reinforced or contradicted, the
  history is retained (`ADR-0047`), so an auditor can see the lesson's full trajectory — including
  when and why it was down-weighted.

---

## 9. Recommendation

The recommended approach is the **hybrid gated matcher with value-weighted retrieval and per-class
decay**:

1. **Structural pre-filter first** on `task_type` and `failure_class`, with **graded `apps`
   affinity** via Jaccard enriched by the Knowledge dependency graph — the primary applicability
   signal and the anti-overfitting guard (`ADR-0019`).
2. **Structural gate** `struct_sim ≥ τ`: no lesson enters the result unless it clears the structural
   floor, regardless of semantic similarity. This is the load-bearing defense against the `ARCH-03`
   overfitting failure mode.
3. **Semantic refinement above the gate** — cosine over an in-partition ANN index breaks ties and
   orders structurally-compatible lessons; semantics assist, never override.
4. **Value-weighted final ranking** — multiply applicability by `value = g(lift)·h(corroboration)·
   (1−contradiction_rate)·decay(age)`, but **report applicability and value separately** on each
   `ExperienceMatch` per the contract (`RFC-0004` §4.2, `RFC-0009`).
5. **Decay via per-task-class half-lives**; **contradiction via `downweight`** (retain history,
   `ADR-0047`); **applicability floor** excludes weak matches with a logged reason.
6. **Graduate hand-tuned structural weights to a learned metric** (§2.3) once enough transfer labels
   accumulate — learning outside the model (`ADR-0003`), starting from the transparent hand-tuned
   weights so cold-start behavior is safe.

**Why this hybrid.** It is the only approach that satisfies the defining constraint of `RFC-0004`
— structural, not merely semantic — while still capturing the paraphrase robustness that makes
semantics worth having, and it keeps the two `Confidence` scores unfused as the `ExperienceMatch`
contract and `RFC-0009` require. The structural pre-filter delivers the sub-100 ms, corpus-size-
independent latency an enterprise fleet needs; append-only inserts and `O(1)` value updates honor
"experience accumulates forever" (`ARCH-03`, `ADR-0005`) cheaply; and the match-breakdown +ledger
lineage give auditors a fully explainable answer to "why was this past lesson applied here?" —
which is exactly the trust the Experience Layer exists to earn.
