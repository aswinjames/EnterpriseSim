# Sprint 11 — Engineering Evolution (2026-05-25 → 2026-06-05)

> Part of [six months of MCG engineering history](../README.md). No release train this sprint (continued evolution).

| Metric | Value |
|---|---|
| Stories delivered | 11 (6 features, 4 debt/spikes, 1 bugs) |
| Incidents | 0 |
| Hotfixes | 0 |
| Worker executions (corpus) | 7 |
| Mean evaluation score | 0.829  (Δ +0.048) |
| Mean fused confidence | 0.823 |

## New features
- `GW-444` Edge oidc verification (APP-024)
- `CAT-943` Product enrichment webhook (APP-005)
- `SRCH-736` Hybrid lexical+semantic ranking (APP-006)
- `CAT-947` Category taxonomy versioning (APP-005)
- `SRCH-741` Hybrid lexical+semantic ranking (APP-006)
- `SRCH-747` Typo-tolerant query parsing (APP-006)

## Technical debt
- `PRC-1124` Refactor: markdown scheduling (APP-007)
- `SRCH-729` Investigate approach for faceted filter performance (APP-006)
- `GW-444` Edge oidc verification (APP-024)
- `SRCH-745` Refactor: personalized recommendations sidebar (APP-006)

## Architecture changes
- `KN-204` Product Catalog & Indexing
- `KN-205` Search Hybrid Ranking
- `KN-206` Pricing Resolution
- `KN-208` Order Management Saga

## New / updated APIs
- `KN-252` Product Catalog Service API v1
- `KN-253` Search & Browse Service API v1
- `KN-254` Pricing Service API v1
- `KN-256` Order Management (OMS) API v1

## Business-rule changes
- _(none this sprint)_

## Incidents
- _(none this sprint)_

## Hotfixes
- _(none this sprint)_

## Release notes
- _(no release train; changes rolled continuously)_

## Knowledge updates
- _(none this sprint)_

## Experience updates
- `EXP-055` reinforced — Pricing/promotion changes during a promo window require a write-through APP-008 
- `EXP-202` reinforced — 3DS challenge flows need PSP-sandbox contract tests to prevent auth regressions.
- `EXP-203` reinforced — Multi-warehouse ATP requires reservation locks to prevent oversell.
- `EXP-205` reinforced — Rate-limit thresholds must be load-tested against realistic traffic shapes.
- `EXP-206` reinforced — Saga compensations must be idempotent and tested for partial failure.
- `EXP-208` reinforced — Returns-eligibility rules need a golden-case suite across order states.
- `EXP-209` reinforced — Synchronous promo calls on the checkout path must be made async or cached.

## Evaluation improvements
- Mean Worker evaluation score **0.829** (up +0.048 vs previous sprint); mean fused confidence **0.823**.
- Cold-start failures in new task families produce experiences that lift later scores (see [`../../corpus/`](../../corpus/)).

