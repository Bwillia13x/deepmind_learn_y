"""
Curriculum RAG - Vector Store for Alberta Program of Studies.

Provides semantic search over curriculum outcomes to enable
cultural bridging and contextual learning.
"""

import logging
from dataclasses import dataclass
from typing import Any

from ..voice_engine.multilang import (
    get_cultural_bridge_hint,
    get_language_context,
)

logger = logging.getLogger(__name__)


@dataclass
class CurriculumMatch:
    """A curriculum outcome match from vector search."""

    outcome_code: str
    subject: str
    grade: int
    outcome_text: str
    similarity_score: float
    cultural_bridge_hints: list[str] | None = None


class CurriculumVectorStore:
    """
    In-memory vector store for curriculum outcomes.

    Uses simple cosine similarity for development.
    In production, use pgvector or ChromaDB.
    """

    def __init__(self) -> None:
        self._outcomes: dict[str, dict[str, Any]] = {}
        self._embeddings: dict[str, list[float]] = {}
        self._is_initialized = False

    def add_outcome(
        self,
        outcome_code: str,
        subject: str,
        grade: int,
        outcome_text: str,
        keywords: list[str] | None = None,
        cultural_bridge_hints: list[str] | None = None,
        embedding: list[float] | None = None,
    ) -> None:
        """Add a curriculum outcome to the store."""
        self._outcomes[outcome_code] = {
            "outcome_code": outcome_code,
            "subject": subject,
            "grade": grade,
            "outcome_text": outcome_text,
            "keywords": keywords or [],
            "cultural_bridge_hints": cultural_bridge_hints or [],
        }
        if embedding:
            self._embeddings[outcome_code] = embedding

        logger.debug(f"Added curriculum outcome: {outcome_code}")

    def search(
        self,
        query: str,
        grade_filter: int | None = None,
        subject_filter: str | None = None,
        top_k: int = 3,
    ) -> list[CurriculumMatch]:
        """
        Search for relevant curriculum outcomes.

        Simple keyword matching for development.
        Production would use vector similarity.
        """
        query_lower = query.lower()
        results: list[tuple[str, float]] = []

        for code, outcome in self._outcomes.items():
            # Apply filters
            if grade_filter is not None and outcome["grade"] != grade_filter:
                continue
            if subject_filter and subject_filter.lower() not in outcome["subject"].lower():
                continue

            # Simple keyword scoring
            score = 0.0
            searchable = (
                outcome["outcome_text"].lower()
                + " "
                + " ".join(outcome["keywords"])
            )

            # Check for query terms in outcome
            query_terms = query_lower.split()
            for term in query_terms:
                if term in searchable:
                    score += 1.0

            if score > 0:
                results.append((code, score / len(query_terms)))

        # Sort by score and return top_k
        results.sort(key=lambda x: x[1], reverse=True)

        return [
            CurriculumMatch(
                outcome_code=code,
                subject=self._outcomes[code]["subject"],
                grade=self._outcomes[code]["grade"],
                outcome_text=self._outcomes[code]["outcome_text"],
                similarity_score=score,
                cultural_bridge_hints=self._outcomes[code].get("cultural_bridge_hints"),
            )
            for code, score in results[:top_k]
        ]

    def get_outcome(self, outcome_code: str) -> dict[str, Any] | None:
        """Get a specific outcome by code."""
        return self._outcomes.get(outcome_code)

    def count(self) -> int:
        """Return the number of outcomes in the store."""
        return len(self._outcomes)

    def load_from_json(self, json_path: str) -> int:
        """
        Load curriculum outcomes from a JSON file.

        Args:
            json_path: Path to the JSON file containing curriculum data.

        Returns:
            Number of outcomes loaded.
        """
        import json
        from pathlib import Path

        path = Path(json_path)
        if not path.exists():
            logger.warning(f"Curriculum JSON file not found: {json_path}")
            return 0

        try:
            with open(path) as f:
                outcomes = json.load(f)

            count = 0
            for outcome in outcomes:
                self.add_outcome(
                    outcome_code=outcome.get("outcome_code", ""),
                    subject=outcome.get("subject", ""),
                    grade=outcome.get("grade", 5),
                    outcome_text=outcome.get("outcome_text", ""),
                    keywords=outcome.get("keywords", []),
                    cultural_bridge_hints=outcome.get("cultural_bridge_hints", []),
                )
                count += 1

            logger.info(f"Loaded {count} curriculum outcomes from {json_path}")
            self._is_initialized = True
            return count

        except Exception as e:
            logger.error(f"Error loading curriculum JSON: {e}")
            return 0

    def initialize_sample_data(self) -> None:
        """
        Initialize with sample Alberta curriculum outcomes.

        This is for development. Production would load from database.
        """
        if self._is_initialized:
            return

        sample_outcomes = [
            {
                "outcome_code": "SS-5-1-1",
                "subject": "Social Studies",
                "grade": 5,
                "outcome_text": "Students will appreciate the complexity of identity in the Canadian context",
                "keywords": ["identity", "Canada", "culture", "diversity"],
                "cultural_bridge_hints": ["personal identity", "cultural heritage", "belonging"],
            },
            {
                "outcome_code": "SS-5-1-2",
                "subject": "Social Studies",
                "grade": 5,
                "outcome_text": "Students will examine historical events in the Canadian context",
                "keywords": ["history", "Canada", "events", "Confederation"],
                "cultural_bridge_hints": ["national formation", "unification", "colonial history"],
            },
            {
                "outcome_code": "SS-5-2-1",
                "subject": "Social Studies",
                "grade": 5,
                "outcome_text": "Students will examine the histories and stories of First Nations peoples",
                "keywords": ["First Nations", "Indigenous", "history", "stories"],
                "cultural_bridge_hints": ["indigenous peoples", "oral traditions", "land"],
            },
            {
                "outcome_code": "LA-5-1-1",
                "subject": "Language Arts",
                "grade": 5,
                "outcome_text": "Students will listen, speak, read and write to explore thoughts and ideas",
                "keywords": ["listening", "speaking", "reading", "writing", "communication"],
                "cultural_bridge_hints": ["expression", "storytelling", "conversation"],
            },
            {
                "outcome_code": "LA-5-2-1",
                "subject": "Language Arts",
                "grade": 5,
                "outcome_text": "Students will use strategies to generate ideas for oral and written texts",
                "keywords": ["strategies", "ideas", "oral", "written", "brainstorming"],
                "cultural_bridge_hints": ["creativity", "planning", "expression"],
            },
            {
                "outcome_code": "SCI-5-1",
                "subject": "Science",
                "grade": 5,
                "outcome_text": "Students will describe the properties of wetland ecosystems",
                "keywords": ["wetlands", "ecosystems", "water", "plants", "animals"],
                "cultural_bridge_hints": ["marshes", "water systems", "rice paddies", "deltas"],
            },
            {
                "outcome_code": "SCI-5-2",
                "subject": "Science",
                "grade": 5,
                "outcome_text": "Students will investigate weather and climate patterns",
                "keywords": ["weather", "climate", "patterns", "seasons"],
                "cultural_bridge_hints": ["monsoons", "dry seasons", "climate zones"],
            },
        ]

        for outcome in sample_outcomes:
            self.add_outcome(**outcome)

        self._is_initialized = True
        logger.info(f"Initialized curriculum store with {self.count()} outcomes")


