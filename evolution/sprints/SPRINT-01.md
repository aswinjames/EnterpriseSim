# Sprint 1 — Engineering Evolution (2026-01-05 → 2026-01-16)

> Part of [six months of MCG engineering history](../README.md). Release train **REL-2026-001 — Guest Checkout & Cart Resilience**.

| Metric | Value |
|---|---|
| Stories delivered | 11 (6 features, 3 debt/spikes, 2 bugs) |
| Incidents | 2 |
| Hotfixes | 1 |
| Worker executions (corpus) | 3 |
| Mean evaluation score | 0.68 |
| Mean fused confidence | 0.673 |

## New features
- `CHK-1421` Support guest checkout in the Checkout Service (APP-003)
- `CHK-1403` Split-tender payment support (APP-003)
- `CAT-936` Sub-minute catalog reindex (APP-005)
- `CHK-1405` Graceful degradation when promotions unavailable (APP-003)
- `CHK-1411` Add idempotency keys to order placement (APP-003)
- `CRT-555` Expire abandoned carts (APP-004)

## Technical debt
- `CAT-936` Sub-minute catalog reindex (APP-005)
- `CHK-1426` Refactor: reduce p99 checkout latency (APP-003)
- `INV-1241` Refactor: low-stock event publishing (APP-010)

## Architecture changes
- `KN-202` Checkout Orchestration
- `KN-203` Cart State & Redis Resilience
- `KN-204` Product Catalog & Indexing
- `KN-205` Search Hybrid Ranking

## New / updated APIs
- `KN-250` Checkout Service API v1
- `KN-251` Cart Service API v1
- `KN-252` Product Catalog Service API v1
- `KN-253` Search & Browse Service API v1

## Business-rule changes
- _(none this sprint)_

## Incidents
- `INC-2026-001` [Sev2] Cart Redis primary failover caused elevated errors — root cause: capacity
- `INC-2026-002` [Sev2] Guest checkout created orphaned loyalty accounts — root cause: code_regression → hotfix `PR-0312`

## Hotfixes
- `PR-0312` CHK-1421: guard against loyalty account creation for guests

## Release notes
See [`REL-2026-001`](../release-notes/REL-2026-001.md) — Reduce friction for unauthenticated buyers and harden cart state under load.

## Knowledge updates
- `KN-300` postmortem (Postmortem: Cart Redis primary failover caused elevated errors)
- `KN-301` postmortem (Postmortem: Guest checkout created orphaned loyalty accounts)

## Experience updates
- `EXP-090` created — When implementing guest flows in Checkout (APP-003), ensure no code path provisi
- `EXP-207` created — Cart writes need optimistic concurrency plus Redis failover drills.

## Evaluation improvements
- Mean Worker evaluation score **0.68** (first measured sprint); mean fused confidence **0.673**.
- Cold-start failures in new task families produce experiences that lift later scores (see [`../../corpus/`](../../corpus/)).

