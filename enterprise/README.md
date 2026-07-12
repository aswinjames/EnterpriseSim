# EnterpriseSim Reference Enterprise

> The canonical **Meridian Commerce Group (MCG)** reference enterprise — the coherent,
> evolving corpus that every Enterprise AI Worker builds, tests and benchmarks against.
> Governed by and consistent with [`../CANON.md`](../CANON.md) (`CANON-001`). Nothing here
> contradicts canon; where this corpus is narrower than canon, it is a **focused slice**, not
> a change.

## Scope of the reference enterprise

The full MCG (per `CANON-001` §3) spans 24 applications and 30 teams. The reference
implementation features a coherent **commerce-path slice**:

| Dimension | Count | Notes |
|---|---|---|
| **Focal applications** | 12 | `APP-001, 003, 004, 005, 006, 007, 008, 009, 010, 012, 021, 024` — see [`registry/applications.json`](registry/applications.json). Data matches `CANON-001` §3 exactly (owner, deps, stack, criticality, repo). |
| **Featured teams** | 10 | The product squads owning the focal apps — see [`registry/teams.json`](registry/teams.json). |
| **Repositories** | 25 | 12 focal-app repos + 5 adjacent-app repos + 8 platform/tooling repos — see [`registry/repositories.json`](registry/repositories.json). |
| **Releases** | 10 | Fortnightly trains `REL-2026-001…010`, Jan–May 2026 — see [`registry/releases.json`](registry/releases.json). |

### Adjacent canonical apps

The focal apps depend on, and releases/incidents/stories reference, a set of **adjacent
apps** that are real `CANON-001` §3 entities (not new inventions) and appear here via their
repositories and cross-references, but are *not* counted among the 12 focal application
records: `APP-011` (Warehouse/WMS), `APP-013` (Wallet), `APP-014` (Identity), `APP-015`
(Loyalty), `APP-020` (Data Platform), `APP-023` (Notifications). Likewise, repositories and
incidents may reference **horizontal teams** defined in `CANON-001` §2.2 beyond the featured
10 — e.g. `TEAM-031` (DevEx), `TEAM-032` (SRE), `TEAM-040` (Security), `TEAM-050` (QE),
`TEAM-060` (Data).

## Directory layout

| Path | Contents | Schema |
|---|---|---|
| `registry/` | applications, teams, repositories, releases | `schemas/{application,team,repository,release}.schema.json` |
| `knowledge/` | business rules as `KnowledgeObject`s (`KN-###`) + a knowledge index for arch docs/runbooks/API specs | `../schemas/knowledge_object.schema.json` |
| `architecture/` | enterprise architecture documents (prose) | registered as `KN-###` |
| `api-specs/` | API specifications (OpenAPI/AsyncAPI-style) | registered as `KN-###` |
| `runbooks/` | operational runbooks (prose) | registered as `KN-###` |
| `jira/` | Jira stories dataset | `schemas/jira_story.schema.json` |
| `pull-requests/` | pull-request dataset | `schemas/pull_request.schema.json` |
| `commits/` | commit-metadata dataset | `schemas/commit.schema.json` |
| `tests/` | automated test-case dataset | `schemas/test_case.schema.json` |
| `incidents/` | production incidents dataset | `schemas/incident.schema.json` |
| `postmortems/` | incident postmortems (prose) | registered as `KN-###` |

## Design rules for this corpus

- **Everything references existing IDs.** Stories reference apps/repos/releases; PRs
  reference stories; commits reference PRs; tests reference apps; incidents reference
  releases/apps and are analyzed by postmortems; postmortems produce knowledge and feed the
  learning corpus in [`../corpus/`](../corpus/).
- **Everything builds over time.** A 6-month calendar of **13 two-week sprints** (2026-01-05
  → 2026-06-28) and 10 release trains gives every artifact a place in history.
- **Everything validates.** Structured datasets validate against `enterprise/schemas/` (which
  extend the frozen `../schemas/common.schema.json`); knowledge validates against the frozen
  `KnowledgeObject` schema. Validate with `python3 tools/refgen/validate.py`.
- **No isolated objects, no placeholders.**

## Sprint & release calendar

| Sprint | Window (2026) | Release |
|---|---|---|
| 1 | Jan 05–16 | `REL-2026-001` Guest Checkout & Cart Resilience |
| 2 | Jan 19–30 | `REL-2026-002` Search Relevance & Catalog Freshness |
| 3 | Feb 02–13 | `REL-2026-003` Dynamic Pricing Foundations |
| 4 | Feb 16–27 | `REL-2026-004` Promotions Engine Hardening |
| 5 | Mar 02–13 | `REL-2026-005` Payments Reliability & 3DS |
| 6 | Mar 16–27 | `REL-2026-006` Order Orchestration & Inventory ATP |
| 7 | Mar 30–Apr 10 | `REL-2026-007` Gateway Rate-Limiting & Edge Auth |
| 8 | Apr 13–24 | `REL-2026-008` Customer Portal Self-Service Returns |
| 9 | Apr 27–May 08 | `REL-2026-009` Peak-Readiness & Observability |
| 10 | May 11–22 | `REL-2026-010` Checkout Latency & Promo Cache |
| 11–13 | May 25–Jun 28 | continued evolution (see [`../corpus/`](../corpus/) and Part 3 evolution) |
