# Adaptive Context Ranking

> This document is part of EnterpriseSim's reference-runtime algorithm research (see
> [`README.md`](README.md) and [`NOTICE.md`](NOTICE.md)).

| Field | Value |
|---|---|
| Satisfies (EnterpriseSim contract) | `sdk.context.ContextAssembler` — ranking & budget-aware selection |
| Supporting types | `sdk.context.Candidate`, `sdk.context.BudgetPolicy`, `sdk.context.Retriever`, `sdk.context.TaskIntent` |
| Architecture reference | `ARCH-01` (Context Layer) |
| Protocol reference | `RFC-0002` (Context Assembly Protocol); confidence per `RFC-0009` |
| Status | Research — design only |

---

## 1. Problem statement

`ARCH-01` charges the Context Layer with assembling the *right, minimal, sufficient* working
set for one task and holding it only for that task's life. `RFC-0002` fixes the *shape* of that
work — retrieve via composable `Retriever`s, rank heterogeneous `Candidate`s on one comparable
scale, select a subset that fits the model window through a `BudgetPolicy`, and compose a
`ContextObject` with mandatory included **and** excluded provenance — but it deliberately leaves
the **ranking function itself open** (`RFC-0002` §5: "Ranking is the hard part … the protocol
fixes the shape of rank/select but not the ranking function"). The runtime must supply that
function inside its `ContextAssembler.assemble` / `enrich` implementations.

Concretely, given a `TaskIntent` and a pool of `n` candidates each carrying `(ref, kind, score,
tokens, payload)`, the runtime must produce an **ordered selection** `S ⊆ candidates` such that
`Σ tokens(S) ≤ window_tokens − reserved_output` and `S` maximizes expected task success. This
is not plain top-k: it is a **budget-constrained, diversity-aware, staleness/authority-weighted
selection** whose omissions matter as much as its inclusions.

Four sub-problems, all named in `ARCH-01`, must be solved together:

1. **Relevance scoring** across heterogeneous sources (knowledge, experience, code, live state)
   on one `Confidence` scale (`RFC-0002` §4.3).
2. **Budget-aware selection** — a knapsack over token cost, not a relevance cutoff, enforced
   *before* the Gateway call (`ADR-0006`; never rely on provider truncation).
3. **Staleness / authority weighting** — freshness and source authority modulate raw relevance
   (`ARCH-01` "prefer live state for volatile facts"; staleness index signal).
4. **The dropped-candidate problem** — a high-scoring item evicted purely for budget (the
   canonical `KN-047` at 0.61) must be *flagged*, because "the fix was in a doc we dropped" is
   the single most common failure root cause (`ARCH-01` signals; `RFC-0002` §4.3).

Success is measured by EnterpriseSim's benchmark suites (retrieval hit ratio, coverage
confidence calibration, and downstream `EVAL-###` lift), not by ranking metrics in isolation.

---

## 2. Approaches

Five concrete, named approaches, roughly in increasing sophistication. Each is a real IR/ML
technique; the design question is which to compose.

### 2.1 BM25 / lexical scoring (baseline)

Score each candidate by Okapi BM25 over the intent's tokens (goal + constraints +
success_criteria + app IDs) against the candidate payload. Fast, transparent, zero training,
strong exact-match behavior on canonical IDs (`APP-003`, `KN-052`) and code symbols. Serves as
the interpretable floor and a fallback when embeddings are unavailable (cold model, air-gapped
deployment).

### 2.2 Dense bi-encoder retrieval

Embed intent and each candidate independently with a bi-encoder (`E(intent)`, `E(cand)`), score
by cosine similarity, retrieve via an ANN index (HNSW/IVF-PQ). Captures paraphrase and
semantic relatedness BM25 misses ("guest flow" ≈ "unauthenticated checkout"). Embeddings are
precomputable and indexable, so query-time cost is sublinear. This is the workhorse recall
layer.

### 2.3 Cross-encoder re-ranking

For the top-`m` candidates from 2.1/2.2, run a cross-encoder that jointly attends over
`(intent, candidate)` and emits a calibrated relevance logit. Far more accurate than cosine
(it models term interaction, negation, scope) but `O(m)` model calls per task, so it is applied
only to a shortlist. This is the precision layer.

### 2.4 MMR / diversity-aware selection

Relevance alone over-selects near-duplicates (three docs restating the same idempotency rule),
wasting budget and starving other task facets. Maximal Marginal Relevance selects greedily to
balance relevance against redundancy:

