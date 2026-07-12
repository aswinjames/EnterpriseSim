# Sprint 10 — Engineering Evolution (2026-05-11 → 2026-05-22)

> Part of [six months of MCG engineering history](../README.md). Release train **REL-2026-010 — Checkout Latency & Promo Cache**.

| Metric | Value |
|---|---|
| Stories delivered | 10 (3 features, 4 debt/spikes, 3 bugs) |
| Incidents | 2 |
| Hotfixes | 0 |
| Worker executions (corpus) | 8 |
| Mean evaluation score | 0.781  (Δ +0.016) |
| Mean fused confidence | 0.786 |

## New features
- `PRM-1015` Exclusion-list handling (APP-008)
- `CHK-1427` Split-tender payment support (APP-003)
- `PRM-1030` Write-through promo cache (APP-008)

## Technical debt
- `CHK-1415` Fix incorrect behavior in add idempotency keys to order placement (APP-003)
- `POR-632` Refactor: saved payment methods UI (APP-021)
- `PAY-985` Investigate approach for PSP failover routing (APP-012)
- `PRM-1041` Refactor: coupon eligibility engine (APP-008)

## Architecture changes
- `KN-201` Customer Portal & Self-Service Returns (My Meridian)
- `KN-202` Checkout Orchestration
- `KN-204` Product Catalog & Indexing
- `KN-207` Promotions Engine & Cache

## New / updated APIs
- `KN-250` Checkout Service API v1
- `KN-252` Product Catalog Service API v1
- `KN-255` Promotions Engine API v1
- `KN-258` Payments Service API v1

## Business-rule changes
- _(none this sprint)_

## Incidents
- `INC-2026-018` [Sev1] Third promo-cache staleness incident triggers systemic fix — root cause: cache_staleness
- `INC-2026-019` [Sev3] Checkout p99 latency regression from synchronous promo call — root cause: capacity

## Hotfixes
- _(none this sprint)_

## Release notes
See [`REL-2026-010`](../release-notes/REL-2026-010.md) — Cut p99 checkout latency and eliminate promo-cache staleness at write time.

## Knowledge updates
- `KN-312` postmortem (Postmortem: Third promo-cache staleness incident triggers systemic fix)
- `KN-313` postmortem (Postmortem: Checkout p99 latency regression from synchronous promo call)

## Experience updates
- `EXP-055` reinforced — Pricing/promotion changes during a promo window require a write-through APP-008 
- `EXP-201` reinforced — Regional rounding rules must be validated per-currency before rollout.
- `EXP-202` reinforced — 3DS challenge flows need PSP-sandbox contract tests to prevent auth regressions.
- `EXP-203` reinforced — Multi-warehouse ATP requires reservation locks to prevent oversell.
- `EXP-205` reinforced — Rate-limit thresholds must be load-tested against realistic traffic shapes.
- `EXP-206` reinforced — Saga compensations must be idempotent and tested for partial failure.
- `EXP-208` reinforced — Returns-eligibility rules need a golden-case suite across order states.
- `EXP-209` reinforced — Synchronous promo calls on the checkout path must be made async or cached.

## Evaluation improvements
- Mean Worker evaluation score **0.781** (up +0.016 vs previous sprint); mean fused confidence **0.786**.
- Cold-start failures in new task families produce experiences that lift later scores (see [`../../corpus/`](../../corpus/)).

