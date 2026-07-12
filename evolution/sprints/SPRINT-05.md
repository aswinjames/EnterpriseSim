# Sprint 5 — Engineering Evolution (2026-03-02 → 2026-03-13)

> Part of [six months of MCG engineering history](../README.md). Release train **REL-2026-005 — Payments Reliability & 3DS**.

| Metric | Value |
|---|---|
| Stories delivered | 12 (6 features, 4 debt/spikes, 1 bugs) |
| Incidents | 1 |
| Hotfixes | 0 |
| Worker executions (corpus) | 8 |
| Mean evaluation score | 0.7  (Δ +0.033) |
| Mean fused confidence | 0.715 |

## New features
- `PAY-980` Implement 3DS2 challenge flow for card authorization (APP-012)
- `PAY-975` Tokenized card vault (APP-012)
- `POR-636` Order timeline view (APP-021)
- `PAY-981` Tokenized card vault (APP-012)
- `GW-464` Load-shedding under pressure (APP-024)
- `PAY-991` Refund idempotency (APP-012)

## Technical debt
- `PAY-978` Investigate approach for tokenized card vault (APP-012)
- `PAY-979` Refactor: tokenized card vault (APP-012)
- `OMS-1334` Refactor: idempotent event consumption (APP-009)
- `CHK-1436` Investigate approach for graceful degradation when promotions unavailable (APP-003)

## Architecture changes
- `KN-201` Customer Portal & Self-Service Returns (My Meridian)
- `KN-202` Checkout Orchestration
- `KN-206` Pricing Resolution
- `KN-208` Order Management Saga

## New / updated APIs
- `KN-250` Checkout Service API v1
- `KN-254` Pricing Service API v1
- `KN-256` Order Management (OMS) API v1
- `KN-258` Payments Service API v1

## Business-rule changes
- _(none this sprint)_

## Incidents
- `INC-2026-009` [Sev2] Primary PSP degraded; authorization latency spiked — root cause: third_party

## Hotfixes
- _(none this sprint)_

## Release notes
See [`REL-2026-005`](../release-notes/REL-2026-005.md) — Authorization reliability and Strong Customer Authentication.

## Knowledge updates
- `KN-305` postmortem (Postmortem: Primary PSP degraded; authorization latency spiked)

## Experience updates
- `EXP-055` reinforced — Pricing/promotion changes during a promo window require a write-through APP-008 
- `EXP-090` reinforced — When implementing guest flows in Checkout (APP-003), ensure no code path provisi
- `EXP-142` reinforced — Async webhook tests need deterministic clocks or they flake.
- `EXP-201` reinforced — Regional rounding rules must be validated per-currency before rollout.
- `EXP-202` created — 3DS challenge flows need PSP-sandbox contract tests to prevent auth regressions.
- `EXP-204` reinforced — Relevance changes need offline judgment-set evaluation before shipping.
- `EXP-207` reinforced — Cart writes need optimistic concurrency plus Redis failover drills.
- `EXP-210` reinforced — Catalog ingestion needs backpressure and data-platform outage handling.

## Evaluation improvements
- Mean Worker evaluation score **0.7** (up +0.033 vs previous sprint); mean fused confidence **0.715**.
- Cold-start failures in new task families produce experiences that lift later scores (see [`../../corpus/`](../../corpus/)).

