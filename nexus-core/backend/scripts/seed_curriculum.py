#!/usr/bin/env python3
"""
Seed Curriculum Data Script

Populates the vector store with sample Alberta Program of Studies outcomes
for the NEXUS Curriculum RAG system.

Usage:
    poetry run python scripts/seed_curriculum.py
"""

import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Sample Alberta Curriculum Outcomes
# Based on Alberta Program of Studies for Grades 4-6 (EAL focus)
# Source: Alberta Education - https://www.alberta.ca/programs-of-study

CURRICULUM_OUTCOMES: list[dict] = [
    # === English Language Arts ===
    {
        "outcome_code": "ELA-4-1.1",
        "subject": "English Language Arts",
        "grade": 4,
        "outcome_text": "Express ideas and develop understanding by listening, speaking, reading, writing, viewing, and representing.",
        "keywords": ["speaking", "listening", "communication", "express", "ideas"],
        "cultural_bridge_hints": [
            "Connect to storytelling traditions from student's culture",
            "Use familiar topics from home life as conversation starters",
        ],
    },
    {
        "outcome_code": "ELA-5-2.1",
        "subject": "English Language Arts",
        "grade": 5,
        "outcome_text": "Use oral language to clarify and extend understanding of ideas and information.",
        "keywords": ["oral", "clarify", "understand", "information", "discussion"],
        "cultural_bridge_hints": [
            "Encourage students to explain concepts using examples from their background",
            "Value multilingual explanations as a bridge to understanding",
        ],
    },
    {
        "outcome_code": "ELA-6-3.1",
        "subject": "English Language Arts",
        "grade": 6,
        "outcome_text": "Plan and focus: identify and analyze factors that affect communication situations.",
        "keywords": ["communication", "planning", "analyze", "factors", "audience"],
        "cultural_bridge_hints": [
            "Discuss how communication styles differ across cultures",
            "Explore formal vs. informal language in different contexts",
        ],
    },
    # === Social Studies ===
    {
        "outcome_code": "SS-4-4.1",
        "subject": "Social Studies",
        "grade": 4,
        "outcome_text": "Alberta: A Sense of the Land - Appreciate the physical geography and peoples of Alberta.",
        "keywords": ["Alberta", "geography", "land", "peoples", "landscape", "mountains", "prairies"],
        "cultural_bridge_hints": [
            "Compare Alberta's geography to landscapes in student's country of origin",
            "Connect Indigenous peoples' relationship with land to similar concepts in other cultures",
        ],
    },
    {
        "outcome_code": "SS-5-5.1",
        "subject": "Social Studies",
        "grade": 5,
        "outcome_text": "Canada: Stories of Canada - How stories, history and ways of life of diverse peoples contribute to the vitality of Canada.",
        "keywords": ["Canada", "stories", "history", "diverse", "peoples", "heritage", "Confederation"],
        "cultural_bridge_hints": [
            "Draw parallels between Canada's formation and nation-building in student's heritage country",
            "Connect immigration stories to student's family journey",
            "Use the concept of 'coming together' from different backgrounds as a bridge",
        ],
    },
    {
        "outcome_code": "SS-6-6.2",
        "subject": "Social Studies",
        "grade": 6,
        "outcome_text": "Citizens Participating in Decision Making - Recognize the responsibilities of citizenship.",
        "keywords": ["citizenship", "democracy", "participation", "voting", "rights", "responsibilities"],
        "cultural_bridge_hints": [
            "Compare democratic systems in Canada with governance in student's country of origin",
            "Discuss concepts of community participation across cultures",
        ],
    },
    # === Science ===
    {
        "outcome_code": "SCI-4-7",
        "subject": "Science",
        "grade": 4,
        "outcome_text": "Wetland Ecosystems - Analyze a local wetland ecosystem and the human impacts on it.",
        "keywords": ["wetland", "ecosystem", "environment", "habitat", "water", "plants", "animals"],
        "cultural_bridge_hints": [
            "Connect wetlands to water ecosystems familiar to the student (rivers, lakes, rice paddies)",
            "Discuss environmental stewardship practices from different cultures",
        ],
    },
    {
        "outcome_code": "SCI-5-9",
        "subject": "Science",
        "grade": 5,
        "outcome_text": "Weather Watch - Identify patterns in weather and understand how data is collected.",
        "keywords": ["weather", "patterns", "seasons", "temperature", "precipitation", "climate"],
        "cultural_bridge_hints": [
            "Compare Alberta's seasons with climate patterns from student's country of origin",
            "Discuss traditional weather knowledge from different cultures",
        ],
    },
    {
        "outcome_code": "SCI-6-4",
        "subject": "Science",
        "grade": 6,
        "outcome_text": "Sky Science - Observe and explain astronomical phenomena.",
        "keywords": ["space", "planets", "stars", "moon", "sun", "solar system", "astronomy"],
        "cultural_bridge_hints": [
            "Connect to astronomy traditions and star names from student's culture",
            "Discuss moon phases and their cultural significance across different traditions",
        ],
    },
    # === Mathematics ===
    {
        "outcome_code": "MATH-4-N1",
        "subject": "Mathematics",
        "grade": 4,
        "outcome_text": "Develop number sense: represent and describe whole numbers to 10,000.",
        "keywords": ["numbers", "counting", "place value", "thousands", "number sense"],
        "cultural_bridge_hints": [
            "Use familiar number contexts (currency, populations) from student's background",
            "Explore number systems and counting traditions from different cultures",
        ],
    },
    {
        "outcome_code": "MATH-5-SS1",
        "subject": "Mathematics",
        "grade": 5,
        "outcome_text": "Describe and compare 3-D objects and 2-D shapes.",
        "keywords": ["shapes", "geometry", "3D", "2D", "objects", "compare"],
        "cultural_bridge_hints": [
            "Connect shapes to architecture and art from student's culture",
            "Use familiar objects from student's daily life as shape examples",
        ],
    },
    {
        "outcome_code": "MATH-6-PR1",
        "subject": "Mathematics",
        "grade": 6,
        "outcome_text": "Relate improper fractions, mixed numbers, decimals and percents.",
        "keywords": ["fractions", "decimals", "percent", "numbers", "conversion"],
        "cultural_bridge_hints": [
            "Use cooking measurements and recipes from student's cuisine",
            "Connect percentages to real-world contexts (discounts, sports statistics)",
        ],
    },
]


