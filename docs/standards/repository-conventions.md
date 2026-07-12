# Repository Conventions

> How the EnterpriseSim repository is laid out, who owns what, and how files and artifacts
> are named. Instantiates `CANON-001` **§5 (Naming)** and **§6 (IDs)** for *this* repository.

EnterpriseSim is a **single, public monorepo**. The intelligence architecture (ECL), its
typed contracts (SDK), its schemas, its decision records and its benchmarks live together so
that a change to a contract, its schema, its decision record and its tests can land in one
reviewable pull request. This is deliberate: referential integrity across artifacts (CANON
§6, `ADR-0023`) is easiest to enforce when the artifacts share a tree.

## 1. Repository layout

```
EnterpriseSim/
├── CANON.md                      # CANON-001 — authoritative, immutable (Architecture Office)
├── README.md                     # project front door
├── LICENSE                       # Apache-2.0 (ADR-0049)
├── CONTRIBUTING.md               # pointer → docs/standards/contribution-guidelines.md
├── CODE_OF_CONDUCT.md            # Contributor Covenant (see contribution-guidelines.md)
├── CODEOWNERS                    # ownership routing (see §4)
├── pyproject.toml                # single source of Python tooling config (see python-standards.md)
├── .gitignore
├── sdk/                          # ECL abstract interfaces — NO implementation (ADR-0029)
│   ├── __init__.py               # __version__, SCHEMA_VERSION
│   ├── objects.py                # canonical object Protocols (mirror schemas/)
│   └── <layer>/                  # one package per ECL layer
│       ├── __init__.py
│       ├── interfaces.py         # ABCs, Protocols, frozen dataclasses
│       └── README.md             # layer purpose, interfaces, extension points
├── schemas/                      # JSON Schema (Draft 2020-12) — authoritative object shapes
│   ├── *.schema.json
│   └── examples/                 # worked, cross-referenced, valid instances
├── docs/
│   ├── architecture/             # ARCH-01…ARCH-07 (frozen; ADR to change)
│   ├── adr/                      # ADR-000N.md (Architecture Office)
│   ├── rfcs/                     # RFC-000N.md (contract/cross-team proposals)
│   ├── guides/                   # how-to guides for implementers & contributors
│   └── standards/                # THIS directory — engineering standards
├── benchmarks/                   # Worker benchmark suites & harness contracts
└── tests/                        # repo-level tests (schema conformance, contract, doc lint)
```

**Directory rules**

- The `sdk/` tree contains **contracts only**. If a file has a runnable method body other
  than `...`, it does not belong in `sdk/` (`ADR-0029`; enforced by CI, see coding-standards).
- `schemas/` is the **source of truth for object shape**; `sdk/objects.py` mirrors it. A
  shape change touches both in the same PR (see versioning.md).
- `docs/architecture/` is **frozen**: it changes only via an ADR. Do not edit `ARCH-*` prose
  to reflect a new decision without the accompanying `ADR-####`.
- New top-level directories require an RFC.

## 2. File naming

| Artifact | Convention | Example |
|---|---|---|
| Documentation (Markdown) | **kebab-case** `.md` | `release-strategy.md` |
| ADR files | `ADR-<4 digit>.md`, zero-padded, never reused | `docs/adr/ADR-0032.md` |
| RFC files | `RFC-<4 digit>.md`, zero-padded, never reused | `docs/rfcs/RFC-0021.md` |
| Architecture docs | `NN_snake_case.md` (ordered) | `docs/architecture/02_knowledge_layer.md` |
| Python modules & packages | **snake_case** | `sdk/learning/interfaces.py` |
| JSON Schema files | `snake_case.schema.json` | `schemas/context_object.schema.json` |
| Schema examples | `<object>.example.json` | `schemas/examples/context_object.example.json` |
| Config / dotfiles | tool-native names | `pyproject.toml`, `.github/workflows/ci.yml` |

- CANON §5 uses `ADR-###` / `RFC-###` (3-digit) as the *display* form; **files in this repo
  are zero-padded to 4 digits** (`ADR-0001`) for stable lexical sort, matching the existing
  `docs/adr/ADR-0001.md`. Both refer to the same decision; 4-digit is the on-disk form.
