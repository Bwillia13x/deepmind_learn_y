"""
End-to-end tests for voice streaming WebSocket endpoint.

Tests the full flow from WebSocket connection through LLM response.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from app.api.v1.websockets.voice_stream import (
    VoiceStreamManager,
    SessionState,
    MessageType,
)
from app.services.voice_engine.llm_driver import (
    SessionContext,
    MockLLMDriver,
)


class TestVoiceStreamManager:
    """Tests for the VoiceStreamManager class."""

    @pytest.fixture
    def manager(self) -> VoiceStreamManager:
        """Create a fresh manager for each test."""
        return VoiceStreamManager()

    @pytest.fixture
    def mock_websocket(self) -> AsyncMock:
        """Create a mock WebSocket."""
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.receive = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_create_session(self, manager: VoiceStreamManager, mock_websocket: AsyncMock) -> None:
        """Test session creation."""
        student_code = "STU-test123"
        
        session = await manager.create_session(student_code, mock_websocket)
        
        assert session is not None
        assert session.student_code == student_code
        assert session.session_id is not None
        assert session.is_active is True
        assert session.turn_count == 0

    @pytest.mark.asyncio
    async def test_end_session(self, manager: VoiceStreamManager, mock_websocket: AsyncMock) -> None:
        """Test session termination."""
        student_code = "STU-test123"
        session = await manager.create_session(student_code, mock_websocket)
        session_id = session.session_id
        
        ended_session = await manager.end_session(session_id)
        
        assert ended_session is not None
        assert ended_session.is_active is False
        
        # Session should be removed
        retrieved = await manager.get_session(session_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_record_turn(self, manager: VoiceStreamManager, mock_websocket: AsyncMock) -> None:
        """Test recording conversation turns."""
        session = await manager.create_session("STU-test123", mock_websocket)
        
        await manager.record_turn(session.session_id, latency_ms=150.0)
        await manager.record_turn(session.session_id, latency_ms=200.0)
        
        updated = await manager.get_session(session.session_id)
        assert updated is not None
        assert updated.turn_count == 2
        assert len(updated.latencies) == 2
        assert updated.latencies[0] == 150.0
        assert updated.latencies[1] == 200.0

    @pytest.mark.asyncio
    async def test_add_conversation_turn(self, manager: VoiceStreamManager, mock_websocket: AsyncMock) -> None:
        """Test adding conversation history."""
        session = await manager.create_session("STU-test123", mock_websocket)
        
        await manager.add_conversation_turn(session.session_id, "user", "Hello")
        await manager.add_conversation_turn(session.session_id, "assistant", "Hi there!")
        
        updated = await manager.get_session(session.session_id)
        assert updated is not None
        assert len(updated.conversation_history) == 2
        assert updated.conversation_history[0]["role"] == "user"
        assert updated.conversation_history[0]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_get_ai_response_mock(self, manager: VoiceStreamManager, mock_websocket: AsyncMock) -> None:
        """Test AI response generation with mock driver."""
        session = await manager.create_session("STU-test123", mock_websocket)
        
        response, latency = await manager.get_ai_response(
            session.session_id,
            "Hello, how are you?",
        )
        
        assert response is not None
        assert len(response) > 0
        assert latency >= 0

    @pytest.mark.asyncio
    async def test_get_ai_response_updates_history(self, manager: VoiceStreamManager, mock_websocket: AsyncMock) -> None:
        """Test that AI response updates conversation history."""
        session = await manager.create_session("STU-test123", mock_websocket)
        
        await manager.get_ai_response(session.session_id, "Test message")
        
        updated = await manager.get_session(session.session_id)
        assert updated is not None
        # Should have user message and assistant response
        assert len(updated.conversation_history) == 2

    @pytest.mark.asyncio
    async def test_session_not_found(self, manager: VoiceStreamManager) -> None:
        """Test handling of non-existent session."""
        response, latency = await manager.get_ai_response("non-existent", "Hello")
        
        assert response == "Session not found."
        assert latency == 0.0


class TestSessionState:
    """Tests for SessionState model."""

    def test_session_state_defaults(self) -> None:
        """Test default values for SessionState."""
        state = SessionState(
            session_id="test-123",
            student_code="STU-abc",
            started_at=datetime.now(timezone.utc),
        )
        
        assert state.student_grade == 5
        assert state.student_language == "Unknown"
        assert state.curriculum_outcome is None
        assert state.turn_count == 0
        assert state.is_active is True
        assert len(state.latencies) == 0
        assert len(state.conversation_history) == 0

    def test_session_state_with_context(self) -> None:
        """Test SessionState with full context."""
        state = SessionState(
            session_id="test-123",
            student_code="STU-abc",
            student_grade=3,
            student_language="Ukrainian",
            curriculum_outcome="SS-3-1-1: Communities",
            started_at=datetime.now(timezone.utc),
        )
        
        assert state.student_grade == 3
        assert state.student_language == "Ukrainian"
        assert state.curriculum_outcome is not None
        assert "Communities" in state.curriculum_outcome


class TestMockLLMDriver:
    """Tests for the MockLLMDriver."""

    @pytest.fixture
    def driver(self) -> MockLLMDriver:
        """Create a mock driver."""
        return MockLLMDriver()

    @pytest.mark.asyncio
    async def test_generate_response(self, driver: MockLLMDriver) -> None:
        """Test mock response generation."""
        context = SessionContext(
            student_code="STU-test",
            grade=5,
            primary_language="English",
        )
        
        response = await driver.generate_response("Hello", context)
        
        assert response is not None
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_response_cycling(self, driver: MockLLMDriver) -> None:
        """Test that mock responses cycle through predefined list."""
        context = SessionContext(
            student_code="STU-test",
            grade=5,
            primary_language="English",
        )
        
        responses = []
        for _ in range(6):
            resp = await driver.generate_response("Hello", context)
            responses.append(resp)
        
        # After 5 responses, should cycle back to first
        assert responses[5] == responses[0]


class TestMessageTypes:
    """Tests for WebSocket message type enum."""

    def test_client_message_types(self) -> None:
        """Test client-to-server message types."""
        assert MessageType.AUDIO_CHUNK.value == "audio_chunk"
        assert MessageType.SESSION_START.value == "session_start"
        assert MessageType.SESSION_END.value == "session_end"
        assert MessageType.USER_MESSAGE.value == "user_message"

    def test_server_message_types(self) -> None:
        """Test server-to-client message types."""
        assert MessageType.AI_AUDIO.value == "ai_audio"
        assert MessageType.AI_TEXT.value == "ai_text"
        assert MessageType.TRANSCRIPT.value == "transcript"
        assert MessageType.SESSION_READY.value == "session_ready"
        assert MessageType.SESSION_ENDED.value == "session_ended"
        assert MessageType.ERROR.value == "error"
        assert MessageType.LATENCY_UPDATE.value == "latency_update"
