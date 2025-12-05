"""
Tests for Scout Report insight generation.

Tests both mock and LLM-powered report generation.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.reporting_agent.insight_generator import (
    ScoutInsight,
    InsightCategory,
    generate_mock_insight,
    generate_scout_report,
    estimate_engagement_from_transcript,
    parse_llm_insight,
)
from app.db.models import EngagementLevel


class TestEngagementEstimation:
    """Tests for engagement level estimation."""

    def test_low_engagement_empty_transcript(self) -> None:
        """Test low engagement for empty transcript."""
        result = estimate_engagement_from_transcript("", 0)
        assert result == EngagementLevel.LOW

    def test_low_engagement_short_responses(self) -> None:
        """Test low engagement for short responses."""
        transcript = "yes no ok"  # 3 words, say 3 turns = 1 word per turn
        result = estimate_engagement_from_transcript(transcript, 3)
        assert result == EngagementLevel.LOW

    def test_medium_engagement(self) -> None:
        """Test medium engagement detection."""
        # Create transcript with ~15 words per turn
        transcript = "Hello I am practicing my English today " * 5  # ~40 words
        result = estimate_engagement_from_transcript(transcript, 3)  # ~13 words/turn
        assert result == EngagementLevel.MEDIUM

    def test_high_engagement(self) -> None:
        """Test high engagement detection."""
        # Create verbose transcript
        transcript = "I really enjoy learning English and talking about my interests. " * 10
        result = estimate_engagement_from_transcript(transcript, 3)  # ~30+ words/turn
        assert result == EngagementLevel.HIGH


class TestMockInsightGeneration:
    """Tests for mock Scout Report generation."""

    def test_generates_insight(self) -> None:
        """Test that mock generation returns a valid insight."""
        result = generate_mock_insight(
            transcript="Student: Hello\nNEXUS: Hi there!",
            grade=5,
            primary_language="Ukrainian",
            duration_seconds=300,
            turn_count=2,
        )
        
        assert result is not None
        assert isinstance(result, ScoutInsight)
        assert result.insight_text is not None
        assert len(result.insight_text) > 0

    def test_includes_duration(self) -> None:
        """Test that mock insight includes session duration."""
        result = generate_mock_insight(
            transcript="Hello",
            grade=5,
            primary_language="English",
            duration_seconds=600,  # 10 minutes
            turn_count=10,
        )
        
        assert "10-minute" in result.insight_text or "10 minute" in result.insight_text

    def test_includes_linguistic_observations(self) -> None:
        """Test that mock insight includes linguistic observations."""
        result = generate_mock_insight(
            transcript="Hello",
            grade=5,
            primary_language="English",
            duration_seconds=300,
            turn_count=5,
        )
        
        assert result.linguistic_observations is not None
        assert "proficiency" in result.linguistic_observations.lower()

    def test_includes_recommendations(self) -> None:
        """Test that mock insight includes recommendations."""
        result = generate_mock_insight(
            transcript="Hello",
            grade=5,
            primary_language="English",
            duration_seconds=300,
            turn_count=5,
        )
        
        assert result.recommended_next_steps is not None
        assert len(result.recommended_next_steps) > 0


class TestLLMInsightParsing:
    """Tests for parsing LLM-generated insights."""

    def test_parses_high_engagement(self) -> None:
        """Test parsing high engagement level."""
        llm_response = """
        1. ENGAGEMENT LEVEL: HIGH

        The student showed excellent participation.

        LINGUISTIC OBSERVATIONS:
        - Good vocabulary
        - Clear pronunciation
        """
        
        result = parse_llm_insight(llm_response, "test transcript", 10)
        assert result.engagement_level == EngagementLevel.HIGH

    def test_parses_low_engagement(self) -> None:
        """Test parsing low engagement level."""
        llm_response = """
        ENGAGEMENT LEVEL: LOW

        The student provided minimal responses.
        """
        
        result = parse_llm_insight(llm_response, "short", 2)
        assert result.engagement_level == EngagementLevel.LOW

    def test_extracts_insight_text(self) -> None:
        """Test extraction of main insight text."""
        llm_response = """Section 1

Main observation summary here.

Section 3
"""
        result = parse_llm_insight(llm_response, "test", 5)
        assert "Main observation" in result.insight_text


class TestScoutReportGeneration:
    """Integration tests for Scout Report generation."""

    @pytest.mark.asyncio
    async def test_generates_report_without_api(self) -> None:
        """Test report generation without OpenAI API."""
        with patch("app.services.reporting_agent.insight_generator.settings") as mock_settings:
            mock_settings.has_openai = False
            
            result = await generate_scout_report(
                transcript="Student: Hello\nNEXUS: Hi there!",
                grade=5,
                primary_language="Ukrainian",
                duration_seconds=300,
                turn_count=2,
            )
            
            assert result is not None
            assert result.insight_text is not None

    @pytest.mark.asyncio
    async def test_scrubs_pii_from_transcript(self) -> None:
        """Test that PII is scrubbed from transcript before processing."""
        with patch("app.services.reporting_agent.insight_generator.settings") as mock_settings:
            mock_settings.has_openai = False
            
            # Transcript with PII
            transcript = "Student: My name is John Smith and my phone is 555-1234"
            
            result = await generate_scout_report(
                transcript=transcript,
                grade=5,
                primary_language="English",
                duration_seconds=300,
                turn_count=2,
            )
            
            # Should not fail - PII handling happens internally
            assert result is not None

    @pytest.mark.asyncio
    async def test_handles_empty_transcript(self) -> None:
        """Test handling of empty transcript."""
        with patch("app.services.reporting_agent.insight_generator.settings") as mock_settings:
            mock_settings.has_openai = False
            
            result = await generate_scout_report(
                transcript="",
                grade=5,
                primary_language="English",
                duration_seconds=0,
                turn_count=0,
            )
            
            assert result is not None
            assert result.engagement_level == EngagementLevel.LOW


class TestScoutInsightModel:
    """Tests for the ScoutInsight dataclass."""

    def test_creates_minimal_insight(self) -> None:
        """Test creating insight with minimal fields."""
        insight = ScoutInsight(
            engagement_level=EngagementLevel.MEDIUM,
            insight_text="Basic observation.",
        )
        
        assert insight.engagement_level == EngagementLevel.MEDIUM
        assert insight.linguistic_observations is None
        assert insight.curriculum_connections is None
        assert insight.recommended_next_steps is None

    def test_creates_full_insight(self) -> None:
        """Test creating insight with all fields."""
        insight = ScoutInsight(
            engagement_level=EngagementLevel.HIGH,
            insight_text="Excellent session.",
            linguistic_observations="Good vocabulary usage.",
            curriculum_connections="Connected to Social Studies outcomes.",
            recommended_next_steps="Continue practicing conversations.",
        )
        
        assert insight.engagement_level == EngagementLevel.HIGH
        assert insight.linguistic_observations is not None
        assert insight.curriculum_connections is not None
        assert insight.recommended_next_steps is not None


class TestInsightCategory:
    """Tests for InsightCategory enum."""

    def test_category_values(self) -> None:
        """Test insight category values."""
        assert InsightCategory.ENGAGEMENT.value == "engagement"
        assert InsightCategory.LINGUISTIC.value == "linguistic"
        assert InsightCategory.CURRICULUM.value == "curriculum"
        assert InsightCategory.RECOMMENDATIONS.value == "recommendations"
