# Review Process

> How code review works on EnterpriseSim. Instantiates `CANON-001` **§4.2 (Pull Requests)**
> and the approval workflow in **§7.5**, and depends on the ownership model in
> [`repository-conventions.md`](repository-conventions.md) (CODEOWNERS) and
> [`contribution-guidelines.md`](contribution-guidelines.md).

Review is where a public benchmark earns trust: it is how we keep the contracts precise, the
world CANON-consistent, and the decision graph honest. Every change into `main` is reviewed;
there are no exceptions (CANON §4.2).

## 1. Reviewer roles

| Role | Who (CANON §2.2) | Responsibility |
|---|---|---|
| **Author** | Contributor | Small, focused, tested, signed-off PR; responds to feedback. |
| **Code owner** | The CODEOWNERS team for the touched paths | Correctness, fit with the module's contract; approval is required to merge. |
| **Architecture reviewer** | Architecture Office (`TEAM-090`) | Required for `schemas/`, `sdk/objects.py`, `docs/architecture/`, ADRs/RFCs, and any invariant-touching change. |
| **Security reviewer** | Security Engineering (`TEAM-040`) | Required for changes touching sensitivity handling, secrets surfaces, dependencies, or `sensitivity ∈ {pci,pii}` fields. |
| **Maintainer / merger** | DevEx (`TEAM-031`) + owning team | Confirms gates + approvals, performs the squash-merge, cuts releases. |

CODEOWNERS (repository-conventions §4) routes reviewers automatically; the matching owner's
approval is enforced by branch protection.

## 2. Required approvals by risk tier (CANON §7.5)

Mapped from CANON's approval workflow to this repo's change classes:

| Change class | Min approvals | Additional required gates |
|---|---|---|
| Docs / tooling / test-only (Tier 2/3 analog) | **1** (code owner) | CI green |
| SDK interface change (new/changed ABC, Protocol, extension point) | **2** incl. code owner | CI green, contract-parity test |
| **Schema / `sdk/objects.py` shape change** (Tier 0 analog) | **2** incl. **Architecture Office** | RFC merged; schema-conformance + parity green |
| **Security-relevant** (sensitivity, deps, secrets surface) | **2** incl. **Security Engineering** | SAST/SCA/secret scan; threat note if new surface |
| Breaking / invariant change | **2** incl. Architecture Office | **RFC + ADR** merged; deprecation cycle recorded |
| Hotfix (release-strategy §6) | **1–2** by class above | Incident `INC-####` linked; security + validation gates |
| CANON change | Architecture Office (`TEAM-090`) only | Canon changelog entry |

"2 approvals" always means **two distinct people**, at least one a code owner for the touched
paths, and the required specialist (Architecture Office / Security) where the table demands it
(CANON §7.5).

## 3. What blocks merge

A PR **cannot merge** while any of these hold:

- Any **required CI gate is red**: ruff, `black --check`, mypy (strict), unit + contract +
  schema-conformance tests, or a high/critical SAST/SCA/secret finding (CANON §4.6).
- **Required approvals not met** for the change's risk tier (§2), or a **CODEOWNERS** owner has
  not approved.
- An **unresolved review thread** or a "request changes".
- A **contract change without its RFC** (or an invariant change without its ADR).
- **Schema changed but `sdk/objects.py` / tests not updated** (parity test fails) — or the
  reverse (repository-conventions §5).
- **Docs / docstrings / changelog not updated** to match the change
  (documentation-standards §1, §7).
- **Non-synthetic or non-CANON-consistent content**, or any secret, present
  (contribution-guidelines §1).
- **Missing DCO sign-off** on any commit (contribution-guidelines §5).
- Direct push to `main`, or a branch older than 3 days without rebase (CANON §4.1).

## 4. Reviewer checklist

A reviewer confirms, in roughly this order:

**Contract correctness**
- [ ] `sdk/` stays **interfaces-only** — every method body is `...`; no logic, I/O, or state
      (`ADR-0029`, coding-standards §1).
- [ ] Types are precise: PEP 604 unions, `Mapping`/`Sequence` in signatures, shared aliases
      (`CanonicalId`, `Timestamp`, `Confidence`); mypy strict clean (python-standards §3).
- [ ] `ABC` vs `Protocol` vs `@dataclass(frozen=True)` used per convention (python-standards §4).
- [ ] Object Protocols still **mirror their JSON Schema**; parity test green (testing §3).

**Canon & integrity**
- [ ] Consistent with `CANON-001` §4/§5/§6/§8 and the frozen `ARCH-*`; no contradiction.
- [ ] Canonical **IDs used correctly** and never reused (`ADR-0022`); cross-references resolve
      (`ADR-0023`).
- [ ] Naming: kebab-case docs, snake_case Python, `ADR-0000`/`RFC-0000` 4-digit files
      (repository-conventions §2).

**Process & safety**
- [ ] Right process for the change (RFC/ADR where required); linked `ES-###` issue.
- [ ] Docstrings cite the governing ADR/RFC and match signatures (documentation-standards §6).
- [ ] Changelog updated; breaking changes state migration + compatibility window (versioning).
- [ ] Tests present and deterministic (testing §5); coverage floor held.
- [ ] Synthetic-only, no secrets, DCO signed off.

## 5. Review etiquette & quality

- Review the **contract and its consequences for implementers**, not personal style — style is
  black/ruff's job (python-standards §5). Never nit what a formatter owns.
- Prefer **suggested edits** and questions over vague objections; explain the *why*, cite the
  ADR/RFC/CANON section.
- Distinguish **blocking** ("request changes", with a reason from §3) from **non-blocking**
  ("nit:", "consider:"). Non-blocking comments never hold a merge.
- Authors keep PRs **small (< 400 LOC)** so review is fast and thorough (CANON §4.2).
- Assume good faith; the Code of Conduct governs all review interaction
  (contribution-guidelines §7).

## 6. Review SLAs

- **First response within 2 business days** of review request; hotfixes (`INC-####`) are
  same-day, expedited (CANON §7.3).
- Re-reviews after the author pushes changes: within **1 business day**.
- If a code owner is unresponsive past SLA, DevEx (`TEAM-031`) reassigns to a backup owner from
  the same team so no PR stalls on a single person (CANON §2.3 "no unowned services").
- Blocking a merge past SLA without a stated reason is itself escalated to the owning EM.
