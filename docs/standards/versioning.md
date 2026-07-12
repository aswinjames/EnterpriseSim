# Versioning

> How the SDK and the schemas are versioned. Realizes `ADR-0032` (SemVer), `RFC-0021` (schema
> versioning) and `ADR-0033` (expand-contract), consistent with the API/event evolution rules
> in `CANON-001` §4.8. Referential integrity across versions is invariant (`ADR-0022/0023`).

Two version numbers exist and are both declared in `sdk/__init__.py`:

```python
__version__   = "0.1.0"        # SemVer of the SDK contracts (ADR-0032)
SCHEMA_VERSION = "2020-12.v1"  # schema family these interfaces target (RFC-0021)
```

They move together in principle but are distinct axes: the Python typing surface can gain a
patch without a schema change, but a **schema shape change forces an SDK version bump** because
`sdk/objects.py` mirrors the schema.

## 1. SemVer for the SDK (`ADR-0032`)

`__version__` follows **Semantic Versioning `MAJOR.MINOR.PATCH`**:

- **MAJOR** — a backward-incompatible contract change: removing/renaming an interface,
  method, or object attribute; tightening a type; making an optional field required; changing
  a method signature incompatibly.
- **MINOR** — backward-compatible additions: a new interface, a new optional attribute, a new
  extension point, a new (additive) Protocol.
- **PATCH** — no contract change: docstring fixes, clarifications, tooling, non-semantic
  metadata.
- **Pre-1.0 caveat.** While `0.y.z` (the current `0.1.0`), the contract is explicitly
  **unstable**: `0.MINOR` may carry breaking changes, still announced via RFC + changelog.
  `1.0.0` is the point at which the full compatibility guarantees below take effect.

## 2. Schema versioning (`RFC-0021`)

The schema family carries its own version, surfaced in **every instance's `schema_version`**
and tracked by `sdk.SCHEMA_VERSION` (`schemas/README.md`):

- Form: `2020-12.v1`, `2020-12.v2`, … — the `2020-12` names the JSON Schema draft, `.vN` the
  MCG schema-family revision. The `schema_version` field is constrained by the pattern
  `^2020-12\.v\d+$` in `common.schema.json`.
- **SemVer semantics apply** (`RFC-0021`, `ADR-0032`): additive/optional field changes are a
  **minor** family revision; a required-field addition, removal, or type change is a **major**
  revision and bumps `.vN`.
- `$id` versions, `SCHEMA_VERSION`, and instance `schema_version` are kept **in lockstep** —
  a schema PR updates all three, and the contract-parity test (testing-standards §3) enforces
  the SDK side.

## 3. Expand → migrate → contract (`ADR-0033`)

Schema evolution never rewrites instances in place (`schemas/README.md` migration strategy):

1. **Expand** — add new fields as **optional** first. Producers may start emitting them;
   readers tolerate their absence.
2. **Migrate** — dual-write and backfill; new versions are **new records**, old instances are
   never mutated (immutability of `KnowledgeObject`; append-only `ExperienceObject`).
3. **Contract** — only once **no producer emits the old shape** do you make a field required
   or remove a deprecated field, in a **major** revision.

This mirrors CANON §7.4: migrations are backward-compatible so a rollback never needs a
"down-migration" under fire.

## 4. Compatibility windows

- **Schema readers accept the current and previous MAJOR schema version** during a migration
  window (`schemas/README.md` step 3); readers always tolerate unknown `metadata` (the
  sanctioned additive extension surface).
- The compatibility window for a deprecated schema major is **at least one minor SDK release
  and no less than 90 days**, whichever is longer, before removal — announced in the
  changelog at deprecation time.
- **Referential integrity is invariant across versions** (`ADR-0022/0023`): an ID never
  changes meaning; a cross-reference (`PLAN-0072`, `EVAL-0061`) remains resolvable across a
  migration. A change that would break a reference requires an **ADR** (`schemas/README.md`
  step 4).

## 5. Deprecation policy

Nothing is removed without a deprecation cycle:

1. **Announce** — mark the interface/field deprecated, name its replacement and the target
   removal version. In Python, add a `Deprecated:` note in the docstring and (for anything
   importable at runtime) emit `DeprecationWarning` in the reference implementation, not the
   contract. In schemas, add `"deprecated": true` and a `description` pointing to the successor.
2. **Record** — one `Deprecated` changelog entry (documentation-standards §7) citing the RFC
   (and ADR if an invariant changes).
3. **Wait** — keep it working through the compatibility window (§4).
4. **Remove** — in a **MAJOR** SDK bump / **major** schema revision, with a `Removed`
   changelog entry and migration notes.

Deprecated ≠ gone: it keeps validating and importing until the window closes.

## 6. Tagging & the version source of truth

- The version lives in **`sdk/__init__.py`** (`__version__`, `SCHEMA_VERSION`) and is
  referenced by `pyproject.toml`; these never disagree.
- A release is a **git tag `vMAJOR.MINOR.PATCH`** on `main` (CANON §4.1 release tags), e.g.
  `v0.2.0`. Tags are immutable; a mistake is fixed by a new tag, never by moving one.
- The coordinated release train (`REL-<YYYY>-<###>`, CANON §7.2) references the tags it
  bundles — see [`release-strategy.md`](release-strategy.md).

## 7. What triggers which bump — quick reference

| Change | SDK version | Schema revision | Needs |
|---|---|---|---|
| Docstring / comment / tooling only | PATCH | — | PR |
| New optional schema field (+ mirrored optional Protocol attr) | MINOR | minor `.vN` unchanged shape-major | RFC |
| New interface / extension point | MINOR | — | RFC (ADR if it adds an invariant) |
| Make optional field required | MAJOR | major `.vN+1` | RFC + ADR |
| Remove / rename field, method, interface | MAJOR | major `.vN+1` | RFC + ADR, deprecation cycle |
| Change a type incompatibly | MAJOR | major `.vN+1` | RFC + ADR |
| Change what an ID means / break a reference | MAJOR | major `.vN+1` | **ADR** (hard requirement) |
