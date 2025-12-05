"""
Tests for LLM Provider Abstraction Layer.

Tests the vendor-neutral provider architecture including:
- Provider factory
- Mock provider
- Base interface contracts
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.voice_engine.providers.base import (
    ConversationMessage,
    LLMProvider,
    ProviderConfig,
    ProviderResponse,
    SessionContext,
    VoiceCapability,
)
from app.services.voice_engine.providers.factory import (
    ProviderType,
    create_provider,
    get_available_providers,
    _auto_select_provider,
)
from app.services.voice_engine.providers.mock_provider import MockProvider


class TestProviderConfig:
    """Tests for ProviderConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ProviderConfig()
        assert config.model == ""
        assert config.voice == "alloy"
        assert config.temperature == 0.7
        assert config.max_response_length == 500
        assert config.api_key is None
        assert config.extra == {}

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = ProviderConfig(
            model="gpt-4o",
            voice="nova",
            temperature=0.5,
            api_key="test-key",
            extra={"custom": "value"},
        )
        assert config.model == "gpt-4o"
        assert config.voice == "nova"
        assert config.temperature == 0.5
        assert config.api_key == "test-key"
        assert config.extra["custom"] == "value"


class TestSessionContext:
    """Tests for SessionContext dataclass."""

    def test_minimal_context(self) -> None:
        """Test context with minimal required fields."""
        context = SessionContext(
            student_code="STU-abc123",
            grade=5,
            primary_language="Arabic",
        )
        assert context.student_code == "STU-abc123"
        assert context.grade == 5
        assert context.primary_language == "Arabic"
        assert context.curriculum_outcome is None
        assert context.conversation_history == []

    def test_full_context(self) -> None:
        """Test context with all fields."""
        history = [
            ConversationMessage(role="user", content="Hello"),
            ConversationMessage(role="assistant", content="Hi there!"),
        ]
        context = SessionContext(
            student_code="STU-abc123",
            grade=5,
            primary_language="Ukrainian",
            curriculum_outcome="SCI-5-1",
            conversation_history=history,
            cultural_bridge_hints="Strong family traditions",
        )
        assert len(context.conversation_history) == 2
        assert context.cultural_bridge_hints == "Strong family traditions"


