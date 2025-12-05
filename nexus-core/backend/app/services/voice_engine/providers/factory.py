"""
LLM Provider Factory.

Creates appropriate provider instances based on configuration.
Ensures vendor neutrality by abstracting provider selection.
"""

import logging
from enum import Enum

from app.core.config import settings
from app.services.voice_engine.providers.base import (
    LLMProvider,
    ProviderConfig,
)

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Available LLM provider types."""

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    GEMINI = "gemini"
    MOCK = "mock"


def get_available_providers() -> list[ProviderType]:
    """
    Get list of providers that are configured and available.

    Returns:
        List of provider types that can be used
    """
    available = [ProviderType.MOCK]  # Mock is always available

    if settings.openai_api_key:
        available.append(ProviderType.OPENAI)

    if settings.azure_openai_endpoint and settings.azure_openai_key:
        available.append(ProviderType.AZURE_OPENAI)

    if getattr(settings, "google_api_key", None):
        available.append(ProviderType.GEMINI)

    return available


def create_provider(
    provider_type: ProviderType | str | None = None,
    config: ProviderConfig | None = None,
) -> LLMProvider:
    """
    Create an LLM provider instance.

    Args:
        provider_type: Type of provider to create. If None, auto-selects based on config.
        config: Provider configuration. If None, uses settings.

    Returns:
        Configured LLMProvider instance

    Raises:
        ValueError: If provider type is unknown or not configured
    """
    # Convert string to enum if needed
    if isinstance(provider_type, str):
        try:
            provider_type = ProviderType(provider_type.lower())
        except ValueError:
            raise ValueError(f"Unknown provider type: {provider_type}")

    # Auto-select provider if not specified
    if provider_type is None:
        provider_type = _auto_select_provider()

    # Build config if not provided
    if config is None:
        config = _build_config_from_settings(provider_type)

    # Create provider instance
    return _create_provider_instance(provider_type, config)


def _auto_select_provider() -> ProviderType:
    """
    Auto-select the best available provider.

    Priority:
    1. Azure OpenAI (for enterprise/education compliance)
    2. OpenAI (most capable)
    3. Gemini (alternative)
    4. Mock (fallback)
    """
    if settings.azure_openai_endpoint and settings.azure_openai_key:
        logger.info("Auto-selected Azure OpenAI provider (enterprise)")
        return ProviderType.AZURE_OPENAI

    if settings.openai_api_key:
        logger.info("Auto-selected OpenAI provider")
        return ProviderType.OPENAI

    if getattr(settings, "google_api_key", None):
        logger.info("Auto-selected Gemini provider")
        return ProviderType.GEMINI

    logger.warning("No LLM provider configured, using mock")
    return ProviderType.MOCK


def _build_config_from_settings(provider_type: ProviderType) -> ProviderConfig:
    """Build provider config from application settings."""
    config = ProviderConfig(
        temperature=0.7,
        max_response_length=500,
        voice="alloy",
    )

    if provider_type == ProviderType.OPENAI:
        config.api_key = settings.openai_api_key
        config.model = getattr(settings, "openai_model", "gpt-4o-mini")

    elif provider_type == ProviderType.AZURE_OPENAI:
        config.api_key = settings.azure_openai_key
        config.azure_endpoint = settings.azure_openai_endpoint
        config.azure_deployment = getattr(settings, "azure_openai_deployment", "gpt-4o")
        config.api_version = getattr(settings, "azure_openai_version", "2024-02-15-preview")

    elif provider_type == ProviderType.GEMINI:
        config.api_key = getattr(settings, "google_api_key", "")
        config.model = getattr(settings, "gemini_model", "gemini-pro")

    return config


def _create_provider_instance(
    provider_type: ProviderType,
    config: ProviderConfig,
) -> LLMProvider:
    """Create the actual provider instance."""
    if provider_type == ProviderType.OPENAI:
        from app.services.voice_engine.providers.openai_provider import OpenAIProvider

        return OpenAIProvider(config)

    elif provider_type == ProviderType.AZURE_OPENAI:
        from app.services.voice_engine.providers.azure_openai_provider import (
            AzureOpenAIProvider,
        )

        return AzureOpenAIProvider(config)

    elif provider_type == ProviderType.GEMINI:
        from app.services.voice_engine.providers.gemini_provider import GeminiProvider

        return GeminiProvider(config)

    elif provider_type == ProviderType.MOCK:
        from app.services.voice_engine.providers.mock_provider import MockProvider

        return MockProvider(config)

    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


# Convenience function for getting a ready-to-use provider
def get_provider(provider_type: ProviderType | str | None = None) -> LLMProvider:
    """
    Get a configured LLM provider instance.

    This is the main entry point for getting a provider.
    Uses auto-selection if no type specified.

    Args:
        provider_type: Optional provider type to use

    Returns:
        Ready-to-use LLMProvider instance
    """
    return create_provider(provider_type)