- Python identifiers: `snake_case` functions/variables, `PascalCase` classes, `UPPER_SNAKE`
  constants (`SCHEMA_VERSION`). See [`python-standards.md`](python-standards.md).

## 3. Canonical IDs inside artifacts

Every artifact that references another artifact MUST use the other's **canonical ID** exactly
as defined in CANON §6 — never a paraphrase or a link alone. This referential integrity is
the backbone of EnterpriseSim (`ADR-0023`).

- **ECL object IDs** carry their canonical prefix and zero-padding: `KN-045`, `CTX-0118`,
  `PLAN-0072`, `EVAL-0061`, `REF-0019`, `EXP-090`, `PR-0312`, `TR-0442`.
- **Decision/proposal IDs**: `ADR-0032`, `RFC-0021`, `CANON-001`, `ARCH-02`.
- IDs are **globally unique within their namespace, zero-padded, and immutable once assigned**
  (never reused even after deletion — CANON §6, `ADR-0022`).
- A docstring, README, ADR or schema `description` that mentions a decision cites its ID
  (existing SDK code does this, e.g. `"immutable once published (ADR-0004)"`). Keep that
  style; it makes rationale greppable.
- When adding a *new* ADR/RFC, take the next unused number globally; never fill a gap left by
  a superseded record.

## 4. Ownership & CODEOWNERS

Ownership mirrors CANON §2 "you build it, you run it": every path has exactly one accountable
team. Ownership is expressed in the root `CODEOWNERS` file and enforced by branch protection
(a matching owner review is required to merge — see [`review-process.md`](review-process.md)).

Illustrative `CODEOWNERS` (teams per CANON §2.2):

```
# EnterpriseSim ownership — canonical teams from CANON-001 §2.2
*                       @enterprisesim/architecture-office     # TEAM-090 default owner
/CANON.md               @enterprisesim/architecture-office     # canon is Architecture Office only
/docs/architecture/     @enterprisesim/architecture-office     # ARCH-* frozen
/docs/adr/              @enterprisesim/architecture-office
/docs/rfcs/             @enterprisesim/architecture-office
/docs/standards/        @enterprisesim/architecture-office @enterprisesim/devex   # TEAM-031
/sdk/models/            @enterprisesim/ai-engineering          # TEAM-070 (model gateway)
/sdk/                   @enterprisesim/ai-engineering @enterprisesim/architecture-office
/schemas/               @enterprisesim/architecture-office @enterprisesim/data-platform  # TEAM-060
/benchmarks/            @enterprisesim/quality-engineering     # TEAM-050
/tests/                 @enterprisesim/quality-engineering
/.github/               @enterprisesim/devex                   # TEAM-031
/pyproject.toml         @enterprisesim/devex
```

Rules:

- **CANON.md and `docs/architecture/` are owned solely by the Architecture Office** (`TEAM-090`).
  No other team can approve a change there.
- Every source path resolves to at least one owning team; there are **no unowned paths**
  (CANON §2.3). The `*` default catches new paths until an explicit owner is added.
- Cross-cutting changes (e.g. a schema change that ripples into `sdk/objects.py`) require
  **each** affected owner's approval; CODEOWNERS makes this automatic.
- Ownership metadata in Python belongs in the layer README and, where relevant, the module
  docstring — mirroring how `sdk/knowledge/README.md` names the layer and its ADRs.

## 5. Monorepo hygiene

- **One logical change per PR**, spanning all the files that change together (schema +
  `objects.py` + tests + ADR/RFC). See [`review-process.md`](review-process.md).
- Generated artifacts and caches are never committed (see `.gitignore`:
  `__pycache__/`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`, `dist/`, `*.egg-info/`).
- No secrets, tokens or credentials in any file, ever (CANON §4.6). Secret scanning is a
  required CI gate (see release-strategy.md).
- Large binaries and datasets do not belong in the repo; benchmark fixtures are small,
  synthetic, and MCG-canon-consistent (see contribution-guidelines.md synthetic-only rule).
