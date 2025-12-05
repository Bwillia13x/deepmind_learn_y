"""
OpenAI LLM Provider.

Supports OpenAI's GPT models with real-time audio capabilities.
Uses the OpenAI Realtime API for bidirectional audio streaming.
"""

import base64
import io
import json
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


class OpenAIProvider(LLMProvider):
    """
    OpenAI GPT provider with real-time audio support.

    Supports:
    - GPT-4o, GPT-4o-mini for text generation
    - Whisper for speech-to-text
    - TTS-1 for text-to-speech
    - GPT-4o Realtime API for bidirectional audio
    """

    # Default models
    DEFAULT_CHAT_MODEL = "gpt-4o-mini"
    DEFAULT_REALTIME_MODEL = "gpt-4o-realtime-preview-2024-12-17"
    DEFAULT_STT_MODEL = "whisper-1"
    DEFAULT_TTS_MODEL = "tts-1"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client = None
        self._async_client = None

        if not config.model:
            config.model = self.DEFAULT_CHAT_MODEL

    @property
    def name(self) -> str:
        return "OpenAI"

    @property
    def capabilities(self) -> set[VoiceCapability]:
        return {
            VoiceCapability.TEXT_GENERATION,
            VoiceCapability.AUDIO_TO_TEXT,
            VoiceCapability.TEXT_TO_AUDIO,
            VoiceCapability.REALTIME_AUDIO,
            VoiceCapability.STREAMING,
        }

    def _get_async_client(self):
        """Lazy initialization of async client."""
        if self._async_client is None:
            from openai import AsyncOpenAI

            self._async_client = AsyncOpenAI(api_key=self.config.api_key)
        return self._async_client

    async def generate_text(
        self,
        messages: list[ConversationMessage],
        context: SessionContext | None = None,
    ) -> ProviderResponse:
        """Generate text response using OpenAI Chat API."""
        import time

        client = self._get_async_client()
        start_time = time.time()

        # Build messages for API
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
                model=self.config.model,
                messages=api_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_response_length,
            )

            latency = (time.time() - start_time) * 1000

            return ProviderResponse(
                text=response.choices[0].message.content or "",
                latency_ms=latency,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                model=self.config.model,
                provider=self.name,
            )

        except Exception as e:
            logger.error(f"OpenAI text generation error: {e}")
            raise

    async def transcribe_audio(self, audio: bytes) -> str:
        """Transcribe audio using Whisper."""
        client = self._get_async_client()

        try:
            # Create file-like object
            audio_file = io.BytesIO(audio)
            audio_file.name = "audio.wav"

            response = await client.audio.transcriptions.create(
                model=self.DEFAULT_STT_MODEL,
                file=audio_file,
                language="en",
            )

            return response.text

        except Exception as e:
            logger.error(f"OpenAI transcription error: {e}")
            return ""

    async def synthesize_audio(self, text: str) -> bytes:
        """Synthesize audio using TTS-1."""
        client = self._get_async_client()

        try:
            response = await client.audio.speech.create(
                model=self.DEFAULT_TTS_MODEL,
                voice=self.config.voice,
                input=text,
                response_format="pcm",
            )

            return response.content

        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            return b""

    async def stream_audio_response(
        self,
        audio_input: bytes,
        context: SessionContext | None = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream audio using OpenAI Realtime API.

        Uses WebSocket connection for bidirectional audio streaming.
        """
        import websockets

        realtime_url = "wss://api.openai.com/v1/realtime"
        model = self.config.extra.get("realtime_model", self.DEFAULT_REALTIME_MODEL)

        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "OpenAI-Beta": "realtime=v1",
            }

            async with websockets.connect(
                f"{realtime_url}?model={model}",
                extra_headers=headers,
            ) as ws:
                # Configure session
                system_prompt = self.build_system_prompt(context) if context else ""
                session_config = {
                    "type": "session.update",
                    "session": {
                        "modalities": ["text", "audio"],
                        "instructions": system_prompt,
                        "voice": self.config.voice,
                        "input_audio_format": "pcm16",
                        "output_audio_format": "pcm16",
                        "input_audio_transcription": {"model": "whisper-1"},
                        "turn_detection": {
                            "type": "server_vad",
                            "threshold": 0.5,
                            "prefix_padding_ms": 300,
                            "silence_duration_ms": 500,
                        },
                        "temperature": self.config.temperature,
                        "max_response_output_tokens": self.config.max_response_length,
                    },
                }
                await ws.send(json.dumps(session_config))

                # Send audio input
                audio_base64 = base64.b64encode(audio_input).decode("utf-8")
                await ws.send(json.dumps({
                    "type": "input_audio_buffer.append",
                    "audio": audio_base64,
                }))
                await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
                await ws.send(json.dumps({"type": "response.create"}))

                # Receive audio chunks
                async for message in ws:
                    try:
                        event = json.loads(message)
                        event_type = event.get("type", "")

                        if event_type == "response.audio.delta":
                            audio_chunk = base64.b64decode(event.get("delta", ""))
                            if audio_chunk:
                                yield audio_chunk

                        elif event_type in ("response.audio.done", "response.done"):
                            break

                        elif event_type == "error":
                            logger.error(f"Realtime API error: {event}")
                            break

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"OpenAI Realtime error: {e}")
            yield b""

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            client = self._get_async_client()
            # Simple models list call to verify API key
            await client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
