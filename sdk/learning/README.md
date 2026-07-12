# `sdk.learning` — Learning Engine

Interfaces for reflection and learning. Realizes **Reflection** and **Learning** (`CANON-001`
§9, Stages 6 & 8) per [`ARCH-05`](../../docs/architecture/05_learning_engine.md). No
implementation.

## Architecture

The Learning Engine turns evaluated outcomes into improvement — **outside the model**
(`ADR-0003`; no fine-tuning). A `Reflector` produces root-cause `ReflectionObject`s (`REF-###`)
grounded in evaluation evidence and the context provenance (always inspecting the
dropped-candidate log first). The engine then `distill()`s reusable `ExperienceObject`s,
`emit()`s `LearningEvent`s (experience written, promotion proposed, policy updated, pattern
detected), and tracks **loop closure** — the definition of learning (`ADR-0034`): a lesson
that never changes a later execution is not learning. Promotion to Knowledge is governed and
requires corroboration (`ADR-0036`, `RFC-0018`). The reflection pipeline is specified in
`RFC-0016`; learning-event propagation in `RFC-0017`.

## Python abstract interfaces

See [`interfaces.py`](interfaces.py): `Reflector` (reflect / diagnose), `LearningEngine`
(distill / emit / loop_closed / systemic_patterns), `PromotionPolicy` (ready), and `RootCause`.

## Extension points

- **Reflection strategy.** Implement `Reflector` for different root-cause methods.
- **Promotion.** Implement `PromotionPolicy` to tune the corroboration bar.
- **Engine.** Subclass `LearningEngine` for custom policy-update propagation.

## Responsibilities

Reflect, distill experiences, diagnose root causes, propose promotions, improve retrieval &
planning policies, detect systemic patterns, close the loop.

## Examples

```python
from sdk.learning.interfaces import Reflector, LearningEngine

def learn(reflector: Reflector, engine: LearningEngine, evaluation, plan, context) -> None:
    reflection = reflector.reflect(evaluation, plan, context)
    for event in engine.emit(reflection):
        print(event.kind, event.target, event.loop_closed)
```

## Future evolution

Automated policy search (evidence-grounded, not weight updates), meta-learning, cross-Worker
curricula, queryable incident causal graphs, and human-in-the-loop reflection for high-stakes
lessons (see `ARCH-05` §Future Evolution).
