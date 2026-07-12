# EnterpriseSim Engineering Standards

> The engineering standards for the **EnterpriseSim open-source repository itself** — the
> ECL SDK (`sdk/`), the JSON Schemas (`schemas/`), the architecture and decision records
> (`docs/`), and the benchmarks (`benchmarks/`).

These standards are a concrete instantiation of, and are strictly subordinate to,
[`../../CANON.md`](../../CANON.md) (`CANON-001`) — in particular **§4 Technology Standards**,
**§5 Naming Conventions**, **§6 ID Conventions** and **§7 Release Process**. Where canon
defines a standard (trunk-based development, PR rules, the test pyramid, release cadence),
these documents elaborate it for *this* repository. **Canon wins on any conflict.** A change
here that would contradict canon requires an ADR (`ADR-0001`, `ADR-0050`).

Audience: the senior Python engineers who implement the ECL against the SDK interfaces, plus
external open-source contributors.

## Documents

| # | Document | Scope | Primary canon tie-in |
|---|---|---|---|
| 1 | [`repository-conventions.md`](repository-conventions.md) | Repo layout, folder ownership, file/artifact naming, CODEOWNERS | §5, §6 |
| 2 | [`coding-standards.md`](coding-standards.md) | Language-agnostic engineering principles: interface-first, errors, logging, security, determinism | §4.6, §8 |
| 3 | [`python-standards.md`](python-standards.md) | Python 3.11+, typing, `ABC` vs `Protocol`, black/ruff/mypy, docstrings, `pyproject.toml` | §4, ADR-0028/0029 |
| 4 | [`testing-standards.md`](testing-standards.md) | Test pyramid, coverage tiers, contract & schema-conformance tests, flaky quarantine | §4.4 |
| 5 | [`documentation-standards.md`](documentation-standards.md) | Docs-with-code, READMEs, ADR/RFC usage, Mermaid, changelog | §4.7 |
| 6 | [`versioning.md`](versioning.md) | SemVer for SDK & schemas, expand-contract, deprecation, compatibility windows | ADR-0032, RFC-0021, ADR-0033 |
| 7 | [`release-strategy.md`](release-strategy.md) | Trunk-based branching, release trains, tagging, publishing, hotfix/rollback | §4.1, §7 |
| 8 | [`contribution-guidelines.md`](contribution-guidelines.md) | Issues, RFC/ADR process, PRs, DCO sign-off, Apache-2.0, synthetic-only rule | §4.2, ADR-0049 |
| 9 | [`review-process.md`](review-process.md) | Reviewer roles, CODEOWNERS, approvals by risk tier, checklist, SLAs | §4.2, §7.5 |

## How these fit together

```
CANON-001 §4/§5/§6/§7   ──governs──▶  docs/standards/*   ──govern──▶  sdk/  schemas/  benchmarks/
        │                                     │
     ADR-/RFC-  ◀──record decisions & contract changes that shape these standards──┘
```

- **Naming and IDs** (doc 1) instantiate CANON §5/§6 for the files and artifacts *inside this
  repo* — the `mcg-*` service repos live elsewhere; here the artifacts are ADRs, RFCs,
  schemas and SDK modules.
- **Coding and Python standards** (docs 2–3) govern the interfaces-only SDK: `abc.ABC` /
  `typing.Protocol`, no implementation, model- and domain-agnostic (per `sdk/README.md` and
  ADR-0028/0029).
- **Testing** (doc 4) aligns tier-by-tier with the CANON §4.4 pyramid and adds
  schema-conformance testing for `schemas/`.
- **Versioning and release** (docs 6–7) bind `sdk.__version__` and `sdk.SCHEMA_VERSION` to
  SemVer (ADR-0032) and the expand-contract schema policy (RFC-0021 / ADR-0033).
- **Contribution and review** (docs 8–9) operationalize CANON §4.2 and §7.5 for an OSS
  project under Apache-2.0 (ADR-0049).

## Conventions used in these documents

- **Kebab-case** filenames for docs; **snake_case** for Python; canonical IDs (`ADR-####`,
  `RFC-####`, `KN-###`, …) exactly as CANON §6 defines them.
- Short illustrative snippets (config fragments, signatures, trees, command examples) are
  intentional and normative-by-example; **no implementation code** appears anywhere.
- "MUST / SHOULD / MAY" carry RFC-2119 force.

*These standards govern the EnterpriseSim repo. They do not describe MCG's internal `mcg-*`
service repositories, which follow CANON directly.*
