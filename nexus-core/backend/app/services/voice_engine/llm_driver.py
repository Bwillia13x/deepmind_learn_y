"""
Voice Engine - LLM Driver for Oracy Sessions.

Handles real-time voice interaction with LLM backends (OpenAI Realtime API).
Audio is NEVER stored per .context/02_privacy_charter.md.
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

from app.core.config import settings
from app.core.privacy_guard import scrub_pii

logger = logging.getLogger(__name__)


@dataclass
class VoiceConfig:
    """Configuration for voice engine."""

    model: str = "gpt-4o-realtime-preview-2024-12-17"
    voice: str = "alloy"  # OpenAI voice options
    temperature: float = 0.7
    max_response_length: int = 500


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""

    role: str  # "user" or "assistant"
    content: str
    audio_duration_ms: int | None = None
    latency_ms: float | None = None


@dataclass
class SessionContext:
    """Context for an oracy session."""

    student_code: str
    grade: int
    primary_language: str
    curriculum_outcome: str | None = None
    conversation_history: list[ConversationTurn] = field(default_factory=list)


NEXUS_SYSTEM_PROMPT = """You are NEXUS, a supportive and patient AI tutor for Grade {grade} EAL (English as Additional Language) students in Alberta, Canada.

Your role:
- Practice conversational English through friendly dialogue
- Speak simply and clearly, adjusting to the student's level
- Encourage the student to speak and express themselves
- Gently correct pronunciation and grammar when appropriate
- Connect topics to Alberta curriculum when relevant
- Be culturally sensitive and welcoming

Student context:
- Grade level: {grade}
- Primary language: {primary_language}
{curriculum_context}

Guidelines:
- Use short, clear sentences
- Ask open-ended questions to encourage speaking
- Praise effort and progress
- If the student struggles, offer to explain in simpler terms
- Never ask for personal information (names, addresses, phone numbers)
- Keep conversations educational but fun

Start by greeting the student warmly and asking about their day or interests."""


class LLMDriver(ABC):
    """Abstract base class for LLM voice drivers."""

    @abstractmethod
    async def generate_response(
        self,
        user_message: str,
        context: SessionContext,
    ) -> str:
        """Generate a text response from the LLM."""
        pass

    @abstractmethod
    def generate_audio_response(
        self,
        user_audio: bytes,
        context: SessionContext,
    ) -> AsyncGenerator[bytes, None]:
        """Generate audio response from audio input (real-time streaming)."""
        pass

    @abstractmethod
    async def transcribe_audio(self, audio: bytes) -> str:
        """Transcribe audio to text."""
        pass

    @abstractmethod
    async def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech audio."""
        pass


class MockLLMDriver(LLMDriver):
    """
    Mock LLM driver for development and testing.

    Returns predefined responses without calling external APIs.
    """

    def __init__(self, config: VoiceConfig | None = None):
        self.config = config or VoiceConfig()
        self._responses = [
            "That's a great observation! Tell me more about that.",
            "Interesting! How does that make you feel?",
            "I understand. Can you explain that in a different way?",
            "That's wonderful! You're doing great with your English.",
            "Let's explore that idea further. What do you think happens next?",
        ]
        self._response_index = 0

    async def generate_response(
        self,
        user_message: str,
        context: SessionContext,
    ) -> str:
        """Generate a mock text response."""
        logger.info(f"Mock LLM generating response for: {scrub_pii(user_message)[:50]}...")

        # Cycle through responses
        response = self._responses[self._response_index % len(self._responses)]
        self._response_index += 1

        return response

    async def generate_audio_response(
        self,
        user_audio: bytes,
        context: SessionContext,
    ) -> AsyncGenerator[bytes, None]:
        """Generate mock audio response (returns empty for mock)."""
        # In mock mode, we don't generate actual audio
        logger.info(f"Mock LLM received {len(user_audio)} bytes of audio")
        yield b""  # Empty audio chunk

    async def transcribe_audio(self, audio: bytes) -> str:
        """Mock transcription - returns placeholder text."""
        logger.info(f"Mock transcribing {len(audio)} bytes of audio")
        return "Hello, this is mock transcription."

    async def text_to_speech(self, text: str) -> bytes:
        """Mock TTS - returns empty audio."""
        logger.info(f"Mock TTS for: {text[:50]}...")
        return b""