```
MMR(c) = λ · rel(c, intent) − (1 − λ) · max_{s ∈ S} sim(c, s)
```

This directly serves the `ARCH-01` **coverage** requirement (all facets represented: target
code, rules, experience, dependency context) and the anti-flooding failure mode.

### 2.5 Learning-to-rank + budget-aware knapsack + learned policy

The full target, three composed pieces:

- **Learning-to-rank (LambdaMART / listwise λ-loss).** Train a gradient-boosted or listwise
  ranker on features `[bm25, cosine, cross_enc, authority, staleness, kind, applicability
  (for EXP), facet_id, token_cost]` with the training label = did including this candidate
  raise the downstream `EVAL-###` score? Labels come *free* from EnterpriseSim's learning corpus
  and the dropped-candidate log (a dropped item later implicated in a failure is a positive that
  was wrongly excluded). This is learning **outside the model** (`ADR-0003`), exactly as the
  charter requires.
- **Budget-aware knapsack selection.** Given per-candidate value `v(c)` (the LTR score, after
  staleness/authority weighting) and cost `tokens(c)`, select `S` maximizing `Σ v(c)` s.t.
  `Σ tokens(c) ≤ B`. This is 0/1 knapsack; the runtime uses the **greedy density heuristic**
  (sort by `v(c)/tokens(c)`, fill) with an MMR diversity penalty folded into `v`, giving a
  well-known `(1 − 1/e)`-style guarantee for the submodular coverage objective and near-optimal
  behavior in practice. `BudgetPolicy.evict` records every drop.
- **RL / bandit budget allocation (advanced).** Treat *how much budget to spend per facet* and
  *when to stop retrieving* as a contextual bandit / RL policy trained on EVAL feedback — e.g.
  allocate more window to the "prior experience" facet on task types where experience has
  historically been decisive ("confidence-calibrated budgets", `ARCH-01` future evolution). The
  `enrich` self-loop is naturally a sequential decision problem (re-retrieve vs. proceed).

---

## 3. Trade-offs

| Approach | Relevance quality | Latency (query) | Training data | Budget-aware | Diversity | Explainability | Cold-start |
|---|---|---|---|---|---|---|---|
| BM25 lexical | Low–med | Very low | None | No (needs knapsack bolt-on) | No | **Excellent** (term scores) | **Excellent** |
| Dense bi-encoder | Medium | Low (ANN) | Pretrained embeddings | No | No | Poor (opaque vector) | Good |
| Cross-encoder rerank | **High** | High (`O(m)` calls) | Pretrained/fine-tune | No | No | Medium (attribution possible) | Good |
| MMR / diversity | (selection, not scoring) | Low | None | Partial | **Excellent** | Good (redundancy visible) | Good |
| LTR + knapsack + policy | **Highest** | Medium | **Needs EVAL corpus** | **Yes** | Yes (via feature) | Medium (feature attribution) | Poor (needs history) |

Cross-cutting tensions:

- **Recall vs. precision vs. budget.** Bi-encoder maximizes recall cheaply; cross-encoder buys
  precision at cost; knapsack converts precision into the best *affordable* set. None alone
  solves all three — hence a pipeline.
- **Accuracy vs. explainability.** Every step toward learned scoring erodes the term-level
  transparency of BM25. The runtime must reconstruct explanations at the feature level (§8).
- **Static vs. learned budget.** A fixed relevance floor is simple and predictable; a learned
  per-facet budget policy is better but introduces a feedback loop that can drift and must be
  guarded by calibration (mirrors `RFC-0009` §4.6 calibration concern).
- **Freshness vs. relevance.** A perfectly relevant but stale doc can be *worse than nothing*
  (`ARCH-01` "stale context" failure). Staleness must be able to veto, not merely nudge.

---

## 4. Advantages

- **Budget-native.** Framing selection as knapsack (not top-k with a cutoff) directly honors
  `RFC-0002`'s "budget before the model" invariant and the `BudgetPolicy.evict` contract; the
  drop log falls out of the algorithm for free.
- **Heterogeneous by construction.** LTR features normalize BM25/cosine/cross-encoder/EXP-
  applicability onto one comparable value, satisfying `RFC-0002` §4.3's requirement to rank
  knowledge, experience, code and state on a single `Confidence` scale.
- **Coverage-aware.** MMR/submodular diversity operationalizes the `ARCH-01` coverage facet of
  `coverage_confidence`, defending against context flooding.
