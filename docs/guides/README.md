# EnterpriseSim Guides

> Developer-facing, how-to documentation for **EnterpriseSim**. These guides orient and explain;
> the authoritative sources remain [`../../CANON.md`](../../CANON.md) (`CANON-001`), the frozen
> architecture in [`../architecture/`](../architecture/) (`ARCH-01`…`ARCH-07`), the
> interfaces-only SDK in [`../../sdk/`](../../sdk/), and the JSON Schemas in
> [`../../schemas/`](../../schemas/). Nothing here contradicts those.

EnterpriseSim defines **Meridian Commerce Group (MCG)** — a fictional Fortune 500 omnichannel
retailer (`CANON-001`) — and the **Enterprise Cognitive Layer (ECL)**, the model-agnostic,
domain-agnostic intelligence architecture that every Enterprise AI Worker runs on. The founding
idea: the LLM is stateless, so all memory, knowledge, orchestration and learning live *outside*
the model, in the ECL.

## Start here

New to the project? Read [`developer-guide.md`](developer-guide.md) first — it is the front door.

## The guides

| Guide | Read it when you want to… |
|---|---|
| [`developer-guide.md`](developer-guide.md) | Onboard: the mental model, repo tour, prerequisites, and one task (`CHK-1421`) walked end to end. **Start here.** |
| [`architecture-guide.md`](architecture-guide.md) | Understand the ECL as a system: the six components + Model Gateway, the loop, durable vs. ephemeral memory, composable confidence, and how model-/domain-agnosticism are structural. |
| [`extension-guide.md`](extension-guide.md) | Implement or replace a layer: which abstract interface to implement per module, the contracts to honor, and how to test against the schemas. |
| [`plugin-guide.md`](plugin-guide.md) | Package and register an extension: entry-point groups, plugin lifecycle, versioning, and worked `KnowledgeIndex` and `Tool` examples (`RFC-0027`, `ADR-0030`). |
| [`worker-guide.md`](worker-guide.md) | Build a new Enterprise AI Worker: the four specialization axes, authoring a `WorkerSpec`, wiring via `WorkerRuntime`, running/replaying, and a full new Support Worker (`ADR-0024/0025`, `RFC-0019/0024`). |
| [`schema-guide.md`](schema-guide.md) | Use and validate the JSON Schemas: the object model, referential integrity, Draft 2020-12 validation via a `$id` registry, authoring objects, and expand-contract migration (`RFC-0021`, `ADR-0033`). |

## The running example

Every guide reuses the same task — **`CHK-1421`**, guest checkout on the Checkout Service
(`APP-003`) without creating a Loyalty account (`APP-015`). Its worked object instances
(`KN-045`, `CTX-0118`, `PLAN-0072`, `PR-0312`, `EVAL-0061`, `REF-0019`, `EXP-090`) live in
[`../../schemas/examples/`](../../schemas/examples/) and demonstrate the full ECL loop and its
referential integrity.

## How these relate to the authoritative sources

```
CANON-001  ─┐  (the enterprise + conventions — wins over everything)
ARCH-01..07 ┤  (the permanent ECL architecture — depth)
sdk/        ┤  (the abstract contracts you build against — interfaces only)
schemas/    ┘  (the authoritative object shapes)
      │
      ▼
docs/guides/   (this folder — orientation and how-to over the above)
```

If a guide ever seems to conflict with `CANON-001` or the architecture, the authoritative source
wins — please open an issue.

## Conventions used across the guides

- **Canonical IDs** — artifacts are referred to by their canonical ID (`KN-###`, `CTX-###`,
  `PLAN-###`, `EVAL-###`, `REF-###`, `EXP-###`, `PR-####`, `TR-####`, `APP-###`, `TEAM-###`),
  and decisions/proposals by `ADR-####` / `RFC-####`. These follow `CANON-001` §5–§6.
- **SDK references** — module paths (`sdk.knowledge`, `sdk.context`, …) and interface names
  (`KnowledgeStore`, `ContextAssembler`, `Orchestrator`, `Evaluator`, `WorkerSpec`, …) refer to
  the real, interfaces-only definitions in [`../../sdk/`](../../sdk/). Every code snippet shows
  *signatures only* — bodies are `...` or `raise NotImplementedError`, matching the SDK's
  no-implementation contract.
- **Schema references** — object shapes point at the Draft 2020-12 files in
  [`../../schemas/`](../../schemas/), keyed by their `$id` basename.

## Suggested reading paths

- **New contributor:** developer → architecture → schema.
- **Implementing a layer:** architecture → extension → plugin → schema.
- **Building a Worker:** developer → worker → plugin.
