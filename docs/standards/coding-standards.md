# Coding Standards

> Language-agnostic engineering principles for the EnterpriseSim repository. Python-specific
> rules live in [`python-standards.md`](python-standards.md). These principles instantiate
> `CANON-001` **§4.6 (Security)** and **§8 (Architecture Principles)** for the ECL SDK.

The SDK is an **interfaces-only contract layer** (`sdk/README.md`, `ADR-0029`). "Good code"
here means a precise, minimal, well-documented contract that a team of senior engineers can
implement against tomorrow — not clever implementation. Everything below serves that.

## 1. Interface-first, no implementation

- The SDK defines **what, never how**. Every method body is `...`; there is no control flow,
  no I/O, no state mutation, no provider calls anywhere under `sdk/` except the model-gateway
  abstractions in `sdk/models/` (which are *still* abstract — they name providers, they don't
  call them). This is `ADR-0029` and is CI-enforced.
- Contracts are **designed and reviewed before implementation** (CANON §8 "API-First"). For
  the SDK, the JSON Schema in `schemas/` is the shape source of truth; the Python `Protocol`
  in `sdk/objects.py` is the typing surface that mirrors it (`sdk/README.md`).
- A contract change is a **contract event**: it needs an RFC (and an ADR if it alters an
  invariant). See [`versioning.md`](versioning.md) and [`documentation-standards.md`](documentation-standards.md).
- Keep interfaces **small and orthogonal**. Prefer several focused Protocols over one broad
  interface; prefer composition (`WorkerDecision(DecisionObject, Protocol)`) over widening an
  existing contract.

## 2. Determinism & reproducibility

EnterpriseSim is a **public benchmark**; its own artifacts must be reproducible the way it
demands Worker artifacts be reproducible (`ADR-0001` rationale).

- Interfaces MUST NOT bake in wall-clock time, randomness, network state or environment as
  hidden inputs. Where a capability is inherently non-deterministic (model routing, retrieval
  ranking), that variability is an **explicit, typed input or a documented signal** — e.g.
  `ContextObject.signals`, `DecisionObject.fused_confidence` — never an implicit side effect.
- Object identity is by **canonical ID**, assigned once and never reused (`ADR-0022`). Two
  runs referencing `PLAN-0072` mean the same plan.
- Timestamps are ISO-8601 UTC strings (`Timestamp` in `sdk/objects.py`, e.g.
  `"2026-06-30T12:00:00Z"`). No local time, no implicit `now()` in a contract.
- Immutability is a contract property, not a convention: `KnowledgeObject` is immutable once
  published, `ExperienceObject` is append-only, `ContextObject` is ephemeral and never
  persisted as durable truth (`sdk/objects.py` header; `ADR-0004/0005/0006`).

## 3. Error handling

- Contracts declare their **failure modes explicitly**. Prefer typed, named exceptions in a
  module's namespace (e.g. `KnowledgeNotFound`, `SchemaVersionUnsupported`) over returning
  sentinels or bare `Exception`. Document each on the raising method (see python-standards
  docstring "Raises").
- Distinguish **expected domain outcomes** (model into the return type or a status enum, e.g.
  `ExecutionObject.status ∈ {succeeded, failed, partial}`) from **exceptional faults** (raise).
- Never swallow errors silently and never `except:`/`except Exception: pass`. An interface
  that can fail says so in its signature and docstring.
- Failures carry **provenance**: which object, which ID, which layer. This mirrors the
  Reflection contract, where `root_cause` has `{category, detail, confidence}`.

## 4. Logging & observability

CANON §8.6: "you cannot operate what you cannot observe." The SDK does not log (it has no
implementation), but it **shapes** how implementers will observe the ECL:

- Interfaces expose the hooks that make a run inspectable: decision traces
  (`WorkerDecision.trace_seq`), execution artifacts (`WorkerArtifact.ref` → `PR-0312`),
  per-layer confidences fused in a decision. Preserve these; do not collapse them.
- Guidance for implementers (normative for the reference implementation): **structured logs**
  (key/value, JSON), one event per meaningful state transition, correlation by canonical ID
  and Worker `run_id`. Standard telemetry follows OpenTelemetry (CANON §9 "Open Standards").
- **Never log secrets, credentials, or `sensitivity ∈ {pci, pii}` payloads** (CANON §4.6).
  `KnowledgeObject.sensitivity` exists so implementers can enforce this at the boundary.

## 5. Dependency hygiene

- The SDK's runtime dependency footprint is **near-zero by design** — it is types and
  abstractions. `sdk/objects.py` imports only from `typing`. Do not add a runtime dependency
  to `sdk/` without an ADR; a contract layer that drags in a web framework is a smell.
- Third-party libraries appear only in tooling/test extras (validators, `pytest`, `mypy`,
  `ruff`) — declared in `pyproject.toml` (see python-standards.md), pinned for CI
  reproducibility, and scanned by SCA on every pipeline (CANON §4.6).
- Prefer **open standards and formats** over proprietary ones (CANON §8.9): JSON Schema
  Draft 2020-12, OpenAPI, protobuf, CloudEvents, SPDX/SBOM.
- New dependencies require: a stated reason in the PR, a compatible OSI license (Apache-2.0
  compatible — see contribution-guidelines.md), and a maintainer's review.

## 6. Security by design

Built in from the start, not bolted on (CANON §4.6, §8.7):

- **Sensitivity is a first-class field.** Contracts that carry potentially sensitive content
  (`KnowledgeObject.sensitivity`) let implementations enforce classification (`public |
  internal | pci | pii`). Interfaces MUST propagate, never strip, this signal.
- **Least privilege in the contract shape.** Tools, model access and execution are mediated
  through explicit registries and gateways (`ToolRegistry`, `ModelGateway`, `PolicyGuard`) so
  a Worker cannot reach a capability it was not granted.
- No secrets in code, config, tests, fixtures, examples, docstrings, or commit messages —
  ever. Secret scanning blocks merge.
- Synthetic content only. All example data (`schemas/examples/`, benchmark fixtures) is
  fictional MCG data consistent with CANON; never real company data (see contribution-guidelines).

## 7. Simplicity & consistency

- Follow the patterns already in `sdk/`: `from __future__ import annotations`, PEP 604 unions
  (`CanonicalId | None`), `@dataclass(frozen=True)` for value objects, `@runtime_checkable`
  Protocols for structural object types, concise docstrings citing the governing ADR/RFC.
- One concept, one name, everywhere — the **ubiquitous language** of CANON §8.5. A "plan" is
  `PLAN-###` / `PlanningObject` in code, schema, docs and tests alike. Do not introduce
  synonyms.
- Dead code, commented-out blocks, and TODOs without a linked issue do not merge. A TODO
  carries a Jira-style key or an issue link (CANON §4.2 links every change to an issue).
- When in doubt, optimize for the reader who will implement this interface, and for the
  benchmark reviewer who will audit it.