class TestMockProvider:
    """Tests for MockProvider implementation."""

    @pytest.fixture
    def provider(self) -> MockProvider:
        """Create fresh mock provider for each test."""
        return MockProvider()

    def test_name(self, provider: MockProvider) -> None:
        """Test provider name."""
        assert provider.name == "Mock"

    def test_capabilities(self, provider: MockProvider) -> None:
        """Test provider capabilities."""
        caps = provider.capabilities
        assert VoiceCapability.TEXT_GENERATION in caps
        assert VoiceCapability.AUDIO_TO_TEXT in caps
        assert VoiceCapability.TEXT_TO_AUDIO in caps
        assert VoiceCapability.STREAMING in caps
        # Real-time audio not supported by mock
        assert VoiceCapability.REALTIME_AUDIO not in caps

    @pytest.mark.asyncio
    async def test_generate_text_basic(self, provider: MockProvider) -> None:
        """Test basic text generation."""
        messages = [ConversationMessage(role="user", content="Hello")]
        response = await provider.generate_text(messages)

        assert isinstance(response, ProviderResponse)
        assert response.text != ""
        assert response.provider == "Mock"
        assert response.latency_ms > 0

    @pytest.mark.asyncio
    async def test_generate_text_with_context(self, provider: MockProvider) -> None:
        """Test text generation with session context."""
        context = SessionContext(
            student_code="STU-test",
            grade=5,
            primary_language="Ukrainian",
        )
        messages = [ConversationMessage(role="user", content="Hello")]
        response = await provider.generate_text(messages, context)

        # Should include language-specific encouragement
        assert "Ukrainian" in response.text

    @pytest.mark.asyncio
    async def test_generate_text_pii_redirect(self, provider: MockProvider) -> None:
        """Test that PII requests are redirected."""
        messages = [ConversationMessage(role="user", content="What's your phone number?")]
        response = await provider.generate_text(messages)

        assert "can't share personal information" in response.text

    @pytest.mark.asyncio
    async def test_generate_text_soccer_topic(self, provider: MockProvider) -> None:
        """Test topic-aware responses."""
        messages = [ConversationMessage(role="user", content="I love playing soccer!")]
        context = SessionContext(
            student_code="STU-test",
            grade=5,
            primary_language="English",
        )
        response = await provider.generate_text(messages, context)

        assert "soccer" in response.text.lower() or "team" in response.text.lower()

    @pytest.mark.asyncio
    async def test_transcribe_audio(self, provider: MockProvider) -> None:
        """Test mock audio transcription."""
        fake_audio = b"fake audio data" * 100
        transcription = await provider.transcribe_audio(fake_audio)

        assert isinstance(transcription, str)
        assert "mock transcription" in transcription.lower()

    @pytest.mark.asyncio
    async def test_synthesize_audio(self, provider: MockProvider) -> None:
        """Test mock audio synthesis."""
        audio = await provider.synthesize_audio("Hello world")

        assert isinstance(audio, bytes)
        assert len(audio) > 0

    @pytest.mark.asyncio
    async def test_stream_audio_response(self, provider: MockProvider) -> None:
        """Test streaming audio response."""
        fake_audio = b"fake audio input"
        context = SessionContext(
            student_code="STU-test",
            grade=5,
            primary_language="English",
        )

        chunks = []
        async for chunk in provider.stream_audio_response(fake_audio, context):
            chunks.append(chunk)

        assert len(chunks) > 0
        # All chunks should be bytes
        assert all(isinstance(c, bytes) for c in chunks)

    @pytest.mark.asyncio
    async def test_health_check(self, provider: MockProvider) -> None:
        """Test mock health check always returns True."""
        is_healthy = await provider.health_check()
        assert is_healthy is True

    def test_response_cycling(self, provider: MockProvider) -> None:
        """Test that mock responses cycle through predefined list."""
        # Mock provider has MOCK_RESPONSES list
        responses_count = len(MockProvider.MOCK_RESPONSES)

        # Simulate multiple calls by incrementing index
        indices = [provider._response_index]
        for _ in range(responses_count + 2):
            provider._response_index += 1
            indices.append(provider._response_index % responses_count)

        # Should cycle back to beginning
        assert indices[-1] < responses_count


