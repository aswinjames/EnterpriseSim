# Plugin Guide — Packaging and Registering ECL Extensions

> How the ECL discovers and loads third-party implementations at runtime. The mechanism is
> **entry-point-based plugin registration** (`RFC-0027`), governed by the plugin architecture
> decision (`ADR-0030`). This is how an index backend, a tool, a model provider, a rubric or a
> whole Worker gets wired into the runtime **without editing the core**.

Read [`extension-guide.md`](extension-guide.md) first — it tells you *which* interface to
implement per module. This guide tells you how to **ship** that implementation.

---

## Why plugins

The SDK is interfaces only, and the core must stay closed to modification but open to extension
(`ARCH-07`: "specialize at the edges, share the core"). Plugins are the edge. A plugin is an
ordinary installable Python package that:

1. implements one or more SDK interfaces (an ABC subclass or a Protocol-satisfying class), and
2. **advertises** those implementations through Python **entry points** so the ECL runtime can
   discover and load them by name — no import of your package by the core, no registry edit.

The invariant (`ADR-0030`): **the core never imports a plugin directly.** It resolves plugins
only through the entry-point registry, which keeps model-agnosticism and domain-agnosticism
structural rather than conventional.

---

## Entry-point groups

Each extension axis has a reserved entry-point group (`RFC-0027`). Declare your implementations
under the matching group in your package metadata:

| Entry-point group | SDK interface you implement | Module |
|---|---|---|
| `enterprisesim.knowledge_index` | `KnowledgeIndex` (Protocol) | `sdk.knowledge` |
| `enterprisesim.retriever` | `Retriever` (Protocol) | `sdk.context` |
| `enterprisesim.tool` | `Tool` (Protocol) | `sdk.execution` |
| `enterprisesim.model_provider` | `ModelProvider` (Protocol) | `sdk.models` |
| `enterprisesim.rubric` | `Rubric` (ABC) | `sdk.evaluation` |
| `enterprisesim.objective_gate` | `ObjectiveGate` (Protocol) | `sdk.evaluation` |
| `enterprisesim.policy_guard` | `PolicyGuard` (ABC) | `sdk.decision` |
| `enterprisesim.worker_spec` | `WorkerSpec` provider | `sdk.workers` |

The entry-point **name** (left of `=`) is the stable identifier a `WorkerSpec` refers to (e.g. a
tool name in `WorkerSpec.tools`, a rubric id in `WorkerSpec.rubrics`). The **value** (right of
`=`) is the import path to your class or factory.

---

## Packaging (worked layout)

A minimal plugin distribution:

```
mcg-vector-plugin/
├── pyproject.toml
└── src/
    └── mcg_vector_plugin/
        ├── __init__.py
        ├── index.py        # implements KnowledgeIndex
        └── tools.py        # implements Tool
```

`pyproject.toml` declares the entry points and the SDK compatibility range:

```toml
[project]
name = "mcg-vector-plugin"
version = "1.2.0"
requires-python = ">=3.11"
dependencies = ["enterprisesim-sdk>=0.1,<0.2"]   # compatible SDK contract range (ADR-0032)

[project.entry-points."enterprisesim.knowledge_index"]
pgvector = "mcg_vector_plugin.index:PgVectorIndex"

[project.entry-points."enterprisesim.tool"]
github = "mcg_vector_plugin.tools:GitHubPRTool"
```

---

## Discovery and the plugin lifecycle

The runtime loads plugins in four phases (`RFC-0027`, `ADR-0030`):

```mermaid
sequenceDiagram
    autonumber
    participant RT as ECL Runtime
    participant EP as Entry-point registry
    participant PL as Plugin class
    participant WS as WorkerSpec
    RT->>EP: 1. DISCOVER — enumerate groups (importlib.metadata.entry_points)
    RT->>RT: 2. COMPATIBILITY — check SDK version range (ADR-0032)
    RT->>PL: 3. LOAD — import path, instantiate/adapt to interface
    RT->>RT: 3a. VALIDATE — isinstance/Protocol conformance + ToolSpec/CapabilityDescriptor
    WS->>RT: 4. BIND — WorkerRuntime.bind(spec) resolves plugins by name
    Note over RT,WS: unbound plugins stay dormant; least-privilege enforced at bind
```

1. **Discover** — enumerate installed entry points for each group.
2. **Compatibility gate** — reject a plugin whose declared SDK range excludes the running
   `sdk.__version__` / `sdk.SCHEMA_VERSION` (see Versioning below).
