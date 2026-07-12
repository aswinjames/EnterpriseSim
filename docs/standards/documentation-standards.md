# Documentation Standards

> How EnterpriseSim documents itself. Instantiates `CANON-001` **§4.7 (Documentation)** and
> the ADR discipline established by `ADR-0001`. Documentation is a **deliverable of every
> change, not an afterthought** (CANON §4.7).

EnterpriseSim is a public benchmark; its reasoning must be as inspectable as the artifacts it
asks Workers to produce (`ADR-0001` rationale). Documentation is how that reasoning stays
durable, greppable and onboarding-friendly.

## 1. Docs live with the code

- Documentation lives **in the repository**, beside what it describes (CANON §4.7). No wiki,
  no external doc site as the source of truth.
- Layout (see [`repository-conventions.md`](repository-conventions.md)):
  `docs/architecture/` (ARCH-*), `docs/adr/`, `docs/rfcs/`, `docs/guides/`,
  `docs/standards/` (this set), plus a `README.md` in every `sdk/<layer>/` package.
- A change that alters behavior, shape or a decision updates the relevant docs **in the same
  PR**. "Docs to follow" is not accepted (review-process.md checklist blocks it).

## 2. README requirements

Every `sdk/<layer>/` package README follows the shape the layer READMEs already use
(e.g. `sdk/knowledge/README.md`). Required sections:

1. **Title + one-line purpose** naming the ECL stage and its `CANON-001` §9 concept.
2. **Architecture** — what the layer owns, its object type (`KN-###`, `CTX-###`, …), and the
   `ARCH-`/`ADR-`/`RFC-` IDs that govern it.
3. **Python abstract interfaces** — the ABCs/Protocols in `interfaces.py`, one line each.
4. **Extension points** — what implementers subclass/register, and how (`RFC-0027` entry
   points).
5. **Responsibilities** — the layer's job in one paragraph.
6. **Examples** — a short, valid snippet.

The repo root `README.md` orients newcomers and links to CANON, the architecture reading
order, and `docs/standards/`.

## 3. ADRs — recording decisions

Per `ADR-0001`, every architecturally significant decision is an **Architecture Decision
Record** in strict **Michael Nygard format**:

- One decision per file at `docs/adr/ADR-000N.md`, zero-padded to 4 digits, numbered globally,
  **never reused** (`ADR-0022`).
- Sections: a metadata header (`Status`, `Date`, `Deciders`, `Related`) then
  **Context / Decision / Consequences** (with Consequences split into Positive / Negative /
  Neutral, as `ADR-0001` itself does).
- An **Accepted ADR is immutable**: never edit a decision in place; supersede it with a new
  ADR and update the old one's `Status: Superseded by ADR-####`. This preserves the decision
  history.
- Every ADR cites the `CANON-`, `ARCH-`, `RFC-` and prior `ADR-` IDs it depends on, so the
  decision graph is navigable.
- **Authored and owned by the Architecture Office** (`TEAM-090`); significance is their
  judgment call (`ADR-0001` Consequences).

## 4. RFCs — proposing contract & cross-team changes

- An **RFC** (`docs/rfcs/RFC-000N.md`, same numbering discipline) is used for contract changes
  and cross-team proposals *before* they land — e.g. a schema evolution (`RFC-0021`), a new
  extension mechanism (`RFC-0027`), a retrieval strategy (`RFC-0005/0006`).
- RFC → ADR relationship: an **RFC proposes and details**; where the change alters an
  invariant it is accompanied by an **ADR that records the decision** (`ADR-0001`,
  `schemas/README.md` migration step 5). Contract change ⇒ RFC; invariant change ⇒ RFC + ADR.
- Suggested RFC sections: Summary, Motivation, Proposal (with schema/interface deltas),
  Alternatives, Compatibility & Migration (tie to [`versioning.md`](versioning.md)),
  Drawbacks, Open Questions.
- See [`contribution-guidelines.md`](contribution-guidelines.md) for when a contributor must
  open an RFC versus a plain PR.

## 5. Diagrams — Mermaid

- Diagrams are **Mermaid fenced code blocks** committed inline in Markdown, so they diff and
  render on the hosting platform — matching the architecture docs' convention (component,
  sequence, lifecycle, deployment; see `docs/architecture/README.md`).
- Do not commit binary image exports as the source of a diagram; the Mermaid source is the
  artifact. ASCII diagrams (as in CANON §2.1 and the SDK compose diagram) are acceptable for
  simple trees/flows.
- Keep one idea per diagram; label nodes with canonical IDs where they represent artifacts
  (`KN-045`, `PLAN-0072`).

## 6. Docstring ↔ doc ↔ schema consistency

The same fact must not disagree across surfaces:

- A method's **docstring** matches its **signature** and the **rule it cites** (an ADR/RFC).
- An object **Protocol** in `sdk/objects.py` matches its **JSON Schema** in `schemas/`
  (enforced by the contract-parity test, [`testing-standards.md`](testing-standards.md) §3).
- A **README's** interface list matches the actual ABCs/Protocols in `interfaces.py`.
- When any one changes, the others change in the same PR. Reviewers verify this
  (review-process.md checklist).

## 7. Changelog discipline

- The repo maintains a root `CHANGELOG.md` in **Keep a Changelog** style, with entries under
  `Added / Changed / Deprecated / Removed / Fixed / Security`.
- Every release tags a changelog section keyed to the SemVer version (`ADR-0032`) and the
  `SCHEMA_VERSION` it targets. See [`release-strategy.md`](release-strategy.md) and
  [`versioning.md`](versioning.md).
- **Breaking changes are called out explicitly**, reference the RFC/ADR that authorized them,
  and state the migration path and compatibility window.
- Deprecations are announced in the changelog *before* removal, one entry when deprecated and
  one when removed (versioning.md deprecation policy).

## 8. Writing style

- Precise, concise, imperative. American English. RFC-2119 keywords (MUST/SHOULD/MAY) carry
  their normative force.
- **Reference by canonical ID**, always (`APP-003`, `TEAM-004`, `ADR-0032`) — never a vague
  "the pricing service" where an ID exists (CANON §6 cross-referencing rule).
- Synthetic, original content only; MCG is fictional and every example must stay
  CANON-consistent (hard constraint — see contribution-guidelines.md).
- Kebab-case filenames for docs; fenced code blocks for every command, config fragment and
  signature.
