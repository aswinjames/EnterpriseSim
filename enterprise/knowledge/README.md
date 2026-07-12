# Reference Enterprise Knowledge

> The Meridian Commerce Group **Knowledge Layer** corpus — durable enterprise truth
> (`ARCH-02`). Every item is a schema-valid `KnowledgeObject` (`KN-###`) validating against
> [`../../schemas/knowledge_object.schema.json`](../../schemas/knowledge_object.schema.json).

## Contents

| Set | File | KN range | Count | Backing artifacts |
|---|---|---|---|---|
| Business rules | [`business-rules.json`](business-rules.json) | `KN-045`, `KN-052`, `KN-063`, `KN-100…146` | 50 | inline `body` |
| Architecture documents | [`architecture-docs.json`](architecture-docs.json) | `KN-200…229` | 30 | [`../architecture/AD-*.md`](../architecture/) |
| API specifications | [`api-specs.json`](api-specs.json) | `KN-250…274` | 25 | [`../api-specs/*.yaml`](../api-specs/) |
| Postmortems | [`postmortems.json`](postmortems.json) | `KN-300…314` | 15 | [`../postmortems/INC-*.md`](../postmortems/) |
| Runbooks | [`runbooks.json`](runbooks.json) | `KN-400…424` | 25 | [`../runbooks/RB-*.md`](../runbooks/) |
| **Master index** | [`index.json`](index.json) | all of the above | **145** | union of the five sets |

Each `KnowledgeObject` carries `metadata.doc_type` (`business_rule` \| `architecture` \|
`api_spec` \| `postmortem` \| `runbook`) and, for the document-backed sets, `metadata.path`
pointing at the prose/spec file. Business rules carry their rule text inline in `body`.

## Why these are Knowledge

`ARCH-02` §Purpose defines the Knowledge Layer's contents as "architecture documents,
business rules, runbooks, engineering standards, API contracts and validated post-incident
learnings." This corpus instantiates exactly that for MCG, so an Enterprise AI Worker
retrieves it through the same Knowledge Layer interface (`sdk.knowledge`) it uses for any
truth — no special-casing.

## Anchor knowledge (consistent with the frozen Foundation examples)

- **`KN-045`** Checkout domain rules — mirrors
  [`../../schemas/examples/knowledge_object.example.json`](../../schemas/examples/knowledge_object.example.json)
  (guest checkout must not create a loyalty account; payment auth precedes inventory commit;
  idempotency required). Referenced by `CTX-0118`, `PLAN-0072`, `EXP-090`.
- **`KN-052`** Order-placement idempotency standard; **`KN-063`** Promotion cache invalidation
  rule — the two rules `KN-045` depends on, and the rule behind the `INC-2026-007/011/018`
  promo-cache trio.
- **`KN-301`** Postmortem for `INC-2026-002` (guest-checkout orphaned loyalty) — the incident
  whose lesson became `EXP-090` via reflection `REF-0019` (see `ARCH-05`).
- **`KN-304/306/312`** Postmortems for the promo-cache-staleness progression that drove the
  systemic write-through fix (`ARCH-05` Example C).

## Referential integrity

- All 145 IDs are globally unique (`ADR-0022`); ranges do not overlap.
- Every postmortem `KN-3NN` matches the `postmortem` field of its `INC-2026-###` record.
- Every `metadata.path` resolves to an existing file.
- `owner_team` and `app` references resolve to CANON entities.

Validate the whole corpus:

```bash
python3 tools/refgen/validate.py knowledge_object.schema.json enterprise/knowledge/index.json
```
