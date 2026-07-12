# BENCH-02 — Knowledge Retrieval

| Field | Value |
|---|---|
| Suite | `BENCH-02` |
| Name | Knowledge Retrieval |
| Primarily exercises | Knowledge Layer (`ARCH-02`) |
| Canon / Arch | `CANON-001` §9 (Stage 1), `ARCH-02`, `ARCH-04` |
| Owner | AI Engineering (`TEAM-070`) + Data Platform (`TEAM-060`) |

---

## Purpose

Measure whether the Worker can find the **governed enterprise truth** a task needs — the
`KN-###` documents, standards, API contracts and business rules that make it *knowledgeable*
about MCG rather than merely clever (`ARCH-02`). This isolates retrieval quality *before* it is
composed into context (BENCH-01).

## What it measures

- **Retrieval recall / precision** against a labelled ideal knowledge set.
- **Ranking quality** — are the highest-authority, most-relevant items surfaced first (nDCG/MRR)?
- **Hybrid-retrieval strength** — does the Worker find items reachable only by keyword or graph,
  not semantic similarity alone (the canonical `APP-012` keyword + threat-model graph case)?
- **Authority/freshness sensitivity** — does it prefer canon-derived, fresh knowledge over stale
  or deprecated items?

## Task design

Given a natural-language information need (or a task trigger) and the knowledge corpus with
labelled relevance, the Worker returns a ranked list of `KN-###` candidates. Cases include
**semantic-miss** variants (the answer shares no surface terms with the query), **exact-ID**
variants (must match `APP-012`), **graph** variants (multi-hop: "what breaks if `APP-007`
changes?"), and **staleness** variants (a deprecated item must be down-ranked).

## Inputs

- `inputs.query` — the information need or task trigger.
- `inputs.corpus` — `KN-###` handles with hidden relevance/authority/freshness labels.
- `inputs.retrieval_budget` — max items to return (forces ranking, not dumping).

## Ground truth

`type: ranking` with an ideal ordering plus `must_include` for non-negotiable items:

- ideal ranked set derived from labelled relevance × authority × freshness (`source: KN-045`
  and its `relations`).
- `must_exclude` — deprecated/contradicted items that must not surface at the top.

## Scoring (objective-first)

| Metric | Kind | Weight | Notes |
|---|---|---|---|
| `recall_at_k` | objective | 0.30 | Relevant items found within the budget `k`. |
| `precision_at_k` | objective | 0.25 | Relevant / returned within `k`. |
| `ndcg` | objective | 0.25 | Rank-aware: high-authority items ranked first. |
| `authority_freshness_fit` | objective | 0.10 | Canon/fresh preferred over stale/deprecated. |
| `citation_appropriateness` | rubric | 0.10 | Are returned items actually usable for the need? |

Objective share = 0.90. `aggregation: weighted_sum`; a `must_exclude` deprecated item in top-k
is a hard gate → cap.

## Confidence handling

Judgment confidence high (objective-dominant). Ranking metrics are deterministic given a fixed
tie-break rule, which the harness pins for reproducibility.

## Pass/fail thresholds

`pass ≥ 0.80`, `partial ≥ 0.60`.

## Model-independence notes

Ground truth is defined over MCG `KN-###` IDs and their authority metadata, never over model
phrasing, so the suite is provider-neutral. Embedding-model differences show up as *retrieval
quality*, which is exactly what is being measured — the ECL treats the retriever as part of the
Knowledge Layer, not the LLM (`ARCH-02`).

## Failure modes / anti-gaming

- **Semantic-only retrieval** misses the exact-ID and graph cases by design (hybrid required).
- **Recall stuffing** defeated by `precision_at_k` + budget `k`.
- **Deprecated resurfacing** hard-gated (`ARCH-02` "over-retention" failure).
- Held-out queries per domain detect memorization of the public query set.

## Example case

```json
{
  "id": "BC-0201",
  "suite": "BENCH-02",
  "schema_version": "2020-12.v1",
  "created_at": "2026-07-05T09:00:00Z",
  "title": "Retrieve PCI cardholder-data boundary knowledge",
  "ecl_layer": "ARCH-02",
  "task_ref": "INC-2026-007",
  "apps": ["APP-012"],
  "inputs": {
    "query": "Where is the PCI cardholder data boundary and what governs it?",
    "corpus": ["KN-045","KN-052","KN-063","KN-101"],
    "retrieval_budget": { "k": 5 }
  },
  "ground_truth": {
    "type": "ranking",
    "expected": ["KN-052"],
    "must_include": ["KN-052"],
    "must_exclude": ["KN-101"],
    "source": "KN-052",
    "notes": "Semantic search alone misses the exact APP-012 token; keyword + graph recover it."
  },
  "rubric": { "id": "RUBRIC-knowledge-retrieval", "version": 1 },
  "scoring": { "objective_first": true, "aggregation": "weighted_sum",
    "metrics": [
      { "name": "recall_at_k", "kind": "objective", "weight": 0.30 },
      { "name": "precision_at_k", "kind": "objective", "weight": 0.25 },
      { "name": "ndcg", "kind": "objective", "weight": 0.25 },
      { "name": "authority_freshness_fit", "kind": "objective", "weight": 0.10 },
      { "name": "citation_appropriateness", "kind": "rubric", "weight": 0.10 }
    ] },
  "thresholds": { "pass": 0.80, "partial": 0.60 },
  "repeats": 5,
  "references": ["KN-052","KN-045","APP-012","INC-2026-007"]
}
```

## Relationship to ECL layers

Scores the **Knowledge Layer** (`ARCH-02`) retrieval surface in isolation. Its output feeds the
**Context Layer** (BENCH-01); a Worker can retrieve well (BENCH-02) yet compose poorly (BENCH-01),
or vice-versa — separating them localizes the defect. Promoted experience (`ARCH-03`→`ARCH-02`)
enters the corpus over time, so BENCH-02 scores should ratchet up as the flywheel turns (visible
in BENCH-09).
