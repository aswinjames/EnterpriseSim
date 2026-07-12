# Sprint 12 — Engineering Evolution (2026-06-08 → 2026-06-19)

> Part of [six months of MCG engineering history](../README.md). No release train this sprint (continued evolution).

| Metric | Value |
|---|---|
| Stories delivered | 9 (5 features, 3 debt/spikes, 1 bugs) |
| Incidents | 1 |
| Hotfixes | 0 |
| Worker executions (corpus) | 7 |
| Mean evaluation score | 0.909  (Δ +0.08) |
| Mean fused confidence | 0.87 |

## New features
- `PAY-976` Partial capture support (APP-012)
- `OMS-1313` Backorder handling (APP-009)
- `OMS-1315` Backorder handling (APP-009)
- `PAY-993` Refund idempotency (APP-012)
- `OMS-1352` Order state machine hardening (APP-009)

## Technical debt
- `OMS-1327` Refactor: order state machine hardening (APP-009)
- `PRC-1158` Refactor: price-consistency verification job (APP-007)
- `OMS-1352` Order state machine hardening (APP-009)

## Architecture changes
- `KN-206` Pricing Resolution
- `KN-208` Order Management Saga
- `KN-210` Payments & PCI Boundary

## New / updated APIs
- `KN-254` Pricing Service API v1
- `KN-256` Order Management (OMS) API v1
- `KN-258` Payments Service API v1
- `KN-265` Order Events (Kafka) v1

## Business-rule changes
- _(none this sprint)_

## Incidents
- `INC-2026-021` [Sev3] Catalog ingestion stalled on data-platform outage — root cause: dependency_failure

## Hotfixes
- _(none this sprint)_

## Release notes
- _(no release train; changes rolled continuously)_

## Knowledge updates
- `KN-314` postmortem (Postmortem: Catalog ingestion stalled on data-platform outage)

## Experience updates
- `EXP-055` reinforced — Pricing/promotion changes during a promo window require a write-through APP-008 
- `EXP-202` reinforced — 3DS challenge flows need PSP-sandbox contract tests to prevent auth regressions.
- `EXP-203` reinforced — Multi-warehouse ATP requires reservation locks to prevent oversell.
- `EXP-205` reinforced — Rate-limit thresholds must be load-tested against realistic traffic shapes.
- `EXP-206` reinforced — Saga compensations must be idempotent and tested for partial failure.
- `EXP-208` reinforced — Returns-eligibility rules need a golden-case suite across order states.
- `EXP-209` reinforced — Synchronous promo calls on the checkout path must be made async or cached.

## Evaluation improvements
- Mean Worker evaluation score **0.909** (up +0.080 vs previous sprint); mean fused confidence **0.87**.
- Cold-start failures in new task families produce experiences that lift later scores (see [`../../corpus/`](../../corpus/)).

