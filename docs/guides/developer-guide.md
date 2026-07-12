# Developer Guide — Onboarding to EnterpriseSim

> The front door. Read this first, then branch out to the specialized guides. It assumes you
> are a senior Python engineer or Worker author who has never seen this repository before.

EnterpriseSim is an open-source project with two halves that stay strictly separated:

- **The enterprise** — *Meridian Commerce Group (MCG)*, a fictional Fortune 500 omnichannel
  retailer defined once and for all in [`../../CANON.md`](../../CANON.md) (`CANON-001`). MCG is
  a realistic software-engineering organization (services, Jira, GitHub, TestRail, incidents)
  that generates believable engineering work. It is the *backdrop*, not the subject.
- **The intelligence** — the *Enterprise Cognitive Layer (ECL)*, a reusable architecture that
  every **Enterprise AI Worker** runs on. It is model-agnostic and domain-agnostic, shipped
  here as an **interfaces-only Python SDK** ([`../../sdk/`](../../sdk/)) plus **JSON Schemas**
  ([`../../schemas/`](../../schemas/)).

> EnterpriseSim provides the enterprise; the ECL provides the intelligence. Keep that line
> clear and everything else falls into place.

The project's purpose is to **build, evaluate and benchmark** Enterprise AI Workers doing real
engineering tasks against MCG. This guide gets you oriented; the others go deep.

---

## The mental model: a stateless LLM wrapped in durable memory

The single founding constraint of the whole architecture (`ARCH-07`) is:

> **The LLM is stateless.** It has no memory, no enterprise knowledge, no accumulated
> experience, and cannot improve itself between calls.

So everything that makes a Worker *enterprise-grade* lives **outside the model**, in the ECL:

| Where "smarts" live | Component | Nature |
|---|---|---|
| What is true about MCG | Knowledge Layer (`sdk.knowledge`) | Durable memory |
| What MCG has learned by doing | Experience Layer (`sdk.experience`) | Durable memory |
| What this one task needs, right now | Context Layer (`sdk.context`) | Ephemeral memory |
| What to do and in what order | Planning (`sdk.planner`) | Per-task artifact |
| Interpreting, orchestrating, gating autonomy | Decision Intelligence (`sdk.decision`) | The orchestrator |
| Acting on the enterprise via tools | Execution Runtime (`sdk.execution`) | Side effects |
| Judging the work objectively | Evaluation Layer (`sdk.evaluation`) | Judgment |
| Explaining *why* and improving | Learning Engine (`sdk.learning`) | Improvement |
| The only place a provider SDK is imported | Model Gateway (`sdk.models`) | Model-agnostic seam |

Two consequences fall out of "the improvement is data, not weights":

1. **Model-agnostic.** Swap OpenAI, Anthropic, Gemini, an open-source model, or a local SLM by
   changing one adapter in `sdk.models`. Every lesson MCG ever learned still applies.
2. **Domain-agnostic.** A new Worker type (QA, Finance, Privacy, Support, …) is *not* new
   architecture — it is four bindings (knowledge domains, tools, rubrics, policies) over the
   same shared core.

---

## The ECL loop

Every task traverses one loop, and every loop leaves durable memory richer than it found it:

```
Knowledge → Context → Planning → Decision Intelligence → Execution
     ↑                                                       │
     └── Learning ← Experience ← Reflection ← Evaluation ←───┘
```

`CANON-001` §9 names nine concepts (Knowledge, Context, Planning, Decision Intelligence,
Execution, Evaluation, Reflection, Experience, Continuous Improvement). The ECL realizes them
across **six components** plus the Model Gateway. The authoritative mapping lives in `ARCH-07`;
a newcomer-friendly narrative is in [`architecture-guide.md`](architecture-guide.md).

---

## Repository tour

```
EnterpriseSim/
├── CANON.md                     # CANON-001: the immutable MCG enterprise + conventions
├── docs/
│   ├── architecture/            # ARCH-01..07: the permanent ECL architecture (depth)
│   │   ├── README.md            #   reading order + the loop
│   │   ├── 01_context_layer.md  #   one file per component
│   │   ├── ...                  #   02 knowledge, 03 experience, 04 evaluation,
│   │   └── 07_architecture.md   #   05 learning, 06 decision intelligence
│   │                            #   07 = master (read first)
│   ├── adr/                     # ADR-####: immutable decision records (Nygard format)
│   ├── rfcs/                    # RFC-####: cross-team proposals (contracts)
│   └── guides/                  # ← YOU ARE HERE (developer-facing how-to)
├── sdk/                         # interfaces-only Python SDK — the abstract contract layer
│   ├── objects.py               #   canonical object Protocols (mirror the schemas)
│   ├── __init__.py              #   __version__, SCHEMA_VERSION
│   ├── knowledge/  context/  planner/  decision/  execution/
│   ├── evaluation/ experience/ learning/ models/  workers/
│   │     └── each: interfaces.py + README.md
├── schemas/                     # JSON Schema (Draft 2020-12) for every ECL object
│   ├── common.schema.json       #   shared $defs (IDs, confidence, provenance, base)
│   ├── *_object.schema.json     #   one per object type
│   └── examples/                #   worked, cross-referenced CHK-1421 instances
└── benchmarks/                  # benchmark suites (Evaluation is the substrate)
```

**Where the source of truth lives, in priority order:** `CANON.md` (`CANON-001`) wins over
everything; the frozen architecture (`ARCH-01`…`ARCH-07`) wins over the SDK; the JSON Schemas
are the source of truth for object *shape*; the Protocols in `sdk/objects.py` are the typing
surface that mirrors them.

---

## Prerequisites

