# Sprint 13 — Engineering Evolution (2026-06-22 → 2026-07-03)

> Part of [six months of MCG engineering history](../README.md). No release train this sprint (continued evolution).

| Metric | Value |
|---|---|
| Stories delivered | 13 (8 features, 6 debt/spikes, 1 bugs) |
| Incidents | 0 |
| Hotfixes | 0 |
| Worker executions (corpus) | 9 |
| Mean evaluation score | 0.948  (Δ +0.039) |
| Mean fused confidence | 0.923 |

## New features
- `STF-819` Hydrate cart badge without full reload (APP-001)
- `STF-822` Server-side render product detail pages (APP-001)
- `CRT-543` Cart-level price preview (APP-004)
- `STF-826` Lazy-load below-the-fold imagery (APP-001)
- `POR-640` Address book management (APP-021)
- `POR-644` Saved payment methods ui (APP-021)
- `POR-647` Order timeline view (APP-021)
- `POR-650` Loyalty points balance widget (APP-021)

## Technical debt
- `STF-819` Hydrate cart badge without full reload (APP-001)
- `CRT-543` Cart-level price preview (APP-004)
- `POR-627` Investigate approach for download invoice as PDF (APP-021)
- `POR-630` Investigate approach for download invoice as PDF (APP-021)
- `INV-1239` Refactor: low-stock event publishing (APP-010)
- `POR-644` Saved payment methods ui (APP-021)

## Architecture changes
- `KN-200` Storefront Rendering & BFF
- `KN-201` Customer Portal & Self-Service Returns (My Meridian)
- `KN-203` Cart State & Redis Resilience
- `KN-209` Inventory Available-to-Promise (ATP)

## New / updated APIs
- `KN-251` Cart Service API v1
- `KN-257` Inventory Service API v1
- `KN-259` Storefront BFF API v1
- `KN-260` Customer Portal (My Meridian) API v1

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
- Mean Worker evaluation score **0.948** (up +0.039 vs previous sprint); mean fused confidence **0.923**.
- Cold-start failures in new task families produce experiences that lift later scores (see [`../../corpus/`](../../corpus/)).

