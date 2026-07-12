# Sprint 4 — Engineering Evolution (2026-02-16 → 2026-02-27)

> Part of [six months of MCG engineering history](../README.md). Release train **REL-2026-004 — Promotions Engine Hardening**.

| Metric | Value |
|---|---|
| Stories delivered | 14 (7 features, 8 debt/spikes, 1 bugs) |
| Incidents | 1 |
| Hotfixes | 0 |
| Worker executions (corpus) | 7 |
| Mean evaluation score | 0.667  (Δ +0.049) |
| Mean fused confidence | 0.693 |

## New features
- `PRM-1014` Budget caps per campaign (APP-008)
- `PRM-1017` Write-through promo cache (APP-008)
- `PRC-1146` Price-consistency verification job (APP-007)
- `PRM-1022` Coupon eligibility engine (APP-008)
- `PAY-987` Retry-storm protection (APP-012)
- `PRM-1040` Stacked promotion rules v2 (APP-008)
- `PRC-1164` Cost-plus margin guardrails (APP-007)

## Technical debt
- `PRM-1014` Budget caps per campaign (APP-008)
- `INV-1237` Refactor: stock reconciliation job (APP-010)
- `PRC-1141` Investigate approach for markdown scheduling (APP-007)
- `CRT-558` Refactor: merge guest cart on sign-in (APP-004)
- `PRM-1034` Refactor: write-through promo cache (APP-008)
- `PRM-1037` Refactor: budget caps per campaign (APP-008)
- `PAY-987` Retry-storm protection (APP-012)
- `PRM-1040` Stacked promotion rules v2 (APP-008)

## Architecture changes
- `KN-203` Cart State & Redis Resilience
- `KN-206` Pricing Resolution
- `KN-207` Promotions Engine & Cache
- `KN-209` Inventory Available-to-Promise (ATP)

## New / updated APIs
- `KN-251` Cart Service API v1
- `KN-254` Pricing Service API v1
- `KN-255` Promotions Engine API v1
- `KN-257` Inventory Service API v1

## Business-rule changes
- _(none this sprint)_

## Incidents
- `INC-2026-007` [Sev1] Promotion-window price change did not invalidate promo cache — root cause: cache_staleness

## Hotfixes
- _(none this sprint)_

## Release notes
See [`REL-2026-004`](../release-notes/REL-2026-004.md) — Correctness of stacked promotions and promotion-cache invalidation.

## Knowledge updates
- `KN-304` postmortem (Postmortem: Promotion-window price change did not invalidate promo cache)

## Experience updates
- `EXP-055` created — Pricing/promotion changes during a promo window require a write-through APP-008 
- `EXP-090` reinforced — When implementing guest flows in Checkout (APP-003), ensure no code path provisi
- `EXP-142` reinforced — Async webhook tests need deterministic clocks or they flake.
- `EXP-201` reinforced — Regional rounding rules must be validated per-currency before rollout.
- `EXP-204` reinforced — Relevance changes need offline judgment-set evaluation before shipping.
- `EXP-207` reinforced — Cart writes need optimistic concurrency plus Redis failover drills.
- `EXP-210` reinforced — Catalog ingestion needs backpressure and data-platform outage handling.

## Evaluation improvements
- Mean Worker evaluation score **0.667** (up +0.049 vs previous sprint); mean fused confidence **0.693**.
- Cold-start failures in new task families produce experiences that lift later scores (see [`../../corpus/`](../../corpus/)).