# Global instance
_curriculum_store: CurriculumVectorStore | None = None

# Possible paths for curriculum JSON file
CURRICULUM_JSON_PATHS = [
    "scripts/curriculum_data.json",
    "../scripts/curriculum_data.json",
    "/app/scripts/curriculum_data.json",  # Docker path
    "backend/scripts/curriculum_data.json",
]


def get_curriculum_store() -> CurriculumVectorStore:
    """Get the global curriculum vector store instance."""
    global _curriculum_store
    if _curriculum_store is None:
        _curriculum_store = CurriculumVectorStore()

        # Try to load from JSON file first
        loaded = False
        for path in CURRICULUM_JSON_PATHS:
            if _curriculum_store.load_from_json(path) > 0:
                loaded = True
                break

        # Fall back to hardcoded sample data if JSON not found
        if not loaded:
            logger.info("No curriculum JSON found, using sample data")
            _curriculum_store.initialize_sample_data()

    return _curriculum_store


async def search_curriculum(
    query: str,
    grade: int | None = None,
    subject: str | None = None,
    top_k: int = 3,
) -> list[CurriculumMatch]:
    """
    Search curriculum outcomes for relevant matches.

    Convenience function for the global store.
    """
    store = get_curriculum_store()
    return store.search(query, grade_filter=grade, subject_filter=subject, top_k=top_k)


async def get_cultural_bridge(
    concept: str,
    student_background: str,
    grade: int = 5,
) -> str | None:
    """
    Generate a cultural bridge explanation for a concept.

    Connects Alberta curriculum concepts to student's cultural background.

    Args:
        concept: The curriculum concept to explain.
        student_background: Student's primary language/cultural background.
        grade: Student's grade level.

    Returns:
        A culturally-bridged explanation, or None if not available.
    """
    # Search for relevant curriculum outcomes
    matches = await search_curriculum(concept, grade=grade, top_k=1)

    if not matches:
        return None

    match = matches[0]
    hints = match.cultural_bridge_hints or []

    # Get language-specific cultural bridge hint
    lang_specific_hint = get_cultural_bridge_hint(student_background, concept)
    lang_ctx = get_language_context(student_background)

    # Build a bridge explanation with language-specific context
    bridge_parts = []

    if lang_specific_hint:
        bridge_parts.append(
            f"In {lang_ctx.language_name}, you might think of this like: {lang_specific_hint}"
        )

    if hints:
        bridge_parts.append(f"This connects to: {', '.join(hints)}")

    if bridge_parts:
        return (
            f"In the Alberta curriculum, '{concept}' relates to {match.outcome_text}. "
            + " ".join(bridge_parts)
        )

    return None


async def get_language_specific_prompt_context(
    primary_language: str,
    topic: str | None = None,
    grade: int = 5,
) -> dict[str, Any]:
    """
    Get language-specific context for system prompts.

    Args:
        primary_language: Student's home language
        topic: Optional current topic being discussed
        grade: Student's grade level

    Returns:
        Dictionary with language context for prompt building
    """
    lang_ctx = get_language_context(primary_language)

    context = {
        "language_name": lang_ctx.language_name,
        "language_code": lang_ctx.language_code,
        "greeting_native": lang_ctx.greeting_native,
        "encouragement_native": lang_ctx.encouragement_native,
        "common_difficulties": lang_ctx.common_difficulties[:3],  # Top 3
        "cultural_notes": lang_ctx.cultural_notes[:2],  # Top 2
        "alphabet_type": lang_ctx.alphabet_type,
    }

    # Add topic-specific bridge if available
    if topic:
        bridge_hint = get_cultural_bridge_hint(primary_language, topic)
        if bridge_hint:
            context["topic_bridge"] = bridge_hint

        # Also search curriculum for related outcomes
        matches = await search_curriculum(topic, grade=grade, top_k=1)
        if matches:
            context["curriculum_outcome"] = matches[0].outcome_text
            context["curriculum_hints"] = matches[0].cultural_bridge_hints

    return context