3. **Load & validate** — import the target, instantiate, confirm it satisfies the interface
   (ABC `isinstance` or Protocol shape) and that declared metadata (a `Tool`'s `ToolSpec`, a
   provider's `CapabilityDescriptor`) is well-formed.
4. **Bind** — `WorkerRuntime.bind(spec)` resolves only the plugins named by the `WorkerSpec`,
   applying least-privilege (`ADR-0042`): a tool not in `WorkerSpec.tools` is never available to
   that Worker even if installed.

Plugins are **dormant until bound**. Nothing installed can act on the enterprise unless a
`WorkerSpec` names it and a `PolicyGuard` allows it.

---

## Versioning & compatibility

- **SDK contract SemVer** (`ADR-0032`): `sdk.__version__` (`0.1.0`) versions the *interfaces*.
  Additive/optional changes are minor; a changed method signature or removed interface is major.
  Pin your plugin to a compatible range: `enterprisesim-sdk>=0.1,<0.2`.
- **Schema version** (`RFC-0021`): `sdk.SCHEMA_VERSION` (`2020-12.v1`) is the object-shape
  family your plugin emits. Objects your plugin produces must set `schema_version` accordingly
  and validate against [`../../schemas/`](../../schemas/) (see [`schema-guide.md`](schema-guide.md)).
- **Migration window:** during a schema migration the runtime accepts the current and previous
  major version (`ADR-0033` expand-contract); readers tolerate unknown `metadata`. Never break a
  cross-reference — that requires an ADR (`ADR-0022/0023`).

---

## Worked example 1 — a `KnowledgeIndex` backend

Implement the Protocol from `sdk.knowledge.interfaces` (signatures only — no logic here):

```python
# src/mcg_vector_plugin/index.py
from typing import Sequence
from sdk.knowledge.interfaces import KnowledgeIndex, KnowledgeQuery, KnowledgeCandidate
from sdk.objects import CanonicalId, KnowledgeObject

class PgVectorIndex:                         # satisfies the KnowledgeIndex Protocol structurally
    """Postgres + pgvector hybrid index (semantic + lexical + graph neighbors)."""

    def upsert(self, obj: KnowledgeObject) -> None:
        raise NotImplementedError            # index title/body/relations; respect immutability

    def search(self, query: KnowledgeQuery) -> Sequence[KnowledgeCandidate]:
        raise NotImplementedError            # honor query.modes ("semantic","keyword","graph")

    def neighbors(self, node: CanonicalId, relation: str) -> Sequence[CanonicalId]:
        raise NotImplementedError            # graph hop for relation-aware retrieval
```

Register it (already shown in `pyproject.toml`):

```toml
[project.entry-points."enterprisesim.knowledge_index"]
pgvector = "mcg_vector_plugin.index:PgVectorIndex"
```

After `pip install mcg-vector-plugin`, the runtime discovers `pgvector` under the
`enterprisesim.knowledge_index` group; a `KnowledgeRetriever` can then fuse over it with no core
change. Confirm the loader sees it:

```python
from importlib.metadata import entry_points
eps = entry_points(group="enterprisesim.knowledge_index")
print([ep.name for ep in eps])              # ['pgvector']
```

---

## Worked example 2 — a `Tool`

A tool is the per-Worker *tools* specialization axis. Implement the `Tool` Protocol from
`sdk.execution.interfaces`, declaring side-effects and a least-privilege scope in its `ToolSpec`:

```python
# src/mcg_vector_plugin/tools.py
from typing import Mapping
from sdk.execution.interfaces import Tool, ToolSpec, ToolResult

class GitHubPRTool:                          # satisfies the Tool Protocol
    spec = ToolSpec(
        name="github",
        description="Open and manage pull requests against mcg-* repositories.",
        input_schema={"type": "object", "required": ["repo", "title"]},
        side_effects="write",                # none | read | write | irreversible
        least_privilege_scope="repo:mcg-checkout-service:pr",   # ADR-0042
    )

    def invoke(self, args: Mapping[str, object]) -> ToolResult:
        raise NotImplementedError            # returns ToolResult(ok, output, artifacts=[PR-####], error)
```

```toml
[project.entry-points."enterprisesim.tool"]
github = "mcg_vector_plugin.tools:GitHubPRTool"
```

A Worker gets this tool only if its `WorkerSpec.tools` includes `"github"`; the `ToolRegistry`
returns it from `available(worker)` subject to policy, and `ExecutionRuntime.execute_step()`
invokes it, capturing the `WorkerArtifact` (`PR-0312`) it produces. See the `CHK-1421` flow in
[`worker-guide.md`](worker-guide.md).

---

## Checklist before you publish

- [ ] Implements the correct SDK interface; passes the runtime's conformance validation.
- [ ] Declared under the correct `enterprisesim.*` entry-point group with a stable name.
- [ ] SDK range pinned (`>=0.1,<0.2`); emitted objects set `schema_version` and validate.
- [ ] `Tool`/`ModelProvider` metadata (`ToolSpec` side-effects & scope, `CapabilityDescriptor`)
      is complete and honest — least privilege (`ADR-0042`), no hidden irreversible actions.
- [ ] No import of the ECL core internals; the core resolves you *only* via entry points.
- [ ] Tested against the `CHK-1421` example fixtures; a bound Worker runs and replays.
