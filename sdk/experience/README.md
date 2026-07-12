# `sdk.experience` — Experience Layer

Interfaces for accumulated, situation-linked lessons. Realizes **Experience** (`CANON-001`
§9, Stage 7) per [`ARCH-03`](../../docs/architecture/03_experience_layer.md). No implementation.

## Architecture

The Experience Layer is **append-only** (`ADR-0005`): `ExperienceObject`s (`EXP-###`) are
distilled by the Learning Engine from reflections and retrieved back into context assembly,
closing the improvement loop. Lessons are matched by **structural** situation similarity (same
app + failure class), not just semantics, guarding against overfitting. Contradicted lessons
are **down-weighted, never deleted** (`ADR-0047`). High-value, repeatedly-corroborated lessons
become promotion candidates for the Knowledge Layer (`RFC-0018`). Experience retrieval is
specified in `RFC-0004`.

## Python abstract interfaces

See [`interfaces.py`](interfaces.py): `ExperienceStore` (append / reinforce / downweight /
promotion_candidates), `ExperienceRetriever` (retrieve), and the `SituationDescriptor` /
`ExperienceMatch` value types.

## Extension points

- **Store backend.** Implement `ExperienceStore` over your durable store + vector index.
- **Retrieval.** Subclass `ExperienceRetriever` to change applicability/value ranking.
- **Decay models.** Provide domain-specific down-weighting policies.

## Responsibilities

Persist lessons with lineage, preserve traceability, index for situational retrieval, score
applicability + value, accumulate monotonically, surface promotion candidates, decay
gracefully.

## Examples

```python
from sdk.experience.interfaces import ExperienceRetriever, SituationDescriptor

def recall(retriever: ExperienceRetriever) -> None:
    sit = SituationDescriptor(task_type="feature_change", apps=["APP-003", "APP-015"],
                              failure_class="unintended_side_effect")
    for m in retriever.retrieve(sit):
        print(m.object.id, m.applicability, m.value)
```

## Future evolution

Counterfactual experiences, cross-domain transfer, experience clustering into playbooks,
principled decay models, and value-weighted retrieval (see `ARCH-03` §Future Evolution).
