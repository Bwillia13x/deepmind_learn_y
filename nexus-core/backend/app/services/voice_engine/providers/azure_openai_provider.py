"""
Azure OpenAI LLM Provider.

Supports Azure-hosted OpenAI models for organizations requiring
data residency in Azure regions (important for Alberta school boards).
"""

import io
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


class AzureOpenAIProvider(LLMProvider):
    """
    Azure OpenAI provider for enterprise deployments.

    Key benefits for education:
    - Data residency in Canada/Azure regions
    - Enterprise compliance (FOIP, PIPA)
    - Integration with Azure AD for SSO

    Requires:
    - Azure OpenAI resource endpoint
    - Deployment name for the model
    - API key or Azure AD credentials
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._async_client = None

        if not config.azure_endpoint:
            raise ValueError("Azure endpoint is required for Azure OpenAI provider")
        if not config.azure_deployment:
            raise ValueError("Azure deployment name is required")

    @property
    def name(self) -> str:
        return "Azure OpenAI"

    @property
    def capabilities(self) -> set[VoiceCapability]:
        return {
            VoiceCapability.TEXT_GENERATION,
            VoiceCapability.AUDIO_TO_TEXT,
            VoiceCapability.TEXT_TO_AUDIO,
            VoiceCapability.STREAMING,
        }

    def _get_async_client(self):
        """Lazy initialization of async Azure client."""
        if self._async_client is None:
            from openai import AsyncAzureOpenAI

            self._async_client = AsyncAzureOpenAI(
                azure_endpoint=self.config.azure_endpoint,
                api_key=self.config.api_key,
                api_version=self.config.api_version or "2024-02-15-preview",
            )
        return self._async_client

    async def generate_text(
        self,
        messages: list[ConversationMessage],
        context: SessionContext | None = None,
    ) -> ProviderResponse:
        """Generate text using Azure OpenAI."""
        import time

        client = self._get_async_client()
        start_time = time.time()

        api_messages = []
        if context:
            api_messages.append({
                "role": "system",
                "content": self.build_system_prompt(context),
            })

        for msg in messages:
            api_messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        try:
            response = await client.chat.completions.create(
                model=self.config.azure_deployment,
                messages=api_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_response_length,
            )

            latency = (time.time() - start_time) * 1000

            return ProviderResponse(
                text=response.choices[0].message.content or "",
                latency_ms=latency,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                model=self.config.azure_deployment or "",
                provider=self.name,
            )

        except Exception as e:
            logger.error(f"Azure OpenAI generation error: {e}")
            raise

    async def transcribe_audio(self, audio: bytes) -> str:
        """Transcribe using Azure Whisper deployment."""
        client = self._get_async_client()

        try:
            audio_file = io.BytesIO(audio)
            audio_file.name = "audio.wav"

            # Use Whisper deployment name from config
            whisper_deployment = self.config.extra.get(
                "whisper_deployment", "whisper"
            )

            response = await client.audio.transcriptions.create(
                model=whisper_deployment,
                file=audio_file,
                language="en",
            )

            return response.text

        except Exception as e:
            logger.error(f"Azure transcription error: {e}")
            return ""

    async def synthesize_audio(self, text: str) -> bytes:
        """Synthesize audio using Azure TTS deployment."""
        client = self._get_async_client()

        try:
            tts_deployment = self.config.extra.get("tts_deployment", "tts")

            response = await client.audio.speech.create(
                model=tts_deployment,
                voice=self.config.voice,
                input=text,
                response_format="pcm",
            )

            return response.content

        except Exception as e:
            logger.error(f"Azure TTS error: {e}")
            return b""

    async def stream_audio_response(
        self,
        audio_input: bytes,
        context: SessionContext | None = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream audio response.

        Azure doesn't have native real-time like OpenAI,
        so we use the default transcribe->generate->synthesize flow.
        """
        async for chunk in super().stream_audio_response(audio_input, context):
            yield chunk

    async def health_check(self) -> bool:
        """Check Azure OpenAI connectivity."""
        try:
            client = self._get_async_client()
            # Simple completion to verify deployment
            await client.chat.completions.create(
                model=self.config.azure_deployment,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
            )
            return True
        except Exception as e:
            logger.warning(f"Azure OpenAI health check failed: {e}")
            return False
