# Sprint 9 — Engineering Evolution (2026-04-27 → 2026-05-08)

> Part of [six months of MCG engineering history](../README.md). Release train **REL-2026-009 — Peak-Readiness & Observability**.

| Metric | Value |
|---|---|
| Stories delivered | 17 (12 features, 4 debt/spikes, 2 bugs) |
| Incidents | 1 |
| Hotfixes | 0 |
| Worker executions (corpus) | 10 |
| Mean evaluation score | 0.765  (Δ +0.002) |
| Mean fused confidence | 0.772 |

## New features
- `GW-437` Edge oidc verification (APP-024)
- `CAT-940` Sub-minute catalog reindex (APP-005)
- `GW-450` Token-bucket rate limiting (APP-024)
- `CHK-1409` Graceful degradation when promotions unavailable (APP-003)
- `GW-453` Circuit breaker per upstream (APP-024)
- `GW-457` Token-bucket rate limiting (APP-024)
- `CHK-1419` Support guest checkout (APP-003)
- `CRT-554` Redis failover for cart state (APP-004)
- `CHK-1422` Split-tender payment support (APP-003)
- `CHK-1423` Reduce p99 checkout latency (APP-003)

## Technical debt
- `GW-450` Token-bucket rate limiting (APP-024)
- `CHK-1417` Refactor: split-tender payment support (APP-003)
- `CHK-1419` Support guest checkout (APP-003)
- `CHK-1433` Investigate approach for handle partial payment authorization (APP-003)

## Architecture changes
- `KN-200` Storefront Rendering & BFF
- `KN-202` Checkout Orchestration
- `KN-203` Cart State & Redis Resilience
- `KN-204` Product Catalog & Indexing

## New / updated APIs
- `KN-250` Checkout Service API v1
- `KN-251` Cart Service API v1
- `KN-252` Product Catalog Service API v1
- `KN-253` Search & Browse Service API v1

## Business-rule changes
- _(none this sprint)_

## Incidents
- `INC-2026-016` [Sev2] Storefront latency degradation under load test — root cause: capacity

## Hotfixes
- _(none this sprint)_

## Release notes
See [`REL-2026-009`](../release-notes/REL-2026-009.md) — Prepare the commerce path for peak traffic with SLO-driven observability.

## Knowledge updates
- `KN-311` postmortem (Postmortem: Storefront latency degradation under load test)

## Experience updates
- `EXP-055` reinforced — Pricing/promotion changes during a promo window require a write-through APP-008 
- `EXP-142` reinforced — Async webhook tests need deterministic clocks or they flake.
- `EXP-201` reinforced — Regional rounding rules must be validated per-currency before rollout.
- `EXP-202` reinforced — 3DS challenge flows need PSP-sandbox contract tests to prevent auth regressions.
- `EXP-203` reinforced — Multi-warehouse ATP requires reservation locks to prevent oversell.
- `EXP-204` reinforced — Relevance changes need offline judgment-set evaluation before shipping.
- `EXP-205` reinforced — Rate-limit thresholds must be load-tested against realistic traffic shapes.
- `EXP-206` reinforced — Saga compensations must be idempotent and tested for partial failure.
- `EXP-208` reinforced — Returns-eligibility rules need a golden-case suite across order states.
- `EXP-209` created — Synchronous promo calls on the checkout path must be made async or cached.

## Evaluation improvements
- Mean Worker evaluation score **0.765** (up +0.002 vs previous sprint); mean fused confidence **0.772**.
- Cold-start failures in new task families produce experiences that lift later scores (see [`../../corpus/`](../../corpus/)).

