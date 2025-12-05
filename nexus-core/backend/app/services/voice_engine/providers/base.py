"""
Base LLM Provider Interface.

Abstract base class defining the contract all LLM providers must implement.
This ensures vendor neutrality as specified in context.md.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..multilang import build_language_aware_prompt


class VoiceCapability(Enum):
    """Capabilities supported by LLM providers."""

    TEXT_GENERATION = "text_generation"  # Basic text completion
    AUDIO_TO_TEXT = "audio_to_text"  # Speech-to-text (STT)
    TEXT_TO_AUDIO = "text_to_audio"  # Text-to-speech (TTS)
    REALTIME_AUDIO = "realtime_audio"  # Bidirectional real-time audio
    STREAMING = "streaming"  # Streaming responses


@dataclass
class ProviderConfig:
    """
    Configuration for an LLM provider.

    Shared across all provider implementations.
    """

    # Model configuration
    model: str = ""
    voice: str = "alloy"
    temperature: float = 0.7
    max_response_length: int = 500

    # API configuration
    api_key: str | None = None
    api_base: str | None = None
    api_version: str | None = None

    # Azure-specific
    azure_deployment: str | None = None
    azure_endpoint: str | None = None

    # Additional provider-specific options
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationMessage:
    """A message in the conversation history."""

    role: str  # "system", "user", "assistant"
    content: str
    audio_duration_ms: int | None = None


@dataclass
class SessionContext:
    """
    Context for an oracy session.

    Passed to providers for personalized responses.
    """

    student_code: str
    grade: int
    primary_language: str
    curriculum_outcome: str | None = None
    conversation_history: list[ConversationMessage] = field(default_factory=list)
    cultural_bridge_hints: str | None = None


@dataclass
class ProviderResponse:
    """Response from an LLM provider."""

    text: str
    audio: bytes | None = None
    latency_ms: float = 0.0
    tokens_used: int = 0
    model: str = ""
    provider: str = ""


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement this interface to ensure
    seamless switching between OpenAI, Azure, Gemini, etc.
    """

    def __init__(self, config: ProviderConfig):
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> set[VoiceCapability]:
        """Set of capabilities this provider supports."""
        pass

    def has_capability(self, capability: VoiceCapability) -> bool:
        """Check if provider supports a specific capability."""
        return capability in self.capabilities

    @abstractmethod
    async def generate_text(
        self,
        messages: list[ConversationMessage],
        context: SessionContext | None = None,
    ) -> ProviderResponse:
        """
        Generate a text response from messages.

        Args:
            messages: Conversation history including system prompt
            context: Session context for personalization

        Returns:
            ProviderResponse with generated text
        """
        pass

    @abstractmethod
    async def transcribe_audio(self, audio: bytes) -> str:
        """
        Transcribe audio to text (STT).

        Args:
            audio: Raw audio bytes (WAV/PCM format)

        Returns:
            Transcribed text
        """
        pass

    @abstractmethod
    async def synthesize_audio(self, text: str) -> bytes:
        """
        Convert text to audio (TTS).

        Args:
            text: Text to synthesize

        Returns:
            Audio bytes in configured format
        """
        pass

    async def stream_audio_response(
        self,
        audio_input: bytes,
        context: SessionContext | None = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream audio response from audio input (real-time).

        Default implementation: transcribe -> generate -> synthesize.
        Override for providers with native real-time support.

        Args:
            audio_input: Input audio bytes
            context: Session context

        Yields:
            Audio chunks as they're generated
        """
        # Default implementation for providers without native real-time
        transcript = await self.transcribe_audio(audio_input)

        messages = []
        if context and context.conversation_history:
            messages = context.conversation_history.copy()
        messages.append(ConversationMessage(role="user", content=transcript))

        response = await self.generate_text(messages, context)
        audio = await self.synthesize_audio(response.text)

        # Yield audio in chunks for streaming
        chunk_size = 4096
        for i in range(0, len(audio), chunk_size):
            yield audio[i : i + chunk_size]

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is available and configured correctly.

        Returns:
            True if provider is healthy, False otherwise
        """
        pass

    def build_system_prompt(self, context: SessionContext) -> str:
        """
        Build the system prompt for the conversation.

        Uses the multilang module for language-specific adaptations.
        Can be overridden by specific providers if needed.
        """
        return build_language_aware_prompt(
            grade=context.grade,
            primary_language=context.primary_language,
            curriculum_outcome=context.curriculum_outcome,
            cultural_bridge_hints=context.cultural_bridge_hints,
        )
