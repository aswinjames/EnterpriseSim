# Community & Governance Charter — The Open Enterprise AI Foundation

> **Status:** Governance charter (Draft for foundation review). **Scope:** Part 10 of the
> ecosystem blueprint — the community, governance, contribution, release, certification and
> sustainability model for the **Open Enterprise AI Foundation (OEAF)** and its five artifacts.
> **Prime directive (inherited):** *evolution over replacement.* This charter **elevates the
> RFC + ADR process EnterpriseSim V1 already runs** (`docs/rfcs/`, `docs/adr/`) to a
> foundation-wide instrument; it does not replace it. **Method:** copy proven patterns — CNCF
> project lifecycle and neutral hosting, OpenTelemetry SIGs, Apache meritocracy and the
> "Apache Way," MLPerf/SWE-bench benchmark discipline — rather than invent governance.
> **Companion documents:** `ENTERPRISE_AI_ECOSYSTEM.md` (Parts 1–3, 5, 9, 11),
> `ENTERPRISESIM_V2_MIGRATION.md`, `ENTERPRISE_WORKER_SDK_CHARTER.md`,
> `REFERENCE_RUNTIME_CHARTER.md`, `OPEN_STANDARDS_ROADMAP.md`. **Builds on:**
> `docs/standards/contribution-guidelines.md`, `docs/standards/review-process.md`.

This charter expands Part 9 of `ENTERPRISE_AI_ECOSYSTEM.md` into a full governance instrument
and is kept strictly consistent with it. Where Part 9 states a principle, this document states
the mechanism. Nothing here contradicts the locked facts: a neutral foundation, five artifacts,
Apache-2.0 + DCO, synthetic-only content (`ADR-0049`), backward-compatibility first-class, and
benchmark neutrality as an existential requirement.

---

## Part 10 — Community & Governance

### 10.0 Guiding principles

