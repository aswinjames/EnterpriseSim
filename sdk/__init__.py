"""EnterpriseSim SDK — the Enterprise Cognitive Layer (ECL) reference contracts.

This package defines the **abstract interfaces** for the Enterprise Cognitive Layer
described in ``docs/architecture/`` and governed by ``CANON.md`` (``CANON-001``).

It intentionally contains **no implementation**. Every class here is an abstract
interface (``abc.ABC``) or a structural type (``typing.Protocol``). Implementations
are provided by ECL runtimes and by Enterprise AI Worker authors, who plug in through
the documented extension points.

Design invariants (see ``docs/architecture/07_architecture.md``):

* The LLM is stateless; all memory and learning live in these components.
* Durable memory: :mod:`sdk.knowledge`, :mod:`sdk.experience`.
* Ephemeral memory: :mod:`sdk.context`.
* Orchestration: :mod:`sdk.decision`, :mod:`sdk.planner`.
* Judgment & improvement: :mod:`sdk.evaluation`, :mod:`sdk.learning`.
* Model access is funneled through :mod:`sdk.models` (model-agnostic).
* Workers (:mod:`sdk.workers`) specialize the shared core at four edges:
  knowledge domains, tools, rubrics, policies.

The canonical object shapes exchanged between modules are declared in
:mod:`sdk.objects` and formally specified as JSON Schema in ``schemas/``.
"""

from __future__ import annotations

__all__ = [
    "__version__",
    "SCHEMA_VERSION",
]

#: Semantic version of the SDK contracts (see ADR-0032). Independent of any runtime.
__version__ = "0.1.0"

#: Version of the object schemas in ``schemas/`` that these interfaces target
#: (see RFC-0021 Schema Versioning). Kept in lockstep with the ``$id`` versions.
SCHEMA_VERSION = "2020-12.v1"
