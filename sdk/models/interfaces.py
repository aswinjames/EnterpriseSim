"""Model Gateway interfaces (ARCH-07). The single, model-agnostic point of provider access.

No implementation. See ``sdk/models/README.md`` and ``docs/architecture/07_architecture.md``.

Only this module is aware that LLM providers exist. No other SDK module imports a provider
SDK (ADR-0009/0010). Swapping OpenAI / Anthropic / Gemini / open-source / local SLM changes
only an adapter here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from sdk.objects import ContextObject


@dataclass(frozen=True)
class CapabilityDescriptor:
    """What a model can do — negotiated, not assumed (ADR-0012)."""

    provider: str
    model: str
    context_window: int
    supports_tools: bool
    supports_structured_output: bool
    cost_per_1k_input: float
    cost_per_1k_output: float
    typical_latency_ms: int


@dataclass(frozen=True)
class ModelRequest:
    """A provider-agnostic reasoning request built from a ContextObject."""

    context: ContextObject
    instruction: str
    tools: Sequence[Mapping[str, object]]     # tool schemas, if any
    max_output_tokens: int
    response_format: str                      # text | json | tool_calls


@dataclass(frozen=True)
class ModelResponse:
    """A normalized response, independent of provider wire format."""

    text: str | None
    tool_calls: Sequence[Mapping[str, object]]
    usage: Mapping[str, int]                  # input_tokens, output_tokens
    raw_provider_id: str


class ModelProvider(Protocol):
    """A provider adapter. The ONLY place a vendor SDK is imported (ADR-0009)."""

    def capabilities(self) -> CapabilityDescriptor: ...

    def render_and_call(self, request: ModelRequest) -> ModelResponse:
        """Render the structured request into the provider's format, call, normalize back."""
        ...


class ModelRouter(ABC):
    """Selects a provider/model by difficulty, cost, latency and capability (RFC-0010)."""

    @abstractmethod
    def route(self, request: ModelRequest, hints: Mapping[str, object]) -> CapabilityDescriptor:
        ...

    @abstractmethod
    def fallback(self, failed: CapabilityDescriptor) -> CapabilityDescriptor:
        """Return an alternate provider on failure; local SLM is the availability floor (ADR-0044)."""
        ...


class ModelGateway(ABC):
    """The single entry point for all model calls in the ECL (RFC-0011)."""

    @abstractmethod
    def register(self, provider: ModelProvider) -> None: ...

    @abstractmethod
    def call(self, request: ModelRequest, hints: Mapping[str, object]) -> ModelResponse:
        """Route, render, call, normalize — with fallback. No layer bypasses this method."""
        ...

    @abstractmethod
    def capabilities(self) -> Sequence[CapabilityDescriptor]:
        """Advertise available models so Context and Decision layers can adapt to budgets."""
        ...
