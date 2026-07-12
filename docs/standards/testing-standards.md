# Testing Standards

> How EnterpriseSim tests itself. Aligns tier-by-tier with the MCG test pyramid in
> `CANON-001` **§4.4** (owned in canon by Quality Engineering, `TEAM-050`) and applies it to
> an interfaces-only SDK plus authoritative JSON Schemas.

The SDK has no implementation, so "testing" here means proving the **contracts are coherent**:
schemas validate their examples, the Python typing surface matches the schemas, extension
points behave as advertised, and the benchmark harness contracts hold. This is what keeps a
public benchmark trustworthy.

## 1. The pyramid, mapped to this repo

CANON §4.4 defines the layers; here is what each means for EnterpriseSim (`tests/` at repo
root, per repository-conventions.md):

| CANON §4.4 layer | In EnterpriseSim | Required |
|---|---|---|
| **Unit** | Structural checks on `sdk/objects.py` Protocols, `@dataclass(frozen=True)` value objects, aliases | Yes |
| **Contract** | Schema↔Protocol conformance: every field in a `*.schema.json` has a matching attribute on the mirroring Protocol in `sdk/objects.py`, and vice versa | Yes |
| **Integration** | Cross-artifact referential integrity across `schemas/examples/` (the `CHK-1421` loop resolves) | Yes |
| **End-to-end** | Full-loop example set validates as one consistent story (`KN-045 → … → EXP-090`) | Yes |
| **Performance** | Validator throughput / import-time budget (lightweight; SDK is types) | Advisory |
| **Security** | SAST/SCA/secret-scan on the repo & tooling deps (CANON §4.6) | Yes (pipeline) |

There are no service-level perf/DAST layers here because the SDK ships no running service;
those apply to the `mcg-*` implementations that consume the SDK.

## 2. Schema-conformance tests (the load-bearing tier)

`schemas/` is the source of truth for object shape (`schemas/README.md`). Required tests:

- **Every schema is valid Draft 2020-12** and loads into a registry keyed by `$id` so
  relative `$ref`s resolve (use the `jsonschema>=4.18` + `referencing` recipe in
  `schemas/README.md`).
- **Every example in `schemas/examples/` validates** against its schema. This is a merge gate.
- **Base composition holds**: each object schema composes
  `common.schema.json#/$defs/eclObjectBase` via `allOf` and closes with
  `unevaluatedProperties: false`; a test asserts a stray field is rejected and an inherited
  base field is accepted (the exact behavior `schemas/README.md` calls out).
- **ID patterns**: instances' IDs match the canonical patterns in `common.schema.json`
  (CANON §6), including the Jira project-key form (`CHK-1421`).
- **A dependency-free structural validator** runs in CI environments without network access —
  keep the one referenced in `schemas/README.md` green.

## 3. Contract tests: schema ↔ Python parity

Because `sdk/objects.py` Protocols mirror the schemas, drift is the primary risk. A contract
test asserts, for each object type, that the Protocol's declared attributes and the schema's
properties are the same set (modulo the shared `ECLObject`/`eclObjectBase` fields). A field
added to `context_object.schema.json` without a matching `ContextObject` attribute (or the
reverse) **fails CI** — this is what forces schema and SDK to change in the same PR
(see [`versioning.md`](versioning.md)).

## 4. Coverage thresholds by tier

Coverage is measured on any Python that *is* testable (test helpers, the structural
validator, benchmark harness code) — not on `...` bodies, which have nothing to cover.
Aligned to CANON §4.4:

- **Tier-0/1-equivalent code** (schema validation, contract-parity, benchmark harness
  contracts): **≥ 80%** line coverage.
- **Everything else** (docs tooling, helper scripts): **≥ 70%**.
- Thresholds are enforced in `pyproject.toml` `[tool.coverage]` and fail the build below the
  floor. Coverage may never be *lowered* without an approving review that says why.

## 5. Determinism

Tests are deterministic or they do not merge (mirrors coding-standards §2):

- No wall-clock, no network, no randomness without a **fixed seed**. Freeze time and seed RNG
  explicitly; assert on canonical IDs, not on generated timestamps.
- Schema validation runs offline (bundled schemas + local registry). CI has no network
  dependency for the required tiers.
- The same test on the same commit produces the same result on every machine and every OS in
  the matrix (Linux/macOS).

## 6. Fixtures & synthetic data

- Test fixtures reuse the **worked examples in `schemas/examples/`** as the canonical corpus;
  add new examples there rather than inventing ad-hoc payloads in test files.
- All fixture data is **synthetic and CANON-consistent**: real MCG apps/teams/IDs from
  CANON (`APP-003`, `TEAM-004`, `CHK-1421`), never real-world company data (hard constraint;
  see [`contribution-guidelines.md`](contribution-guidelines.md)).
- Fixtures are small and committed; large/binary data is out (repository-conventions §5).
- Cross-referenced fixtures preserve referential integrity — a fixture that mentions
  `PLAN-0072` uses the same object the rest of the corpus uses.

## 7. Flaky-test quarantine

Directly per CANON §4.4:

- A test that fails intermittently is **auto-quarantined** (marked, excluded from the merge
  gate) and immediately filed as a tracked bug with a linked issue.
- Quarantine is a countdown, not a hiding place: a test quarantined **> 14 days is a Sev3**
  and blocks the owning area's next release train until fixed or deleted with justification.
- A quarantined test is either fixed to be deterministic (§5) or removed — it is never left
  silently skipped.

## 8. Running tests

Illustrative commands (exact config in `pyproject.toml`):

```bash
# full required gate, mirroring the CI pipeline order (python-standards §5)
ruff check . && ruff format --check . && mypy sdk && pytest --cov=sdk --cov=tests --cov-fail-under=80

# schemas only
pytest tests/schemas -q

# a single object's schema↔Protocol parity
pytest tests/contract -k context_object
```

CI runs this on every PR across the 3.11–3.13 matrix; **all required tiers green is a
precondition to merge** (see [`review-process.md`](review-process.md)). New behavior lands
with its tests in the same PR — tests are a deliverable, not a follow-up (CANON §4.7 spirit).
