# Sprint 2 — Engineering Evolution (2026-01-19 → 2026-01-30)

> Part of [six months of MCG engineering history](../README.md). Release train **REL-2026-002 — Search Relevance & Catalog Freshness**.

| Metric | Value |
|---|---|
| Stories delivered | 10 (5 features, 3 debt/spikes, 3 bugs) |
| Incidents | 1 |
| Hotfixes | 0 |
| Worker executions (corpus) | 3 |
| Mean evaluation score | 0.57  (Δ -0.11) |
| Mean fused confidence | 0.613 |

## New features
- `CAT-933` Category taxonomy versioning (APP-005)
- `SRCH-724` Reduce reindex propagation lag (APP-006)
- `OMS-1318` Idempotent event consumption (APP-009)
- `OMS-1349` Cancellation and refund flow (APP-009)
- `SRCH-738` Personalized recommendations sidebar (APP-006)

## Technical debt
- `SRCH-724` Reduce reindex propagation lag (APP-006)
- `CRT-547` Refactor: cap line-item quantity (APP-004)
- `OMS-1318` Idempotent event consumption (APP-009)

## Architecture changes
- `KN-203` Cart State & Redis Resilience
- `KN-204` Product Catalog & Indexing
- `KN-205` Search Hybrid Ranking
- `KN-206` Pricing Resolution

## New / updated APIs
- `KN-251` Cart Service API v1
- `KN-252` Product Catalog Service API v1
- `KN-253` Search & Browse Service API v1
- `KN-254` Pricing Service API v1

## Business-rule changes
- _(none this sprint)_

## Incidents
- `INC-2026-003` [Sev3] Search reindex lag surfaced stale prices in results — root cause: data_issue

## Hotfixes
- _(none this sprint)_

## Release notes
See [`REL-2026-002`](../release-notes/REL-2026-002.md) — Improve query relevance and shorten catalog-to-index propagation.

## Knowledge updates
- `KN-302` postmortem (Postmortem: Search reindex lag surfaced stale prices in results)

## Experience updates
- `EXP-204` created — Relevance changes need offline judgment-set evaluation before shipping.
- `EXP-207` reinforced — Cart writes need optimistic concurrency plus Redis failover drills.
- `EXP-210` created — Catalog ingestion needs backpressure and data-platform outage handling.

## Evaluation improvements
- Mean Worker evaluation score **0.57** (down -0.110 vs previous sprint); mean fused confidence **0.613**.
- Cold-start failures in new task families produce experiences that lift later scores (see [`../../corpus/`](../../corpus/)).