- **Python 3.11+.** The SDK uses `from __future__ import annotations`, `abc.ABC`,
  `typing.Protocol` and `enum.Enum`. It has **no runtime dependencies** — it is interfaces
  only, every method body is `...`.
- To *validate* schema instances: a Draft 2020-12 validator. The recommended stack is
  `jsonschema >= 4.18` + `referencing` (see [`schema-guide.md`](schema-guide.md)). A
  dependency-free structural validator is also kept in the test suite for offline CI.
- Comfort with retrieval-augmented systems, JSON Schema, and abstract-base-class design.

```python
# The SDK imports cleanly with no third-party packages installed:
import sdk
print(sdk.__version__)       # 0.1.0   (contract SemVer, ADR-0032)
print(sdk.SCHEMA_VERSION)    # 2020-12.v1  (schema family this SDK targets, RFC-0021)
```

---

## How the pieces fit (one composition)

A single task composes the modules like this (from [`../../sdk/README.md`](../../sdk/README.md)):

```
workers.Worker.run(trigger)
   └─ decision.Orchestrator             # interpret intent, drive the loop
        ├─ context.ContextAssembler     # assemble CTX-### from knowledge + experience + state
        │     ├─ knowledge.KnowledgeRetriever
        │     └─ experience.ExperienceRetriever
        ├─ planner.Planner              # produce PLAN-###
        ├─ models.ModelGateway          # route reasoning to a provider (agnostic)
        ├─ execution.ExecutionRuntime   # act via tools -> WorkerArtifact(s)
        ├─ evaluation.Evaluator         # score -> EVAL-###
        └─ learning.LearningEngine      # reflect -> REF-###, EXP-###, LearningEvent(s)
```

Each arrow exchanges a **canonical object** (`sdk.objects`), and each object is specified as a
JSON Schema. Objects reference one another **by canonical ID** — this referential integrity
(`ADR-0023`) is the backbone of the whole system.

---

## Walk through one task end to end — `CHK-1421`

`CHK-1421` is the repository's running example: a Jira story to add **guest checkout** to the
Checkout Service (`APP-003`) *without* creating a Loyalty (`APP-015`) account. The worked
object instances live in [`../../schemas/examples/`](../../schemas/examples/). Follow the loop:

1. **Trigger → intent.** `CHK-1421` arrives at `decision.Orchestrator.interpret(...)`, which
   produces a `TaskIntent` (goal, constraints, success criteria, apps `[APP-003]`).
2. **Context assembly (`CTX-0118`).** `context.ContextAssembler.assemble(...)` pulls candidates
   from `knowledge.KnowledgeRetriever` and `experience.ExperienceRetriever`. It selects
   `KN-045` (checkout invariants), `KN-052` (idempotency), and **`EXP-090`** — the lesson from
   a *prior failure* that guests must not get loyalty accounts. It records what it **included**
   and **excluded** (with a dropped-candidate log) and a `coverage_confidence` of `0.86`.
   → [`context_object.example.json`](../../schemas/examples/context_object.example.json)
3. **Plan (`PLAN-0072`).** `planner.Planner.plan(...)` emits ordered steps, success criteria, a
   **negative test** (`GuestNoLoyaltyTest`), a **feature-flag rollback**, and `risk_tier: 0`.
   `planner.PlanValidator.validate(...)` confirms rollback present, dependency direction
   respected, and (per `CANON-001` §7) two approvals required for a Tier 0 change.
   → [`planning_object.example.json`](../../schemas/examples/planning_object.example.json)
4. **Route + execute (`PR-0312`).** `models.ModelGateway.call(...)` routes reasoning to a
   high-reasoning model. `execution.ExecutionRuntime.execute_step(...)` acts via `Tool`s: opens
   `PR-0312` against `mcg-checkout-service`, adds the test, runs `TR-0442`/`TR-0443`.
5. **Evaluate (`EVAL-0061`).** `evaluation.Evaluator.evaluate(...)` scores objective gates
   first (tests, coverage `0.84 ≥ 0.80`, dependency rule) then rubric items, with linked
   evidence and **dual confidence** — verdict `pass`, score `0.91`.
   → [`evaluation_object.example.json`](../../schemas/examples/evaluation_object.example.json)
6. **Reflect + learn.** The *earlier* failure produced `REF-0019` and `EXP-090`. This success
   **closes that loop** (`learning.LearningEngine.loop_closed(...)` → true), reinforces
   `EXP-090`, and makes it a promotion candidate into `KN-045`.
   → [`reflection_object.example.json`](../../schemas/examples/reflection_object.example.json),
   [`experience_object.example.json`](../../schemas/examples/experience_object.example.json)
7. **Baseline raised.** The next guest-flow task starts smarter — with the *same* stateless
   model.

That is the entire flywheel `CANON-001` §9 describes, made concrete and inspectable.

---

## Where to go next

| If you want to… | Read |
|---|---|
| Understand the ECL as a system | [`architecture-guide.md`](architecture-guide.md) |
| Implement or replace a layer | [`extension-guide.md`](extension-guide.md) |
| Package a backend or tool as a plugin | [`plugin-guide.md`](plugin-guide.md) |
| Build a brand-new Enterprise AI Worker | [`worker-guide.md`](worker-guide.md) |
| Validate, author or migrate JSON objects | [`schema-guide.md`](schema-guide.md) |
| The immutable truth about MCG | [`../../CANON.md`](../../CANON.md) (`CANON-001`) |
| The permanent architecture, in depth | [`../architecture/`](../architecture/) (`ARCH-01`…`07`) |

**Golden rules for every contributor:** keep the model stateless and swappable; durable vs.
ephemeral memory is sacred (Knowledge/Experience persist, Context never does); specialize at
the edges and share the core; and if you cannot trace it or score it, it does not belong in the
ECL.