class OpenAIRealtimeDriver(LLMDriver):
    """
    OpenAI Realtime API driver for voice interaction.

    Uses the GPT-4o Realtime API for bidirectional audio streaming.
    Note: This is a simplified implementation. Full implementation would
    handle WebSocket connections to OpenAI's Realtime API.
    """

    def __init__(self, config: VoiceConfig | None = None):
        self.config = config or VoiceConfig()
        self._api_key = settings.openai_api_key

        if not self._api_key:
            logger.warning("OpenAI API key not configured, using mock responses")

    def _build_system_prompt(self, context: SessionContext) -> str:
        """Build the system prompt with context."""
        curriculum_context = ""
        if context.curriculum_outcome:
            curriculum_context = f"- Current learning focus: {context.curriculum_outcome}"

        return NEXUS_SYSTEM_PROMPT.format(
            grade=context.grade,
            primary_language=context.primary_language,
            curriculum_context=curriculum_context,
        )

    async def generate_response(
        self,
        user_message: str,
        context: SessionContext,
    ) -> str:
        """Generate a text response using OpenAI API."""
        if not self._api_key:
            # Fallback to mock
            mock = MockLLMDriver(self.config)
            return await mock.generate_response(user_message, context)

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self._api_key)

            # Build messages from conversation history
            messages = [{"role": "system", "content": self._build_system_prompt(context)}]

            for turn in context.conversation_history:
                messages.append({
                    "role": turn.role,
                    "content": turn.content,
                })

            # Add current user message (scrubbed for safety)
            messages.append({
                "role": "user",
                "content": scrub_pii(user_message),
            })

            response = await client.chat.completions.create(
                model="gpt-4o-mini",  # Use mini for text, realtime for audio
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_response_length,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Fallback to mock on error
            mock = MockLLMDriver(self.config)
            return await mock.generate_response(user_message, context)

    async def generate_audio_response(
        self,
        user_audio: bytes,
        context: SessionContext,
    ) -> AsyncGenerator[bytes, None]:
        """
        Generate audio response using OpenAI Realtime API.

        Uses WebSocket connection to OpenAI's Realtime API for
        bidirectional audio streaming with GPT-4o.
        """
        if not self._api_key:
            logger.warning("OpenAI API key not configured for audio")
            yield b""
            return

        import base64
        import json

        import websockets

        realtime_url = "wss://api.openai.com/v1/realtime"
        model = self.config.model

        try:
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "OpenAI-Beta": "realtime=v1",
            }

            async with websockets.connect(
                f"{realtime_url}?model={model}",
                extra_headers=headers,
            ) as ws:
                # Configure the session
                session_config = {
                    "type": "session.update",
                    "session": {
                        "modalities": ["text", "audio"],
                        "instructions": self._build_system_prompt(context),
                        "voice": self.config.voice,
                        "input_audio_format": "pcm16",
                        "output_audio_format": "pcm16",
                        "input_audio_transcription": {
                            "model": "whisper-1",
                        },
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

                # Send the audio input
                audio_base64 = base64.b64encode(user_audio).decode("utf-8")
                audio_event = {
                    "type": "input_audio_buffer.append",
                    "audio": audio_base64,
                }
                await ws.send(json.dumps(audio_event))

                # Commit the audio buffer to trigger processing
                await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))

                # Request a response
                await ws.send(json.dumps({"type": "response.create"}))

                # Receive and yield audio chunks
                async for message in ws:
                    try:
                        event = json.loads(message)
                        event_type = event.get("type", "")

                        if event_type == "response.audio.delta":
                            # Decode and yield audio chunk
                            audio_chunk = base64.b64decode(event.get("delta", ""))
                            if audio_chunk:
                                yield audio_chunk

                        elif event_type == "response.audio.done":
                            # Audio response complete
                            logger.debug("Audio response completed")
                            break

                        elif event_type == "response.done":
                            # Full response complete
                            break

                        elif event_type == "error":
                            error_msg = event.get("error", {}).get("message", "Unknown error")
                            logger.error(f"OpenAI Realtime error: {error_msg}")
                            break

                    except json.JSONDecodeError:
                        logger.warning("Failed to decode WebSocket message")
                        continue

        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket connection error: {e}")
            yield b""

        except Exception as e:
            logger.error(f"OpenAI Realtime API error: {e}")
            yield b""

    async def transcribe_audio(self, audio: bytes) -> str:
        """
        Transcribe audio to text using Whisper API.

        Useful for getting text transcripts of voice sessions.
        """
        if not self._api_key:
            return ""

        try:
            import io

            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self._api_key)

            # Create a file-like object from bytes
            audio_file = io.BytesIO(audio)
            audio_file.name = "audio.wav"

            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en",
            )

            return response.text

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    async def text_to_speech(self, text: str) -> bytes:
        """
        Convert text to speech using OpenAI TTS API.

        Returns PCM16 audio bytes at 24kHz.
        """
        if not self._api_key:
            return b""

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self._api_key)

            response = await client.audio.speech.create(
                model="tts-1",
                voice=self.config.voice,
                input=text,
                response_format="pcm",
            )

            return response.content

        except Exception as e:
            logger.error(f"TTS error: {e}")
            return b""


def get_llm_driver(config: VoiceConfig | None = None) -> LLMDriver:
    """
    Factory function to get the appropriate LLM driver.

    Returns OpenAI driver if configured, otherwise mock driver.
    """
    if settings.has_openai:
        return OpenAIRealtimeDriver(config)
    return MockLLMDriver(config)
