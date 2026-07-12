# Contribution Guidelines

> How to contribute to EnterpriseSim. EnterpriseSim is **Apache-2.0** open source
> (`ADR-0049`). These guidelines operationalize `CANON-001` **§4.2 (Pull Requests)** and the
> ADR/RFC discipline (`ADR-0001`) for external and internal contributors alike.

Welcome. EnterpriseSim is a public benchmark for Enterprise AI Workers built around a
fictional company, **Meridian Commerce Group (MCG)**. Contributions must keep that world
coherent and its contracts precise. Start by reading [`../../CANON.md`](../../CANON.md)
(`CANON-001`) and the [standards index](README.md).

## 1. The synthetic-only rule (non-negotiable)

**Everything in this repository is original, synthetic, and public.**

- All content — schemas, examples, fixtures, docs, benchmark tasks — describes **fictional MCG**
  and must stay **consistent with CANON** (apps `APP-###`, teams `TEAM-###`, IDs per §6). Any
  resemblance to a real company is coincidental (CANON front matter).
- **Never** copy real company handbooks, proprietary standards, internal docs, or real
  customer/company data into the repo. Public open-source practice is *inspiration only*,
  never text to paste.
- No secrets, credentials, tokens, or real personal data — ever (CANON §4.6). Secret scanning
  is a merge gate.
- A PR that introduces non-synthetic or non-CANON-consistent content is closed on sight.

## 2. Before you start

- **Search first** — check open issues, ADRs (`docs/adr/`) and RFCs (`docs/rfcs/`) so you are
  not re-litigating a settled decision (`ADR-0001`).
- **Open an issue** describing the problem or proposal. Use the templates: bug, enhancement,
  or schema/contract change. Link the CANON section, `ARCH-`, `ADR-` or `RFC-` involved.
- Issues are tracked with an `ES-###` project key (the repo's Jira-style key, CANON §5 Jira
  key convention); reference it in branches and commits.

## 3. When you need an RFC or ADR

Not every change is a plain PR. Match the change to the process (see
[`documentation-standards.md`](documentation-standards.md) §3–4):

| Change | Process |
|---|---|
| Docs fix, typo, test, tooling, clarification | **PR** only |
| New optional schema field / new interface / extension point | **RFC** first, then PR |
| Breaking contract change (remove/rename/retype, make required) | **RFC + ADR**, then PR (with deprecation cycle) |
| Anything that alters an ECL invariant (statelessness, immutability, ID meaning) | **RFC + ADR**; canon supremacy applies (`ADR-0050`) |
| A change to CANON itself | Architecture Office (`TEAM-090`) only; versioned in the canon changelog |

- **RFCs** are authored as `docs/rfcs/RFC-000N.md` and discussed before code lands; contract
  changes always carry one (`schemas/README.md` migration step 5).
- **ADRs** are authored and owned by the **Architecture Office** (`TEAM-090`); an external
  contributor proposes the decision in the RFC and the Architecture Office records the ADR.
- `docs/architecture/` (ARCH-*) and `CANON.md` are **frozen to outside edits** — propose
  changes via RFC; they are applied only with the accompanying ADR by their owners.

## 4. Pull request requirements (CANON §4.2)

Every change lands via PR into `main`. Your PR MUST:

- **Link its issue** (`ES-###`) and, for contract changes, the `RFC-####`/`ADR-####`.
- **Pass all required CI gates**: ruff, black `--check`, mypy strict, unit + contract +
  schema-conformance tests, and the security scans (see [`testing-standards.md`](testing-standards.md),
  [`release-strategy.md`](release-strategy.md)).
- **Receive the required approvals** (see [`review-process.md`](review-process.md)): **≥1**
  normally, **≥2** for schema/contract, security, or CANON-adjacent changes.
- Fill in the **PR template**: summary, linked issue, what changed and why, testing evidence,
  risk tier, and a rollback note (CANON §4.2 / §7.4).
- Keep the diff **focused and < 400 lines** where practical; split unrelated changes.
- Update **docs, docstrings and the changelog in the same PR** — no "docs later"
  (documentation-standards §1, §7).
- Change **schema + `sdk/objects.py` + tests together** when altering an object shape
  (repository-conventions §5; the parity test enforces it).

## 5. DCO sign-off & CLA stance

- EnterpriseSim uses the **Developer Certificate of Origin (DCO)**, **not a CLA**. There is no
  copyright-assignment agreement to sign; the lightweight DCO keeps the barrier low for OSS
  contributors while asserting provenance.
- **Every commit must be signed off**, certifying you have the right to submit it under the
  project license:

  ```
  Signed-off-by: Jordan Rivera <jordan.rivera@example.com>
  ```

  Add it automatically with `git commit -s`. A DCO check blocks unsigned commits.
- By contributing you agree your contribution is licensed under **Apache-2.0** (§6).

## 6. Licensing (Apache-2.0, `ADR-0049`)

- The project is licensed under **Apache License 2.0** (`LICENSE` at repo root, `ADR-0049`).
- New source files carry the standard SPDX identifier where practical:

  ```python
  # SPDX-License-Identifier: Apache-2.0
  ```

- New dependencies must have an **Apache-2.0-compatible** license (permissive: MIT, BSD,
  Apache-2.0, ISC). Copyleft (GPL/LGPL/AGPL) dependencies are **not** accepted without an ADR.
  License compatibility is checked by SCA (CANON §4.6).

## 7. Code of Conduct

- The project adopts the **Contributor Covenant** (`CODE_OF_CONDUCT.md` at repo root). All
  participation — issues, PRs, reviews, discussions — is governed by it.
- Report concerns to the maintainers listed in `CODE_OF_CONDUCT.md`. Be respectful, assume
  good faith, and keep reviews about the work.

## 8. Contributor workflow at a glance

```
open ES-### issue ─▶ (RFC if contract change) ─▶ branch feature/ES-###-slug from main
   ─▶ implement (contracts only under sdk/; synthetic content only)
   ─▶ ruff • black • mypy • pytest green locally
   ─▶ commit -s (DCO)  ─▶ open PR (template, <400 LOC, docs+changelog updated)
   ─▶ CI green + required approvals ─▶ squash-merge to main
```

Thank you for helping make enterprise AI work inspectable and reproducible.
