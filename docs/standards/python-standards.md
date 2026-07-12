# Python Standards

> Python-specific rules for the ECL SDK. Elaborates `CANON-001` §4 and realizes `ADR-0028`
> (Python as reference language) and `ADR-0029` (abstract interfaces only). Read alongside
> [`coding-standards.md`](coding-standards.md).

Python is the **reference contract language** for EnterpriseSim (`ADR-0028`). The SDK is
interfaces-only (`ADR-0029`): the value of this document is precision and consistency, so
that every module reads like `sdk/knowledge/interfaces.py` reads today.

## 1. Target version

- **Python 3.11+.** All contracts must type-check and import on 3.11, 3.12 and 3.13. CI runs
  the matrix. 3.11 is the floor because the SDK relies on modern typing ergonomics and
  `tomllib`.
- Do not use syntax or stdlib features newer than the declared floor without raising the
  floor via an ADR.

## 2. `from __future__ import annotations`

- **Every module** begins with `from __future__ import annotations` (as `sdk/objects.py` and
  every `interfaces.py` already do). Annotations are strings; this keeps forward references
  and PEP 604 unions cheap and import-order-independent.

## 3. Typing

Typing is the product here — treat it as load-bearing.

- **PEP 484 + PEP 604.** Use `X | None`, not `Optional[X]`; `A | B`, not `Union[A, B]`. Match
  the existing style: `loop_closed_by: CanonicalId | None`.
- **Fully annotate every public signature** — parameters and return. No implicit `Any`.
  `disallow_untyped_defs` and `disallow_incomplete_defs` are on (see §7).
- Prefer the **narrowest accurate abstract type**: `Mapping`/`Sequence` (read-only) over
  `dict`/`list` in signatures, exactly as the SDK does (`Mapping[str, Any]`,
  `Sequence[CanonicalId]`).
- Reuse the shared aliases from `sdk/objects.py` — `CanonicalId`, `Timestamp`, `Confidence` —
  rather than bare `str`/`float`, so intent is legible.
- `Any` is a deliberate escape hatch (e.g. `Mapping[str, Any]` for open sub-documents that a
  schema pins down); never a substitute for thinking. Justify non-obvious `Any` in a comment.

## 4. `abc.ABC` vs `typing.Protocol`

Follow the convention the SDK already establishes:

| Use | When | Example in SDK |
|---|---|---|
| **`typing.Protocol`** (often `@runtime_checkable`) | **Object shapes / data contracts** and **pluggable backends** the runtime supplies — structural typing, no inheritance required | `KnowledgeObject`, `ContextObject` (`sdk/objects.py`); `KnowledgeIndex` (`sdk/knowledge/interfaces.py`) |
| **`abc.ABC` + `@abstractmethod`** | **Service interfaces the SDK owns** and expects implementers to subclass explicitly — behavioral contracts with identity | `KnowledgeStore`, `KnowledgeRetriever` |
| **`@dataclass(frozen=True)`** | **Immutable value objects / query & candidate DTOs** passed across interfaces | `KnowledgeQuery`, `KnowledgeCandidate` |

Rules:

- Object contracts that mirror a JSON Schema in `schemas/` are **Protocols** in `objects.py`,
  `@runtime_checkable`, deriving from `ECLObject` (which carries `id`, `schema_version`,
  `created_at`, `metadata`). Do not turn these into concrete classes.
- Abstract service methods use `@abstractmethod` and a `...` body with a one-line docstring
  citing the governing ADR (e.g. `"""Return a published knowledge object by ID (ADR-0004)."""`).
- **No method has an implementation.** Bodies are `...`. `@dataclass(frozen=True)` value
  objects may declare defaults (`top_k: int = 20`) — that is contract shape, not logic.

## 5. Formatting, linting, type-checking

Configured centrally in `pyproject.toml` (§8). These are **required CI gates** (CANON §4.5):

