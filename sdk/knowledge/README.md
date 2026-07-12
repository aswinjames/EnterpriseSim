# `sdk.knowledge` — Knowledge Layer

Interfaces for durable, governed enterprise truth. Realizes **Knowledge** (`CANON-001` §9,
Stage 1) per [`ARCH-02`](../../docs/architecture/02_knowledge_layer.md). No implementation.

## Architecture

The Knowledge Layer is the system of record for `KnowledgeObject` (`KN-###`) — architecture
docs, business rules, runbooks, standards, API contracts and validated learnings. Knowledge
is **immutable once published** (`ADR-0004`): new facts are new versions; deprecation retains
history. Retrieval is **hybrid** — semantic + keyword + graph (`ADR-0019`, `RFC-0005/0006`) —
behind a pluggable `KnowledgeIndex`. A `KnowledgeGovernance` gate guards what becomes truth,
including experience promoted by the Learning Engine (`RFC-0018`).

## Python abstract interfaces

See [`interfaces.py`](interfaces.py):

- `KnowledgeStore` — get / publish / deprecate / staleness (system of record).
- `KnowledgeRetriever` — serve ranked `KnowledgeCandidate`s to the Context Layer.
- `KnowledgeIndex` (Protocol) — pluggable vector/lexical/graph backend.
- `KnowledgeGovernance` — review drafts, resolve contradictions.

## Extension points

- **Index backends.** Implement `KnowledgeIndex` for your vector DB, search engine and graph
  store; register via plugin entry points (`RFC-0027`).
- **Retrieval strategy.** Subclass `KnowledgeRetriever` to change ranking/fusion; the Learning
  Engine may tune this via policy updates.
- **Governance.** Implement `KnowledgeGovernance` to encode your approval workflow.

## Responsibilities

Store truth, govern quality, index for hybrid retrieval, serve scored candidates, track
freshness/lineage, absorb promoted experience, enforce sensitivity classification.

## Examples

```python
from sdk.knowledge.interfaces import KnowledgeQuery, KnowledgeRetriever

def gather(retriever: KnowledgeRetriever) -> None:
    q = KnowledgeQuery(text="checkout order-placement invariants",
                       filters={"app": "APP-003", "sensitivity": "internal"})
    for cand in retriever.retrieve(q):
        print(cand.object.id, cand.relevance, cand.authority, cand.freshness)
```

## Future evolution

Active curation by Workers, graph-native multi-hop reasoning, automated freshness from data
lineage, federated per-domain stores, and confidence-calibrated retrieval (see `ARCH-02`
§Future Evolution and `RFC-0006`).
