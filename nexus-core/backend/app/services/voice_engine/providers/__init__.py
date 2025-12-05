"""
LLM Provider Abstraction Layer.

Provides vendor-agnostic interface for LLM voice services.
Supports OpenAI, Azure OpenAI, Google Gemini, and mock providers.

This enables school boards to choose their preferred provider
based on data residency, cost, or other requirements.
"""

from app.services.voice_engine.providers.base import (
    LLMProvider,
    ProviderConfig,
    VoiceCapability,
)
from app.services.voice_engine.providers.factory import (
    create_provider,
    get_available_providers,
    ProviderType,
)

__all__ = [
    "LLMProvider",
    "ProviderConfig",
    "VoiceCapability",
    "create_provider",
    "get_available_providers",
    "ProviderType",
]
