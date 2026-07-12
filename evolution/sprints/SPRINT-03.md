# Sprint 3 — Engineering Evolution (2026-02-02 → 2026-02-13)

> Part of [six months of MCG engineering history](../README.md). Release train **REL-2026-003 — Dynamic Pricing Foundations**.

| Metric | Value |
|---|---|
| Stories delivered | 9 (6 features, 1 debt/spikes, 2 bugs) |
| Incidents | 1 |
| Hotfixes | 0 |
| Worker executions (corpus) | 6 |
| Mean evaluation score | 0.618  (Δ +0.048) |
| Mean fused confidence | 0.653 |

## New features
- `STF-825` Server-side render product detail pages (APP-001)
- `PRC-1128` Regional price resolution (APP-007)
- `PRC-1133` Cost-plus margin guardrails (APP-007)
- `PRC-1137` Currency rounding rules (APP-007)
- `PRC-1149` Cost-plus margin guardrails (APP-007)
- `PRM-1020` Write-through promo cache (APP-008)

## Technical debt
- `PRC-1152` Fix incorrect behavior in cost-plus margin guardrails (APP-007)

## Architecture changes
- `KN-200` Storefront Rendering & BFF
- `KN-206` Pricing Resolution
- `KN-207` Promotions Engine & Cache
- `KN-228` Promotion-Cache Write-Through Design

## New / updated APIs
- `KN-254` Pricing Service API v1
- `KN-255` Promotions Engine API v1
- `KN-259` Storefront BFF API v1
- `KN-269` Pricing Events (Kafka) v1

## Business-rule changes
- _(none this sprint)_

## Incidents
- `INC-2026-004` [Sev2] Regional price rule misconfiguration in APAC — root cause: config_change

## Hotfixes
- _(none this sprint)_

## Release notes
See [`REL-2026-003`](../release-notes/REL-2026-003.md) — Regional price resolution and price-consistency guarantees.

## Knowledge updates
- `KN-303` postmortem (Postmortem: Regional price rule misconfiguration in APAC)

## Experience updates
- `EXP-090` reinforced — When implementing guest flows in Checkout (APP-003), ensure no code path provisi
- `EXP-142` created — Async webhook tests need deterministic clocks or they flake.
- `EXP-201` created — Regional rounding rules must be validated per-currency before rollout.
- `EXP-204` reinforced — Relevance changes need offline judgment-set evaluation before shipping.
- `EXP-207` reinforced — Cart writes need optimistic concurrency plus Redis failover drills.
- `EXP-210` reinforced — Catalog ingestion needs backpressure and data-platform outage handling.

## Evaluation improvements
- Mean Worker evaluation score **0.618** (up +0.048 vs previous sprint); mean fused confidence **0.653**.
- Cold-start failures in new task families produce experiences that lift later scores (see [`../../corpus/`](../../corpus/)).