- **Self-improving without touching the model.** LTR/policy learn from the EVAL corpus and
  dropped-candidate log, realizing `ARCH-01`'s "learned retrieval policies" future evolution and
  honoring `ADR-0003` (learning lives outside the model). The open benchmark grades the
  proprietary ranker.
- **Graceful degradation.** The pipeline collapses cleanly: if embeddings/cross-encoder are
  unavailable, BM25 + knapsack still produces a well-formed, budgeted, provenance-complete
  context.

---

## 5. Weaknesses

- **Label latency and bias.** LTR labels depend on downstream `EVAL-###` outcomes that arrive
  after execution; early corpora are sparse (cold start), and the drop log only reveals
  *observed* mistakes — never the counterfactual value of items that were included but useless.
- **Token-count estimation error.** Knapsack optimality is only as good as `tokens(c)`, which is
  model-family-specific (`RFC-0002` §5, §8). A mis-estimate risks wasted headroom or a late
  Gateway rejection. The runtime must budget against a conservative tokenizer hint from the Gateway.
- **Greedy sub-optimality.** The density heuristic is near-optimal but not exact; adversarial
  token/value distributions (one huge high-value doc vs. many small ones) can mislead it.
- **Diversity vs. decisiveness conflict.** MMR can *penalize* the second copy of the truly
  decisive fact if it looks redundant; λ must be tuned per task type or the decisive-but-similar
  item is dropped.
- **Feedback-loop drift.** A learned budget policy trained on its own past selections can entrench
  blind spots (never retrieve a facet → never learn it was needed). Requires exploration
  (ε-greedy / Thompson) and periodic recalibration.
- **Staleness signal quality.** Freshness weighting is only as good as the freshness metadata on
  candidates; volatile live-state facts without reliable timestamps degrade to guesswork.

---

## 6. Computational complexity

Let `n` = candidates retrieved, `m` = cross-encoder shortlist (`m ≪ n`), `d` = embedding dim,
`t` = tokens per candidate, `N` = indexed corpus size, `k` = final selection size.

| Stage | Complexity | Notes |
|---|---|---|
| BM25 scoring | `O(n · q)` for query length `q` | Inverted-index lookup; negligible. |
| Bi-encoder embedding (query) | `O(d)` amortized | Candidate vectors precomputed offline. |
| ANN retrieval | `O(log N)` per query (HNSW) | Sublinear in corpus size; the scalability win. |
| Cross-encoder rerank | `O(m · L²)` | `L` = joint sequence length; dominant model cost, bounded by `m`. |
| LTR scoring | `O(n · F)` for `F` features | GBM inference is cheap per candidate. |
| MMR selection | `O(k · n)` naïve; `O(k · n · d)` with sim | Greedy; `k` passes over remaining. |
| Knapsack (greedy density) | `O(n log n)` | Dominated by the sort. |
| Exact knapsack (DP, if ever) | `O(n · B)` pseudo-poly | Avoided; `B` (tokens) is large. |

**End-to-end query cost:** `O(n log N + m · L² + n log n)` — dominated by the `m` cross-encoder
calls. The `enrich` self-loop multiplies this by the number of re-retrieval turns, which
`RFC-0002` §5 and `RFC-0029` bound with a budget. Offline indexing is `O(N · d)` and incremental.

---

## 7. Enterprise scalability

**Throughput & latency.** At Fortune-500 scale a single Worker fleet may run thousands of tasks
concurrently over corpora of `10^6–10^8` knowledge/experience/code chunks. The two-stage
recall→rerank design keeps query latency near-constant in corpus size: ANN recall is
`O(log N)`, and the expensive cross-encoder touches only the `m ≈ 50–200` shortlist. Target
budget: recall < 50 ms, rerank < 300 ms (batched on an inference server), selection < 10 ms —
well inside a Worker's per-turn latency envelope.

**Indexing & sharding.** Embeddings live in an ANN index sharded by tenant/domain (checkout,
payments, privacy) so retrieval never crosses a policy boundary it should not (feeds the
`RFC-0002` sensitivity filter). BM25 inverted indices shard the same way. Cross-encoder and LTR
models are stateless services behind an autoscaling pool.

**Incremental update.** Knowledge and experience grow continuously (Experience is append-only,
`ADR-0005`). HNSW supports incremental insert; new `EXP-###`/`KN-###` chunks are embedded and
inserted without a full rebuild. LTR/policy models are retrained on a batch cadence (nightly)
from accumulated EVAL labels — never in the hot path.

