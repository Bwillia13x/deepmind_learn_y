"""
WebSocket endpoint for real-time voice streaming (Oracy Sessions).

This module handles the bidirectional audio stream between the student client
and the NEXUS voice engine. Audio is processed in real-time and NEVER stored
to disk per .context/02_privacy_charter.md.
"""

import asyncio
import base64
import contextlib
import json
import logging
import time
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.privacy_guard import scrub_pii
from app.db.models import OracySession, SessionStatus, Student
from app.services.curriculum_rag.vector import get_curriculum_store
from app.services.voice_engine.llm_driver import (
    ConversationTurn,
    SessionContext,
    VoiceConfig,
    get_llm_driver,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class MessageType(str, Enum):
    """WebSocket message types for voice streaming protocol."""

    # Client -> Server
    AUDIO_CHUNK = "audio_chunk"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    USER_MESSAGE = "user_message"

    # Server -> Client
    AI_AUDIO = "ai_audio"
    AI_TEXT = "ai_text"
    TRANSCRIPT = "transcript"
    SESSION_READY = "session_ready"
    SESSION_ENDED = "session_ended"
    ERROR = "error"
    LATENCY_UPDATE = "latency_update"


class SessionState(BaseModel):
    """State tracking for an active oracy session."""

    session_id: str
    student_code: str
    student_id: str | None = None
    student_grade: int = 5
    student_language: str = "Unknown"
    curriculum_outcome: str | None = None
    started_at: datetime
    turn_count: int = 0
    latencies: list[float] = []
    conversation_history: list[dict[str, Any]] = []
    is_active: bool = True
    audio_buffer: bytes = b""  # Buffer for accumulating audio chunks
    last_activity: datetime = datetime.now(UTC)  # For session recovery


# Session recovery: keep recently disconnected sessions for potential reconnection
DISCONNECTED_SESSION_TTL_SECONDS = 300  # 5 minutes


class VoiceStreamManager:
    """
    Manages active voice streaming sessions.

    Tracks connected clients and provides methods for session management.
    This is a singleton that maintains state across all WebSocket connections.
    Supports session recovery for brief disconnections.
    """

    def __init__(self) -> None:
        self.active_sessions: dict[str, SessionState] = {}
        self._disconnected_sessions: dict[str, SessionState] = {}  # For recovery
        self._student_sessions: dict[str, str] = {}  # student_code -> session_id mapping
        self._lock = asyncio.Lock()
        self._llm_driver = get_llm_driver()
        self._audio_buffers: dict[str, bytearray] = {}  # Session ID -> audio buffer
        self._processing_tasks: dict[str, asyncio.Task] = {}  # Track ongoing processing

    async def create_session(self, student_code: str, websocket: WebSocket) -> SessionState:
        """Create a new oracy session for a student, or recover existing session."""
        async with self._lock:
            # Check if student has a recoverable session
            if student_code in self._student_sessions:
                existing_session_id = self._student_sessions[student_code]
                if existing_session_id in self._disconnected_sessions:
                    # Recover the session
                    state = self._disconnected_sessions.pop(existing_session_id)
                    state.is_active = True
                    state.last_activity = datetime.now(UTC)
                    self.active_sessions[existing_session_id] = state
                    if existing_session_id not in self._audio_buffers:
                        self._audio_buffers[existing_session_id] = bytearray()
                    logger.info(f"Recovered session {existing_session_id} for student {student_code}")
                    return state
                elif existing_session_id in self.active_sessions:
                    # Session still active - just return it (client reconnected quickly)
                    state = self.active_sessions[existing_session_id]
                    state.last_activity = datetime.now(UTC)
                    logger.info(f"Reconnected to active session {existing_session_id} for student {student_code}")
                    return state

            # Create new session
            session_id = str(uuid4())
            state = SessionState(
                session_id=session_id,
                student_code=student_code,
                started_at=datetime.now(UTC),
                last_activity=datetime.now(UTC),
            )
            self.active_sessions[session_id] = state
            self._audio_buffers[session_id] = bytearray()
            self._student_sessions[student_code] = session_id
            logger.info(f"Created oracy session: {session_id} for student: {student_code}")
            return state

    async def disconnect_session(self, session_id: str) -> SessionState | None:
        """
        Mark session as disconnected (for potential recovery).

        Session data is kept for DISCONNECTED_SESSION_TTL_SECONDS to allow reconnection.
        """
        async with self._lock:
            state = self.active_sessions.pop(session_id, None)
            if state:
                state.is_active = False
                state.last_activity = datetime.now(UTC)
                self._disconnected_sessions[session_id] = state
                logger.info(f"Session {session_id} disconnected, available for recovery")

                # Schedule cleanup after TTL
                asyncio.create_task(self._cleanup_disconnected_session(session_id))

            return state

    async def _cleanup_disconnected_session(self, session_id: str) -> None:
        """Remove disconnected session after TTL expires."""
        await asyncio.sleep(DISCONNECTED_SESSION_TTL_SECONDS)
        async with self._lock:
            if session_id in self._disconnected_sessions:
                state = self._disconnected_sessions.pop(session_id)
                # Clean up student mapping
                if state.student_code in self._student_sessions:
                    if self._student_sessions[state.student_code] == session_id:
                        del self._student_sessions[state.student_code]
                # Clean up audio buffer
                self._audio_buffers.pop(session_id, None)
                logger.info(f"Cleaned up expired disconnected session: {session_id}")

    async def end_session(self, session_id: str) -> SessionState | None:
        """End an active session permanently (no recovery)."""
        async with self._lock:
            state = self.active_sessions.pop(session_id, None)
            if not state:
                state = self._disconnected_sessions.pop(session_id, None)

            if state:
                # Clean up student mapping
                if state.student_code in self._student_sessions:
                    if self._student_sessions[state.student_code] == session_id:
                        del self._student_sessions[state.student_code]

            # Clean up audio buffer
            self._audio_buffers.pop(session_id, None)
            # Cancel any ongoing processing task
            if session_id in self._processing_tasks:
                self._processing_tasks[session_id].cancel()
                del self._processing_tasks[session_id]
            if state:
                state.is_active = False
                logger.info(f"Ended oracy session: {session_id}")
            return state

    async def append_audio(self, session_id: str, audio_chunk: bytes) -> None:
        """Append audio chunk to session buffer."""
        if session_id in self._audio_buffers:
            self._audio_buffers[session_id].extend(audio_chunk)

    async def get_audio_buffer(self, session_id: str) -> bytes:
        """Get and clear the accumulated audio buffer."""
        if session_id in self._audio_buffers:
            audio = bytes(self._audio_buffers[session_id])
            self._audio_buffers[session_id] = bytearray()
            return audio
        return b""

    def get_session_context(self, session_id: str) -> SessionContext | None:
        """Get the session context for LLM processing."""
        state = self.active_sessions.get(session_id)
        if not state:
            return None

        history = [
            ConversationTurn(role=turn["role"], content=turn["content"])
            for turn in state.conversation_history
        ]

        return SessionContext(
            student_code=state.student_code,
            grade=state.student_grade,
            primary_language=state.student_language,
            curriculum_outcome=state.curriculum_outcome,
            conversation_history=history,
        )

    async def process_audio_and_respond(
        self,
        session_id: str,
        websocket: WebSocket,
    ) -> None:
        """
        Process accumulated audio and stream AI response back.

        This handles:
        1. Getting the accumulated audio buffer
        2. Transcribing it for the conversation log
        3. Generating an audio response from the LLM
        4. Streaming the audio response back to the client
        """
        start_time = time.perf_counter()

        # Get accumulated audio
        audio_data = await self.get_audio_buffer(session_id)
        if len(audio_data) < 1000:  # Minimum audio threshold (very short)
            logger.debug(f"Audio buffer too small ({len(audio_data)} bytes), skipping")
            return

        context = self.get_session_context(session_id)
        if not context:
            await send_error(websocket, "Session not found")
            return

        try:
            # First, transcribe the audio to get text (for logging and response)
            transcript = await self._llm_driver.transcribe_audio(audio_data)
            if transcript:
                # Send transcript to client
                await send_json_message(
                    websocket,
                    MessageType.TRANSCRIPT,
                    {"text": scrub_pii(transcript)},
                )
                # Add to conversation history
                await self.add_conversation_turn(session_id, "user", scrub_pii(transcript))

            # Generate audio response from LLM
            response_chunks = []
            async for audio_chunk in self._llm_driver.generate_audio_response(audio_data, context):
                if audio_chunk:
                    # Send audio chunk as binary to client
                    await websocket.send_bytes(audio_chunk)
                    response_chunks.append(audio_chunk)

            # Calculate latency
            latency_ms = (time.perf_counter() - start_time) * 1000
            await self.record_turn(session_id, latency_ms)

            # Send latency update
            await send_json_message(
                websocket,
                MessageType.LATENCY_UPDATE,
                {"latency_ms": round(latency_ms, 2)},
            )

            logger.info(f"Processed audio response in {latency_ms:.0f}ms for session {session_id}")

        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            await send_error(websocket, "Failed to process audio")

    async def get_session(self, session_id: str) -> SessionState | None:
        """Get the current state of a session."""
        return self.active_sessions.get(session_id)

    async def record_turn(self, session_id: str, latency_ms: float) -> None:
        """Record a conversation turn with its latency."""
        async with self._lock:
            if session_id in self.active_sessions:
                self.active_sessions[session_id].turn_count += 1
                self.active_sessions[session_id].latencies.append(latency_ms)

    async def add_conversation_turn(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Add a turn to the conversation history."""
        async with self._lock:
            if session_id in self.active_sessions:
                self.active_sessions[session_id].conversation_history.append({
                    "role": role,
                    "content": content,
                })

    async def get_ai_response(
        self,
        session_id: str,
        user_message: str,
    ) -> tuple[str, float]:
        """
        Get AI response for user message using the LLM driver.

        Returns:
            Tuple of (response_text, latency_ms)
        """
        state = self.active_sessions.get(session_id)
        if not state:
            return "Session not found.", 0.0

        # Build conversation history for context
        history = [
            ConversationTurn(role=turn["role"], content=turn["content"])
            for turn in state.conversation_history
        ]

        # Create session context
        context = SessionContext(
            student_code=state.student_code,
            grade=state.student_grade,
            primary_language=state.student_language,
            curriculum_outcome=state.curriculum_outcome,
            conversation_history=history,
        )

        # Generate response and measure latency
        start_time = time.perf_counter()
        response = await self._llm_driver.generate_response(user_message, context)
        latency_ms = (time.perf_counter() - start_time) * 1000

        # Update conversation history
        await self.add_conversation_turn(session_id, "user", user_message)
        await self.add_conversation_turn(session_id, "assistant", response)

        return response, latency_ms

    def get_relevant_curriculum(self, grade: int, message: str) -> str | None:
        """Get a relevant curriculum outcome based on the conversation."""
        try:
            store = get_curriculum_store()
            matches = store.search(message, grade_filter=grade, top_k=1)
            if matches:
                return matches[0].outcome_text
        except Exception as e:
            logger.warning(f"Failed to fetch curriculum context: {e}")
        return None


# Global session manager
session_manager = VoiceStreamManager()


async def get_or_create_student(db: AsyncSession, student_code: str) -> Student | None:
    """Fetch student by code, or return None if not found."""
    result = await db.execute(
        select(Student).where(Student.student_code == student_code)
    )
    return result.scalar_one_or_none()


async def update_session_with_student_context(
    session_state: SessionState,
    student: Student,
) -> None:
    """Update session state with student context from database."""
    session_state.student_id = student.id
    session_state.student_grade = student.grade
    session_state.student_language = student.primary_language or "Unknown"


async def create_oracy_session_record(
    db: AsyncSession,
    student_id: str,
    session_state: SessionState,
) -> OracySession:
    """Create a database record for the oracy session."""
    oracy_session = OracySession(
        id=session_state.session_id,
        student_id=student_id,
        status=SessionStatus.ACTIVE,
        started_at=session_state.started_at,
    )
    db.add(oracy_session)
    await db.commit()
    await db.refresh(oracy_session)
    return oracy_session


async def finalize_oracy_session(
    db: AsyncSession,
    session_state: SessionState,
    transcript_summary: str | None = None,
) -> None:
    """Update the oracy session record with final statistics."""
    result = await db.execute(
        select(OracySession).where(OracySession.id == session_state.session_id)
    )
    oracy_session = result.scalar_one_or_none()

    if oracy_session:
        oracy_session.status = SessionStatus.COMPLETED
        oracy_session.ended_at = datetime.now(UTC)
        oracy_session.turn_count = session_state.turn_count
        oracy_session.duration_seconds = int(
            (datetime.now(UTC) - session_state.started_at).total_seconds()
        )
        if session_state.latencies:
            oracy_session.avg_response_latency_ms = sum(session_state.latencies) / len(
                session_state.latencies
            )
        if transcript_summary:
            # Scrub PII before storing
            oracy_session.transcript_summary = scrub_pii(transcript_summary)

        await db.commit()


async def send_json_message(websocket: WebSocket, msg_type: MessageType, data: dict[str, Any]) -> None:
    """Send a JSON message to the client."""
    message = {"type": msg_type.value, "data": data}
    await websocket.send_json(message)


async def send_error(websocket: WebSocket, error: str) -> None:
    """Send an error message to the client."""
    await send_json_message(websocket, MessageType.ERROR, {"error": error})


@router.websocket("/ws/oracy/{student_code}")
async def oracy_voice_stream(websocket: WebSocket, student_code: str) -> None:
    """
    WebSocket endpoint for real-time voice streaming.

    Protocol:
    1. Client connects with student_code
    2. Server validates student and creates session
    3. Client sends audio chunks (binary or base64)
    4. Server processes audio, returns AI response audio
    5. Session ends on disconnect or explicit end message

    Message Format (JSON):
    {
        "type": "audio_chunk" | "session_start" | "session_end" | "user_message",
        "data": { ... }
    }

    Audio Format:
    - PCM 16-bit signed, 24kHz mono
    - Sent as binary WebSocket frames or base64-encoded in JSON
    """
    await websocket.accept()

    session_state: SessionState | None = None
    transcript_buffer: list[str] = []

    try:
        # Create session
        session_state = await session_manager.create_session(student_code, websocket)

        # Validate student exists (or create in dev mode)
        async with async_session_factory() as db:
            student = await get_or_create_student(db, student_code)
            if student:
                await update_session_with_student_context(session_state, student)
                await create_oracy_session_record(db, student.id, session_state)

                # Try to get relevant curriculum context
                curriculum = session_manager.get_relevant_curriculum(
                    session_state.student_grade,
                    "conversation practice",  # Default topic
                )
                if curriculum:
                    session_state.curriculum_outcome = curriculum
            else:
                logger.warning(f"Student not found: {student_code}")
                # In production, we might reject; for now, allow anonymous sessions

        # Send session ready confirmation
        await send_json_message(
            websocket,
            MessageType.SESSION_READY,
            {
                "session_id": session_state.session_id,
                "student_code": student_code,
            },
        )

        # Main message loop
        while True:
            # Receive message (can be text JSON or binary audio)
            message = await websocket.receive()

            if "text" in message:
                # JSON message
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")
                    payload = data.get("data", {})

                    if msg_type == MessageType.SESSION_END.value:
                        break

                    elif msg_type == MessageType.AUDIO_CHUNK.value:
                        # Process audio chunk (base64 encoded in JSON)
                        audio_b64 = payload.get("audio", "")
                        if audio_b64:
                            try:
                                audio_bytes = base64.b64decode(audio_b64)
                                # Append to buffer
                                await session_manager.append_audio(
                                    session_state.session_id, audio_bytes
                                )

                                # Check buffer size and process if threshold reached
                                buffer = await session_manager.get_audio_buffer(
                                    session_state.session_id
                                )
                                if len(buffer) > 0:
                                    # Re-add buffer (peek behavior)
                                    await session_manager.append_audio(
                                        session_state.session_id, buffer
                                    )
                                    # Process when we have ~2 seconds of audio
                                    if len(buffer) >= 96000:
                                        await session_manager.process_audio_and_respond(
                                            session_state.session_id,
                                            websocket,
                                        )
                            except Exception as e:
                                logger.error(f"Error decoding audio: {e}")
                                await send_error(websocket, "Invalid audio data")

                    elif msg_type == MessageType.USER_MESSAGE.value:
                        # Text message (for testing without audio)
                        user_text = payload.get("text", "")

                        # Scrub PII before processing
                        clean_text = scrub_pii(user_text)
                        transcript_buffer.append(f"Student: {clean_text}")

                        # Get AI response from LLM driver
                        ai_response, latency_ms = await session_manager.get_ai_response(
                            session_state.session_id,
                            clean_text,
                        )
                        transcript_buffer.append(f"NEXUS: {ai_response}")

                        await send_json_message(
                            websocket,
                            MessageType.AI_TEXT,
                            {"text": ai_response},
                        )

                        await session_manager.record_turn(
                            session_state.session_id,
                            latency_ms=latency_ms,
                        )

                        # Send latency update to client
                        await send_json_message(
                            websocket,
                            MessageType.LATENCY_UPDATE,
                            {"latency_ms": round(latency_ms, 2)},
                        )

                except json.JSONDecodeError:
                    await send_error(websocket, "Invalid JSON message")

            elif "bytes" in message:
                # Binary audio chunk - accumulate in buffer
                audio_bytes = message["bytes"]
                logger.debug(f"Received {len(audio_bytes)} bytes of audio")

                # Append to audio buffer
                await session_manager.append_audio(session_state.session_id, audio_bytes)

                # Check if we should process (simple heuristic: buffer size > threshold)
                # A proper implementation would use Voice Activity Detection (VAD)
                buffer = await session_manager.get_audio_buffer(session_state.session_id)
                if len(buffer) == 0:
                    # Buffer was just cleared, likely being processed
                    continue

                # Re-add the buffer since we just retrieved it (peek behavior)
                await session_manager.append_audio(session_state.session_id, buffer)

                # Process when we have enough audio (about 2 seconds at 24kHz mono 16-bit)
                # 24000 samples/sec * 2 bytes/sample * 2 sec = 96000 bytes
                AUDIO_PROCESS_THRESHOLD = 96000

                if len(buffer) >= AUDIO_PROCESS_THRESHOLD:
                    # Process the audio and send response
                    await session_manager.process_audio_and_respond(
                        session_state.session_id,
                        websocket,
                    )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_state.session_id if session_state else 'unknown'}")
        # Mark as disconnected (allows recovery) rather than ending
        if session_state:
            await session_manager.disconnect_session(session_state.session_id)

    except Exception as e:
        logger.error(f"Error in voice stream: {e}")
        with contextlib.suppress(Exception):
            await send_error(websocket, str(e))
        # On error, also mark as disconnected for potential recovery
        if session_state:
            await session_manager.disconnect_session(session_state.session_id)

    finally:
        # Only finalize if session was explicitly ended (not just disconnected)
        if session_state and session_state.session_id not in session_manager._disconnected_sessions:
            final_state = await session_manager.end_session(session_state.session_id)

            # Save session to database
            if final_state and final_state.student_id:
                async with async_session_factory() as db:
                    transcript_summary = "\n".join(transcript_buffer) if transcript_buffer else None
                    await finalize_oracy_session(db, final_state, transcript_summary)

            # Send session ended message
            try:
                await send_json_message(
                    websocket,
                    MessageType.SESSION_ENDED,
                    {
                        "session_id": session_state.session_id,
                        "duration_seconds": int(
                            (datetime.now(UTC) - session_state.started_at).total_seconds()
                        ),
                        "turn_count": session_state.turn_count,
                    },
                )
            except Exception:
                pass  # Connection may already be closed