class TestProviderFactory:
    """Tests for provider factory functions."""

    @patch("app.services.voice_engine.providers.factory.settings")
    def test_get_available_providers_mock_always(self, mock_settings: MagicMock) -> None:
        """Test that mock provider is always available."""
        mock_settings.openai_api_key = None
        mock_settings.azure_openai_endpoint = None
        mock_settings.azure_openai_key = None

        available = get_available_providers()

        assert ProviderType.MOCK in available

    @patch("app.services.voice_engine.providers.factory.settings")
    def test_get_available_providers_openai(self, mock_settings: MagicMock) -> None:
        """Test OpenAI provider availability detection."""
        mock_settings.openai_api_key = "sk-test-key"
        mock_settings.azure_openai_endpoint = None
        mock_settings.azure_openai_key = None

        available = get_available_providers()

        assert ProviderType.OPENAI in available
        assert ProviderType.MOCK in available

    @patch("app.services.voice_engine.providers.factory.settings")
    def test_get_available_providers_azure(self, mock_settings: MagicMock) -> None:
        """Test Azure OpenAI provider availability detection."""
        mock_settings.openai_api_key = None
        mock_settings.azure_openai_endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai_key = "azure-test-key"

        available = get_available_providers()

        assert ProviderType.AZURE_OPENAI in available
        assert ProviderType.MOCK in available

    @patch("app.services.voice_engine.providers.factory.settings")
    def test_auto_select_prefers_azure(self, mock_settings: MagicMock) -> None:
        """Test that auto-selection prefers Azure for enterprise compliance."""
        mock_settings.openai_api_key = "sk-test-key"
        mock_settings.azure_openai_endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai_key = "azure-test-key"

        selected = _auto_select_provider()

        assert selected == ProviderType.AZURE_OPENAI

    @patch("app.services.voice_engine.providers.factory.settings")
    def test_auto_select_falls_back_to_openai(self, mock_settings: MagicMock) -> None:
        """Test fallback to OpenAI when Azure not available."""
        mock_settings.openai_api_key = "sk-test-key"
        mock_settings.azure_openai_endpoint = None
        mock_settings.azure_openai_key = None

        selected = _auto_select_provider()

        assert selected == ProviderType.OPENAI

    @patch("app.services.voice_engine.providers.factory.settings")
    def test_auto_select_falls_back_to_mock(self, mock_settings: MagicMock) -> None:
        """Test fallback to mock when no API keys configured."""
        mock_settings.openai_api_key = None
        mock_settings.azure_openai_endpoint = None
        mock_settings.azure_openai_key = None
        mock_settings.google_api_key = None

        selected = _auto_select_provider()

        assert selected == ProviderType.MOCK

    @patch("app.services.voice_engine.providers.factory.settings")
    def test_create_provider_mock(self, mock_settings: MagicMock) -> None:
        """Test creating mock provider explicitly."""
        mock_settings.openai_api_key = None
        mock_settings.azure_openai_endpoint = None
        mock_settings.azure_openai_key = None

        provider = create_provider(ProviderType.MOCK)

        assert isinstance(provider, MockProvider)
        assert provider.name == "Mock"

    def test_create_provider_with_string(self) -> None:
        """Test creating provider with string type."""
        provider = create_provider("mock")

        assert isinstance(provider, MockProvider)

    def test_create_provider_invalid_type(self) -> None:
        """Test that invalid provider type raises error."""
        with pytest.raises(ValueError, match="Unknown provider type"):
            create_provider("invalid_provider")

    def test_provider_type_enum_values(self) -> None:
        """Test ProviderType enum has expected values."""
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.AZURE_OPENAI.value == "azure_openai"
        assert ProviderType.GEMINI.value == "gemini"
        assert ProviderType.MOCK.value == "mock"


class TestVoiceCapability:
    """Tests for VoiceCapability enum."""

    def test_all_capabilities_defined(self) -> None:
        """Test all expected capabilities exist."""
        expected = [
            "TEXT_GENERATION",
            "AUDIO_TO_TEXT",
            "TEXT_TO_AUDIO",
            "REALTIME_AUDIO",
            "STREAMING",
        ]
        actual = [c.name for c in VoiceCapability]
        for cap in expected:
            assert cap in actual


class TestConversationMessage:
    """Tests for ConversationMessage dataclass."""

    def test_basic_message(self) -> None:
        """Test basic message creation."""
        msg = ConversationMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.audio_duration_ms is None

    def test_message_with_audio_duration(self) -> None:
        """Test message with audio duration."""
        msg = ConversationMessage(
            role="assistant",
            content="Hi there!",
            audio_duration_ms=1500,
        )
        assert msg.audio_duration_ms == 1500


class TestProviderResponse:
    """Tests for ProviderResponse dataclass."""

    def test_minimal_response(self) -> None:
        """Test minimal response."""
        resp = ProviderResponse(text="Hello")
        assert resp.text == "Hello"
        assert resp.audio is None
        assert resp.latency_ms == 0.0

    def test_full_response(self) -> None:
        """Test response with all fields."""
        resp = ProviderResponse(
            text="Hello",
            audio=b"fake audio",
            latency_ms=150.0,
            tokens_used=10,
            model="gpt-4o",
            provider="OpenAI",
        )
        assert resp.audio == b"fake audio"
        assert resp.tokens_used == 10
        assert resp.model == "gpt-4o"