**Cost.** Cross-encoder calls dominate token/compute cost; capping `m` and caching candidate
scores within a task (`ARCH-01` "cache candidate scores within a task", anti budget-thrash) keeps
per-task cost bounded and predictable. The learned budget policy is itself a cost optimizer:
spend cross-encoder calls only where they historically changed the selection. Predictive
pre-fetch (`ARCH-01` future) amortizes recall for recurring task shapes.

**Multi-tenant isolation.** Per-tenant indices, per-tenant LTR models (or tenant as a feature),
and per-tenant calibration prevent cross-customer leakage of both data and learned policy — a
hard requirement for a commercial runtime.

---

## 8. Explainability

The `ContextObject`'s mandatory included/excluded provenance (`RFC-0002` §4.4) is the audit
surface; the ranker must populate it with *reasons an engineer or auditor can act on*.

- **Per-item score decomposition.** Every included/excluded candidate records the contributing
  feature values: `{bm25: 7.1, cosine: 0.82, cross_enc: 0.90, authority: 0.95, staleness: 0.12,
  ltr_value: 0.94, tokens: 1_800, value_density: 5.2e-4}`. The `reason` string is generated from
  the top-weighted features ("primary change site; high cross-encoder relevance").
- **Drop attribution.** For every excluded item the log records *why*: `dropped_for_budget` (with
  the value-density threshold it fell below), `below_relevance_floor`, or `out_of_scope`. `KN-047`
  reads `dropped_for_budget @ density 3.4e-4 < cutoff 4.1e-4`. This is the diagnostic surface
  Reflection (`ARCH-05`) inspects first on failure.
- **Feature attribution for the learned ranker.** SHAP/gain values over the LTR features make the
  learned model's ordering inspectable ("staleness dominated the down-rank of KN-047"), recovering
  much of the transparency lost versus BM25.
- **Coverage explanation.** `coverage_confidence` is reported as a facet checklist (target code ✓,
  domain rules ✓, applicable experience ✓, dependency context ✗ → confidence capped), so DI and
  auditors see *which* facet was thin, not just a number.
- **Reproducibility.** Because the `ContextObject` is structured (`ADR-0011`), a ranking is
  replayable (`RFC-0024`): re-run the frozen feature vectors and model version, get the identical
  selection.

---

## 9. Recommendation

The recommended approach is a **hybrid cascade with a learned selection layer**:

1. **Recall** — BM25 ∪ dense bi-encoder (ANN), unioned for high recall and robust to
   embedding/lexical blind spots. BM25 alone is the graceful-degradation fallback.
2. **Precision** — cross-encoder re-rank of the top `m` shortlist, batched on an inference server.
3. **Scoring** — a LambdaMART/listwise **learning-to-rank** model over
   `[lexical, dense, cross, authority, staleness, kind, EXP-applicability, facet, token_cost]`,
   trained offline on the EnterpriseSim EVAL corpus + dropped-candidate log (learning outside the
   model, `ADR-0003`). Staleness and authority enter as features *and* as hard vetoes for volatile
   facts (prefer live state, `ARCH-01`).
4. **Selection** — **budget-aware greedy knapsack on value-density with an MMR diversity penalty**,
   implementing `BudgetPolicy.evict`, emitting the full drop log, with eviction **hysteresis** for
   the `enrich` self-loop (anti budget-thrash, `RFC-0002` §4.6).
5. **Budget allocation** — begin with a **static per-facet floor**; graduate to a **contextual
   bandit** budget-allocation policy (with ε-greedy exploration) once the EVAL corpus is dense
   enough to calibrate it. This is the "confidence-calibrated budgets" evolution.

**Why this hybrid.** It matches each `RFC-0002` concern to the cheapest technique that satisfies
it: ANN for scale, cross-encoder for precision, LTR for heterogeneous fusion, knapsack for the
budget invariant, MMR for coverage, bandit for adaptive allocation. It degrades gracefully to a
fully transparent BM25 + knapsack path when models are unavailable, keeps all learning outside
the model per `ADR-0003`, and produces the feature-decomposed provenance that `ARCH-01`/`RFC-0002`
make mandatory. Crucially, selection is knapsack-first, not top-k — so the dropped-candidate log,
the ECL's most valuable failure-diagnosis surface, is a first-class output rather than an
afterthought. The open benchmark grades it; the runtime stays proprietary.