def save_curriculum_json(outcomes: list[dict], output_path: Path) -> None:
    """Save curriculum outcomes to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(outcomes, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(outcomes)} curriculum outcomes to {output_path}")


def seed_vector_store() -> None:
    """
    Seed the curriculum vector store with sample outcomes.
    
    This function initializes the in-memory vector store with curriculum data.
    In production, this would use pgvector or ChromaDB with real embeddings.
    """
    # Import here to avoid circular imports and allow standalone script usage
    try:
        from app.services.curriculum_rag.vector import CurriculumVectorStore, get_curriculum_store
        
        store = get_curriculum_store()
        
        for outcome in CURRICULUM_OUTCOMES:
            store.add_outcome(
                outcome_code=outcome["outcome_code"],
                subject=outcome["subject"],
                grade=outcome["grade"],
                outcome_text=outcome["outcome_text"],
                keywords=outcome.get("keywords"),
                cultural_bridge_hints=outcome.get("cultural_bridge_hints"),
            )
        
        logger.info(f"Seeded vector store with {len(CURRICULUM_OUTCOMES)} curriculum outcomes")
        
        # Test search
        results = store.search("wetland ecosystem", grade_filter=4, top_k=3)
        logger.info(f"Test search found {len(results)} results")
        for result in results:
            logger.info(f"  - {result.outcome_code}: {result.outcome_text[:50]}...")
            
    except ImportError as e:
        logger.warning(f"Could not import vector store modules: {e}")
        logger.info("Saving curriculum data to JSON file instead...")
        
        # Fallback: save to JSON for later import
        output_path = Path(__file__).parent / "curriculum_data.json"
        save_curriculum_json(CURRICULUM_OUTCOMES, output_path)


def main() -> None:
    """Main entry point for curriculum seeding script."""
    logger.info("=" * 60)
    logger.info("NEXUS Curriculum Seeding Script")
    logger.info("=" * 60)
    
    logger.info(f"Loading {len(CURRICULUM_OUTCOMES)} Alberta curriculum outcomes...")
    
    # Save to JSON first (useful for debugging and backup)
    scripts_dir = Path(__file__).parent
    json_path = scripts_dir / "curriculum_data.json"
    save_curriculum_json(CURRICULUM_OUTCOMES, json_path)
    
    # Attempt to seed vector store
    seed_vector_store()
    
    logger.info("=" * 60)
    logger.info("Curriculum seeding complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