- **black** — the formatter; line length **100**. No hand-formatting debates.
- **ruff** — linter and import sorter (replaces flake8 + isort). Recommended rule sets:
  `E,F,W` (pyflakes/pycodestyle), `I` (import order), `UP` (pyupgrade), `B` (bugbear),
  `D` (pydocstyle, see §6), `ANN` (annotations). `--fix` locally; CI runs `ruff check` +
  `ruff format --check`.
- **mypy** in **strict** mode — the contract layer must type-check cleanly. Zero errors to
  merge.
- Order in the pipeline mirrors CANON §4.5: `ruff → black --check → mypy → pytest`.

## 6. Docstrings

Every public module, class and method has a docstring. Style matches the existing SDK:
**concise, imperative, and it cites the governing ADR/RFC ID.**

- **Module docstring**: one-line summary naming the ECL layer and its `ARCH-`/`ADR-` refs,
  and the "No implementation" reminder — e.g. the header of `sdk/knowledge/interfaces.py`.
- **Class docstring**: what the contract *is* plus the canonical object it produces/owns and
  its invariant — e.g. `"""Durable, governed enterprise truth (KN-###). Immutable once published."""`.
- **Method docstring**: one imperative line; add sections only when they add information:
  - `Args:` for non-obvious parameters,
  - `Returns:` when the return needs explaining beyond the type,
  - `Raises:` **required** whenever the contract can raise (list each typed exception),
  - a trailing ADR/RFC citation for the rule the method encodes.
- Docstrings are checked (`ruff` `D` rules) and must stay consistent with the schema they
  mirror (see [`documentation-standards.md`](documentation-standards.md) — docstring↔doc↔schema
  consistency).

Example signature (illustrative — the shape and annotations are the standard):

```python
@abstractmethod
def publish(self, draft: KnowledgeObject) -> KnowledgeObject:
    """Publish an approved draft, assigning it a version.

    Never mutates prior versions; publication is append-only (ADR-0004).

    Raises:
        KnowledgeGovernanceError: if the draft has not passed governance review.
    """
    ...
```

## 7. Package layout

- One package per ECL layer under `sdk/` (`knowledge/`, `context/`, `planner/`, `decision/`,
  `execution/`, `evaluation/`, `experience/`, `learning/`, `models/`, `workers/`), each with
  `__init__.py`, `interfaces.py`, and `README.md` — exactly the current shape.
- Shared object contracts live in `sdk/objects.py`; package version and `SCHEMA_VERSION` live
  in `sdk/__init__.py` and nowhere else.
- Imports are absolute (`from sdk.objects import CanonicalId`), sorted by ruff. No wildcard
  imports. `__all__` is declared where a module has a curated public surface (as in
  `sdk/__init__.py`).
- No circular imports: `objects.py` depends on nothing in `sdk/`; layer modules depend on
  `objects.py`, not on each other, except through declared composition points.

## 8. `pyproject.toml` expectations

*Describe the standard; do not create the file here.* The repo uses a **single** root
`pyproject.toml` as the one source of tooling config:

- `[build-system]` — a PEP 517 backend (e.g. `hatchling`); the SDK is an installable package
  `enterprisesim` exposing `sdk`.
- `[project]` — `requires-python = ">=3.11"`, Apache-2.0 license (`ADR-0049`), and a
  **minimal/empty runtime `dependencies`** list (the SDK is types-only, coding-standards §5).
- `[project.optional-dependencies]` — `dev`/`test` extras: `mypy`, `ruff`, `black`, `pytest`,
  `pytest-cov`, `jsonschema>=4.18`, `referencing` (schema validation per `schemas/README.md`).
- `[project.entry-points]` — the plugin group used by extension points (`RFC-0027`), so
  implementers register `KnowledgeIndex`, `Tool`, `ModelProvider`, etc.
- `[tool.black]` (line-length 100), `[tool.ruff]` (target-version `py311`, the rule sets in
  §5), `[tool.mypy]` (`strict = true`), `[tool.pytest.ini_options]`, `[tool.coverage]`
  (thresholds per [`testing-standards.md`](testing-standards.md)).
- `[project.version]` (or a dynamic hook) stays in lockstep with `sdk.__version__` (SemVer,
  `ADR-0032`; see [`versioning.md`](versioning.md)).
