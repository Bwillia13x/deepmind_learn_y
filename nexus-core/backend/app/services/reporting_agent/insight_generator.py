"""
Scout Report Insight Generator.

Generates qualitative insights from oracy session transcripts for teachers.
This is NOT a grade - it's a "Draft 0" to reduce teacher admin burden.
"""

import logging
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings
from app.core.privacy_guard import scrub_pii
from app.db.models import EngagementLevel

logger = logging.getLogger(__name__)


class InsightCategory(str, Enum):
    """Categories of insights in a Scout Report."""

    ENGAGEMENT = "engagement"
    LINGUISTIC = "linguistic"
    CURRICULUM = "curriculum"
    RECOMMENDATIONS = "recommendations"


@dataclass
class ScoutInsight:
    """A complete Scout Report insight package."""

    engagement_level: EngagementLevel
    insight_text: str
    linguistic_observations: str | None = None
    curriculum_connections: str | None = None
    recommended_next_steps: str | None = None


INSIGHT_GENERATION_PROMPT = """Analyze this student conversation transcript and generate a brief teacher insight report.

TRANSCRIPT:
{transcript}

CONTEXT:
- Student Grade: {grade}
- Primary Language: {primary_language}
- Session Duration: {duration_seconds} seconds
- Conversation Turns: {turn_count}

Generate a concise report with these sections:

1. ENGAGEMENT LEVEL (choose one: LOW, MEDIUM, or HIGH)
Based on response length, topic engagement, and participation.

2. OBSERVATION SUMMARY (2-3 sentences)
What did you notice about the student's participation today?

3. LINGUISTIC OBSERVATIONS (2-3 bullet points)
- Specific pronunciation patterns
- Grammar usage patterns
- Vocabulary strengths or areas for growth

4. CURRICULUM CONNECTIONS (1-2 sentences, if applicable)
How did the conversation connect to Alberta curriculum outcomes?

5. RECOMMENDED NEXT STEPS (2-3 bullet points)
Specific, actionable suggestions for the teacher.

Keep the tone professional and supportive. This is a draft for the teacher to refine.
Focus on strengths while noting growth areas."""


def estimate_engagement_from_transcript(transcript: str, turn_count: int) -> EngagementLevel:
    """
    Estimate engagement level from transcript content.

    Simple heuristics for when LLM is not available.
    """
    if not transcript or turn_count == 0:
        return EngagementLevel.LOW

    words_per_turn = len(transcript.split()) / max(turn_count, 1)

    if words_per_turn > 20:
        return EngagementLevel.HIGH
    elif words_per_turn > 10:
        return EngagementLevel.MEDIUM
    else:
        return EngagementLevel.LOW


def generate_mock_insight(
    transcript: str,
    grade: int,
    primary_language: str,
    duration_seconds: int,
    turn_count: int,
) -> ScoutInsight:
    """
    Generate a mock Scout Report insight.

    Used when LLM is not available. Provides structured placeholder content.
    """
    engagement = estimate_engagement_from_transcript(transcript, turn_count)

    return ScoutInsight(
        engagement_level=engagement,
        insight_text=(
            f"Student participated in a {duration_seconds // 60}-minute oracy session "
            f"with {turn_count} conversation turns. "
            f"Engagement appeared {engagement.value} based on response patterns. "
            f"Further review of transcript recommended for detailed assessment."
        ),
        linguistic_observations=(
            "• Response patterns indicate developing English proficiency\n"
            "• Sentence structure complexity appropriate for grade level\n"
            "• Consider focused practice on verbal fluency"
        ),
        curriculum_connections=(
            "Session covered conversational English practice. "
            "Connection to specific curriculum outcomes pending review."
        ),
        recommended_next_steps=(
            "• Review transcript for specific language patterns\n"
            "• Consider vocabulary building activities\n"
            "• Continue regular oracy practice sessions"
        ),
    )


async def generate_scout_report(
    transcript: str,
    grade: int = 5,
    primary_language: str = "Unknown",
    duration_seconds: int = 0,
    turn_count: int = 0,
) -> ScoutInsight:
    """
    Generate a Scout Report insight from a session transcript.

    Uses LLM when available, falls back to rule-based generation.

    Args:
        transcript: The PII-scrubbed session transcript.
        grade: Student's grade level.
        primary_language: Student's primary language.
        duration_seconds: Session duration.
        turn_count: Number of conversation turns.

    Returns:
        ScoutInsight with all fields populated.
    """
    # Ensure transcript is scrubbed (defense in depth)
    clean_transcript = scrub_pii(transcript)

    if not settings.has_openai:
        logger.info("Generating mock Scout Report (no LLM configured)")
        return generate_mock_insight(
            clean_transcript,
            grade,
            primary_language,
            duration_seconds,
            turn_count,
        )

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)

        prompt = INSIGHT_GENERATION_PROMPT.format(
            transcript=clean_transcript,
            grade=grade,
            primary_language=primary_language,
            duration_seconds=duration_seconds,
            turn_count=turn_count,
        )

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an educational assessment assistant helping teachers "
                        "understand EAL student progress. Be concise, professional, and supportive."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=800,
        )

        content = response.choices[0].message.content or ""

        # Parse the response into structured fields
        return parse_llm_insight(content, clean_transcript, turn_count)

    except Exception as e:
        logger.error(f"Error generating Scout Report: {e}")
        return generate_mock_insight(
            clean_transcript,
            grade,
            primary_language,
            duration_seconds,
            turn_count,
        )


def parse_llm_insight(llm_response: str, transcript: str, turn_count: int) -> ScoutInsight:
    """
    Parse LLM response into structured ScoutInsight.

    Extracts sections from the LLM's formatted response.
    """
    # Default engagement estimation
    engagement = estimate_engagement_from_transcript(transcript, turn_count)

    # Try to extract engagement level from response
    response_lower = llm_response.lower()
    if "high" in response_lower[:200]:
        engagement = EngagementLevel.HIGH
    elif "low" in response_lower[:200]:
        engagement = EngagementLevel.LOW
    else:
        engagement = EngagementLevel.MEDIUM

    # Simple section extraction (in production, use more robust parsing)
    sections = llm_response.split("\n\n")

    insight_text = sections[1] if len(sections) > 1 else llm_response[:300]
    linguistic = sections[2] if len(sections) > 2 else None
    curriculum = sections[3] if len(sections) > 3 else None
    recommendations = sections[4] if len(sections) > 4 else None

    return ScoutInsight(
        engagement_level=engagement,
        insight_text=insight_text.strip(),
        linguistic_observations=linguistic.strip() if linguistic else None,
        curriculum_connections=curriculum.strip() if curriculum else None,
        recommended_next_steps=recommendations.strip() if recommendations else None,
    )
