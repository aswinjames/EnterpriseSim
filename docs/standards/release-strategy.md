# Release Strategy

> How the EnterpriseSim OSS project releases. Instantiates `CANON-001` **§4.1 (Git
> branching)**, **§4.5 (CI/CD)** and **§7 (Release Process)** for a single public monorepo,
> and builds on the SemVer/schema rules in [`versioning.md`](versioning.md).

EnterpriseSim ships **contracts, not a running service**, so "release" means publishing a
versioned, importable SDK package plus its authoritative schemas — reproducibly, from a
signed, tagged commit on `main`.

## 1. Branching — trunk-based (`ADR-0031`, CANON §4.1)

- **`main` is always releasable and protected.** Direct pushes are forbidden; every change
  lands via PR (CANON §4.2).
- Short-lived branches, **< 3 days**, named per CANON §4.1:
  - `feature/<KEY>-<slug>` — e.g. `feature/RFC-0021-schema-v2`,
  - `bugfix/<KEY>-<slug>`,
  - `hotfix/<INC-ID>-<slug>` — cut from the release tag (§6).
- Large or risky work hides behind a flag/optional path or an unreleased `.vN+1` schema draft,
  not a long-lived branch. Trunk stays green.
- **Squash-merge** is the default; the PR title becomes the commit subject (CANON §4.2). Keep
  PRs **< 400 lines** of diff where practical.

## 2. Commit & PR messages

- Conventional, imperative subject lines; the body links the issue and, for contract changes,
  the `RFC-####` / `ADR-####`.
- Example:

  ```
  feat(schemas): add optional context.signals.novelty (RFC-0021)

  Expand step of expand→migrate→contract (ADR-0033). Mirrors new optional
  ContextObject.signals key in sdk/objects.py. SCHEMA_VERSION unchanged (additive).
  Closes ES-142.

  Signed-off-by: Jordan Rivera <jordan.rivera@example.com>
  ```

- Every commit is **DCO signed-off** (`Signed-off-by:`) — see
  [`contribution-guidelines.md`](contribution-guidelines.md).

## 3. Release model — continuous, with a coordination train

Per CANON §7.2:

- **Continuous by default.** Any merge to `main` that passes all gates is a release
  *candidate*; maintainers cut a tagged release whenever a meaningful, coherent set of changes
  has landed. There is no artificial freeze.
- **Fortnightly release train** `REL-<YYYY>-<###>` (CANON §7.2) is the **coordination and
  narrative** artifact: it bundles notable/breaking/schema-affecting changes for
  communication and changelog, keyed to the SemVer tags it contains. It is **not a deployment
  gate** for a routine patch — a docstring fix can ship the day it merges.
- Release numbering is **sequential per calendar year**: `REL-2026-001`, `REL-2026-002`, …

## 4. Versioning & tagging

- Version source of truth is `sdk/__init__.py` (`__version__`, `SCHEMA_VERSION`), referenced
  by `pyproject.toml` (versioning.md §6).
- A release is an **annotated, immutable git tag `vMAJOR.MINOR.PATCH`** on `main` (CANON §4.1):
  `v0.2.0`. Tags are never moved; a bad release is superseded by a new tag.
- The tag, the `CHANGELOG.md` section, and the `SCHEMA_VERSION` it targets all agree.

## 5. CI/CD pipeline & artifact publishing (CANON §4.5)

Releases are **GitOps-driven and auditable** — no manual publishing steps. The golden-path
pipeline (GitHub Actions in `.github/workflows/`) mirrors CANON §4.5, adapted for a Python
contract package:

```
lint (ruff, black --check) → type-check (mypy strict) → unit + contract + schema-conformance
  → SAST/SCA + secret scan → build sdist+wheel → publish (tag only) → attach SBOM/provenance
```

- **Trigger.** Push to a `v*` tag runs the publish job; PRs run everything up to `build`.
- **Artifacts.** A source distribution and a wheel for the `enterprisesim` package, published
  to PyPI (and a GitHub Release with the changelog section attached). Schemas are versioned
  in-repo and referenced by `$id`; the GitHub Release also attaches the `schemas/` set for the
  version.
- **Provenance.** An **SBOM (SPDX)** and build provenance are attached to every published
  release (CANON §4.5, §8.9 "Open Standards"); artifacts are built from the tagged commit only.
- **Reproducibility.** Pinned tooling versions and the 3.11–3.13 matrix (python-standards §1)
  mean a release is rebuildable from its tag.
- **Gates block the release.** Any red gate (including high/critical SAST/SCA findings —
  CANON §4.6) stops publishing.

## 6. Hotfix policy (CANON §7.3)

- Triggered by a **critical defect in a published release** or a **critical security finding**
  (the OSS analog of a Sev1/Sev2 — tracked as `INC-<YYYY>-<###>`).
- Cut `hotfix/<INC-ID>-<slug>` **from the affected release tag**, make the minimal targeted
  change, and ship a **PATCH** (or MAJOR if the fix must break) release.
- Expedited review still requires **≥1 approval** (**≥2** for anything touching schema
  contracts or security — see [`review-process.md`](review-process.md)), plus the mandatory
  security and smoke/validation gates.
- The hotfix is **forward-merged to `main`** so the fix is never lost.

## 7. Rollback policy (CANON §7.4)

- Because releases are immutable tagged artifacts, "rollback" for consumers is **pin to the
  previous version** — always possible because schema changes are expand-contract and
  backward-compatible within the window (versioning.md §3–4).
- A defective release is **yanked** (marked so on the registry) and **superseded by a new
  patch tag**; the tag itself is never deleted or moved (auditability).
- Every release PR carries the equivalent of CANON §7.4's rollback plan: a one-line statement
  of the prior-good version and whether downgrading is safe (it is, unless an ADR-authorized
  breaking change says otherwise).

## 8. Release checklist

Before tagging `vX.Y.Z`:

- [ ] All required CI gates green on `main` at the release commit (lint, mypy, unit, contract,
      schema-conformance, security).
- [ ] `sdk/__init__.py` `__version__` (and `SCHEMA_VERSION` if changed) bumped per
      [`versioning.md`](versioning.md); `pyproject.toml` agrees.
- [ ] `CHANGELOG.md` section written; breaking changes cite their `RFC-####`/`ADR-####` and
      state migration + compatibility window.
- [ ] Any contract change has its RFC merged (and ADR if it altered an invariant).
- [ ] Schema examples validate; contract-parity test green.
- [ ] If notable/breaking: assign the next `REL-<YYYY>-<###>` and write the train narrative.
