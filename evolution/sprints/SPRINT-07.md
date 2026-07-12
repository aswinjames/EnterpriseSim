# Sprint 7 — Engineering Evolution (2026-03-30 → 2026-04-10)

> Part of [six months of MCG engineering history](../README.md). Release train **REL-2026-007 — Gateway Rate-Limiting & Edge Auth**.

| Metric | Value |
|---|---|
| Stories delivered | 13 (10 features, 3 debt/spikes, 1 bugs) |
| Incidents | 2 |
| Hotfixes | 0 |
| Worker executions (corpus) | 11 |
| Mean evaluation score | 0.743  (Δ +0.021) |
| Mean fused confidence | 0.761 |

## New features
- `GW-440` Token-bucket rate limiting (APP-024)
- `PRM-1018` Exclusion-list handling (APP-008)
- `GW-459` Edge oidc verification (APP-024)
- `GW-460` Edge oidc verification (APP-024)
- `OMS-1330` Idempotent event consumption (APP-009)
- `PRM-1024` Budget caps per campaign (APP-008)
- `CAT-949` Category taxonomy versioning (APP-005)
- `OMS-1355` Cancellation and refund flow (APP-009)
- `CAT-950` Category taxonomy versioning (APP-005)
- `GW-472` Request coalescing (APP-024)

## Technical debt
- `GW-440` Token-bucket rate limiting (APP-024)
- `GW-446` Fix incorrect behavior in canary routing (APP-024)
- `GW-471` Investigate approach for token-bucket rate limiting (APP-024)

## Architecture changes
- `KN-204` Product Catalog & Indexing
- `KN-207` Promotions Engine & Cache
- `KN-208` Order Management Saga
- `KN-211` API Gateway & Edge

## New / updated APIs
- `KN-252` Product Catalog Service API v1
- `KN-255` Promotions Engine API v1
- `KN-256` Order Management (OMS) API v1
- `KN-261` API Gateway Admin API v1

## Business-rule changes
- _(none this sprint)_

## Incidents
- `INC-2026-013` [Sev3] Rate-limit threshold too aggressive after rollout — root cause: config_change
- `INC-2026-014` [Sev2] Edge OIDC verification rejected valid tokens — root cause: deployment

## Hotfixes
- _(none this sprint)_

## Release notes
See [`REL-2026-007`](../release-notes/REL-2026-007.md) — Protect origin services and standardize edge authentication.

## Knowledge updates
- `KN-308` postmortem (Postmortem: Rate-limit threshold too aggressive after rollout)
- `KN-309` postmortem (Postmortem: Edge OIDC verification rejected valid tokens)

## Experience updates
- `EXP-055` reinforced — Pricing/promotion changes during a promo window require a write-through APP-008 
- `EXP-090` reinforced — When implementing guest flows in Checkout (APP-003), ensure no code path provisi
- `EXP-142` reinforced — Async webhook tests need deterministic clocks or they flake.
- `EXP-201` reinforced — Regional rounding rules must be validated per-currency before rollout.
- `EXP-202` reinforced — 3DS challenge flows need PSP-sandbox contract tests to prevent auth regressions.
- `EXP-203` reinforced — Multi-warehouse ATP requires reservation locks to prevent oversell.
- `EXP-204` reinforced — Relevance changes need offline judgment-set evaluation before shipping.
- `EXP-205` created — Rate-limit thresholds must be load-tested against realistic traffic shapes.
- `EXP-206` reinforced — Saga compensations must be idempotent and tested for partial failure.
- `EXP-207` reinforced — Cart writes need optimistic concurrency plus Redis failover drills.
- `EXP-210` reinforced — Catalog ingestion needs backpressure and data-platform outage handling.

## Evaluation improvements
- Mean Worker evaluation score **0.743** (up +0.021 vs previous sprint); mean fused confidence **0.761**.
- Cold-start failures in new task families produce experiences that lift later scores (see [`../../corpus/`](../../corpus/)).

