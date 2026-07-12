# `sdk.models` — Model Gateway

Interfaces for the ECL's single, model-agnostic point of LLM access. Realizes the **Model
Gateway** from [`ARCH-07`](../../docs/architecture/07_architecture.md). No implementation.

## Architecture

This is the **only** module aware that LLM providers exist (`ADR-0009/0010`). Every model call
in the entire ECL flows through `ModelGateway.call()`. Layers pass a provider-agnostic
`ModelRequest` built from a `ContextObject` (structured context, **not** a prompt string —
`ADR-0011`); a `ModelProvider` adapter renders it into the vendor's format and normalizes the
response back into a `ModelResponse`. A `ModelRouter` selects provider/model by difficulty,
cost, latency and negotiated `CapabilityDescriptor` (`ADR-0012`, `RFC-0010`), with fallback to
alternates and a **local SLM as availability floor** (`ADR-0044`). Swapping OpenAI, Anthropic,
Gemini, an open-source model or a local SLM changes only an adapter here — never another
module. This is what makes accumulated intelligence provider-portable.

## Python abstract interfaces

See [`interfaces.py`](interfaces.py): `ModelGateway` (register / call / capabilities),
`ModelProvider` (Protocol — the adapter seam), `ModelRouter` (route / fallback), and the
`CapabilityDescriptor` / `ModelRequest` / `ModelResponse` value types.

## Extension points

- **Providers.** Implement the `ModelProvider` Protocol per vendor/local model; register with
  the gateway. This is the sole provider-coupling point.
- **Routing.** Implement `ModelRouter` for custom cost/latency/quality policies.

## Responsibilities

Provide one entry point for model calls; render structured context per provider; normalize
responses; negotiate capabilities; route and fall back; advertise budgets to Context and
Decision layers.

## Examples

```python
from sdk.models.interfaces import ModelGateway, ModelRequest

def reason(gateway: ModelGateway, context, instruction: str):
    req = ModelRequest(context=context, instruction=instruction, tools=[],
                       max_output_tokens=8000, response_format="json")
    return gateway.call(req, hints={"difficulty": "high", "risk_tier": 0})
```

## Future evolution

Richer capability negotiation, provider health-aware routing, speculative multi-provider
racing, and per-task reasoning-cost budgets (see `RFC-0010`, `RFC-0029`).
