# EnterpriseSim Schemas

> **JSON Schema (Draft 2020-12)** contracts for every ECL object. These are the
> **authoritative shape** of the artifacts the SDK (`../sdk/`) exchanges and that Enterprise
> AI Workers produce. Governed by [`../CANON.md`](../CANON.md) and the ECL architecture
> (`ARCH-01`…`ARCH-07`).

## Contents

| Schema | `$id` (basename) | ECL object | Mirrors SDK type |
|---|---|---|---|
| [`common.schema.json`](common.schema.json) | `common` | shared `$defs` (IDs, confidence, provenance, base) | `sdk.objects` aliases |
| [`knowledge_object.schema.json`](knowledge_object.schema.json) | `knowledge_object` | `KnowledgeObject` (`KN-###`) | `sdk.objects.KnowledgeObject` |
| [`context_object.schema.json`](context_object.schema.json) | `context_object` | `ContextObject` (`CTX-###`) | `sdk.objects.ContextObject` |
| [`planning_object.schema.json`](planning_object.schema.json) | `planning_object` | `PlanningObject` (`PLAN-###`) | `sdk.objects.PlanningObject` |
| [`decision_object.schema.json`](decision_object.schema.json) | `decision_object` | `DecisionObject` | `sdk.objects.DecisionObject` |
| [`execution_object.schema.json`](execution_object.schema.json) | `execution_object` | `ExecutionObject` | `sdk.objects.ExecutionObject` |
| [`evaluation_object.schema.json`](evaluation_object.schema.json) | `evaluation_object` | `EvaluationObject` (`EVAL-###`) | `sdk.objects.EvaluationObject` |
| [`reflection_object.schema.json`](reflection_object.schema.json) | `reflection_object` | `ReflectionObject` (`REF-###`) | `sdk.objects.ReflectionObject` |
| [`experience_object.schema.json`](experience_object.schema.json) | `experience_object` | `ExperienceObject` (`EXP-###`) | `sdk.objects.ExperienceObject` |
| [`learning_event.schema.json`](learning_event.schema.json) | `learning_event` | `LearningEvent` | `sdk.objects.LearningEvent` |
| [`worker_decision.schema.json`](worker_decision.schema.json) | `worker_decision` | `WorkerDecision` | `sdk.objects.WorkerDecision` |
| [`worker_execution.schema.json`](worker_execution.schema.json) | `worker_execution` | `WorkerExecution` | `sdk.objects.WorkerExecution` |
| [`worker_artifact.schema.json`](worker_artifact.schema.json) | `worker_artifact` | `WorkerArtifact` | `sdk.objects.WorkerArtifact` |

Worked, cross-referenced instances live in [`examples/`](examples/).

## Validation

- All schemas are **Draft 2020-12**. Each object schema composes the shared base via
  `allOf: [{ "$ref": "common.schema.json#/$defs/eclObjectBase" }]` and closes the object with
  **`unevaluatedProperties: false`** — this correctly forbids stray fields while still
  allowing the inherited base fields (`additionalProperties: false` cannot see across `allOf`;
  `unevaluatedProperties` can).
- IDs are constrained by canonical patterns in `common.schema.json` (`CANON-001` §6). The
  `canonicalId` pattern also admits Jira project-key issue references (e.g. `CHK-1421`) per
  `CANON-001` §5.
- **Validate with any Draft 2020-12 validator.** Load all schemas into a registry keyed by
  `$id` so relative `$ref`s resolve. Example (Python, `jsonschema >= 4.18` + `referencing`):

  ```python
  import json, glob
  from referencing import Registry, Resource
  from jsonschema import Draft202012Validator

  resources = []
  for path in glob.glob("schemas/*.schema.json"):
      doc = json.load(open(path))
      resources.append((doc["$id"], Resource.from_contents(doc)))
  registry = Registry().with_resources(resources)

  schema = json.load(open("schemas/context_object.schema.json"))
  instance = json.load(open("schemas/examples/context_object.example.json"))
  Draft202012Validator(schema, registry=registry).validate(instance)
  ```

  A dependency-free structural validator is also kept in the test suite for CI environments
  without network access.

## Relationships

Objects reference one another **by canonical ID**, preserving referential integrity
(`ADR-0023`). The `CHK-1421` example set demonstrates a full loop:

```
KN-045 ──cited by──▶ CTX-0118 ──intent_ref──▶ PLAN-0072
  ▲                     ▲                          │
  │ promoted_from       │ applied_experience        │ executed as
  │                     │                           ▼
EXP-090 ◀─create_experience─ REF-0019 ◀─reflects── EVAL-0061 ◀─scores── PR-0312
   │                                                   ▲
   └──────────── prevented_regressions ────────────────┘
```

- `ContextObject.included[].source` → `KN-###` / `EXP-###` (provenance).
- `PlanningObject.applied_experience` → `EXP-###`.
- `EvaluationObject.execution` → `PR-####`; `.plan` → `PLAN-###`; `.regression_check.checked_against` → `EXP-###`.
- `ReflectionObject` → `EVAL-###`, `PLAN-###`, execution; `.lessons[].create_experience` → `EXP-###`.
- `ExperienceObject.evidence` → origin execution, `EVAL-###`, `REF-###`; `.promoted_to_knowledge` → `KN-###`.
- `LearningEvent.source_reflection` → `REF-###`; `.target` → the `KN`/`EXP`/policy affected.

## Metadata

- Every object carries `id`, `schema_version` (`^2020-12\.v\d+$`) and `created_at`, plus an
  open `metadata` object for additive, non-semantic annotations (never used to carry required
  meaning). `metadata` is the sanctioned place for extension fields so that core validation
  stays strict.

## Examples

See [`examples/`](examples/): `knowledge_object`, `context_object`, `planning_object`,
`evaluation_object`, `reflection_object`, `experience_object` — all mutually consistent and
all passing validation.

## Migration strategy

Schema evolution follows `RFC-0021` (Schema Versioning) and `ADR-0033` (expand-contract):

1. **Versioning.** The schema family carries a version (`2020-12.v1`, `.v2`, …) surfaced in
   every instance's `schema_version` and tracked by `sdk.SCHEMA_VERSION`. SemVer semantics
   (`ADR-0032`): additive/optional changes are minor; required-field or type changes are major.
2. **Expand → migrate → contract.** Add new optional fields first (expand); dual-write and
   backfill; only later make them required or remove old fields (contract) once no producer
   emits the old shape. Instances are never rewritten in place; new versions are new records.
3. **Backward compatibility window.** Validators accept the current and previous major schema
   version during a migration window; readers tolerate unknown `metadata`.
4. **Referential integrity is invariant.** IDs never change meaning across versions
   (`ADR-0022`); cross-references remain resolvable. A migration that would break a reference
   requires an ADR.
5. **Provenance of change.** Every schema change is recorded via an RFC (contract change) and,
   where it alters an invariant, an ADR — consistent with canon supremacy (`ADR-0050`).
