# Sprint 8 — Engineering Evolution (2026-04-13 → 2026-04-24)

> Part of [six months of MCG engineering history](../README.md). Release train **REL-2026-008 — Customer Portal Self-Service Returns**.

| Metric | Value |
|---|---|
| Stories delivered | 7 (3 features, 2 debt/spikes, 1 bugs) |
| Incidents | 1 |
| Hotfixes | 0 |
| Worker executions (corpus) | 11 |
| Mean evaluation score | 0.763  (Δ +0.02) |
| Mean fused confidence | 0.776 |

## New features
- `POR-643` Download invoice as pdf (APP-021)
- `OMS-1338` Backorder handling (APP-009)
- `PRC-1161` Markdown scheduling (APP-007)

## Technical debt
- `POR-625` Refactor: address book management (APP-021)
- `STF-828` Refactor: localize currency and units per region (APP-001)

## Architecture changes
- `KN-200` Storefront Rendering & BFF
- `KN-201` Customer Portal & Self-Service Returns (My Meridian)
- `KN-206` Pricing Resolution
- `KN-208` Order Management Saga

## New / updated APIs
- `KN-254` Pricing Service API v1
- `KN-256` Order Management (OMS) API v1
- `KN-259` Storefront BFF API v1
- `KN-260` Customer Portal (My Meridian) API v1

## Business-rule changes
- _(none this sprint)_

## Incidents
- `INC-2026-015` [Sev3] Self-service returns showed incorrect eligibility — root cause: code_regression

## Hotfixes
- _(none this sprint)_

## Release notes
See [`REL-2026-008`](../release-notes/REL-2026-008.md) — Let customers self-serve returns and track order state.

## Knowledge updates
- `KN-310` postmortem (Postmortem: Self-service returns showed incorrect eligibility)

## Experience updates
- `EXP-055` reinforced — Pricing/promotion changes during a promo window require a write-through APP-008 
- `EXP-090` reinforced — When implementing guest flows in Checkout (APP-003), ensure no code path provisi
- `EXP-142` reinforced — Async webhook tests need deterministic clocks or they flake.
- `EXP-201` reinforced — Regional rounding rules must be validated per-currency before rollout.
- `EXP-202` reinforced — 3DS challenge flows need PSP-sandbox contract tests to prevent auth regressions.
- `EXP-203` reinforced — Multi-warehouse ATP requires reservation locks to prevent oversell.
- `EXP-204` reinforced — Relevance changes need offline judgment-set evaluation before shipping.
- `EXP-205` reinforced — Rate-limit thresholds must be load-tested against realistic traffic shapes.
- `EXP-206` reinforced — Saga compensations must be idempotent and tested for partial failure.
- `EXP-208` created — Returns-eligibility rules need a golden-case suite across order states.
- `EXP-210` reinforced — Catalog ingestion needs backpressure and data-platform outage handling.

## Evaluation improvements
- Mean Worker evaluation score **0.763** (up +0.020 vs previous sprint); mean fused confidence **0.776**.
- Cold-start failures in new task families produce experiences that lift later scores (see [`../../corpus/`](../../corpus/)).

