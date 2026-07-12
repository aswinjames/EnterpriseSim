# EnterpriseSim — Six Months of Engineering Evolution

> A synthesized, fully-referenced history of Meridian Commerce Group engineering across
> **13 two-week sprints** (2026-01-05 → 2026-06-28) and **10 release trains**. Every line
> cites a real artifact from the reference enterprise ([`../enterprise/`](../enterprise/)) and
> learning corpus ([`../corpus/`](../corpus/)) — this is a *view over* the corpus, not new
> disconnected data.

## What's here

| Path | Contents |
|---|---|
| [`sprints/SPRINT-01.md … SPRINT-13.md`](sprints/) | Per-sprint evolution digest |
| [`release-notes/REL-2026-001.md … 010.md`](release-notes/) | Release notes per train |
| [`timeline.json`](timeline.json) | Machine-readable per-sprint aggregation |

## Each sprint digest covers

Per the evolution brief, every sprint records: **new features**, **technical debt**,
**architecture changes** (`AD-####`/`KN-2##`), **new/updated APIs** (`KN-25#`),
**business-rule changes** (`KN-045/052/063/1##`), **incidents** (`INC-2026-###`),
**hotfixes** (`PR-####`), **release notes**, **knowledge updates** (postmortems `KN-3##`),
**experience updates** (`EXP-###` created/reinforced from [`../corpus/`](../corpus/)), and
**evaluation improvements** (mean Worker evaluation score + fused confidence, with the
sprint-over-sprint delta).

## The enterprise evolves — and improves

The history is not flat. Reading `timeline.json`:

- **Early sprints** stand up new capabilities and hit their failure classes: cold-start
  Worker executions in new task families **fail**, and incidents (e.g. the guest-checkout
  orphaned-loyalty `INC-2026-002`, the promo-cache trio `INC-2026-007/011/018`) drive
  postmortems and **new experiences**.
- **Later sprints** apply that accumulated knowledge and experience: Worker executions
  **retrieve prior lessons**, confidence rises, and the **mean evaluation score climbs from
  ~0.68 (Sprint 1) to ~0.95 (Sprint 13)**. Technical-debt paydown, architecture hardening
  (promo-cache write-through, checkout latency, peak-readiness) and evaluation gains compound.

This is CANON-001 §9's continuous-improvement flywheel made visible over calendar time:
Knowledge → Context → Planning → Execution → Evaluation → Reflection → Experience →
Continuous Improvement, sprint after sprint.

## Reproduce

```bash
python3 tools/refgen/generate_evolution.py   # derives everything from the committed artifacts
```

The generator reads only already-validated artifacts, so the history stays consistent with
the enterprise and corpus by construction; a referential check confirms every cited ID
resolves.
