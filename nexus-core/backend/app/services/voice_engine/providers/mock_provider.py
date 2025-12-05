"""
Mock LLM Provider.

Provides predictable responses for testing and development.
No external API calls required.
"""

import logging
from collections.abc import AsyncGenerator

from app.services.voice_engine.providers.base import (
    ConversationMessage,
    LLMProvider,
    ProviderConfig,
    ProviderResponse,
    SessionContext,
    VoiceCapability,
)

logger = logging.getLogger(__name__)


class MockProvider(LLMProvider):
    """
    Mock provider for testing and development.

    Returns predefined responses without external API calls.
    Useful for:
    - Unit testing
    - Development without API keys
    - CI/CD pipelines
    - Demo environments
    """

    MOCK_RESPONSES = [
        "That's a great observation! Tell me more about that.",
        "Interesting! How does that make you feel?",
        "I understand. Can you explain that in a different way?",
        "That's wonderful! You're doing great with your English.",
        "Let's explore that idea further. What do you think happens next?",
        "Very good! Your English is improving. Can you use that word in a sentence?",
        "I see what you mean. That reminds me of something in your Alberta studies.",
        "Excellent effort! Would you like to try saying that again?",
    ]

    def __init__(self, config: ProviderConfig | None = None):
        super().__init__(config or ProviderConfig())
        self._response_index = 0

    @property
    def name(self) -> str:
        return "Mock"

    @property
    def capabilities(self) -> set[VoiceCapability]:
        return {
            VoiceCapability.TEXT_GENERATION,
            VoiceCapability.AUDIO_TO_TEXT,
            VoiceCapability.TEXT_TO_AUDIO,
            VoiceCapability.STREAMING,
        }

    async def generate_text(
        self,
        messages: list[ConversationMessage],
        context: SessionContext | None = None,
    ) -> ProviderResponse:
        """Return a mock response."""
        response = self.MOCK_RESPONSES[self._response_index % len(self.MOCK_RESPONSES)]
        self._response_index += 1

        # Check for PII-related questions (works without context)
        if messages:
            last_message = messages[-1].content.lower()

            if "address" in last_message or "phone" in last_message:
                response = "I can't share personal information, but I'd love to hear about your interests instead! What do you enjoy doing after school?"

        # Add context-aware variation
        if context and messages:
            last_message = messages[-1].content.lower()

            if "soccer" in last_message or "football" in last_message:
                response = "Soccer is great! Do you play on a team? Tell me about your favorite player."

            elif "hate" in last_message or "don't like" in last_message:
                response = "I hear that you're feeling frustrated. It's okay to feel that way. Would you like to talk about what's bothering you?"

            elif context.primary_language != "English":
                response = f"{response} By the way, if you ever want to explain something in {context.primary_language}, I'll try my best to understand!"

        return ProviderResponse(
            text=response,
            latency_ms=50.0,  # Simulated latency
            tokens_used=len(response.split()),
            model="mock-model",
            provider=self.name,
        )

    async def transcribe_audio(self, audio: bytes) -> str:
        """Return mock transcription."""
        logger.info(f"Mock transcription of {len(audio)} bytes")
        return "This is a mock transcription of the audio."

    async def synthesize_audio(self, text: str) -> bytes:
        """Return mock audio (silence)."""
        logger.info(f"Mock TTS for: {text[:50]}...")
        # Return 1 second of silence (16-bit PCM at 24kHz)
        return b"\x00" * 48000

    async def stream_audio_response(
        self,
        audio_input: bytes,
        context: SessionContext | None = None,
    ) -> AsyncGenerator[bytes, None]:
        """Stream mock audio chunks."""
        # Simulate processing delay
        import asyncio

        await asyncio.sleep(0.1)

        # Generate response
        response = await self.generate_text(
            [ConversationMessage(role="user", content="mock input")],
            context,
        )

        # Mock audio
        audio = await self.synthesize_audio(response.text)

        # Yield in chunks
        chunk_size = 4096
        for i in range(0, len(audio), chunk_size):
            yield audio[i : i + chunk_size]
            await asyncio.sleep(0.01)  # Simulate streaming delay

    async def health_check(self) -> bool:
        """Mock provider is always healthy."""
        return True
