# Sprint 6 — Engineering Evolution (2026-03-16 → 2026-03-27)

> Part of [six months of MCG engineering history](../README.md). Release train **REL-2026-006 — Order Orchestration & Inventory ATP**.

| Metric | Value |
|---|---|
| Stories delivered | 14 (11 features, 6 debt/spikes, 1 bugs) |
| Incidents | 2 |
| Hotfixes | 0 |
| Worker executions (corpus) | 10 |
| Mean evaluation score | 0.722  (Δ +0.022) |
| Mean fused confidence | 0.731 |

## New features
- `PRC-1131` Price change audit trail (APP-007)
- `OMS-1323` Cancellation and refund flow (APP-009)
- `CRT-551` Redis failover for cart state (APP-004)
- `INV-1238` Multi-warehouse allocation (APP-010)
- `OMS-1335` Saga-based fulfillment orchestration (APP-009)
- `CAT-945` Category taxonomy versioning (APP-005)
- `OMS-1342` Backorder handling (APP-009)
- `OMS-1346` Partial shipment support (APP-009)
- `INV-1242` Reservation ttl (APP-010)
- `OMS-1350` Cancellation and refund flow (APP-009)

## Technical debt
- `OMS-1323` Cancellation and refund flow (APP-009)
- `CRT-551` Redis failover for cart state (APP-004)
- `CHK-1431` Investigate approach for reduce p99 checkout latency (APP-003)
- `OMS-1342` Backorder handling (APP-009)
- `OMS-1346` Partial shipment support (APP-009)
- `INV-1245` Available-to-promise reservation fix (APP-010)

## Architecture changes
- `KN-202` Checkout Orchestration
- `KN-203` Cart State & Redis Resilience
- `KN-204` Product Catalog & Indexing
- `KN-206` Pricing Resolution

## New / updated APIs
- `KN-250` Checkout Service API v1
- `KN-251` Cart Service API v1
- `KN-252` Product Catalog Service API v1
- `KN-254` Pricing Service API v1

## Business-rule changes
- _(none this sprint)_

## Incidents
- `INC-2026-011` [Sev2] Promo cache staleness recurrence during flash sale — root cause: cache_staleness
- `INC-2026-012` [Sev2] ATP oversell on multi-warehouse SKUs — root cause: data_issue

## Hotfixes
- _(none this sprint)_

## Release notes
See [`REL-2026-006`](../release-notes/REL-2026-006.md) — Order lifecycle robustness and accurate available-to-promise.

## Knowledge updates
- `KN-306` postmortem (Postmortem: Promo cache staleness recurrence during flash sale)
- `KN-307` postmortem (Postmortem: ATP oversell on multi-warehouse SKUs)

## Experience updates
- `EXP-055` reinforced — Pricing/promotion changes during a promo window require a write-through APP-008 
- `EXP-090` reinforced — When implementing guest flows in Checkout (APP-003), ensure no code path provisi
- `EXP-142` reinforced — Async webhook tests need deterministic clocks or they flake.
- `EXP-201` reinforced — Regional rounding rules must be validated per-currency before rollout.
- `EXP-202` reinforced — 3DS challenge flows need PSP-sandbox contract tests to prevent auth regressions.
- `EXP-203` created — Multi-warehouse ATP requires reservation locks to prevent oversell.
- `EXP-204` reinforced — Relevance changes need offline judgment-set evaluation before shipping.
- `EXP-206` created — Saga compensations must be idempotent and tested for partial failure.
- `EXP-207` reinforced — Cart writes need optimistic concurrency plus Redis failover drills.
- `EXP-210` reinforced — Catalog ingestion needs backpressure and data-platform outage handling.

## Evaluation improvements
- Mean Worker evaluation score **0.722** (up +0.022 vs previous sprint); mean fused confidence **0.731**.
- Cold-start failures in new task families produce experiences that lift later scores (see [`../../corpus/`](../../corpus/)).

