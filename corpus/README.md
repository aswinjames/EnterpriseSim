# EnterpriseSim Learning Corpus

> 100 complete **Enterprise Worker executions** — the reference record of the ECL lifecycle
> running against the Meridian Commerce Group enterprise, showing a Worker that **learns and
> improves over time**. Each execution is a schema-valid `WorkerExecutionBundle`.

## What each execution contains

Every [`executions/RUN-00NN.json`](executions/) bundle is one full pass of the
`CANON-001` §9 / `ARCH-07` loop for a single task:

```
knowledge_retrieved → context → experience_retrieved → decision → plan →
execution → evaluation → reflection → experience_update      (+ evolving confidence)
```

Each stage is a schema-valid ECL object embedded in the bundle and validated against the
frozen schemas:

| Field | Schema |
|---|---|
| `context` | [`context_object.schema.json`](../schemas/context_object.schema.json) (`CTX-###`) |
| `decision` | [`worker_decision.schema.json`](../schemas/worker_decision.schema.json) (`DEC-####`) |
| `plan` | [`planning_object.schema.json`](../schemas/planning_object.schema.json) (`PLAN-###`) |
| `execution` | [`worker_execution.schema.json`](../schemas/worker_execution.schema.json) (`EXE-####`) + artifacts |
| `evaluation` | [`evaluation_object.schema.json`](../schemas/evaluation_object.schema.json) (`EVAL-###`) |
| `reflection` | [`reflection_object.schema.json`](../schemas/reflection_object.schema.json) (`REF-###`) |
| bundle wrapper | [`schemas/worker_execution_bundle.schema.json`](schemas/worker_execution_bundle.schema.json) (`RUN-####`) |

The `RUN`/`DEC`/`EXE` ID namespaces were added by [`ADR-0051`](../docs/adr/ADR-0051.md)
(expand-only) — canon evolving through a recorded decision, exactly as `ADR-0050` prescribes.

## Learning over time

The 100 runs are grouped into **13 recurring task families** (guest-checkout, promo-cache,
pricing-regional, payments-3ds, inventory-atp, search-relevance, gateway-ratelimit,
order-saga, cart-resilience, returns-portal, checkout-latency, catalog-freshness,
test-authoring). Within each family the Worker **visibly improves**:

- The **first** run in a family is a cold start: no prior experience, thinner context, and it
  typically **fails** — producing a reflection that **creates** an `ExperienceObject`.
- **Later** runs **retrieve** that experience (and reference prior runs via
  `prior_executions`), so context coverage, fused confidence and evaluation scores **rise**
  and outcomes move to **pass**. Reflection policy updates influence subsequent planning.

Measured across the corpus: every one of the 13 families ends at higher fused confidence than
it started (~0.58 → ~0.93), first-run outcome `fail` → last-run outcome `pass`. Aggregate
outcomes: 62 pass / 25 partial / 13 fail. The accumulating lessons live in
[`experience_store.json`](experience_store.json) (13 experiences, values growing as they are
reinforced). A per-run summary is in [`index.json`](index.json).

## Anchored to the Foundation examples

`RUN-0001` and `RUN-0002` reproduce the canonical guest-checkout loop using the **exact**
frozen example objects, tying the corpus to `schemas/examples/` and the ECL docs:

- **`RUN-0001`** (cold start, **fail**): context `CTX-0091` (loyalty rules dropped for
  budget), plan `PLAN-0051`, execution `PR-0207`, evaluation `EVAL-0044`, reflection
  `REF-0019` → **creates `EXP-090`**. Corresponds to `INC-2026-002` and its postmortem `KN-301`.
- **`RUN-0002`** (**pass**, loop closed): retrieves `EXP-090`; context `CTX-0118`, plan
  `PLAN-0072` (applies `EXP-090`, adds `GuestNoLoyaltyTest`), execution `PR-0312`, evaluation
  `EVAL-0061` (0.91) → **reinforces `EXP-090`**. Matches `ARCH-05` Examples A/B.

## Reproduce & validate

```bash
python3 tools/refgen/generate_corpus.py                       # deterministic (seeded)
for f in corpus/executions/RUN-*.json; do \
  python3 tools/refgen/validate.py worker_execution_bundle.schema.json "$f"; done
python3 tools/refgen/validate.py experience_object.schema.json corpus/experience_store.json
```

All 100 bundles validate (which transitively validates every embedded ECL object); all
`prior_executions`, `experience_retrieved`, `knowledge_retrieved` and task references resolve.