1. **Neutrality is existential, not aspirational.** No single vendor controls the specification
   (OEAS) or the benchmark (EnterpriseSim). This is the non-negotiable condition for adoption;
   every rule below is subordinate to it (`ENTERPRISE_AI_ECOSYSTEM.md` §11, risk #1).
2. **Meritocracy of contribution (the Apache Way).** Influence is earned through sustained,
   reviewed contribution — not employer, title, or funding tier. Roles are individuals, never
   companies.
3. **Governed evolution.** Significant and contract-affecting change flows through the
   established **RFC → ADR** discipline; decisions are recorded, immutable once accepted, and
   superseded only by a new record (`ADR-0001`, `ADR-0050`).
4. **Open by default.** Discussions, roadmaps, votes, meeting notes, benchmark methodology and
   conformance results are public. Private handling is reserved for security embargoes and Code
   of Conduct matters.
5. **Backward compatibility is a first-class deliverable**, not a courtesy (`RFC-0021`,
   `ADR-0032`, `ADR-0033`).

### 10.1 Foundation structure

**Neutral host.** OEAF is chartered as a project under an established neutral non-profit
(target: Linux Foundation / CNCF-style, or the Apache Software Foundation). The host holds
assets in trust for the community; it does not direct the technical work. This mirrors how
Kubernetes (CNCF) and OpenTelemetry (CNCF) achieved credibility that no vendor-owned project
reached — the OpenTelemetry-vs-proprietary-APM lesson (`ENTERPRISE_AI_ECOSYSTEM.md` §11).

**Why neutrality is existential.** The ecosystem's value is that OEAS is *the* contract and
EnterpriseSim is *the* ruler. If either could be steered to advantage one implementer,
procurement teams and competitors would rationally refuse to depend on it, and the market
fragments into competing "standards" (Part 11's governance-capture failure mode). Neutrality is
therefore encoded structurally — in TSC composition caps (§10.2), benchmark independence
(§10.9), and trademark control by the foundation (below) — not left to good intentions.

**IP, license and trademark.**
- **License: Apache-2.0** for all code, schemas, datasets and documentation across all five
  artifacts (`ADR-0049`, `ADR-0026`). New source carries the SPDX identifier; new dependencies
  must be Apache-2.0-compatible (MIT/BSD/ISC/Apache-2.0); copyleft requires an ADR
  (contribution-guidelines §6).
- **Provenance: DCO, not CLA (recommended and retained).** The foundation uses the **Developer
  Certificate of Origin** — a per-commit `Signed-off-by` sign-off — and **does not** require a
  Contributor License Agreement. Rationale: Apache-2.0 already grants the patent and copyright
  license the foundation needs; a CLA adds copyright-assignment friction that suppresses
  drive-by and academic contribution without buying neutrality. DCO keeps the barrier low while
  asserting provenance, and is enforced as a merge gate (contribution-guidelines §5). This
  preserves V1's stance unchanged.
- **Trademarks held by the foundation.** The names/marks **"OEAS-Conformant"** and
  **"EnterpriseSim-Benchmarked,"** plus the project word-marks and logos, are owned by the
  neutral host and licensed only per the certification rules in §10.8. A vendor may state it is
  conformant/benchmarked only under those rules; misuse is a trademark matter, which is precisely
  the enforcement lever that keeps the marks meaningful (the CNCF-conformance pattern).
- **Code of Conduct.** The **Contributor Covenant** governs all participation, foundation-wide
  (`CODE_OF_CONDUCT.md`), with a named CoC committee and a confidential reporting path.

### 10.2 Technical Steering Committee (TSC)

**Mandate.** The TSC is the top technical body. It owns cross-project concerns: the stable-API
contracts (API-1…API-4, `ENTERPRISE_AI_ECOSYSTEM.md` §5), project lifecycle decisions
(§10.4), Working-Group chartering, coordinated releases, and final arbitration of appeals. It
does **not** micromanage day-to-day project work — that belongs to project Maintainers (§10.3).

**Composition (neutrality-capped).**
- 7–9 voting seats, all **individuals**, elected for their technical judgment.
- **No more than two seats (≤ ~25%) may be affiliated with any single employer.** If an
  election or a job change would breach the cap, the most-recently-seated affected member steps
  to non-voting until the cap is restored. This single rule is the structural core of vendor
  neutrality.
- Standing non-voting participants: WG chairs, the security lead, and a foundation liaison.
- Seats are filled by **maintainer vote** (the electorate is the union of all project
  maintainers, §10.3), staggered so roughly half turn over each year.

**Terms.** Two-year terms, staggered; a hard limit of two consecutive terms, then a one-cycle
cooldown, to force renewal and prevent entrenchment. A TSC member who ceases active
contribution for two quarters is moved to emeritus (§10.3).

**Decision rules.** Default is **lazy consensus** (a proposal with no sustained objection after
a stated review window carries). When a vote is required: simple majority of voting seats for
routine matters; **two-thirds supermajority** for charter changes, lifecycle promotion/archival,
adopting or retiring a stable-API major, and anything touching benchmark-neutrality safeguards.
Quorum is two-thirds of voting seats.

**Tie-breaks & escalation.** Ties fail (the status quo holds) — a deliberate bias toward
stability. A failed vote on a live issue returns to the relevant WG for a revised proposal.
There is **no individual casting-vote or "BDFL"**; concentrating a tie-break in one person is
incompatible with neutrality. Conflicts of interest must be declared and the member recuses
from the vote.

### 10.3 Maintainers & Reviewers

Roles are **per-project** (OEAS, EnterpriseSim, EWSDK, Reference Runtime, Conformance) and are
individuals. They extend, not replace, V1's reviewer roles (review-process §1).

| Role | Rights | Duties |
|---|---|---|
| **Contributor** | Open issues, RFCs, PRs | Small, focused, tested, DCO-signed changes (contribution-guidelines §8). |
| **Reviewer** | Binding review on assigned paths (CODEOWNERS) | First-response SLA (review-process §6); correctness and contract fit. |
| **Maintainer** | **Merge rights** on the project; release cutting; vote in TSC elections | Uphold gates, mentor, triage, represent the project. |
| **Project lead** (1–2/project) | Convene maintainers; break process deadlocks within the project | Roadmap stewardship; escalate cross-project issues to TSC. |
| **Emeritus** | Honorary; no merge rights | Advisory; may be fast-tracked back on renewed activity. |

**Merge rights and the two-maintainer rule.** Every change lands via reviewed PR into `main`;
no direct pushes (review-process §3). Approval thresholds follow the V1 risk-tier table
(review-process §2) and are **raised foundation-wide for the two neutrality-critical artifacts**:
any change to **OEAS (the spec)** or to the **benchmark task sets / scoring** requires **two
maintainer approvals from two distinct affiliations**, at least one being the relevant
specialist (Standards WG for spec, Benchmark WG for benchmark). Same-employer double-approval
does not satisfy the rule for these artifacts — this is how the two-maintainer rule also serves
neutrality, not just quality.

**Becoming a maintainer (earned, transparent).** The path is meritocratic and CNCF-style:
sustained, high-quality contribution and review over time (typical guidance: ~6 months of
consistent, non-trivial reviewed work), demonstrated judgment on the project's contracts, and
**nomination by an existing maintainer** confirmed by **lazy consensus of the current
maintainers** (a vote only if objected). Criteria and current rosters live in each project's
`MAINTAINERS.md`; additions are themselves PRs, so the audit trail is public. No seat is granted
by employment or sponsorship.

**Emeritus & inactivity.** A maintainer inactive for two quarters, or who requests it, moves to
**emeritus** — preserving recognition and history while keeping the active roster (and thus the
electorate and neutrality caps) honest. Return is fast-tracked on renewed activity.

### 10.4 Project lifecycle (graduation levels)

Adopt the **CNCF maturity ladder** so the ecosystem can incubate new artifacts (e.g. capability
packs, additional connectors) without diluting the mature core.

- **Sandbox** — early, experimental; foundation infra and CoC apply; no stability promise.
- **Incubating** — demonstrated adoption, healthy contributor diversity, documented governance.
- **Graduated** — production-grade, multi-affiliation maintainers, security posture, sustained
  release cadence.

At charter adoption, the five artifacts enter at: **EnterpriseSim, OEAS, EWSDK — Graduated**
(they are V1-validated and internally consistent); **Reference Runtime — Incubating** (new,
fills the V1 executor gap, `ENTERPRISE_AI_ECOSYSTEM.md` §2 Project C);
**Conformance & Certification — Incubating** (stands up alongside the first certified releases).
Promotion/archival is a **two-thirds TSC** decision (§10.2).

### 10.5 Working Groups (SIGs)

Modeled on **OpenTelemetry SIGs**: standing, chartered, publicly-scheduled groups that do the
detailed design and shepherd RFCs to the TSC. Each WG has 1–2 chairs (max one per employer),
public minutes, and an explicitly bounded charter. The six WGs from Part 9:

1. **Specification / Standards WG** — owns OEAS evolution and external-standards alignment
   (JSON Schema 2020-12, CloudEvents, OpenTelemetry, OpenAPI 3.1, MCP). Guards API-3, the
   ≥10-year contract. Shepherds all spec RFCs; enforces expand-contract (`ADR-0033`, `RFC-0021`).
2. **Benchmark & Evaluation WG** — owns EnterpriseSim tasks, scoring, seasons, and leaderboard
   methodology (`RFC-0025`, `RFC-0026`, `ADR-0048`). Structurally independent of vendors (§10.9);
   custodian of anti-gaming and contamination controls.
3. **SDK & DevEx WG** — owns the Enterprise Worker SDK, WorkerProfiles, capability packs, CLI,
   docs and the contributor experience (`ENTERPRISE_WORKER_SDK_CHARTER.md`, `RFC-0027`).
4. **Memory & Learning WG** — owns the Memory projection (7 types) and learning/reflection
   contracts (`ADR-0034`–`ADR-0036`, `RFC-0016`–`RFC-0018`); coordinates research protocols on
   the environment.
5. **Governance & Security WG** — owns the security process (embargo, disclosure, advisories),
   the synthetic-only + secrets gates (`ADR-0049`), policy/guardrail contracts (`RFC-0030`),
   CoC coordination, and this charter's upkeep.
6. **Telemetry / OTel-alignment WG** — owns the cognition-span semantic conventions and the
   signals bus (`RFC-0028`, `ADR-0038`); drives upstream adoption of cognition spans as an
   OpenTelemetry semantic convention (the 2035 standards goal, §Part 10 vision).

A WG may be chartered, merged or sunset by the TSC. New WGs start with a one-page charter stating
scope, non-goals, and the contracts they steward.

### 10.6 Contribution process

The V1 pipeline (contribution-guidelines §8, review-process) is **elevated verbatim** to the
foundation, using the **existing RFC and ADR templates and numbering** (`docs/rfcs/RFC-000N.md`,
`docs/adr/ADR-000N.md`; zero-padded, immutable, never reused per `CANON-001` §6). The flow:

```
issue (ES-###)  ─▶  RFC (significant / spec / benchmark change)  ─▶  ADR (the decision, if any)
   ─▶  PR (template, DCO -s, <400 LOC, docs+changelog in-PR)
   ─▶  CI gates green  ─▶  required approvals (risk tier)  ─▶  squash-merge to main
```

**When each instrument is required** (extends contribution-guidelines §3 foundation-wide):

| Change | Instrument |
|---|---|
| Docs/typo/test/tooling | PR only |
| New optional field / interface / extension point | **RFC** → PR |
| Any OEAS (spec) change, or any benchmark task/scoring change | **RFC**, and **ADR if it sets a durable decision** → PR, **two maintainers / two affiliations** |
| Breaking contract change | **RFC + ADR** → PR, deprecation cycle (§10.7) |
| Cross-project / stable-API (API-1…4) change | **RFC + ADR**, **TSC ratification** |

- **RFCs** are the reviewable design document; **ADRs** (Nygard *Context / Decision /
  Consequences*, authored by the owning Architecture body) record the durable decision and are
  immutable once accepted. `ADR-0051` is the worked precedent: a governed, expand-only schema
  evolution recorded as an ADR — exactly the mechanism this charter scales.
- **Hierarchy of authority is preserved:** `CANON-001` > ADR > RFC (`ADR-0050`).
- **Synthetic-only rule** (`ADR-0049`) and secret-scanning remain hard merge gates everywhere.

### 10.7 Release process

**Per-project SemVer** (`ADR-0032`). Projects release independently — the whole point of the
polyrepo split is that a glacial spec and a fast SDK need not share a version number
(`ENTERPRISE_AI_ECOSYSTEM.md` §1.2).

- **Time-based minor releases.** Each project ships minors on a predictable cadence (e.g.
  quarterly). Minors are additive and never break readers (expand-contract, `ADR-0033`).
- **LTS majors.** Each major has a defined support window with security-only maintenance after
  the next major ships. **Breaking changes require a new major, a compatibility adapter shipped
  alongside for ≥ 2 minor versions, and a recorded deprecation** (`ENTERPRISE_AI_ECOSYSTEM.md`
  §5 compatibility rules; migration doc). Zero hard deletions is the standing promise.
- **Benchmark "seasons."** EnterpriseSim releases evaluation content as dated **seasons**, each
  with a **frozen, held-out task set** (the SWE-bench/MLPerf split discipline). Held-out tasks
  are not published until the season closes; scores are only comparable within a season. New
  seasons add fresh mission families and retire contaminated ones (§10.9). This is the primary
  defense against overfitting/Goodhart (`ENTERPRISE_AI_ECOSYSTEM.md` §11).
- **Coordinated ecosystem releases.** Once per major cycle the TSC cuts a **coordinated
  release**: a named, tested tuple of (OEAS, EnterpriseSim, EWSDK, Reference Runtime,
  Conformance) versions verified to interoperate — the reference point vendors and universities
  pin to. Individual projects still release on their own cadence between coordinated points.

### 10.8 Certification & compliance

Two distinct, independently-earned marks — this is what turns the ecosystem from a library into
a **market** (the CNCF-conformance / MLPerf pattern):

- **"OEAS-Conformant"** — attests that a runtime/product correctly implements the OEAS
  object/event contract (API-3) and the relevant API surfaces. **Self-certified against the
  open Conformance suite**, then submitted with a reproducible test report; the Conformance
  project (with Governance & Security WG) verifies before the mark and listing are granted.
  Conformance is versioned to an OEAS major.
- **"EnterpriseSim-Benchmarked"** — a public, MLPerf-style **leaderboard** of scores on a named
  season. **Run by the Benchmark & Evaluation WG** (vendor-independent, §10.9), not by
  submitters unilaterally.

**Reproducibility, contamination & anti-gaming rules** (enforced as conditions of the mark;
`ADR-0048`, `ADR-0018` versioned rubrics):
- Every leaderboard entry must ship a **reproducibility bundle**: pinned versions, seeds,
  configuration, and a deterministic replay trace (`RFC-0024`, `ADR-0037`) sufficient for an
  independent third party to reproduce the score.
- **Held-out task sets are never trained/tuned on.** A submitter attests (DCO-style) that the
  held-out season set was not used for development; violations forfeit the mark and delist.
- **Contamination controls & adversarial audits.** The WG may audit entries, re-run on a fresh
  held-out slice, and **retract** scores. Suspected gaming (memorization, prompt-scraping of
  held-out content, outcome-oracle exploitation) is grounds for retraction and temporary
  submission ban.
- **Outcome-verified scoring.** Scores rest on the executable outcome model (verified, not
  asserted — `ENTERPRISE_AI_ECOSYSTEM.md` §2 Project A), closing the Goodhart gap.

The foundation owns both marks (§10.1); the right to display them is a trademark license
contingent on continued compliance and is revocable.

### 10.9 Benchmark governance

Because benchmark neutrality is existential, EnterpriseSim's evaluation content is governed with
extra independence:

- **Vendor independence.** The Benchmark & Evaluation WG's chairs and the maintainers with merge
  rights over task sets and scoring are subject to the same per-employer caps as the TSC (§10.2);
  no single affiliation can carry a task-set or scoring change alone (§10.3 two-affiliation rule).
- **Task submission & curation.** Anyone may **submit** candidate tasks via issue → RFC, with a
  synthetic-only, CANON-consistent world (`ADR-0049`, contribution-guidelines §1). The WG
  curates for difficulty, coverage, outcome-verifiability and non-duplication; accepted tasks
  enter a **staging pool**, then are sealed into a future season's held-out set.
- **Deprecation of contaminated tasks.** When a task is found leaked, memorized, or otherwise
  contaminated, the WG **deprecates** it: it is removed from active held-out sets, publicly
  flagged, and — following the ecosystem norm — retired with a pointer rather than silently
  deleted, so historical scores remain interpretable. Rotating seasons make deprecation routine,
  not disruptive.
- **Methodology is public and RFC-governed.** Scoring formulae, rubric versions and season
  composition rules are published (`RFC-0025`, `RFC-0026`); changes follow §10.6.

### 10.10 Community roadmap

- **Public and RFC-driven.** The roadmap is a living, public artifact assembled from accepted and
  in-flight RFCs per project, reviewed at TSC and WG cadence. Priorities are set in the open; no
  private backlog steers the standard.
- **Stable-API promise dashboard.** A public dashboard tracks the four stable contracts (API-1
  Environment/Mission, API-2 Worker Contract, API-3 OEAS object/event, API-4 App/Integration),
  each with its **stability target** (≥3y / ≥5y / ≥10y / ≥3y), current SemVer, deprecation
  windows, and compatibility-adapter status (`ENTERPRISE_AI_ECOSYSTEM.md` §5). The dashboard is
  how the community *sees* the backward-compatibility promise being kept — turning trust into an
  observable, not a slogan.
- **Coordinated-release calendar** publishes the next ecosystem tuple and benchmark season dates.

### 10.11 Long-term sustainability

**Funding model (neutral by construction).** The foundation is funded by **tiered corporate
membership + individual/community donations**, administered by the neutral host. Critically,
**funding buys no technical control**: members fund shared infrastructure (CI, leaderboard
hosting, security audits, events, a small number of neutral staff/contractors) but **do not**
gain TSC seats, maintainer status, or benchmark influence. Members may seat a non-technical
**Governing/Advisory Board** for budget and marketing — explicitly firewalled from the TSC. This
is the CNCF separation of "money" from "merit."

**Vendor-neutrality safeguards (summary of the structural locks).**
- Per-employer caps on the TSC (§10.2), WG chairs (§10.5) and benchmark maintainers (§10.9).
- Two-maintainer / two-affiliation rule on spec and benchmark changes (§10.3, §10.6).
- Benchmark run by a vendor-independent WG with public methodology (§10.8–10.9).
- Trademarks and marks held by the foundation, licensed on compliance only (§10.1, §10.8).
- Funding firewalled from technical governance (this section).
Any proposal that weakens one of these is a charter change requiring a two-thirds TSC vote.

**Maintainer burnout mitigation.**
- **No unowned surface, no single point of failure.** Every path has ≥2 owners; DevEx-style
  reassignment prevents a PR stalling on one person (review-process §6, `CANON-001` §2.3).
- **Enforced review SLAs and small PRs** (<400 LOC) keep review humane (review-process §5–6).
- **Rotation and sabbatical are normalized** via the emeritus path (§10.3) — stepping back is
  honored, not penalized.
- **Fund the toil.** Membership money pays contractors for release engineering, security triage
  and CI upkeep so volunteers spend their time on design, not on-call.

**Succession.**
- **Staggered, term-limited TSC** guarantees continuous, gradual turnover (§10.2).
- **Documented roles and public rosters** (`MAINTAINERS.md`, WG charters) mean any role can be
  refilled from the recorded electorate without institutional memory loss.
- **Immutable decision record.** The RFC/ADR corpus is the project's durable memory; a new
  maintainer can reconstruct *why* any contract is shaped as it is (`ADR-0001`) — succession
  without amnesia.
- **Foundation continuity clause.** Should activity lapse, the neutral host stewards the
  artifacts and marks in trust and may re-seat a TSC from active maintainers, so the standard
  and benchmark outlive any cohort.

### 10.12 Amendment

This charter is amended by **RFC → two-thirds TSC vote**, with the change recorded as an ADR
under the Governance & Security WG. It is subordinate to `CANON-001` and to the locked facts of
`ENTERPRISE_AI_ECOSYSTEM.md`; any conflict is resolved in favor of neutrality (§10.0).

---

*Consistent with `ENTERPRISE_AI_ECOSYSTEM.md` Part 9, and with the V1 engineering process in
`docs/standards/`. Consolidation only — this charter introduces no new architecture and modifies
no frozen V1 artifact.*
