"""
Google Gemini LLM Provider.

Supports Google's Gemini models as an alternative to OpenAI.
Useful for school boards that prefer Google Cloud Platform.
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


class GeminiProvider(LLMProvider):
    """
    Google Gemini provider.

    Supports:
    - Gemini Pro for text generation
    - Gemini Pro Vision for multimodal (future)
    - Google Cloud Speech-to-Text
    - Google Cloud Text-to-Speech

    Note: Requires google-generativeai and google-cloud-speech packages.
    """

    DEFAULT_MODEL = "gemini-pro"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._model = None
        self._speech_client = None
        self._tts_client = None

        if not config.model:
            config.model = self.DEFAULT_MODEL

    @property
    def name(self) -> str:
        return "Google Gemini"

    @property
    def capabilities(self) -> set[VoiceCapability]:
        return {
            VoiceCapability.TEXT_GENERATION,
            VoiceCapability.AUDIO_TO_TEXT,
            VoiceCapability.TEXT_TO_AUDIO,
            VoiceCapability.STREAMING,
        }

    def _get_model(self):
        """Lazy initialization of Gemini model."""
        if self._model is None:
            import google.generativeai as genai

            genai.configure(api_key=self.config.api_key)
            self._model = genai.GenerativeModel(self.config.model)
        return self._model

    async def generate_text(
        self,
        messages: list[ConversationMessage],
        context: SessionContext | None = None,
    ) -> ProviderResponse:
        """Generate text using Gemini."""
        import time

        model = self._get_model()
        start_time = time.time()

        # Build prompt from messages
        prompt_parts = []
        if context:
            prompt_parts.append(self.build_system_prompt(context))

        for msg in messages:
            prefix = "User: " if msg.role == "user" else "Assistant: "
            prompt_parts.append(f"{prefix}{msg.content}")

        prompt = "\n\n".join(prompt_parts)

        try:
            response = await model.generate_content_async(
                prompt,
                generation_config={
                    "temperature": self.config.temperature,
                    "max_output_tokens": self.config.max_response_length,
                },
            )

            latency = (time.time() - start_time) * 1000

            return ProviderResponse(
                text=response.text,
                latency_ms=latency,
                model=self.config.model,
                provider=self.name,
            )

        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise

    async def transcribe_audio(self, audio: bytes) -> str:
        """Transcribe using Google Cloud Speech-to-Text."""
        try:
            from google.cloud import speech_v1 as speech

            if self._speech_client is None:
                self._speech_client = speech.SpeechAsyncClient()

            audio_content = speech.RecognitionAudio(content=audio)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
                enable_automatic_punctuation=True,
            )

            response = await self._speech_client.recognize(
                config=config, audio=audio_content
            )

            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript

            return transcript

        except ImportError:
            logger.warning("google-cloud-speech not installed, falling back to mock")
            return "[Audio transcription unavailable]"
        except Exception as e:
            logger.error(f"Google STT error: {e}")
            return ""

    async def synthesize_audio(self, text: str) -> bytes:
        """Synthesize using Google Cloud Text-to-Speech."""
        try:
            from google.cloud import texttospeech_v1 as tts

            if self._tts_client is None:
                self._tts_client = tts.TextToSpeechAsyncClient()

            synthesis_input = tts.SynthesisInput(text=text)

            voice = tts.VoiceSelectionParams(
                language_code="en-US",
                name=self.config.extra.get("voice_name", "en-US-Neural2-C"),
            )

            audio_config = tts.AudioConfig(
                audio_encoding=tts.AudioEncoding.LINEAR16,
                sample_rate_hertz=24000,
            )

            response = await self._tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )

            return response.audio_content

        except ImportError:
            logger.warning("google-cloud-texttospeech not installed")
            return b""
        except Exception as e:
            logger.error(f"Google TTS error: {e}")
            return b""

    async def stream_audio_response(
        self,
        audio_input: bytes,
        context: SessionContext | None = None,
    ) -> AsyncGenerator[bytes, None]:
        """Stream using default transcribe->generate->synthesize flow."""
        async for chunk in super().stream_audio_response(audio_input, context):
            yield chunk

    async def health_check(self) -> bool:
        """Check Gemini API availability."""
        try:
            model = self._get_model()
            response = await model.generate_content_async(
                "Hi",
                generation_config={"max_output_tokens": 1},
            )
            return bool(response.text)
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False
